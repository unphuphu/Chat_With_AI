"""Chạy hàm phân tích PDF trong tiến trình con bị giới hạn (BLUEPRINT 3.6.5, DD-02, QA-07).

* Linux: RLIMIT_AS + RLIMIT_CPU đặt trong tiến trình con.
* Windows/macOS: tiến trình cha theo dõi RSS bằng psutil và kết thúc khi vượt giới hạn.
* Luôn có giới hạn thời gian; tiến trình con không nhận socket nào từ cha (start method `spawn`).
"""

from __future__ import annotations

import asyncio
import multiprocessing as mp
import sys
import time
from collections.abc import Callable
from multiprocessing.connection import Connection
from typing import Any

import psutil


class SandboxError(Exception):
    pass


class SandboxTimeout(SandboxError):
    pass


class SandboxCrashed(SandboxError):
    pass


class SandboxBusy(SandboxError):
    pass


def _child(conn: Connection, fn: Callable[..., Any], args: tuple[Any, ...], mem_mb: int, cpu_s: int) -> None:
    if sys.platform.startswith("linux"):
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (mem_mb * 1024 * 1024, mem_mb * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_s, cpu_s + 1))
    try:
        conn.send(("ok", fn(*args)))
    except MemoryError:
        conn.send(("crash", "memory"))
    except BaseException as e:
        conn.send(("error", f"{type(e).__name__}: {e}"))
    finally:
        conn.close()


def run_blocking(fn: Callable[..., Any], args: tuple[Any, ...], timeout_s: float, mem_mb: int) -> Any:
    ctx = mp.get_context("spawn")
    parent, child = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=_child, args=(child, fn, args, mem_mb, int(timeout_s) + 1), daemon=True)
    proc.start()
    child.close()
    deadline = time.monotonic() + timeout_s
    ps = psutil.Process(proc.pid) if proc.pid else None
    try:
        while True:
            if parent.poll(0.05):
                try:
                    status, value = parent.recv()
                except EOFError as e:
                    raise SandboxCrashed("no result") from e
                if status == "ok":
                    return value
                if status == "crash":
                    raise SandboxCrashed(value)
                raise SandboxCrashed(value)
            if not proc.is_alive():
                if parent.poll(0):
                    continue
                raise SandboxCrashed(f"exit code {proc.exitcode}")
            if time.monotonic() > deadline:
                raise SandboxTimeout(f"> {timeout_s}s")
            if ps is not None and not sys.platform.startswith("linux"):
                try:
                    if ps.memory_info().rss > mem_mb * 1024 * 1024:
                        raise SandboxCrashed("memory")
                except psutil.NoSuchProcess:
                    pass
    finally:
        if proc.is_alive():
            proc.kill()
        proc.join(timeout=2)
        parent.close()


class Sandbox:
    def __init__(self, concurrency: int = 2, wait_s: float = 30) -> None:
        self._sem = asyncio.Semaphore(concurrency)
        self._wait_s = wait_s

    async def run(self, fn: Callable[..., Any], args: tuple[Any, ...], *, timeout_s: float, mem_mb: int) -> Any:
        try:
            await asyncio.wait_for(self._sem.acquire(), timeout=self._wait_s)
        except TimeoutError as e:
            raise SandboxBusy("sandbox queue full") from e
        try:
            return await asyncio.to_thread(run_blocking, fn, args, timeout_s, mem_mb)
        finally:
            self._sem.release()
