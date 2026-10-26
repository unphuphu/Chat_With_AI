"""Hàng đợi tác vụ trên bảng `job` (BLUEPRINT ALG-11, 3.7.1; SAD ADR-006)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

from app.infra.db import Conn

JobKind = Literal["ingest_document", "purge_document"]
LOCK_MINUTES = 10


@dataclass(frozen=True)
class Job:
    id: int
    kind: JobKind
    document_id: UUID
    workspace_id: UUID
    attempts: int
    trace_parent: str | None


class JobSignal:
    """Đánh thức worker khi có job mới (thay `LISTEN job_enqueued` trong chế độ một tiến trình)."""

    def __init__(self) -> None:
        self.event = asyncio.Event()

    def notify(self) -> None:
        self.event.set()

    async def wait(self, timeout: float) -> None:
        try:
            await asyncio.wait_for(self.event.wait(), timeout)
        except TimeoutError:
            pass
        finally:
            self.event.clear()


async def enqueue(conn: Conn, kind: JobKind, document_id: UUID, workspace_id: UUID, *,
                  delay_s: float = 0, trace_parent: str | None = None) -> int:
    cur = await conn.execute(
        """INSERT INTO job(kind, document_id, workspace_id, run_after, trace_parent)
           VALUES (%s, %s, %s, now() + make_interval(secs => %s), %s) RETURNING id""",
        (kind, document_id, workspace_id, delay_s, trace_parent))
    row = await cur.fetchone()
    return int(row["id"])  # type: ignore[index]


async def claim(conn: Conn) -> Job | None:
    cur = await conn.execute(
        f"""UPDATE job SET status = 'RUNNING', attempts = attempts + 1,
                   locked_until = now() + interval '{LOCK_MINUTES} minutes'
            WHERE id = (
                SELECT id FROM job
                WHERE (status = 'QUEUED' AND run_after <= now())
                   OR (status = 'RUNNING' AND locked_until < now())
                ORDER BY run_after
                FOR UPDATE SKIP LOCKED
                LIMIT 1)
            RETURNING id, kind, document_id, workspace_id, attempts, trace_parent""")
    row = await cur.fetchone()
    return _job(row) if row else None


def _job(row: dict[str, Any]) -> Job:
    return Job(row["id"], row["kind"], row["document_id"], row["workspace_id"], row["attempts"], row["trace_parent"])


async def heartbeat(conn: Conn, job_id: int) -> None:
    await conn.execute(f"UPDATE job SET locked_until = now() + interval '{LOCK_MINUTES} minutes' "
                       "WHERE id = %s AND status = 'RUNNING'", (job_id,))


async def finish(conn: Conn, job_id: int, status: Literal["DONE", "FAILED", "CANCELLED"],
                 error_code: str | None = None) -> None:
    await conn.execute("UPDATE job SET status = %s, finished_at = now(), locked_until = NULL, "
                       "last_error_code = coalesce(%s, last_error_code) WHERE id = %s",
                       (status, error_code, job_id))


async def retry(conn: Conn, job_id: int, backoff_s: float, error_code: str) -> None:
    await conn.execute("UPDATE job SET status = 'QUEUED', locked_until = NULL, last_error_code = %s, "
                       "run_after = now() + make_interval(secs => %s) WHERE id = %s",
                       (error_code, backoff_s, job_id))


async def release(conn: Conn, job_id: int) -> None:
    """Tắt gọn: trả job đang chạy về hàng đợi (không tăng lượt)."""
    await conn.execute("UPDATE job SET status = 'QUEUED', locked_until = NULL, attempts = greatest(attempts - 1, 0) "
                       "WHERE id = %s AND status = 'RUNNING'", (job_id,))


async def cancel_queued(conn: Conn, document_id: UUID, kind: JobKind) -> int:
    cur = await conn.execute("UPDATE job SET status = 'CANCELLED', finished_at = now() "
                             "WHERE document_id = %s AND kind = %s AND status = 'QUEUED'", (document_id, kind))
    return cur.rowcount


def backoff_for(attempt: int) -> float:
    return [30.0, 120.0][min(max(attempt - 1, 0), 1)]
