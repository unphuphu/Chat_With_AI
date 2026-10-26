"""Circuit breaker cho LLM (BLUEPRINT ALG-07, 3.7.5). Mỗi bản API một bộ đếm trong bộ nhớ."""

from __future__ import annotations

import asyncio
import time
from collections import deque
from collections.abc import Awaitable, Callable
from typing import Literal, TypeVar

from app.ports.llm import LlmRateLimited, LlmTimeout, LlmUnavailable

T = TypeVar("T")
State = Literal["CLOSED", "OPEN", "HALF_OPEN"]
COUNTED = (LlmUnavailable, LlmTimeout, LlmRateLimited)


class CircuitOpen(LlmUnavailable):
    def __init__(self, retry_after: float) -> None:
        super().__init__("circuit open")
        self.retry_after = retry_after


def _discard(aw: Awaitable[object]) -> None:
    """Đóng coroutine không được chạy (tránh cảnh báo 'never awaited')."""
    if hasattr(aw, "close"):
        aw.close()


class CircuitBreaker:
    def __init__(self, threshold: int = 5, window_s: float = 60, open_s: float = 30,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.threshold, self.window_s, self.open_s, self._clock = threshold, window_s, open_s, clock
        self.state: State = "CLOSED"
        self._failures: deque[float] = deque()
        self._opened_at = 0.0
        self._probe = asyncio.Lock()

    def _check_open(self) -> None:
        if self.state == "OPEN":
            elapsed = self._clock() - self._opened_at
            if elapsed < self.open_s:
                raise CircuitOpen(self.open_s - elapsed)
            self.state = "HALF_OPEN"

    async def call(self, aw: Awaitable[T]) -> T:
        try:
            self._check_open()
        except CircuitOpen:
            _discard(aw)
            raise
        if self.state == "HALF_OPEN":
            if self._probe.locked():
                _discard(aw)
                raise CircuitOpen(1)
            async with self._probe:
                return await self._run(aw)
        return await self._run(aw)

    async def _run(self, aw: Awaitable[T]) -> T:
        try:
            result = await aw
        except COUNTED:
            self._record_failure()
            raise
        self._failures.clear()
        self.state = "CLOSED"
        return result

    def _record_failure(self) -> None:
        now = self._clock()
        if self.state == "HALF_OPEN":
            self.state, self._opened_at = "OPEN", now
            return
        self._failures.append(now)
        while self._failures and now - self._failures[0] > self.window_s:
            self._failures.popleft()
        if len(self._failures) >= self.threshold:
            self.state, self._opened_at = "OPEN", now
            self._failures.clear()
