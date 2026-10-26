"""/auth/login, /auth/callback, /auth/logout, /me (T01-03, openapi.yaml, SAD 7.3a)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse

from app.api.deps import CSRF_COOKIE, SESSION_COOKIE, csrf_protected, current_session, get_container, request_id
from app.container import Container
from app.infra.logging import get_logger
from app.modules.identity.domain import NewSession, SessionContext
from app.modules.identity.service import LoginDenied
from app.ports.identity import IdentityError

router = APIRouter(tags=["auth"])
log = get_logger("auth")
TX_COOKIE = "oidc_tx"


def _set_session_cookies(resp: Response, new: NewSession, c: Container) -> None:
    secure = c.settings.cookie_secure
    max_age = int((new.context.absolute_expires_at - new.context.idle_expires_at).total_seconds()) + \
        c.settings.session_idle_min * 60
    resp.set_cookie(SESSION_COOKIE, new.sid, httponly=True, secure=secure, samesite="lax", path="/", max_age=max_age)
    resp.set_cookie(CSRF_COOKIE, new.csrf_token, httponly=False, secure=secure, samesite="strict", path="/",
                    max_age=max_age)


@router.get("/auth/login")
async def login(return_to: str | None = None, c: Container = Depends(get_container)) -> RedirectResponse:
    url, tx = await c.identity.begin_login(return_to)
    resp = RedirectResponse(url, status_code=302)
    resp.set_cookie(TX_COOKIE, tx, httponly=True, secure=c.settings.cookie_secure, samesite="lax",
                    path="/api/v1/auth", max_age=600)
    return resp


@router.get("/auth/callback")
async def callback(request: Request, code: str = "", state: str = "",
                   c: Container = Depends(get_container)) -> RedirectResponse:
    base = c.settings.public_base_url.rstrip("/")
    rid = request_id(request)
    try:
        new, return_to = await c.identity.complete_login(code=code, state=state,
                                                         tx_cookie=request.cookies.get(TX_COOKIE), request_id=rid)
    except LoginDenied:
        resp = RedirectResponse(f"{base}/access-denied", status_code=302)
    except IdentityError as e:
        log.info("login_failed", reason=str(e))
        resp = RedirectResponse(f"{base}/login-error?ref={rid or ''}", status_code=302)
    else:
        resp = RedirectResponse(f"{base}{return_to}", status_code=302)
        _set_session_cookies(resp, new, c)
    resp.delete_cookie(TX_COOKIE, path="/api/v1/auth")
    return resp


@router.post("/auth/logout", status_code=204)
async def logout(request: Request, ctx: SessionContext = Depends(csrf_protected),
                 c: Container = Depends(get_container)) -> Response:
    await c.identity.logout(ctx, request_id(request))
    resp = Response(status_code=204)
    resp.delete_cookie(SESSION_COOKIE, path="/")
    resp.delete_cookie(CSRF_COOKIE, path="/")
    return resp


@router.get("/me")
async def me(ctx: SessionContext = Depends(current_session), c: Container = Depends(get_container)) -> dict[str, Any]:
    used, limit = await c.documents.quota(ctx.workspace_id)
    s = c.settings
    return {
        "user_id": str(ctx.user_id), "email": ctx.email, "role": ctx.role.value,
        "documents_used": used, "documents_limit": limit,
        "session_expires_at": ctx.expires_at.isoformat().replace("+00:00", "Z"),
        "limits": {"max_file_mb": s.max_file_mb, "max_pages": s.max_pages,
                   "max_files_per_batch": s.max_files_per_batch, "question_max_chars": s.question_max_chars},
    }
