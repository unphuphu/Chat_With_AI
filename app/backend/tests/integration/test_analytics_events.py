"""INT-018 – đủ 11 sự kiện EVT-01…EVT-11, thuộc tính nằm trong whitelist, không chứa nội dung (G-07)."""

from __future__ import annotations

import uuid

import pytest

from app.adapters.llm_extractive import ExtractiveLlm
from app.modules.events.analytics import ALLOWED
from app.ports.llm import LlmUnavailable
from tests.conftest import csrf, login, new_client, upload, upload_ready

pytestmark = pytest.mark.integration


async def test_all_eleven_events(app_client, worker, pdfs, container) -> None:
    container.answerer._llm = ExtractiveLlm()
    await login(app_client, "p1")
    # EVT-01/02: tạo lô, một file bị từ chối
    assert (await upload(app_client, pdfs["docx"])).status_code == 422
    # EVT-03: Sẵn sàng; EVT-04: thất bại (scan)
    doc = await upload_ready(app_client, worker, pdfs["contract"])
    await upload(app_client, pdfs["scan"])
    await worker.drain()
    conv = (await app_client.get("/api/v1/conversations/current")).json()["id"]
    # EVT-06/07
    q = "Bên B thanh toán trong vòng bao nhiêu ngày?"
    crid = str(uuid.uuid4())
    container.answerer._llm = container.llm  # FakeLlm lỗi để tạo EVT-08
    container.llm.queue = [LlmUnavailable("x"), LlmUnavailable("x")]
    r = await app_client.post(f"/api/v1/conversations/{conv}/messages", headers=csrf(app_client),
                              json={"client_request_id": crid, "question": q})
    assert r.status_code == 503  # EVT-08
    r = await app_client.post(f"/api/v1/conversations/{conv}/messages", headers=csrf(app_client),
                              json={"client_request_id": crid, "question": q})  # gửi lại → EVT-10, rồi EVT-07
    assert r.status_code == 200
    # EVT-09: mở file từ nguồn
    await app_client.get(f"/api/v1/documents/{doc['id']}/file", params={"from": "citation", "page": 2})
    # EVT-05: xóa
    await app_client.delete(f"/api/v1/documents/{doc['id']}", headers=csrf(app_client))
    # EVT-11: P2 truy cập tài liệu của P1
    other = await new_client(app_client)
    async with other:
        await login(other, "p2")
        await other.delete(f"/api/v1/documents/{doc['id']}", headers=csrf(other))
    async with container.db.admin() as conn:
        rows = await (await conn.execute("SELECT event_name, properties FROM analytics_event")).fetchall()
    names = {r["event_name"] for r in rows}
    assert names == set(ALLOWED), f"thiếu: {set(ALLOWED) - names}; thừa: {names - set(ALLOWED)}"
    blob = str(rows)
    for r in rows:
        assert set(r["properties"]) <= ALLOWED[r["event_name"]]
    assert q not in blob and "hop-dong-A" not in blob and "lan.nguyen" not in blob
