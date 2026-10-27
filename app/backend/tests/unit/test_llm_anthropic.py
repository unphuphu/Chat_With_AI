"""UT-014 – ánh xạ lỗi và stop_reason của adapter Anthropic (client giả, không gọi mạng)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import anthropic
import httpx
import pytest

from app.adapters.llm_anthropic import FALLBACK_BETA, AnthropicLlm
from app.ports.llm import LlmInvalidOutput, LlmRateLimited, LlmTimeout, LlmUnavailable

REQ = httpx.Request("POST", "https://api.anthropic.com/v1/messages")


def _resp(status: int) -> httpx.Response:
    return httpx.Response(status, request=REQ)


class FakeClient:
    def __init__(self, result):
        self.result, self.kwargs, self.timeout = result, None, None
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def with_options(self, timeout):
        self.timeout = timeout
        return self

    async def _create(self, **kwargs):
        self.kwargs = kwargs
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def _ok(text: str, stop="end_turn"):
    return SimpleNamespace(stop_reason=stop, content=[SimpleNamespace(type="text", text=text)])


async def _call(result, **kw):
    client = FakeClient(result)
    llm = AnthropicLlm("k", client=client, **kw)
    out = await llm.complete_json(system="s", user="u", json_schema={"type": "object"}, max_output_tokens=1000,
                                  timeout_s=7)
    return out, client


@pytest.mark.parametrize(("exc", "expected"), [
    (anthropic.APITimeoutError(request=REQ), LlmTimeout),
    (anthropic.RateLimitError("x", response=_resp(429), body=None), LlmRateLimited),
    (anthropic.APIConnectionError(request=REQ), LlmUnavailable),
    (anthropic.InternalServerError("x", response=_resp(500), body=None), LlmUnavailable),
])
async def test_error_mapping(exc, expected) -> None:
    with pytest.raises(expected):
        await _call(exc)


async def test_stop_reasons_and_output() -> None:
    out, _ = await _call(SimpleNamespace(stop_reason="refusal", content=[]))
    assert out["status"] == "insufficient"
    with pytest.raises(LlmInvalidOutput):
        await _call(_ok("{}", stop="max_tokens"))
    with pytest.raises(LlmInvalidOutput):
        await _call(_ok("khong phai json"))
    with pytest.raises(LlmInvalidOutput):
        await _call(SimpleNamespace(stop_reason="end_turn", content=[]))
    out, _ = await _call(_ok(json.dumps({"status": "answered", "answer": "a", "citations": ["S1"], "conflict": False})))
    assert out["citations"] == ["S1"]


async def test_request_shape() -> None:
    _, client = await _call(_ok("{}"), model="claude-opus-5-5", effort="medium")
    k = client.kwargs
    assert k["model"] == "claude-opus-5-5" and k["max_tokens"] == 1000 and client.timeout == 7
    assert k["output_config"]["format"]["type"] == "json_schema"
    assert k["betas"] == [FALLBACK_BETA] and k["fallbacks"] == "default"
    _, client = await _call(_ok("{}"), use_fallbacks=False)
    assert "betas" not in client.kwargs
