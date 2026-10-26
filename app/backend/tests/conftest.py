"""Fixture dùng chung.

Integration test dùng PostgreSQL thật: PGlite (WASM) khởi động trong bộ nhớ trên cổng ngẫu nhiên
(`app/devdb/server.mjs`). Đặt TEST_DATABASE_URL để chạy với PostgreSQL thật (CI có Docker).
"""

from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import sys
import time
import warnings
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse
from uuid import UUID

import httpx
import psycopg
import pytest
import pytest_asyncio

from app.adapters.blob_memory import MemoryBlobStore
from app.adapters.embedding_hashing import HashingEmbedding
from app.adapters.llm_fake import FakeLlm
from app.container import Container
from app.infra.db import Database
from app.infra.migrate import migrate
from app.infra.settings import Settings
from app.main import create_app
from app.ports.identity import IdentityError, IdTokenClaims
from tests.fixtures.pdfgen import make_all

APP_DIR = Path(__file__).resolve().parents[2]
TABLES = ("app_user, workspace, membership, session, upload_batch, document, chunk, job, conversation, message, "
          "citation, rate_limit_counter, audit_event, analytics_event")

USERS = {
    "p1": IdTokenClaims("dev|p1", "lan.nguyen@congty.vn", frozenset({"aichat-users"})),
    "p2": IdTokenClaims("dev|p2", "minh.tran@congty.vn", frozenset({"aichat-users"})),
    "admin": IdTokenClaims("dev|admin", "admin@congty.vn", frozenset({"aichat-admins"})),
    "outsider": IdTokenClaims("dev|outsider", "khach@congty.vn", frozenset()),
}


class FakeIdp:
    async def authorization_url(self, *, state: str, nonce: str, code_challenge: str, redirect_uri: str) -> str:
        return f"http://idp.test/authorize?state={state}&nonce={nonce}"

    async def exchange_code(self, *, code: str, code_verifier: str, nonce: str, redirect_uri: str) -> IdTokenClaims:
        if code not in USERS:
            raise IdentityError("bad_code")
        return USERS[code]


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    if url := os.environ.get("TEST_DATABASE_URL"):
        yield url
        return
    port = _free_port()
    env = {**os.environ, "DEVDB_DIR": "memory://", "DEVDB_PORT": str(port)}
    proc = subprocess.Popen(["node", "server.mjs"], cwd=APP_DIR / "devdb", env=env,  # noqa: S607
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    url = f"postgresql://postgres:postgres@127.0.0.1:{port}/postgres?sslmode=disable"
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            psycopg.connect(url, connect_timeout=2).close()
            break
        except psycopg.OperationalError:
            if proc.poll() is not None:
                raise RuntimeError(proc.stdout.read().decode() if proc.stdout else "devdb exited") from None
            time.sleep(0.3)
    else:
        proc.kill()
        raise RuntimeError("devdb did not start")
    yield url
    proc.terminate()
    try:
        proc.wait(5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope="session")
def settings(database_url: str) -> Settings:
    return Settings(env="test", database_url=database_url, db_mode="single", blob_provider="memory",
                    embedding_provider="hashing", llm_provider="fake", max_pages=5, max_file_mb=2,
                    public_base_url="http://testserver", cookie_secure=False, sandbox_wait_s=30,
                    rate_questions_per_min=1000, rate_files_per_hour=1000, retrieval_min_similarity=0.2)


@pytest_asyncio.fixture(scope="session")
async def db(settings: Settings) -> AsyncIterator[Database]:
    database = Database(settings.database_url, "single")
    await database.open()
    await migrate(database)
    yield database
    await database.close()


@pytest_asyncio.fixture
async def clean_db(db: Database) -> AsyncIterator[Database]:
    async with db.admin() as conn:
        await conn.execute(f"TRUNCATE {TABLES} CASCADE")
    yield db


@pytest.fixture(scope="session")
def pdfs(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    return make_all(tmp_path_factory.mktemp("pdfs"), max_pages=5)


@pytest_asyncio.fixture
async def container(settings: Settings, clean_db: Database) -> Container:
    return Container.from_settings(settings, db=clean_db, blob=MemoryBlobStore(),
                                   embedding=HashingEmbedding(settings.embedding_model_id), llm=FakeLlm(),
                                   idp=FakeIdp())


@pytest_asyncio.fixture
async def app_client(container: Container, settings: Settings) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(settings, container, run_migrations=False, start_worker=False)
    app.state.container = container
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture
async def worker(container: Container) -> Any:
    from worker.main import Worker

    return Worker(container)


async def login(client: httpx.AsyncClient, user: str = "p1") -> httpx.Response:
    r = await client.get("/api/v1/auth/login", params={"return_to": "/"})
    assert r.status_code == 302, r.text
    state = parse_qs(urlparse(r.headers["location"]).query)["state"][0]
    return await client.get("/api/v1/auth/callback", params={"code": user, "state": state})


def csrf(client: httpx.AsyncClient) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("csrf_token") or ""}


async def new_client(app_client: httpx.AsyncClient) -> httpx.AsyncClient:
    """Client thứ hai (người dùng khác) dùng chung app."""
    return httpx.AsyncClient(transport=app_client._transport, base_url="http://testserver")


async def upload(client: httpx.AsyncClient, path: Path, client_file_id: str | None = None,
                 batch_id: str | None = None) -> httpx.Response:
    import uuid

    if batch_id is None:
        r = await client.post("/api/v1/upload-batches", json={"files": [{"name": path.name,
                                                                          "size_bytes": path.stat().st_size}]},
                              headers=csrf(client))
        assert r.status_code == 201, r.text
        batch_id = r.json()["batch_id"]
    cid = client_file_id or str(uuid.uuid4())
    return await client.put(f"/api/v1/upload-batches/{batch_id}/files/{cid}", headers=csrf(client),
                            files={"file": (path.name, path.read_bytes(), "application/pdf")})


async def upload_ready(client: httpx.AsyncClient, worker: Any, path: Path) -> dict[str, Any]:
    r = await upload(client, path)
    assert r.status_code == 201, r.text
    await worker.drain()
    docs = (await client.get("/api/v1/documents")).json()["items"]
    doc = next(d for d in docs if d["id"] == r.json()["id"])
    assert doc["status"] == "READY", doc
    return doc


def uuid_of(value: str) -> UUID:
    return UUID(value)


@pytest.fixture(scope="session")
def event_loop_policy() -> Any:
    # psycopg async không chạy được trên ProactorEventLoop (mặc định của Windows)
    if sys.platform == "win32":
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            return asyncio.WindowsSelectorEventLoopPolicy()
    return asyncio.get_event_loop_policy()
