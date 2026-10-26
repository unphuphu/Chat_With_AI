"""Truy cập CSDL với phạm vi workspace bắt buộc (BLUEPRINT 3.2.3, SAD 5.1).

Mọi transaction chạy `SET LOCAL ROLE <vai trò ứng dụng>` (không có BYPASSRLS) và, khi đọc/ghi dữ liệu
tài liệu, `set_config('app.workspace_id', …, true)` để Row-Level Security có hiệu lực.

Hai chế độ:
* ``single`` – một kết nối dùng chung, tuần tự hóa bằng asyncio.Lock (PGlite dev chỉ cho 1 kết nối).
* ``pool``   – psycopg_pool cho PostgreSQL thật.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Literal
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

Role = Literal["app_api", "app_worker", "app_maintenance", "app_readonly_audit", "app_readonly_analytics"]
Conn = psycopg.AsyncConnection[dict[str, Any]]


class WorkspaceScopeMissing(RuntimeError):
    """Truy vấn bảng có RLS khi chưa đặt phạm vi workspace."""


class Database:
    def __init__(self, url: str, mode: Literal["single", "pool"] = "single", pool_size: int = 10) -> None:
        self._url = url
        self._mode = mode
        self._pool_size = pool_size
        self._conn: Conn | None = None
        self._lock = asyncio.Lock()
        self._pool: Any = None

    async def open(self) -> None:
        if self._mode == "single":
            self._conn = await self._connect()
        else:
            from psycopg_pool import AsyncConnectionPool

            self._pool = AsyncConnectionPool(self._url, min_size=1, max_size=self._pool_size, open=False,
                                             kwargs={"row_factory": dict_row, "autocommit": False})
            await self._pool.open()

    async def _connect(self) -> Conn:
        conn = await psycopg.AsyncConnection.connect(self._url, row_factory=dict_row, autocommit=False)
        await conn.execute("SET TIME ZONE 'UTC'")
        await conn.commit()
        return conn

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    @asynccontextmanager
    async def _raw(self) -> AsyncIterator[Conn]:
        if self._mode == "single":
            async with self._lock:
                if self._conn is None or self._conn.closed:
                    self._conn = await self._connect()
                yield self._conn
        else:
            async with self._pool.connection() as conn:
                yield conn

    @asynccontextmanager
    async def tx(self, role: Role, workspace_id: UUID | None = None) -> AsyncIterator[Conn]:
        """Một transaction với vai trò ứng dụng và (tùy chọn) phạm vi workspace."""
        async with self._raw() as conn:
            try:
                await conn.execute(f"SET LOCAL ROLE {role}")
                if workspace_id is not None:
                    await conn.execute("SELECT set_config('app.workspace_id', %s, true)", (str(workspace_id),))
                yield conn
                await conn.commit()
            except BaseException:
                await conn.rollback()
                raise

    @asynccontextmanager
    async def admin(self) -> AsyncIterator[Conn]:
        """Kết nối chủ sở hữu schema – chỉ dùng cho migration và tác vụ quản trị."""
        async with self._raw() as conn:
            try:
                yield conn
                await conn.commit()
            except BaseException:
                await conn.rollback()
                raise


async def require_scope(conn: Conn) -> UUID:
    """Ném WorkspaceScopeMissing nếu transaction chưa đặt app.workspace_id."""
    cur = await conn.execute("SELECT NULLIF(current_setting('app.workspace_id', true), '') AS ws")
    row = await cur.fetchone()
    if row is None or row["ws"] is None:
        raise WorkspaceScopeMissing("Truy vấn dữ liệu tài liệu cần workspace_scope")
    return UUID(row["ws"])
