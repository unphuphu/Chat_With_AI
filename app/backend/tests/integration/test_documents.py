"""Tải lên/từ chối/hạn mức (T02, T05), xóa + purge (T07), xử lý lại (T11), cách ly (T08), xem file (T11-04)."""

from __future__ import annotations

import uuid

import pytest

from tests.conftest import csrf, login, new_client, upload, upload_ready

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(("key", "code"), [
    ("scan", None),  # PDF scan được nhận, thất bại R-03 khi xử lý
    ("too_many_pages", "too_many_pages"),
    ("encrypted", "encrypted"),
    ("broken", "not_pdf"),
    ("docx", "not_pdf"),
    ("fake_pdf", "not_pdf"),
])
async def test_rejections(app_client, worker, pdfs, key, code) -> None:
    await login(app_client, "p1")
    r = await upload(app_client, pdfs[key])
    if code is None:
        assert r.status_code == 201
        await worker.drain()
        doc = (await app_client.get("/api/v1/documents")).json()["items"][0]
        assert doc["status"] == "FAILED" and doc["failure_code"] == "R-03" and doc["retryable"] is False
        return
    assert r.status_code == 422, r.text
    body = r.json()
    assert body["code"] == code and body["status"] == 422
    assert r.headers["content-type"].startswith("application/problem+json")
    assert (await app_client.get("/api/v1/documents")).json()["items"] == []


async def test_encrypted_without_user_password_is_accepted(app_client, worker, pdfs) -> None:
    await login(app_client, "p1")
    assert (await upload(app_client, pdfs["encrypted_empty"])).status_code == 201


async def test_too_large(app_client, tmp_path) -> None:
    await login(app_client, "p1")
    big = tmp_path / "lon.pdf"
    big.write_bytes(b"%PDF-1.4\n" + b"0" * (2 * 1024 * 1024 + 10))
    r = await upload(app_client, big)
    assert r.status_code == 422 and r.json()["code"] == "too_large"


async def test_upload_idempotent_and_batch_slots(app_client, pdfs) -> None:
    await login(app_client, "p1")
    r = await app_client.post("/api/v1/upload-batches", headers=csrf(app_client),
                              json={"files": [{"name": "a.pdf", "size_bytes": 10}]})
    batch = r.json()["batch_id"]
    cid = str(uuid.uuid4())
    r1 = await upload(app_client, pdfs["contract"], cid, batch)
    r2 = await upload(app_client, pdfs["contract"], cid, batch)
    assert (r1.status_code, r2.status_code) == (201, 200) and r1.json()["id"] == r2.json()["id"]
    r3 = await upload(app_client, pdfs["policy"], None, batch)
    assert r3.status_code == 409 and r3.json()["code"] == "batch_full"


async def test_batch_limits(app_client, container) -> None:
    await login(app_client, "p1")
    r = await app_client.post("/api/v1/upload-batches", headers=csrf(app_client),
                              json={"files": [{"name": f"{i}.pdf", "size_bytes": 1} for i in range(11)]})
    assert r.status_code == 422 and r.json()["code"] == "too_many_files"
    # Hạn mức 100 tài liệu/workspace: chèn sẵn 99 tài liệu
    async with container.db.admin() as conn:
        await conn.execute(
            "INSERT INTO document(workspace_id, client_file_id, file_name, size_bytes, page_count, storage_key, "
            "sha256, uploaded_by) SELECT w.id, gen_random_uuid(), 'x'||g||'.pdf', 1, 1, 'k'||g, "
            "sha256(g::text::bytea), w.personal_owner_id FROM generate_series(1, 99) g, workspace w")
    r = await app_client.post("/api/v1/upload-batches", headers=csrf(app_client),
                              json={"files": [{"name": "a.pdf", "size_bytes": 1}, {"name": "b.pdf", "size_bytes": 1}]})
    assert r.status_code == 422 and r.json()["code"] == "quota_exceeded" and r.json()["remaining"] == 1


async def test_delete_purge_and_answers_exclude(app_client, worker, pdfs, container) -> None:
    await login(app_client, "p1")
    doc = await upload_ready(app_client, worker, pdfs["contract"])
    blob_key = None
    async with container.db.admin() as conn:
        row = await (await conn.execute("SELECT storage_key FROM document WHERE id=%s", (doc["id"],))).fetchone()
        blob_key = row["storage_key"]
    assert await container.blob.exists(blob_key)
    r = await app_client.delete(f"/api/v1/documents/{doc['id']}", headers=csrf(app_client))
    assert r.status_code == 204
    assert (await app_client.get("/api/v1/documents")).json()["items"] == []
    async with container.db.admin() as conn:
        n = (await (await conn.execute("SELECT count(*) AS n FROM chunk WHERE document_id=%s",
                                       (doc["id"],))).fetchone())["n"]
    assert n == 0
    await worker.drain()
    assert not await container.blob.exists(blob_key)
    r = await app_client.get(f"/api/v1/documents/{doc['id']}/file")
    assert r.status_code == 410 and r.json()["code"] == "deleted"
    # Xóa lần 2 → 404 + audit access_denied
    r = await app_client.delete(f"/api/v1/documents/{doc['id']}", headers=csrf(app_client))
    assert r.status_code == 404


async def test_delete_during_processing_cancels(app_client, worker, pdfs, container) -> None:
    await login(app_client, "p1")
    doc = (await upload(app_client, pdfs["contract"])).json()
    assert (await app_client.delete(f"/api/v1/documents/{doc['id']}", headers=csrf(app_client))).status_code == 204
    await worker.drain()
    async with container.db.admin() as conn:
        rows = await (await conn.execute("SELECT kind, status FROM job ORDER BY id")).fetchall()
        chunks = (await (await conn.execute("SELECT count(*) AS n FROM chunk")).fetchone())["n"]
    assert {(r["kind"], r["status"]) for r in rows} == {("ingest_document", "CANCELLED"),
                                                        ("purge_document", "DONE")}
    assert chunks == 0


async def test_reprocess_only_r04(app_client, worker, pdfs, container) -> None:
    await login(app_client, "p1")
    doc = (await upload(app_client, pdfs["contract"])).json()
    container.embedding.fail_times = 99  # embedding hỏng → retry rồi R-04
    for _ in range(container.settings.ingest_max_attempts):
        async with container.db.admin() as conn:
            await conn.execute("UPDATE job SET run_after = now() WHERE status = 'QUEUED'")
        await worker.drain()
    d = (await app_client.get("/api/v1/documents")).json()["items"][0]
    assert d["status"] == "FAILED" and d["failure_code"] == "R-04" and d["retryable"] is True
    container.embedding.fail_times = 0
    r = await app_client.post(f"/api/v1/documents/{doc['id']}/reprocess", headers=csrf(app_client))
    assert r.status_code == 202 and r.json()["status"] == "PROCESSING"
    await worker.drain()
    d = (await app_client.get("/api/v1/documents")).json()["items"][0]
    assert d["status"] == "READY"
    r = await app_client.post(f"/api/v1/documents/{doc['id']}/reprocess", headers=csrf(app_client))
    assert r.status_code == 409 and r.json()["code"] == "not_retryable"


async def test_isolation_between_users(app_client, worker, pdfs, container) -> None:
    await login(app_client, "p1")
    doc = await upload_ready(app_client, worker, pdfs["contract"])
    other = await new_client(app_client)
    async with other:
        await login(other, "p2")
        assert (await other.get("/api/v1/documents")).json()["items"] == []
        assert (await other.get(f"/api/v1/documents/{doc['id']}/file")).status_code == 404
        r = await other.delete(f"/api/v1/documents/{doc['id']}", headers=csrf(other))
        assert r.status_code == 404
        # P2 chưa có tài liệu → không hỏi được; không thấy hội thoại của P1
        conv1 = (await app_client.get("/api/v1/conversations/current")).json()
        r = await other.post(f"/api/v1/conversations/{conv1['id']}/messages", headers=csrf(other),
                             json={"client_request_id": str(uuid.uuid4()), "question": "Thanh toán?"})
        assert r.status_code in (404, 409)
    async with container.db.admin() as conn:
        n = (await (await conn.execute("SELECT count(*) AS n FROM audit_event WHERE action='access_denied'"))
             .fetchone())["n"]
    assert n >= 1
    # Tài liệu P1 vẫn còn
    assert len((await app_client.get("/api/v1/documents")).json()["items"]) == 1


async def test_view_file(app_client, worker, pdfs) -> None:
    await login(app_client, "p1")
    doc = await upload_ready(app_client, worker, pdfs["contract"])
    r = await app_client.get(f"/api/v1/documents/{doc['id']}/file", params={"from": "citation", "page": 2})
    assert r.status_code == 200 and r.content.startswith(b"%PDF-")
    assert r.headers["content-type"] == "application/pdf"
    assert "hop-dong-A.pdf" in r.headers["content-disposition"]
    assert r.headers["x-frame-options"] == "SAMEORIGIN"  # nhúng được vào trình xem S06


async def test_unauthenticated_and_csrf(app_client) -> None:
    assert (await app_client.get("/api/v1/documents")).status_code == 401
    await login(app_client, "p1")
    r = await app_client.post("/api/v1/upload-batches", json={"files": [{"name": "a.pdf", "size_bytes": 1}]})
    assert r.status_code == 403 and r.json()["code"] == "csrf_invalid"
