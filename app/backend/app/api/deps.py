"""Dependency dùng chung: container, phiên, CSRF, giới hạn tần suất (API_DESIGN 3.3)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Depends, Request, Response

from app.container import Container
from app.infra import ratelimit
from app.modules.common.errors import AppError
from app.modules.identity.domain import SessionContext

SESSION_COOKIE = "sid"
CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"


def get_container(request: Request) -> Container:
    return request.app.state.container  # type: ignore[no-any-return]


async def current_session(request: Request, c: Container = Depends(get_container)) -> SessionContext:
    ctx = await c.identity.resolve_session(request.cookies.get(SESSION_COOKIE))
    request.state.session = ctx
    return ctx


async def csrf_protected(request: Request, ctx: SessionContext = Depends(current_session),
                         c: Container = Depends(get_container)) -> SessionContext:
    if not c.identity.csrf_valid(ctx, request.headers.get(CSRF_HEADER)):
        raise AppError(403, "csrf_invalid", "Phiên không hợp lệ, vui lòng tải lại trang.")
    return ctx


def rate_limited(bucket: ratelimit.Bucket) -> Callable[..., Awaitable[None]]:
    async def dep(response: Response, ctx: SessionContext = Depends(current_session),
                  c: Container = Depends(get_container)) -> None:
        s = c.settings
        limit, window = ((s.rate_questions_per_min, 60) if bucket == "question"
                         else (s.rate_files_per_hour, 3600))
        decision = await ratelimit.hit(c.db, ctx.user_id, bucket, limit, window)
        if not decision.allowed:
            raise AppError(429, "rate_limited",
                           f"Bạn thao tác quá nhanh, vui lòng thử lại sau {decision.reset_s} giây.",
                           headers=decision.headers())
        for k, v in decision.headers().items():
            response.headers[k] = v

    dep.csrf_marker = True  # type: ignore[attr-defined]
    return dep


def request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)
