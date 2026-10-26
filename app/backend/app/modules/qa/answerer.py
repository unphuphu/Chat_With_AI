"""ALG-06 – sinh câu trả lời trong ngân sách thời gian, kiểm tra trích dẫn, đổi [S#] → [n] (DD-11)."""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.infra.circuit import CircuitBreaker
from app.infra.settings import Settings
from app.modules.qa.prompt import ANSWER_SCHEMA, PROMPT_SYSTEM, REPAIR_HINT, build_user_prompt
from app.modules.retrieval.service import RetrievedChunk
from app.ports.llm import LlmInvalidOutput, LlmPort, LlmRateLimited, LlmTimeout, LlmUnavailable

MARKER = re.compile(r"\[S(\d+)\]")


@dataclass(frozen=True)
class CitationView:
    ordinal: int
    chunk: RetrievedChunk


@dataclass(frozen=True)
class AnswerDraft:
    status: str  # "ANSWERED" | "INSUFFICIENT"
    answer: str | None
    citations: list[CitationView]
    conflict: bool = False


class AnswerTimeout(Exception):
    pass


def validate_output(out: dict[str, Any], chunks: list[RetrievedChunk]) -> AnswerDraft:
    valid = {f"S{i + 1}": c for i, c in enumerate(chunks)}
    status = out.get("status")
    text = str(out.get("answer") or "")
    if status != "answered":
        return AnswerDraft("INSUFFICIENT", None, [])
    # Xóa mã không hợp lệ khỏi văn bản
    text = MARKER.sub(lambda m: m.group(0) if f"S{m.group(1)}" in valid else "", text)
    order: list[str] = []
    for m in MARKER.finditer(text):
        sid = f"S{m.group(1)}"
        if sid not in order:
            order.append(sid)
    for sid in out.get("citations") or []:
        if isinstance(sid, str) and sid in valid and sid not in order:
            order.append(sid)
    if not order or not text.strip():
        return AnswerDraft("INSUFFICIENT", None, [])
    ordinal = {sid: i + 1 for i, sid in enumerate(order)}
    text = MARKER.sub(lambda m: f"[{ordinal[f'S{m.group(1)}']}]", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"[ \t]+([.,;:])", r"\1", text).strip()
    cites = [CitationView(ordinal[sid], valid[sid]) for sid in order]
    return AnswerDraft("ANSWERED", text, cites, bool(out.get("conflict", False)))


class Answerer:
    def __init__(self, llm: LlmPort, breaker: CircuitBreaker, settings: Settings,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self._llm, self._cb, self._s, self._clock = llm, breaker, settings, clock

    async def answer(self, question: str, chunks: list[RetrievedChunk], t0: float) -> AnswerDraft:
        sources = [(f"S{i + 1}", c.content) for i, c in enumerate(chunks)]
        user = build_user_prompt(question, sources)
        deadline = t0 + self._s.answer_budget_s - self._s.llm_safety_margin_s

        async def call(prompt: str, timeout: float) -> dict[str, Any]:
            return await self._cb.call(self._llm.complete_json(system=PROMPT_SYSTEM, user=prompt,
                                                               json_schema=ANSWER_SCHEMA,
                                                               max_output_tokens=self._s.llm_max_output_tokens,
                                                               timeout_s=timeout))

        try:
            out = await call(user, min(self._s.llm_timeout_s, max(0.5, deadline - self._clock())))
        except (LlmRateLimited, LlmUnavailable):
            if self._clock() - t0 > self._s.llm_retry_window_s:
                raise
            remaining = deadline - self._clock()
            if remaining < 2:
                raise
            out = await call(user, remaining)
        except LlmInvalidOutput:
            remaining = deadline - self._clock()
            if remaining < 2:
                raise
            out = await call(user + REPAIR_HINT, remaining)
        except LlmTimeout as e:
            raise AnswerTimeout() from e
        return validate_output(out, chunks)
