"""Hỏi đáp: idempotency/gửi lại (T04-05, T09), lỗi AI + circuit breaker (T09), rate limit (T10), kiểm tra
câu hỏi, trích dẫn tài liệu đã xóa (T07-03), không lộ nội dung vào log/analytics (NFR-011)."""

from __future__ import annotations

import uuid

import pytest

from app.ports.llm import LlmUnavailable
from tests.conftest import csrf, login, upload_ready

pytestmark = pytest.mark.integration


async def _ready(app_client, worker, pdfs) -> str:
    await login(app_client, "p1")
    await upload_ready(app_client, worker, pdfs["contract"])
    return (await app_client.get("/api/v1/conversations/current")).json()["id"]


async def _ask(client, conv: str, question: str, crid: str | None = None):
    return await client.post(f"/api/v1/conversations/{conv}/messages", headers=csrf(client),
                             json={"client_request_id": crid or str(uuid.uuid4()), "question": question})


async def test_idempotent_ask(app_client, worker, pdfs, container) -> None:
    conv = await _ready(app_client, worker, pdfs)
    crid = str(uuid.uuid4())
    r1 = await _ask(app_client, conv, "Điều khoản thanh toán?", crid)
    r2 = await _ask(app_client, conv, "Điều khoản thanh toán?", crid)
    assert r1.json() == {**r2.json(), "conflict": r1.json()["conflict"]}
    assert len(container.llm.calls) == 1
    r3 = await _ask(app_client, conv, "Câu khác", crid)
    assert r3.status_code == 422 and r3.json()["code"] == "idempotency_mismatch"


async def test_ai_failure_then_resend(app_client, worker, pdfs, container) -> None:
    conv = await _ready(app_client, worker, pdfs)
    container.llm.queue = [LlmUnavailable("down"), LlmUnavailable("down")]
    crid = str(uuid.uuid4())
    r = await _ask(app_client, conv, "Điều khoản thanh toán?", crid)
    assert r.status_code == 503 and r.json()["code"] == "ai_unavailable" and "retry-after" in r.headers
    cur = (await app_client.get("/api/v1/conversations/current")).json()
    assert cur["messages"][0]["status"] == "FAILED"
    r = await _ask(app_client, conv, "Điều khoản thanh toán?", crid)  # gửi lại cùng client_request_id
    assert r.status_code == 200 and r.json()["status"] == "ANSWERED"
    async with container.db.admin() as conn:
        m = await (await conn.execute("SELECT attempt FROM message")).fetchone()
        ev = await (await conn.execute(
            "SELECT count(*) AS n FROM analytics_event WHERE event_name='question_retried'")).fetchone()
    assert m["attempt"] == 2 and ev["n"] == 1


async def test_ai_timeout(app_client, worker, pdfs, container) -> None:
    conv = await _ready(app_client, worker, pdfs)
    container.settings.__dict__["answer_budget_s"] = 1.0
    container.llm.delay_s = 5
    try:
        r = await _ask(app_client, conv, "Điều khoản thanh toán?")
    finally:
        container.settings.__dict__["answer_budget_s"] = 15
        container.llm.delay_s = 0
    assert r.status_code == 504 and r.json()["code"] == "ai_timeout"


async def test_invalid_citation_repaired_or_insufficient(app_client, worker, pdfs, container) -> None:
    conv = await _ready(app_client, worker, pdfs)
    bad = {"status": "answered", "answer": "Bịa [S9].", "citations": ["S9"], "conflict": False}
    container.llm.queue = [bad, bad]
    r = await _ask(app_client, conv, "Điều khoản thanh toán?")
    assert r.status_code == 200 and r.json()["status"] == "INSUFFICIENT" and r.json()["citations"] == []


async def test_gate_skips_llm(app_client, worker, pdfs, container) -> None:
    conv = await _ready(app_client, worker, pdfs)
    container.settings.__dict__["retrieval_min_similarity"] = 0.99
    try:
        r = await _ask(app_client, conv, "Thời tiết Hà Nội hôm nay thế nào?")
    finally:
        container.settings.__dict__["retrieval_min_similarity"] = 0.2
    assert r.json()["status"] == "INSUFFICIENT" and container.llm.calls == []


async def test_circuit_breaker_opens(app_client, worker, pdfs, container) -> None:
    conv = await _ready(app_client, worker, pdfs)
    container.llm.default = LlmUnavailable("down")
    for _ in range(5):
        await _ask(app_client, conv, "Điều khoản thanh toán?")
    calls = len(container.llm.calls)
    r = await _ask(app_client, conv, "Điều khoản thanh toán?")
    assert r.status_code == 503 and int(r.headers["retry-after"]) >= 1
    assert len(container.llm.calls) == calls  # mạch mở → không gọi LLM


async def test_question_validation(app_client, worker, pdfs) -> None:
    conv = await _ready(app_client, worker, pdfs)
    r = await _ask(app_client, conv, "   ")
    assert r.status_code == 422 and r.json()["code"] == "empty_question"
    r = await _ask(app_client, conv, "x" * 2001)
    assert r.status_code == 422 and r.json()["code"] == "question_too_long"
    r = await _ask(app_client, str(uuid.uuid4()), "Hỏi")
    assert r.status_code == 404


async def test_rate_limit_questions(app_client, worker, pdfs, container) -> None:
    conv = await _ready(app_client, worker, pdfs)
    container.settings.__dict__["rate_questions_per_min"] = 2
    try:
        codes = [(await _ask(app_client, conv, f"Câu {i}")).status_code for i in range(3)]
        r = await _ask(app_client, conv, "Câu 4")
    finally:
        container.settings.__dict__["rate_questions_per_min"] = 1000
    assert codes[:2] == [200, 200] and codes[2] == 429
    assert r.json()["code"] == "rate_limited" and int(r.headers["retry-after"]) >= 1


async def test_citation_of_deleted_document(app_client, worker, pdfs, container) -> None:
    conv = await _ready(app_client, worker, pdfs)
    ans = (await _ask(app_client, conv, "Điều khoản thanh toán?")).json()
    doc_id = ans["citations"][0]["document_id"]
    await app_client.delete(f"/api/v1/documents/{doc_id}", headers=csrf(app_client))
    cur = (await app_client.get("/api/v1/conversations/current")).json()
    c = cur["messages"][0]["citations"][0]
    assert c["deleted"] is True and c["document_name"] == "hop-dong-A.pdf"


async def test_no_content_in_analytics(app_client, worker, pdfs, container, capsys) -> None:
    conv = await _ready(app_client, worker, pdfs)
    secret_q = "Bí mật XYZZY thanh toán?"
    await _ask(app_client, conv, secret_q)
    async with container.db.admin() as conn:
        rows = await (await conn.execute("SELECT properties::text AS p FROM analytics_event")).fetchall()
        audit = await (await conn.execute("SELECT row_to_json(a)::text AS p FROM audit_event a")).fetchall()
    blob = " ".join(r["p"] for r in rows + audit)
    assert "XYZZY" not in blob and "hop-dong-A" not in blob and "lan.nguyen" not in blob
    assert "XYZZY" not in capsys.readouterr().out
