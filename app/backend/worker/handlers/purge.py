"""ALG-10 – xóa thật file gốc của tài liệu đã xóa mềm (≤ 24 h, NFR-013) và dọn object mồ côi."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.infra import jobs
from app.infra.db import Database
from app.infra.logging import get_logger
from app.ports.blob import BlobPort, BlobUnavailable, parse_document_key

log = get_logger("purge")


async def purge(db: Database, blob: BlobPort, job: jobs.Job) -> None:
    ws, doc_id = job.workspace_id, job.document_id
    async with db.tx("app_worker", ws) as conn:
        cur = await conn.execute("SELECT storage_key, deleted_at, purged_at FROM document WHERE id = %s", (doc_id,))
        row = await cur.fetchone()
    if row is None or row["deleted_at"] is None or row["purged_at"] is not None:
        async with db.tx("app_worker") as conn:
            await jobs.finish(conn, job.id, "DONE")
        return
    try:
        await blob.delete(row["storage_key"])
    except BlobUnavailable:
        async with db.tx("app_worker") as conn:
            await jobs.retry(conn, job.id, 60, "blob_unavailable")
        return
    async with db.tx("app_worker", ws) as conn:
        await conn.execute("UPDATE document SET purged_at = now() WHERE id = %s", (doc_id,))
        await jobs.finish(conn, job.id, "DONE")
    log.info("purged", document_id=str(doc_id))


async def sweep(db: Database, blob: BlobPort) -> dict[str, float]:
    """Lượt quét hằng giờ: enqueue purge bị sót, xóa object mồ côi, đo độ trễ purge."""
    async with db.tx("app_worker") as conn:
        cur = await conn.execute("SELECT document_id, workspace_id FROM fn_pending_purges(interval '1 hour')")
        pending = await cur.fetchall()
    for r in pending:
        async with db.tx("app_worker", r["workspace_id"]) as conn:
            await jobs.enqueue(conn, "purge_document", r["document_id"], r["workspace_id"])
    orphans = 0
    for key in await blob.list_older_than("ws/", datetime.now(UTC) - timedelta(hours=1)):
        parsed = parse_document_key(key)
        if parsed is None:
            continue
        ws, doc_id = parsed
        async with db.tx("app_worker", ws) as conn:
            cur = await conn.execute("SELECT purged_at FROM document WHERE id = %s", (doc_id,))
            row = await cur.fetchone()
        if row is None or row["purged_at"] is not None:
            await blob.delete(key)
            orphans += 1
    async with db.tx("app_worker") as conn:
        cur = await conn.execute("SELECT fn_purge_lag_max_seconds() AS lag")
        lag = float((await cur.fetchone())["lag"])  # type: ignore[index]
    if lag > 20 * 3600:
        log.warning("purge_lag_high", lag_hours=round(lag / 3600, 1))
    return {"requeued": len(pending), "orphans_deleted": orphans, "purge_lag_seconds": lag}
