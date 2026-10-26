"""Tác vụ bảo trì định kỳ (T10-04; DATABASE_DESIGN A.10) – chạy bằng vai trò app_maintenance."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from app.infra.db import Database
from app.infra.settings import Settings


async def expire_sessions(db: Database) -> int:
    async with db.tx("app_maintenance") as conn:
        cur = await conn.execute("DELETE FROM session WHERE least(idle_expires_at, absolute_expires_at) < now()")
        n = cur.rowcount
        await conn.execute("DELETE FROM upload_batch WHERE expires_at < now() - interval '1 day'")
    return n


async def prune(db: Database, s: Settings) -> None:
    async with db.tx("app_maintenance") as conn:
        await conn.execute("DELETE FROM rate_limit_counter WHERE window_start < now() - interval '2 hours'")
        await conn.execute("DELETE FROM analytics_event WHERE at < now() - make_interval(days => %s)",
                           (s.analytics_retention_days,))
        await conn.execute("DELETE FROM job WHERE status IN ('DONE','CANCELLED','FAILED') "
                           "AND finished_at < now() - interval '7 days'")


async def audit_partitions(db: Database, s: Settings) -> int:
    today = datetime.now(UTC).date()
    next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
    async with db.tx("app_maintenance") as conn:
        await conn.execute("SELECT fn_ensure_audit_partition(%s)", (today,))
        await conn.execute("SELECT fn_ensure_audit_partition(%s)", (next_month,))
        cur = await conn.execute("SELECT fn_drop_audit_partitions_before(%s) AS n",
                                 (today - timedelta(days=s.audit_retention_days),))
        row = await cur.fetchone()
    return int(row["n"]) if row else 0


__all__ = ["audit_partitions", "date", "expire_sessions", "prune"]
