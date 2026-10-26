"""ALG-04 – job `ingest_document`: PROCESSING → READY (đoạn + vector) hoặc FAILED (R-01…R-04)."""

from __future__ import annotations

import tempfile
import time
from enum import StrEnum
from pathlib import Path

from app.infra import jobs
from app.infra.db import Database
from app.infra.logging import get_logger
from app.infra.sandbox import Sandbox, SandboxCrashed, SandboxTimeout
from app.infra.settings import Settings
from app.modules.events.analytics import record_event
from app.modules.events.bus import EventBus
from app.modules.ingestion import extractor
from app.modules.ingestion.chunker import chunk_pages
from app.ports.blob import BlobPort, BlobUnavailable
from app.ports.embedding import EmbeddingPort, EmbeddingUnavailable

log = get_logger("ingestion")


class IngestOutcome(StrEnum):
    READY = "READY"
    FAILED = "FAILED"
    RETRY = "RETRY"
    CANCELLED = "CANCELLED"


class TransientError(Exception):
    pass


def _vec(v: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


class IngestionPipeline:
    def __init__(self, db: Database, blob: BlobPort, embedding: EmbeddingPort, sandbox: Sandbox,
                 bus: EventBus, settings: Settings) -> None:
        self._db, self._blob, self._emb, self._sandbox, self._bus, self._s = db, blob, embedding, sandbox, bus, settings

    async def run(self, job: jobs.Job) -> IngestOutcome:
        started = time.monotonic()
        ws, doc_id = job.workspace_id, job.document_id
        async with self._db.tx("app_worker", ws) as conn:
            cur = await conn.execute("SELECT storage_key, deleted_at, status, page_count, size_bytes "
                                     "FROM document WHERE id = %s", (doc_id,))
            doc = await cur.fetchone()
        if doc is None or doc["deleted_at"] is not None:
            await self._finish(job, "CANCELLED")
            return IngestOutcome.CANCELLED
        try:
            outcome = await self._process(job, doc["storage_key"], started, doc["page_count"], doc["size_bytes"])
        except TransientError as e:
            if job.attempts < self._s.ingest_max_attempts:
                async with self._db.tx("app_worker") as conn:
                    await jobs.retry(conn, job.id, jobs.backoff_for(job.attempts), str(e)[:60])
                log.info("ingest_retry", job_id=job.id, attempt=job.attempts, reason=str(e)[:60])
                return IngestOutcome.RETRY
            await self._mark_failed(job, "R-04")
            return IngestOutcome.FAILED
        return outcome

    async def _process(self, job: jobs.Job, key: str, started: float, page_count: int,
                       size_bytes: int) -> IngestOutcome:
        with tempfile.TemporaryDirectory(prefix="aichat-ingest-") as d:
            path = Path(d) / "doc.pdf"
            try:
                await self._blob.download_to(key, path)
            except (BlobUnavailable, FileNotFoundError) as e:
                raise TransientError("blob_unavailable") from e
            try:
                result: extractor.ExtractOutcome = await self._sandbox.run(
                    extractor.extract, (str(path), self._s.min_chars_per_page),
                    timeout_s=self._s.ingest_timeout_s, mem_mb=self._s.ingest_mem_mb)
            except SandboxTimeout as e:
                raise TransientError("extract_timeout") from e
            except SandboxCrashed as e:
                raise TransientError("extract_crashed") from e
        if result.failure_code:
            await self._mark_failed(job, result.failure_code)
            return IngestOutcome.FAILED
        assert result.pages is not None
        drafts = chunk_pages(result.pages, target=self._s.chunk_target_tokens, max_tokens=self._s.chunk_max_tokens,
                             overlap=self._s.chunk_overlap_tokens)
        if not drafts:
            await self._mark_failed(job, "R-03")
            return IngestOutcome.FAILED
        vectors: list[list[float]] = []
        for i in range(0, len(drafts), self._s.embed_batch):
            batch = drafts[i:i + self._s.embed_batch]
            try:
                vectors += await self._emb.embed([c.content for c in batch], purpose="passage", timeout_s=30)
            except EmbeddingUnavailable as e:
                raise TransientError("embedding_unavailable") from e
            if (i // self._s.embed_batch) % 10 == 9:
                async with self._db.tx("app_worker") as conn:
                    await jobs.heartbeat(conn, job.id)

        ws, doc_id = job.workspace_id, job.document_id
        async with self._db.tx("app_worker", ws) as conn:  # bước 7 – an toàn với xóa
            cur = await conn.execute("SELECT deleted_at FROM document WHERE id = %s FOR UPDATE", (doc_id,))
            row = await cur.fetchone()
            if row is None or row["deleted_at"] is not None:
                cancelled = True
            else:
                cancelled = False
                await conn.execute("DELETE FROM chunk WHERE document_id = %s", (doc_id,))
                # COPY FROM không dùng được trên bảng có RLS → INSERT theo lô (executemany dùng pipeline)
                async with conn.cursor() as cur:
                    await cur.executemany(
                        "INSERT INTO chunk (document_id, workspace_id, page_number, chunk_index, token_count, "
                        "content, embedding_model, embedding) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector)",
                        [(doc_id, ws, c.page_number, c.chunk_index, c.token_count, c.content, self._emb.model_id,
                          _vec(v)) for c, v in zip(drafts, vectors, strict=True)])
                await conn.execute("UPDATE document SET status = 'READY', failure_code = NULL, ready_at = now() "
                                   "WHERE id = %s", (doc_id,))
                await record_event(conn, "document_processing_completed",
                                   {"document_id": doc_id, "page_count": page_count, "size_bytes": size_bytes,
                                    "duration_ms": int((time.monotonic() - started) * 1000),
                                    "chunk_count": len(drafts)}, user_id=None, key=self._s.actor_hash_key)
        if cancelled:
            await self._finish(job, "CANCELLED")
            return IngestOutcome.CANCELLED
        await self._finish(job, "DONE")
        self._bus.publish(ws, "document.status_changed",
                          {"document_id": str(doc_id), "status": "READY", "failure_code": None})
        log.info("ingest_ready", document_id=str(doc_id), chunks=len(drafts))
        return IngestOutcome.READY

    async def _mark_failed(self, job: jobs.Job, code: str) -> None:
        ws, doc_id = job.workspace_id, job.document_id
        async with self._db.tx("app_worker", ws) as conn:
            cur = await conn.execute("SELECT deleted_at, status FROM document WHERE id = %s FOR UPDATE", (doc_id,))
            row = await cur.fetchone()
            if row is not None and row["deleted_at"] is None and row["status"] == "PROCESSING":
                await conn.execute("UPDATE document SET status = 'FAILED', failure_code = %s WHERE id = %s",
                                   (code, doc_id))
                await record_event(conn, "document_processing_failed",
                                   {"document_id": doc_id, "failure_code": code, "attempts": job.attempts},
                                   user_id=None, key=self._s.actor_hash_key)
                published = True
            else:
                published = False
            await jobs.finish(conn, job.id, "FAILED", code)
        if published:
            self._bus.publish(ws, "document.status_changed",
                              {"document_id": str(doc_id), "status": "FAILED", "failure_code": code})
        log.info("ingest_failed", document_id=str(doc_id), failure_code=code)

    async def _finish(self, job: jobs.Job, status: str) -> None:
        async with self._db.tx("app_worker") as conn:
            await jobs.finish(conn, job.id, status)  # type: ignore[arg-type]
