"""Ứng dụng FastAPI (API + worker khi chạy một tiến trình)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.api.errors import install_error_handlers, problem_body
from app.api.middleware import RequestIdMiddleware, SecurityHeadersMiddleware
from app.api.v1 import auth, conversations, documents, events, health
from app.container import Container
from app.infra.logging import configure_logging, get_logger
from app.infra.migrate import migrate
from app.infra.settings import Settings, get_settings

log = get_logger("main")


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Tương đương `client_max_body_size` ở proxy (T05-01): chặn body quá lớn trước khi đọc."""

    def __init__(self, app: object, max_bytes: int) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > self.max_bytes:
            return JSONResponse(problem_body(request, 413, "too_large", "File vượt quá dung lượng cho phép."),
                                status_code=413, media_type="application/problem+json")
        return await call_next(request)


def create_app(settings: Settings | None = None, container: Container | None = None, *,
               run_migrations: bool = True, start_worker: bool | None = None) -> FastAPI:
    s = settings or get_settings()
    configure_logging(s.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        c = container or Container.from_settings(s)
        await c.db.open()
        if run_migrations:
            applied = await migrate(c.db)
            if applied:
                log.info("migrations_applied", versions=applied)
        app.state.container = c
        worker = None
        if start_worker if start_worker is not None else s.run_worker_in_api:
            from worker.main import Worker

            worker = Worker(c)
            worker.start()
            app.state.worker = worker
        log.info("started", env=s.env, db_mode=s.db_mode, llm=s.llm_provider, embedding=s.embedding_provider)
        try:
            yield
        finally:
            if worker:
                await worker.stop()
            await c.db.close()

    app = FastAPI(title="AI Chat PDF API", version="1.0.0-draft.1", lifespan=lifespan,
                  docs_url="/api/v1/docs" if s.env == "dev" else None, redoc_url=None,
                  openapi_url="/api/v1/openapi.json")
    install_error_handlers(app)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=s.max_file_bytes + 1024 * 1024)
    app.add_middleware(RequestIdMiddleware)
    for r in (health.router, auth.router, documents.router, conversations.router, events.router):
        app.include_router(r, prefix="/api/v1")

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


def app_factory() -> FastAPI:
    return create_app()
