"""Giới hạn tần suất cửa sổ cố định trong PostgreSQL (BLUEPRINT ALG-09, DD-04) – đúng cả khi nhiều bản API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from app.infra.db import Database

Bucket = Literal["question", "upload_file"]


@dataclass(frozen=True)
class RateDecision:
    allowed: bool
    limit: int
    remaining: int
    reset_s: int

    def headers(self) -> dict[str, str]:
        h = {"RateLimit-Limit": str(self.limit), "RateLimit-Remaining": str(self.remaining),
             "RateLimit-Reset": str(self.reset_s)}
        if not self.allowed:
            h["Retry-After"] = str(max(1, self.reset_s))
        return h


async def hit(db: Database, user_id: UUID, bucket: Bucket, limit: int, window_s: int) -> RateDecision:
    async with db.tx("app_api") as conn:
        cur = await conn.execute(
            """INSERT INTO rate_limit_counter(user_id, bucket, window_start, count)
               VALUES (%s, %s, date_bin(make_interval(secs => %s), now(), timestamptz '2000-01-01'), 1)
               ON CONFLICT (user_id, bucket, window_start) DO UPDATE SET count = rate_limit_counter.count + 1
               RETURNING count, window_start""", (user_id, bucket, window_s))
        row = await cur.fetchone()
    assert row is not None
    count = int(row["count"])
    reset = int(window_s - (datetime.now(UTC) - row["window_start"]).total_seconds())
    return RateDecision(count <= limit, limit, max(0, limit - count), max(0, reset))
