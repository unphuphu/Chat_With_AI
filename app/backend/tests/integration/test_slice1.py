"""Lát 1 xuyên suốt: schema/RLS (T00-03, T00-05), đăng nhập (T01-*), tải lên (T02-*), xử lý (T03-*),
hỏi đáp có trích dẫn (T04-*)."""

from __future__ import annotations

import uuid

import psycopg
import pytest

from app.infra.db import WorkspaceScopeMissing, require_scope
from tests.conftest import csrf, login, upload, upload_ready

pytestmark = pytest.mark.integration


# ------------------------------------------------------------------ T00-03 / T00-05
async def test_schema_invariants_and_rls(clean_db) -> None:
    db = clean_db
    async with db.admin() as conn:
        await conn.execute("SET app.env = 'dev'")
        seed = (__import__("pathlib").Path(__file__).resolve().parents[2] / "migrations" / "seed_dev.sql")
        await conn.execute(seed.read_text(encoding="utf-8"))
    p1 = uuid.UUID("10000000-0000-4000-8000-000000000001")
    p2 = uuid.UUID("10000000-0000-4000-8000-000000000002")
    async with db.tx("app_api", p1) as conn:
        n1 = (await (await conn.execute("SELECT count(*) AS n FROM document")).fetchone())["n"]
    async with db.tx("app_api", p2) as conn:
        n2 = (await (await conn.execute("SELECT count(*) AS n FROM document")).fetchone())["n"]
    async with db.tx("app_api") as conn:  # không đặt scope → không thấy gì
        n0 = (await (await conn.execute("SELECT count(*) AS n FROM document")).fetchone())["n"]
        with pytest.raises(WorkspaceScopeMissing):
            await require_scope(conn)
    assert (n1, n2, n0) == (3, 0, 0)
    # Trigger hoãn: chèn đoạn cho tài liệu PROCESSING rồi COMMIT → lỗi
    with pytest.raises(psycopg.errors.CheckViolation):
        async with db.admin() as conn:
            await conn.execute(
                "INSERT INTO chunk(document_id, workspace_id, page_number, chunk_index, token_count, content, "
                "embedding_model, embedding) VALUES ('20000000-0000-4000-8000-000000000002', %s, 1, 0, 1, 'x', 'm', "
                "array_fill(0.03125::real, ARRAY[1024])::vector)", (p1,))
    # READY → PROCESSING bị chặn
    with pytest.raises(psycopg.errors.CheckViolation):
        async with db.admin() as conn:
            await conn.execute("UPDATE document SET status='PROCESSING', ready_at=NULL "
                               "WHERE id='20000000-0000-4000-8000-000000000001'")


async def test_set_local_does_not_leak(clean_db) -> None:
    ws = uuid.uuid4()
    async with clean_db.tx("app_api", ws) as conn:
        assert await require_scope(conn) == ws
    async with clean_db.tx("app_api") as conn:
        with pytest.raises(WorkspaceScopeMissing):
            await require_scope(conn)


# ------------------------------------------------------------------ T01
async def test_login_me_logout(app_client, clean_db) -> None:
    r = await login(app_client, "p1")
    assert r.status_code == 302 and r.headers["location"] == "http://testserver/"
    assert app_client.cookies.get("sid") and app_client.cookies.get("csrf_token")
    me = await app_client.get("/api/v1/me")
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "lan.nguyen@congty.vn" and body["documents_limit"] == 100
    assert body["limits"]["max_files_per_batch"] == 10
    # Đăng nhập lần 2 không tạo workspace thứ hai
    await login(app_client, "p1")
    async with clean_db.admin() as conn:
        n = (await (await conn.execute("SELECT count(*) AS n FROM workspace")).fetchone())["n"]
    assert n == 1
    # Đăng xuất cần CSRF
    assert (await app_client.post("/api/v1/auth/logout")).status_code == 403
    assert (await app_client.post("/api/v1/auth/logout", headers=csrf(app_client))).status_code == 204
    r = await app_client.get("/api/v1/me")
    assert r.status_code == 401 and r.json()["code"] == "unauthenticated"


async def test_outsider_denied_and_audited(app_client, clean_db) -> None:
    r = await login(app_client, "outsider")
    assert r.headers["location"] == "http://testserver/access-denied"
    async with clean_db.admin() as conn:
        row = await (await conn.execute("SELECT count(*) AS n FROM audit_event WHERE action='login_denied'")).fetchone()
    assert row["n"] == 1


async def test_open_redirect_blocked(app_client) -> None:
    r = await app_client.get("/api/v1/auth/login", params={"return_to": "https://evil.example"})
    from urllib.parse import parse_qs, urlparse

    state = parse_qs(urlparse(r.headers["location"]).query)["state"][0]
    r = await app_client.get("/api/v1/auth/callback", params={"code": "p1", "state": state})
    assert r.headers["location"] == "http://testserver/"


# ------------------------------------------------------------------ T02–T04 luồng chính
async def test_upload_process_ask(app_client, worker, pdfs, container) -> None:
    await login(app_client, "p1")
    r = await upload(app_client, pdfs["contract"])
    assert r.status_code == 201, r.text
    doc = r.json()
    assert doc["status"] == "PROCESSING" and doc["page_count"] == 3 and doc["retryable"] is False
    # Chưa có tài liệu Sẵn sàng → 409
    conv = (await app_client.get("/api/v1/conversations/current")).json()
    r = await app_client.post(f"/api/v1/conversations/{conv['id']}/messages", headers=csrf(app_client),
                              json={"client_request_id": str(uuid.uuid4()), "question": "Thanh toán?"})
    assert r.status_code == 409 and r.json()["code"] == "no_ready_documents"
    assert await worker.drain() == 1
    docs = (await app_client.get("/api/v1/documents")).json()
    assert docs["items"][0]["status"] == "READY" and docs["documents_used"] == 1
    # Hỏi – LLM giả trích S1
    r = await app_client.post(f"/api/v1/conversations/{conv['id']}/messages", headers=csrf(app_client),
                              json={"client_request_id": str(uuid.uuid4()),
                                    "question": "Điều khoản thanh toán là gì?"})
    assert r.status_code == 200, r.text
    ans = r.json()
    assert ans["status"] == "ANSWERED" and ans["answer"] == "Theo tài liệu [1]."
    assert ans["citations"][0]["document_name"] == "hop-dong-A.pdf" and ans["citations"][0]["page_number"] >= 1
    # Không gửi ID/tên file/số trang ra LLM (NFR-011)
    sent = container.llm.calls[-1]["user"]
    assert "hop-dong-A.pdf" not in sent and doc["id"] not in sent and "<source id=\"S1\">" in sent
    # Hội thoại giữ khi tải lại
    conv2 = (await app_client.get("/api/v1/conversations/current")).json()
    assert conv2["id"] == conv["id"] and len(conv2["messages"]) == 1  # một lượt = câu hỏi + câu trả lời
    assert conv2["messages"][0]["citations"][0]["document_name"] == "hop-dong-A.pdf"


async def test_extractive_answer_cites_correct_page(app_client, worker, pdfs, container) -> None:
    from app.adapters.llm_extractive import ExtractiveLlm

    container.answerer._llm = ExtractiveLlm()
    await login(app_client, "p1")
    await upload_ready(app_client, worker, pdfs["contract"])
    conv = (await app_client.get("/api/v1/conversations/current")).json()
    r = await app_client.post(f"/api/v1/conversations/{conv['id']}/messages", headers=csrf(app_client),
                              json={"client_request_id": str(uuid.uuid4()),
                                    "question": "Bên B thanh toán trong vòng bao nhiêu ngày?"})
    ans = r.json()
    assert ans["status"] == "ANSWERED", ans
    assert "30 ngày" in ans["answer"] and ans["citations"][0]["page_number"] == 2
    r = await app_client.post(f"/api/v1/conversations/{conv['id']}/messages", headers=csrf(app_client),
                              json={"client_request_id": str(uuid.uuid4()),
                                    "question": "Đối thủ cạnh tranh tại thị trường Nhật Bản là ai?"})
    assert r.json()["status"] == "INSUFFICIENT" and r.json()["citations"] == []



async def test_extractive_multi_document_price(app_client, worker, pdfs, container) -> None:
    """Câu hỏi có hư từ ("là bao nhiêu") vẫn qua cổng nhờ full-text OR; trả lời từ hai tài liệu."""
    from app.adapters.llm_extractive import ExtractiveLlm

    container.answerer._llm = ExtractiveLlm()
    container.settings.__dict__["retrieval_min_similarity"] = 0.45  # như dev
    try:
        await login(app_client, "p1")
        for k in ("contract", "policy", "price"):
            await upload_ready(app_client, worker, pdfs[k])
        conv = (await app_client.get("/api/v1/conversations/current")).json()
        r = await app_client.post(f"/api/v1/conversations/{conv['id']}/messages", headers=csrf(app_client),
                                  json={"client_request_id": str(uuid.uuid4()),
                                        "question": "Giá gói Premium là bao nhiêu?"})
    finally:
        container.settings.__dict__["retrieval_min_similarity"] = 0.2
    ans = r.json()
    assert ans["status"] == "ANSWERED", ans
    assert {c["document_name"] for c in ans["citations"]} == {"bang-gia-Q4.pdf", "chinh-sach-ban-hang-2026.pdf"}
    assert "12.500.000" in ans["answer"] and "11.900.000" in ans["answer"]
