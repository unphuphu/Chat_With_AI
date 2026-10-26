"""Vòng đời tài liệu: lô tải lên, nhận file, danh sách, xóa, xử lý lại (BLUEPRINT ALG-01, ALG-02, ALG-12)."""

from __future__ import annotations

import hashlib
import os
import tempfile
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from app.infra import jobs
from app.infra.db import Conn, Database
from app.infra.sandbox import Sandbox, SandboxBusy, SandboxError
from app.infra.settings import Settings
from app.modules.audit.service import record_audit
from app.modules.common.errors import AppError
from app.modules.documents import pdf_inspector
from app.modules.documents.domain import Document, DocumentStatus, FailureCode, InspectionResult
from app.modules.events.analytics import record_event
from app.modules.events.bus import EventBus
from app.modules.identity.domain import SessionContext
from app.ports.blob import BlobPort, BlobUnavailable, document_key

REJECT_DETAIL = {
    "not_pdf": '"{name}" không phải file PDF hợp lệ.',
    "too_large": '"{name}" vượt quá {max_mb} MB.',
    "too_many_pages": '"{name}" có hơn {max_pages} trang.',
    "encrypted": '"{name}" được bảo vệ bằng mật khẩu.',
}

DOC_COLUMNS = "id, file_name, status, failure_code, page_count, size_bytes, uploaded_at, ready_at"


def row_to_document(r: dict[str, Any]) -> Document:
    return Document(r["id"], r["file_name"], DocumentStatus(r["status"]),
                    FailureCode(r["failure_code"]) if r["failure_code"] else None,
                    r["page_count"], r["size_bytes"], r["uploaded_at"], r["ready_at"])


@dataclass(frozen=True)
class AcceptResult:
    document: Document
    created: bool


class DocumentService:
    def __init__(self, db: Database, blob: BlobPort, sandbox: Sandbox, bus: EventBus,
                 job_signal: jobs.JobSignal, settings: Settings) -> None:
        self._db, self._blob, self._sandbox, self._bus = db, blob, sandbox, bus
        self._signal, self._s = job_signal, settings

    # ------------------------------------------------------------------ quota
    async def quota(self, ws: UUID) -> tuple[int, int]:
        async with self._db.tx("app_api", ws) as conn:
            used = await self._used(conn, ws)
        return used, self._s.max_docs_per_workspace

    @staticmethod
    async def _used(conn: Conn, ws: UUID) -> int:
        cur = await conn.execute("SELECT documents_used + reserved_slots AS used FROM vw_workspace_quota "
                                 "WHERE workspace_id = %s", (ws,))
        row = await cur.fetchone()
        return int(row["used"]) if row else 0

    async def _publish_quota(self, ws: UUID) -> None:
        async with self._db.tx("app_api", ws) as conn:
            cur = await conn.execute("SELECT documents_used FROM vw_workspace_quota WHERE workspace_id = %s", (ws,))
            row = await cur.fetchone()
        self._bus.publish(ws, "quota.changed", {"documents_used": int(row["documents_used"]) if row else 0,
                                                "documents_limit": self._s.max_docs_per_workspace})

    # ------------------------------------------------------------------ ALG-01 create_batch
    async def create_batch(self, ctx: SessionContext, files: list[dict[str, Any]]) -> dict[str, Any]:
        n = len(files)
        if n > self._s.max_files_per_batch:
            raise AppError(422, "too_many_files",
                           f"Mỗi lần chỉ tải tối đa {self._s.max_files_per_batch} file.")
        ws = ctx.workspace_id
        async with self._db.tx("app_api", ws) as conn:
            await conn.execute("SELECT 1 FROM workspace WHERE id = %s FOR UPDATE", (ws,))
            used = await self._used(conn, ws)
            limit = self._s.max_docs_per_workspace
            if used + n > limit:
                remaining = max(0, limit - used)
                raise AppError(422, "quota_exceeded", f"Bạn chỉ còn có thể thêm {remaining} tài liệu.",
                               remaining=remaining)
            expires = datetime.now(UTC) + timedelta(seconds=self._s.batch_ttl_s)
            cur = await conn.execute(
                """INSERT INTO upload_batch(workspace_id, created_by, remaining_slots, expires_at)
                   VALUES (%s, %s, %s, %s) RETURNING id, expires_at""", (ws, ctx.user_id, n, expires))
            row = await cur.fetchone()
            assert row is not None
            await record_event(conn, "document_upload_started",
                               {"batch_id": row["id"], "file_count": n,
                                "total_bytes": sum(int(f.get("size_bytes", 0)) for f in files)},
                               user_id=ctx.user_id, key=self._s.actor_hash_key)
        return {"batch_id": str(row["id"]), "expires_at": row["expires_at"].isoformat().replace("+00:00", "Z"),
                "slots": n, "remaining_quota": max(0, limit - used - n)}

    # ------------------------------------------------------------------ ALG-01 accept_file
    async def find_existing(self, ws: UUID, batch_id: UUID, client_file_id: UUID) -> Document | None:
        async with self._db.tx("app_api", ws) as conn:
            cur = await conn.execute(f"SELECT {DOC_COLUMNS} FROM document WHERE batch_id = %s AND client_file_id = %s",
                                     (batch_id, client_file_id))
            row = await cur.fetchone()
        return row_to_document(row) if row else None

    async def accept_file(self, ctx: SessionContext, batch_id: UUID, client_file_id: UUID, file_name: str,
                          stream: AsyncIterator[bytes], request_id: str | None = None) -> AcceptResult:
        ws = ctx.workspace_id
        # Pha 0 – idempotency (API AD-06)
        existing = await self.find_existing(ws, batch_id, client_file_id)
        if existing:
            return AcceptResult(existing, created=False)

        file_name = (os.path.basename(file_name.replace("\\", "/")) or "tai-lieu.pdf")[:255]
        fd, tmp_name = tempfile.mkstemp(prefix="aichat-upload-", suffix=".pdf")
        tmp = Path(tmp_name)
        try:
            # Pha 1 – nhận và kiểm tra file, không mở transaction
            reject: str | None = None
            size = 0
            digest = hashlib.sha256()
            with os.fdopen(fd, "wb") as out:
                async for chunk in stream:
                    size += len(chunk)
                    if size > self._s.max_file_bytes:
                        reject = "too_large"
                        break
                    digest.update(chunk)
                    out.write(chunk)
            result: InspectionResult | None = None
            if reject is None and size == 0:
                reject = "not_pdf"
            if reject is None:
                try:
                    result = await self._sandbox.run(pdf_inspector.inspect,
                                                     (str(tmp), self._s.max_file_bytes, self._s.max_pages),
                                                     timeout_s=self._s.inspect_timeout_s, mem_mb=self._s.inspect_mem_mb)
                except SandboxBusy as e:
                    raise AppError(503, "server_busy", headers={"Retry-After": "10"}) from e
                except SandboxError:
                    result = InspectionResult(False, reject_code="not_pdf")
                if not result.ok:
                    reject = result.reject_code

            # Pha 2 – transaction ngắn: tiêu thụ một chỗ đặt (kể cả khi bị từ chối)
            async with self._db.tx("app_api", ws) as conn:
                cur = await conn.execute(
                    "SELECT remaining_slots, expires_at FROM upload_batch WHERE id = %s FOR UPDATE", (batch_id,))
                batch = await cur.fetchone()
                if batch is None or batch["expires_at"] <= datetime.now(UTC):
                    raise AppError(404, "batch_expired")
                if batch["remaining_slots"] <= 0:
                    raise AppError(409, "batch_full")
                await conn.execute("UPDATE upload_batch SET remaining_slots = remaining_slots - 1 WHERE id = %s",
                                   (batch_id,))
                if reject:
                    await record_audit(conn, "document_reject", actor_id=ctx.user_id, workspace_id=ws,
                                       outcome="denied", request_id=request_id)
                    await record_event(conn, "document_upload_rejected", {"batch_id": batch_id, "reason": reject},
                                       user_id=ctx.user_id, key=self._s.actor_hash_key)
            if reject:
                detail = REJECT_DETAIL[reject].format(name=file_name, max_mb=self._s.max_file_mb,
                                                      max_pages=self._s.max_pages)
                raise AppError(422, reject, detail)

            # Pha 3 – ghi object storage, không giữ khóa
            assert result is not None and result.page_count is not None
            doc_id = uuid4()
            key = document_key(ws, doc_id)
            try:
                await self._blob.put(key, tmp, digest.digest())
            except BlobUnavailable as e:
                raise AppError(503, "storage_unavailable", "Chưa lưu được file, vui lòng tải lại.",
                               headers={"Retry-After": "10"}) from e

            # Pha 4 – transaction ngắn: tạo tài liệu + job
            async with self._db.tx("app_api", ws) as conn:
                cur = await conn.execute(
                    f"""INSERT INTO document(id, workspace_id, batch_id, client_file_id, file_name, size_bytes,
                                            page_count, storage_key, sha256, uploaded_by)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (batch_id, client_file_id) DO NOTHING
                        RETURNING {DOC_COLUMNS}""",
                    (doc_id, ws, batch_id, client_file_id, file_name, size, result.page_count, key, digest.digest(),
                     ctx.user_id))
                row = await cur.fetchone()
                if row is None:  # request trùng chạy song song: hoàn chỗ đặt, dùng tài liệu đã có
                    await conn.execute("UPDATE upload_batch SET remaining_slots = remaining_slots + 1 WHERE id = %s",
                                       (batch_id,))
                else:
                    await jobs.enqueue(conn, "ingest_document", doc_id, ws)
                    await record_audit(conn, "document_upload", actor_id=ctx.user_id, workspace_id=ws,
                                       target_type="document", target_id=doc_id, request_id=request_id)
            if row is None:
                await self._blob.delete(key)
                again = await self.find_existing(ws, batch_id, client_file_id)
                assert again is not None
                return AcceptResult(again, created=False)
            self._signal.notify()
            doc = row_to_document(row)
            self._bus.publish(ws, "document.status_changed",
                              {"document_id": str(doc.id), "status": doc.status.value, "failure_code": None})
            await self._publish_quota(ws)
            return AcceptResult(doc, created=True)
        finally:
            tmp.unlink(missing_ok=True)

    # ------------------------------------------------------------------ list / get
    async def list(self, ws: UUID) -> list[Document]:
        async with self._db.tx("app_api", ws) as conn:
            cur = await conn.execute(f"SELECT {DOC_COLUMNS} FROM document WHERE deleted_at IS NULL "
                                     "ORDER BY uploaded_at DESC")
            rows = await cur.fetchall()
        return [row_to_document(r) for r in rows]

    async def ready_count(self, ws: UUID) -> int:
        async with self._db.tx("app_api", ws) as conn:
            cur = await conn.execute("SELECT count(*) AS n FROM document WHERE status = 'READY' AND deleted_at IS NULL")
            row = await cur.fetchone()
        return int(row["n"]) if row else 0

    # ------------------------------------------------------------------ ALG-12 soft delete
    async def soft_delete(self, ctx: SessionContext, document_id: UUID, request_id: str | None = None) -> None:
        ws = ctx.workspace_id
        async with self._db.tx("app_api", ws) as conn:
            cur = await conn.execute("SELECT status FROM document WHERE id = %s AND deleted_at IS NULL FOR UPDATE",
                                     (document_id,))
            row = await cur.fetchone()
            if row is None:
                await record_audit(conn, "access_denied", actor_id=ctx.user_id, workspace_id=ws,
                                   target_type="document", target_id=document_id, outcome="denied",
                                   request_id=request_id)
                await record_event(conn, "access_denied", {"resource_type": "document"}, user_id=ctx.user_id,
                                   key=self._s.actor_hash_key)
                not_found = True
            else:
                not_found = False
                await conn.execute("UPDATE document SET deleted_at = now() WHERE id = %s", (document_id,))
                await conn.execute("DELETE FROM chunk WHERE document_id = %s", (document_id,))
                await jobs.cancel_queued(conn, document_id, "ingest_document")
                await jobs.enqueue(conn, "purge_document", document_id, ws)
                await record_audit(conn, "document_delete", actor_id=ctx.user_id, workspace_id=ws,
                                   target_type="document", target_id=document_id, request_id=request_id)
                await record_event(conn, "document_deleted", {"document_id": document_id,
                                                              "status_at_delete": row["status"]},
                                   user_id=ctx.user_id, key=self._s.actor_hash_key)
        if not_found:
            raise AppError(404, "not_found", "Không tìm thấy tài liệu.")
        self._signal.notify()
        await self._publish_quota(ws)

    # ------------------------------------------------------------------ US-009 reprocess
    async def reprocess(self, ctx: SessionContext, document_id: UUID, request_id: str | None = None) -> Document:
        ws = ctx.workspace_id
        async with self._db.tx("app_api", ws) as conn:
            cur = await conn.execute(f"SELECT {DOC_COLUMNS} FROM document WHERE id = %s AND deleted_at IS NULL "
                                     "FOR UPDATE", (document_id,))
            row = await cur.fetchone()
            if row is None:
                raise AppError(404, "not_found", "Không tìm thấy tài liệu.")
            doc = row_to_document(row)
            if doc.status != DocumentStatus.FAILED or doc.failure_code != FailureCode.R04:
                raise AppError(409, "not_retryable")
            cur = await conn.execute(
                f"UPDATE document SET status = 'PROCESSING', failure_code = NULL WHERE id = %s RETURNING {DOC_COLUMNS}",
                (document_id,))
            new_row = await cur.fetchone()
            await jobs.enqueue(conn, "ingest_document", document_id, ws)
            await record_audit(conn, "document_reprocess", actor_id=ctx.user_id, workspace_id=ws,
                               target_type="document", target_id=document_id, request_id=request_id)
        self._signal.notify()
        doc = row_to_document(new_row)  # type: ignore[arg-type]
        self._bus.publish(ws, "document.status_changed",
                          {"document_id": str(doc.id), "status": doc.status.value, "failure_code": None})
        return doc

    # ------------------------------------------------------------------ file (US-022)
    async def open_file(self, ctx: SessionContext, document_id: UUID, *, from_citation: bool,
                        page: int | None) -> tuple[str, AsyncIterator[bytes]]:
        ws = ctx.workspace_id
        async with self._db.tx("app_api", ws) as conn:
            cur = await conn.execute("SELECT file_name, storage_key, deleted_at FROM document WHERE id = %s",
                                     (document_id,))
            row = await cur.fetchone()
            if row is not None and from_citation:
                await record_event(conn, "citation_clicked", {"document_id": document_id, "has_page": page is not None},
                                   user_id=ctx.user_id, key=self._s.actor_hash_key)
        if row is None:
            raise AppError(404, "not_found", "Không tìm thấy tài liệu.")
        if row["deleted_at"] is not None:
            raise AppError(410, "deleted", "Tài liệu đã bị xóa.")
        return row["file_name"], self._blob.read(row["storage_key"])
