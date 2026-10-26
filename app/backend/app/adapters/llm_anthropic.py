"""Adapter Claude (Anthropic SDK chính thức) cho LlmPort (T04-02, SAD ADR-007).

* Structured outputs: `output_config.format` = JSON schema của ALG-06 → phản hồi luôn là JSON hợp lệ.
* Server-side fallback khi mô hình từ chối vì chính sách (`fallbacks: "default"`).
* `stop_reason == "refusal"` → coi như "chưa đủ thông tin" (không trả nội dung).
* Không thử lại trong SDK (max_retries=0): ngân sách 15 s và quy tắc thử lại nằm ở Answerer (ALG-06).
* Không ghi prompt hay phản hồi vào log; chỉ gửi câu hỏi + đoạn trích S1…S8 (NFR-011, DD-07).
"""

from __future__ import annotations

import json
from typing import Any

import anthropic

from app.ports.llm import LlmInvalidOutput, LlmRateLimited, LlmTimeout, LlmUnavailable

FALLBACK_BETA = "server-side-fallback-2026-07-01"


class AnthropicLlm:
    name = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-opus-5-5", effort: str = "medium",
                 use_fallbacks: bool = True, client: anthropic.AsyncAnthropic | None = None) -> None:
        self._client = client or anthropic.AsyncAnthropic(api_key=api_key or None, max_retries=0)
        self._model = model
        self._effort = effort
        self._use_fallbacks = use_fallbacks

    async def complete_json(self, *, system: str, user: str, json_schema: dict[str, Any],
                            max_output_tokens: int, timeout_s: float) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": max_output_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "output_config": {"effort": self._effort,
                              "format": {"type": "json_schema", "schema": json_schema}},
        }
        if self._use_fallbacks:
            kwargs["betas"] = [FALLBACK_BETA]
            kwargs["fallbacks"] = "default"
        try:
            response = await self._client.with_options(timeout=timeout_s).beta.messages.create(**kwargs)
        except anthropic.APITimeoutError as e:
            raise LlmTimeout("timeout") from e
        except anthropic.RateLimitError as e:
            raise LlmRateLimited("rate limited") from e
        except anthropic.APIConnectionError as e:
            raise LlmUnavailable("connection error") from e
        except anthropic.APIStatusError as e:
            raise LlmUnavailable(f"status {e.status_code}") from e

        if response.stop_reason == "refusal":
            return {"status": "insufficient", "answer": "", "citations": [], "conflict": False}
        if response.stop_reason == "max_tokens":
            raise LlmInvalidOutput("max_tokens reached")
        text = next((b.text for b in response.content if b.type == "text"), None)
        if not text:
            raise LlmInvalidOutput("no text block")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise LlmInvalidOutput("invalid json") from e
        if not isinstance(data, dict):
            raise LlmInvalidOutput("not an object")
        return data
