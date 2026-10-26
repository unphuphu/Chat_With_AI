"""Bộ chạy migration SQL tối giản (thay Alembic – xem app/README.md "Khác biệt so với kế hoạch").

Áp dụng lần lượt `migrations/sql/NNNN_*.sql`, ghi vào bảng `schema_migration`. Mỗi file chạy trong một
transaction. `0000_roles.sql` tạo vai trò ứng dụng nếu chưa có.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from app.infra.db import Database
from app.infra.settings import get_settings

SQL_DIR = Path(__file__).resolve().parents[2] / "migrations" / "sql"

ROLES_SQL = """
DO $$
DECLARE r text;
BEGIN
  FOREACH r IN ARRAY ARRAY['app_api','app_worker','app_maintenance','app_readonly_audit','app_readonly_analytics'] LOOP
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
      EXECUTE format('CREATE ROLE %I NOLOGIN NOBYPASSRLS', r);
    END IF;
  END LOOP;
END $$;
"""


async def migrate(db: Database) -> list[str]:
    applied: list[str] = []
    async with db.admin() as conn:
        await conn.execute(ROLES_SQL)
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migration "
            "(version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())")
        cur = await conn.execute("SELECT version FROM schema_migration")
        done = {r["version"] for r in await cur.fetchall()}
    for path in sorted(SQL_DIR.glob("*.sql")):
        version = path.stem
        if version in done:
            continue
        sql = path.read_text(encoding="utf-8")
        async with db.admin() as conn:
            await conn.execute(sql)  # type: ignore[arg-type]
            await conn.execute("INSERT INTO schema_migration(version) VALUES (%s)", (version,))
        applied.append(version)
    return applied


async def _main() -> None:
    s = get_settings()
    db = Database(s.database_url, "single")
    await db.open()
    try:
        applied = await migrate(db)
        print("applied:", applied or "nothing")
        if "--seed" in sys.argv:
            seed = (Path(__file__).resolve().parents[2] / "migrations" / "seed_dev.sql").read_text(encoding="utf-8")
            async with db.admin() as conn:
                await conn.execute("SET app.env = 'dev'")
                await conn.execute(seed)  # type: ignore[arg-type]
            print("seeded dev data")
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(_main())
