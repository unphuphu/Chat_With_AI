"""Hội thoại và đặt câu hỏi (BLUEPRINT ALG-08, DD-06; US-012…US-018, US-020, US-027)."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from app.infra.circuit import CircuitOpen
from app.infra.db import Conn, Database
from app.infra.logging import get_logger
from app.infra.settings import Settings
from app.modules.audit.service import record_audit
from app.modules.common.errors import AppError
from app.modules.events.analytics import record_event
from app.modules.identity.domain import SessionContext
from app.modules.qa.answerer import AnswerDraft, Answerer, AnswerTimeout
from app.modules.retrieval.service import RetrievalService
from app.ports.embedding import EmbeddingUnavailable
from app.ports.llm import LlmError, LlmTimeout

log = get_logger("qa")


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


class QAService:
    def __init__(self, db: Database, retrieval: RetrievalService, answerer: Answerer, settings: Settings) -> None:
        self._db, self._retrieval, self._answerer, self._s = db, retrieval, answerer, settings

    # ------------------------------------------------------------------ conversation
    async def current_conversation(self, ctx: SessionContext) -> dict[str, Any]:
        ws = ctx.workspace_id
        async with self._db.tx("app_api", ws) as conn:
            conv_id = await self._get_or_create(conn, ctx)
            cur = await conn.execute(
                """SELECT id, client_request_id, question, status, answer, error_code, created_at, updated_at
                   FROM message WHERE conversation_id = %s ORDER BY created_at""", (conv_id,))
            msgs = await cur.fetchall()
            cites = await self._citations(conn, [m["id"] for m in msgs])
        out = []
        now = datetime.now(UTC)
        for m in msgs:
            status = m["status"]
            error_code = m["error_code"]
            if status == "PENDING" and now - m["updated_at"] > timedelta(seconds=self._s.answer_budget_s + 5):
                status, error_code = "FAILED", "ai_timeout"
            out.append({"message_id": str(m["id"]), "client_request_id": str(m["client_request_id"]),
                        "question": m["question"], "status": status, "answer": m["answer"],
                        "citations": cites.get(m["id"], []), "error_code": error_code,
                        "created_at": _iso(m["created_at"])})
        return {"id": str(conv_id), "messages": out}

    @staticmethod
    async def _get_or_create(conn: Conn, ctx: SessionContext) -> UUID:
        cur = await conn.execute("SELECT id FROM conversation WHERE session_id = %s ORDER BY created_at LIMIT 1",
                                 (ctx.session_id,))
        row = await cur.fetchone()
        if row:
            return row["id"]  # type: ignore[no-any-return]
        cur = await conn.execute("INSERT INTO conversation(session_id, workspace_id) VALUES (%s, %s) RETURNING id",
                                 (ctx.session_id, ctx.workspace_id))
        return (await cur.fetchone())["id"]  # type: ignore[index,no-any-return]

    @staticmethod
    async def _citations(conn: Conn, message_ids: list[UUID]) -> dict[UUID, list[dict[str, Any]]]:
        if not message_ids:
            return {}
        cur = await conn.execute(
            """SELECT c.message_id, c.ordinal, c.document_id, c.document_name_snapshot, c.page_number,
                      (d.deleted_at IS NOT NULL) AS deleted
               FROM citation c JOIN document d ON d.id = c.document_id
               WHERE c.message_id = ANY(%s) ORDER BY c.ordinal""", (message_ids,))
        out: dict[UUID, list[dict[str, Any]]] = {}
        for r in await cur.fetchall():
            out.setdefault(r["message_id"], []).append({
                "ordinal": r["ordinal"], "document_id": str(r["document_id"]),
                "document_name": r["document_name_snapshot"], "page_number": r["page_number"],
                "deleted": bool(r["deleted"])})
        return out

    # ------------------------------------------------------------------ ALG-08 ask
    async def ask(self, ctx: SessionContext, conversation_id: UUID, client_request_id: UUID, question: str,
                  request_id: str | None = None) -> dict[str, Any]:
        t0 = time.monotonic()
        question = question.strip()
        if not question:
            raise AppError(422, "empty_question")
        if len(question) > self._s.question_max_chars:
            raise AppError(422, "question_too_long", f"Câu hỏi tối đa {self._s.question_max_chars} ký tự.")
        ws = ctx.workspace_id
        async with self._db.tx("app_api", ws) as conn:
            cur = await conn.execute("SELECT session_id FROM conversation WHERE id = %s", (conversation_id,))
            conv = await cur.fetchone()
            if conv is None or conv["session_id"] != ctx.session_id:
                raise AppError(404, "not_found")
            cur = await conn.execute("SELECT count(*) AS n FROM document WHERE status = 'READY' AND deleted_at IS NULL")
            ready = int((await cur.fetchone())["n"])  # type: ignore[index]
            if ready == 0:
                raise AppError(409, "no_ready_documents", "Cần ít nhất một tài liệu Sẵn sàng để bắt đầu hỏi.")
            cur = await conn.execute(
                """INSERT INTO message(conversation_id, workspace_id, client_request_id, question, status)
                   VALUES (%s, %s, %s, %s, 'PENDING')
                   ON CONFLICT (conversation_id, client_request_id) DO NOTHING RETURNING id""",
                (conversation_id, ws, client_request_id, question))
            row = await cur.fetchone()
            if row is not None:
                message_id: UUID = row["id"]
                attempt = 1
            else:
                cur = await conn.execute(
                    """SELECT id, question, status, error_code, updated_at, attempt FROM message
                       WHERE conversation_id = %s AND client_request_id = %s FOR UPDATE""",
                    (conversation_id, client_request_id))
                m = await cur.fetchone()
                assert m is not None
                if m["question"] != question:
                    raise AppError(422, "idempotency_mismatch")
                message_id = m["id"]
                stale = datetime.now(UTC) - m["updated_at"] > timedelta(seconds=self._s.answer_budget_s + 5)
                if m["status"] in ("ANSWERED", "INSUFFICIENT"):
                    stored = True
                elif m["status"] == "PENDING" and not stale:
                    raise AppError(409, "request_in_progress")
                else:
                    stored = False
                    attempt = m["attempt"] + 1
                    await conn.execute("UPDATE message SET status = 'PENDING', error_code = NULL, attempt = %s "
                                       "WHERE id = %s", (attempt, message_id))
                    await record_event(conn, "question_retried",
                                       {"message_id": message_id, "previous_error_code": m["error_code"]},
                                       user_id=ctx.user_id, key=self._s.actor_hash_key)
                if stored:
                    return await self._stored_answer(conn, message_id, client_request_id)
            await record_audit(conn, "question_asked", actor_id=ctx.user_id, workspace_id=ws,
                               target_type="message", target_id=message_id, request_id=request_id)
            await record_event(conn, "question_submitted",
                               {"conversation_id": conversation_id, "question_chars": len(question),
                                "ready_documents": ready}, user_id=ctx.user_id, key=self._s.actor_hash_key)
        # COMMIT trước khi gọi LLM – không giữ khóa CSDL (DD-06)
        try:
            result = await self._retrieval.retrieve(ws, question)
            gated = result.below_gate
            draft = AnswerDraft("INSUFFICIENT", None, []) if gated else \
                await self._answerer.answer(question, result.chunks, t0)
        except (AnswerTimeout, LlmTimeout) as e:
            await self._fail(ctx, message_id, "ai_timeout")
            raise AppError(504, "ai_timeout") from e
        except CircuitOpen as e:
            await self._fail(ctx, message_id, "ai_unavailable")
            raise AppError(503, "ai_unavailable", headers={"Retry-After": str(max(1, int(e.retry_after)))}) from e
        except (LlmError, EmbeddingUnavailable) as e:
            await self._fail(ctx, message_id, "ai_unavailable")
            raise AppError(503, "ai_unavailable", headers={"Retry-After": "5"}) from e
        latency = int((time.monotonic() - t0) * 1000)
        async with self._db.tx("app_api", ws) as conn:
            await conn.execute("UPDATE message SET status = %s, answer = %s, error_code = NULL, latency_ms = %s "
                               "WHERE id = %s", (draft.status, draft.answer, latency, message_id))
            # Chỉ câu hỏi mới hoặc FAILED (chưa có trích dẫn) mới tới đây – không cần xóa trích dẫn cũ
            for c in draft.citations:
                await conn.execute(
                    """INSERT INTO citation(message_id, workspace_id, document_id, document_name_snapshot,
                                            page_number, ordinal) VALUES (%s, %s, %s, %s, %s, %s)""",
                    (message_id, ws, c.chunk.document_id, c.chunk.document_name, c.chunk.page_number, c.ordinal))
            await record_event(conn, "answer_returned", {
                "message_id": message_id, "status": draft.status, "latency_ms": latency,
                "citation_count": len(draft.citations),
                "cited_documents": len({c.chunk.document_id for c in draft.citations}),
                "has_page_numbers": all(c.chunk.page_number for c in draft.citations), "gated": gated},
                user_id=ctx.user_id, key=self._s.actor_hash_key)
            out = await self._stored_answer(conn, message_id, client_request_id)
        out["conflict"] = draft.conflict
        log.info("answer", status=draft.status, latency_ms=latency, citations=len(draft.citations), gated=gated)
        return out

    async def _stored_answer(self, conn: Conn, message_id: UUID, client_request_id: UUID) -> dict[str, Any]:
        cur = await conn.execute("SELECT status, answer, latency_ms FROM message WHERE id = %s", (message_id,))
        m = await cur.fetchone()
        assert m is not None
        cites = await self._citations(conn, [message_id])
        return {"message_id": str(message_id), "client_request_id": str(client_request_id), "status": m["status"],
                "answer": m["answer"] if m["status"] == "ANSWERED" else None,
                "citations": cites.get(message_id, []) if m["status"] == "ANSWERED" else [],
                "latency_ms": m["latency_ms"] or 0, "conflict": False}

    async def _fail(self, ctx: SessionContext, message_id: UUID, code: str) -> None:
        async with self._db.tx("app_api", ctx.workspace_id) as conn:
            await conn.execute("UPDATE message SET status = 'FAILED', error_code = %s WHERE id = %s",
                               (code, message_id))
            await record_event(conn, "answer_failed", {"message_id": message_id, "error_code": code},
                               user_id=ctx.user_id, key=self._s.actor_hash_key)
