"""Vòng lặp worker (T03-01): lấy job, gọi handler, lịch bảo trì.

Chế độ một tiến trình (DB_MODE=single): chạy như các asyncio task trong tiến trình API.
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from collections.abc import Awaitable, Callable

from app.container import Container
from app.infra import jobs
from app.infra.logging import get_logger
from worker import maintenance
from worker.handlers import purge

log = get_logger("worker")


class Worker:
    def __init__(self, c: Container) -> None:
        self.c = c
        self._stop = asyncio.Event()
        self._tasks: list[asyncio.Task[None]] = []
        self.processed = 0

    def start(self) -> None:
        for i in range(self.c.settings.ingest_concurrency):
            self._tasks.append(asyncio.create_task(self._loop(i), name=f"worker-{i}"))
        self._tasks.append(asyncio.create_task(self._scheduler(), name="worker-scheduler"))

    async def stop(self) -> None:
        self._stop.set()
        self.c.job_signal.notify()
        for t in self._tasks:
            t.cancel()
        for t in self._tasks:
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await t
        self._tasks.clear()

    async def run_once(self) -> bool:
        """Lấy và xử lý một job; trả False nếu hàng đợi trống (dùng trong test)."""
        async with self.c.db.tx("app_worker") as conn:
            job = await jobs.claim(conn)
        if job is None:
            return False
        try:
            if job.kind == "ingest_document":
                await self.c.ingestion.run(job)
            else:
                await purge.purge(self.c.db, self.c.blob, job)
        except asyncio.CancelledError:
            async with self.c.db.tx("app_worker") as conn:
                await jobs.release(conn, job.id)
            raise
        except Exception:
            log.exception("job_failed_unexpectedly", job_id=job.id, kind=job.kind)
            async with self.c.db.tx("app_worker") as conn:
                await jobs.retry(conn, job.id, 60, "unexpected")
        self.processed += 1
        return True

    async def drain(self, max_jobs: int = 100) -> int:
        n = 0
        while n < max_jobs and await self.run_once():
            n += 1
        return n

    async def _loop(self, i: int) -> None:
        while not self._stop.is_set():
            try:
                if not await self.run_once():
                    await self.c.job_signal.wait(5)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("worker_loop_error", worker=i)
                await asyncio.sleep(2)

    async def _scheduler(self) -> None:
        s = self.c.settings
        plan: list[tuple[str, float, Callable[[], Awaitable[object]]]] = [
            ("expire_sessions", 15 * 60, lambda: maintenance.expire_sessions(self.c.db)),
            ("purge_sweep", 60 * 60, lambda: purge.sweep(self.c.db, self.c.blob)),
            ("prune", 6 * 3600, lambda: maintenance.prune(self.c.db, s)),
            ("audit_partitions", 24 * 3600, lambda: maintenance.audit_partitions(self.c.db, s)),
        ]
        last = dict.fromkeys((name for name, _, _ in plan), 0.0)
        while not self._stop.is_set():
            now = time.monotonic()
            for name, every, fn in plan:
                if now - last[name] >= every:
                    last[name] = now
                    try:
                        result = await fn()
                        log.info("maintenance_done", task=name, result=str(result))
                    except Exception:
                        log.exception("maintenance_failed", task=name)
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=30)
            except TimeoutError:
                pass
