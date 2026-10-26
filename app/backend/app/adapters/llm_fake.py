"""LLM giả cho test: trả đầu ra theo kịch bản (T04-02)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from app.ports.llm import LlmInvalidOutput, LlmRateLimited, LlmTimeout, LlmUnavailable

Script = dict[str, Any] | Exception | Callable[[str, str], dict[str, Any]]


class FakeLlm:
    name = "fake"

    def __init__(self, default: Script | None = None) -> None:
        self.default: Script = default or (lambda system, user: {
            "status": "answered", "answer": "Theo tài liệu [S1].", "citations": ["S1"], "conflict": False})
        self.queue: list[Script] = []
        self.calls: list[dict[str, Any]] = []
        self.delay_s = 0.0

    async def complete_json(self, *, system: str, user: str, json_schema: dict[str, Any],
                            max_output_tokens: int, timeout_s: float) -> dict[str, Any]:
        self.calls.append({"system": system, "user": user, "timeout_s": timeout_s})
        script = self.queue.pop(0) if self.queue else self.default
        if self.delay_s:
            if self.delay_s > timeout_s:
                await asyncio.sleep(timeout_s)
                raise LlmTimeout("fake timeout")
            await asyncio.sleep(self.delay_s)
        if isinstance(script, Exception):
            raise script
        if callable(script):
            return script(system, user)
        return dict(script)


__all__ = ["FakeLlm", "LlmInvalidOutput", "LlmRateLimited", "LlmTimeout", "LlmUnavailable"]
