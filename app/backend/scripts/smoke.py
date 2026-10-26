"""Smoke test đầu-cuối trên môi trường đang chạy (run.py): đăng nhập OIDC qua devidp → tải PDF mẫu →
chờ Sẵn sàng → hỏi → kiểm tra trích dẫn. Dùng: python scripts/smoke.py [http://localhost:8080]"""

from __future__ import annotations

import re
import sys
import time
import uuid
from pathlib import Path

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
SAMPLES = Path(__file__).resolve().parents[2] / "sample-pdfs"


def main() -> None:
    c = httpx.Client(base_url=BASE, timeout=60)
    r = c.get("/api/v1/auth/login", params={"return_to": "/"})
    idp = httpx.Client(timeout=30)
    form = idp.get(r.headers["location"])
    fields = dict(re.findall(r'name="(\w+)" value="([^"]*)"', form.text))
    fields["user"] = "p1"
    r = idp.post(str(form.url).split("?")[0], data=fields)
    cb = r.headers["location"]
    assert cb.startswith(BASE), cb
    r = c.get(cb.removeprefix(BASE))
    assert r.status_code == 302 and c.cookies.get("sid"), r.text
    h = {"X-CSRF-Token": c.cookies["csrf_token"]}
    print("login ok:", c.get("/api/v1/me").json()["email"])

    pdfs = [SAMPLES / n for n in ("hop-dong-A.pdf", "chinh-sach-ban-hang-2026.pdf", "bang-gia-Q4.pdf")]
    existing = {d["file_name"] for d in c.get("/api/v1/documents").json()["items"]}
    todo = [p for p in pdfs if p.name not in existing]
    if todo:
        b = c.post("/api/v1/upload-batches", headers=h,
                   json={"files": [{"name": p.name, "size_bytes": p.stat().st_size} for p in todo]}).json()
        for p in todo:
            r = c.put(f"/api/v1/upload-batches/{b['batch_id']}/files/{uuid.uuid4()}", headers=h,
                      files={"file": (p.name, p.read_bytes(), "application/pdf")})
            print("upload", p.name, r.status_code)
    for _ in range(120):
        docs = c.get("/api/v1/documents").json()["items"]
        if docs and all(d["status"] != "PROCESSING" for d in docs):
            break
        time.sleep(1)
    print("documents:", [(d["file_name"], d["status"]) for d in docs])
    conv = c.get("/api/v1/conversations/current").json()["id"]
    for q in ("Bên B thanh toán trong vòng bao nhiêu ngày?", "Giá gói Premium là bao nhiêu?",
              "Đối thủ cạnh tranh tại thị trường Nhật Bản là ai?"):
        t = time.monotonic()
        a = c.post(f"/api/v1/conversations/{conv}/messages", headers=h,
                   json={"client_request_id": str(uuid.uuid4()), "question": q}).json()
        cites = [(x["document_name"], x["page_number"]) for x in a.get("citations", [])]
        print(f"\nQ: {q}\n  {a.get('status')} ({time.monotonic() - t:.1f}s): {a.get('answer')}\n  nguồn: {cites}")


if __name__ == "__main__":
    main()
