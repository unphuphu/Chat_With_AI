"""UT-013 – rate limit cửa sổ cố định (ALG-09) trên PostgreSQL thật."""

from __future__ import annotations

import uuid

import pytest

from app.infra.ratelimit import hit

pytestmark = pytest.mark.integration


async def _user(db) -> uuid.UUID:
    async with db.admin() as conn:
        row = await (await conn.execute("INSERT INTO app_user(idp_subject, email) VALUES (%s, %s) RETURNING id",
                                        (f"s{uuid.uuid4()}", f"{uuid.uuid4()}@x.vn"))).fetchone()
    return row["id"]


async def test_limit_window_and_headers(clean_db) -> None:
    u = await _user(clean_db)
    ds = [await hit(clean_db, u, "question", 3, 60) for _ in range(4)]
    assert [d.allowed for d in ds] == [True, True, True, False]
    assert [d.remaining for d in ds] == [2, 1, 0, 0]
    h = ds[3].headers()
    assert h["RateLimit-Limit"] == "3" and h["RateLimit-Remaining"] == "0" and int(h["Retry-After"]) >= 1
    assert "Retry-After" not in ds[0].headers()


async def test_buckets_and_users_are_independent(clean_db) -> None:
    a, b = await _user(clean_db), await _user(clean_db)
    for _ in range(3):
        await hit(clean_db, a, "question", 2, 60)
    assert not (await hit(clean_db, a, "question", 2, 60)).allowed
    assert (await hit(clean_db, a, "upload_file", 2, 60)).allowed  # bucket khác
    assert (await hit(clean_db, b, "question", 2, 60)).allowed  # người dùng khác
