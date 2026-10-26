"""LlmPort – sinh câu trả lời dạng JSON (BLUEPRINT 3.2.2, ALG-06, DD-07)."""

from __future__ import annotations

from typing import Any, Protocol


class LlmError(Exception):
    """Lỗi chung khi gọi LLM."""


class LlmRateLimited(LlmError):
    pass


class LlmUnavailable(LlmError):
    pass


class LlmTimeout(LlmError):
    pass


class LlmInvalidOutput(LlmError):
    pass


class LlmPort(Protocol):
    @property
    def name(self) -> str: ...

    async def complete_json(self, *, system: str, user: str, json_schema: dict[str, Any],
                            max_output_tokens: int, timeout_s: float) -> dict[str, Any]: ...
