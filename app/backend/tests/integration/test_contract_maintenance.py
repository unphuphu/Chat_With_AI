"""Hợp đồng API (T00-06: mọi path/method trong openapi.yaml đều được triển khai) và bảo trì (T07-04, T10-04)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from app.main import create_app
from tests.conftest import csrf, login, upload_ready
from worker.handlers.purge import sweep
from worker.maintenance import audit_partitions, expire_sessions, prune

CONTRACT = Path(__file__).resolve().parents[3] / "contracts" / "openapi.yaml"
METHODS = {"get", "post", "put", "patch", "delete"}


def _ops(paths: dict) -> set[tuple[str, str]]:
    return {(p, m) for p, item in paths.items() for m in item if m in METHODS}


def test_openapi_matches_contract(settings, container) -> None:
    spec = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    app = create_app(settings, container, run_migrations=False, start_worker=False)
    generated = app.openapi()
    prefix = spec["servers"][0]["url"].rstrip("/")  # "/api/v1"
    have = _ops(generated["paths"])
    # /healthz, /readyz nằm ngoài tiền tố /api/v1 trong bản triển khai
    missing = {(p, m) for p, m in _ops(spec["paths"]) if (prefix + p, m) not in have and (p, m) not in have}
    assert not missing, f"Chưa triển khai: {sorted(missing)}"


@pytest.mark.integration
async def test_maintenance_tasks(app_client, worker, pdfs, container) -> None:
    await login(app_client, "p1")
    doc = await upload_ready(app_client, worker, pdfs["contract"])
    async with container.db.admin() as conn:
        await conn.execute("UPDATE session SET idle_expires_at = now() - interval '1 minute'")
    assert await expire_sessions(container.db) == 1
    assert (await app_client.get("/api/v1/me")).status_code == 401
    await prune(container.db, container.settings)
    assert await audit_partitions(container.db, container.settings) >= 0
    # Purge bị sót (job mất) được sweep phát hiện
    await login(app_client, "p1")
    await app_client.delete(f"/api/v1/documents/{doc['id']}", headers=csrf(app_client))
    async with container.db.admin() as conn:
        await conn.execute("DELETE FROM job WHERE kind = 'purge_document'")
        await conn.execute("UPDATE document SET deleted_at = now() - interval '2 hours'")
    await sweep(container.db, container.blob)
    await worker.drain()
    async with container.db.admin() as conn:
        row = await (await conn.execute("SELECT purged_at FROM document")).fetchone()
    assert row["purged_at"] is not None
