"""Đăng nhập OIDC, phiên, workspace cá nhân (T01-02, T01-03; SAD 7.3a; BLUEPRINT 3.7.3, DD-01)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.infra.db import Conn, Database
from app.infra.settings import Settings
from app.modules.audit.service import record_audit
from app.modules.common.errors import AppError
from app.modules.identity.domain import LoginTransaction, NewSession, Role, SessionContext
from app.ports.identity import IdentityError, IdentityPort


def sha256(value: str) -> bytes:
    return hashlib.sha256(value.encode()).digest()


def safe_return_to(value: str | None) -> str:
    if not value or not value.startswith("/") or value.startswith("//") or "\\" in value:
        return "/"
    return value


class LoginDenied(Exception):
    """Người dùng hợp lệ nhưng không thuộc nhóm được phép."""


class IdentityService:
    def __init__(self, db: Database, idp: IdentityPort, settings: Settings) -> None:
        self._db = db
        self._idp = idp
        self._s = settings
        self._signer = URLSafeTimedSerializer(settings.session_signing_key, salt="oidc-tx")

    @property
    def redirect_uri(self) -> str:
        return f"{self._s.public_base_url.rstrip('/')}/api/v1/auth/callback"

    # ------------------------------------------------------------------ login
    async def begin_login(self, return_to: str | None) -> tuple[str, str]:
        tx = LoginTransaction(state=secrets.token_urlsafe(24), nonce=secrets.token_urlsafe(24),
                              code_verifier=secrets.token_urlsafe(48), return_to=safe_return_to(return_to))
        challenge = base64.urlsafe_b64encode(hashlib.sha256(tx.code_verifier.encode()).digest()).rstrip(b"=").decode()
        url = await self._idp.authorization_url(state=tx.state, nonce=tx.nonce, code_challenge=challenge,
                                                redirect_uri=self.redirect_uri)
        cookie = self._signer.dumps(tx.__dict__)
        return url, cookie

    def read_login_tx(self, cookie: str | None) -> LoginTransaction:
        if not cookie:
            raise IdentityError("missing_tx")
        try:
            data: dict[str, Any] = self._signer.loads(cookie, max_age=600)
        except (BadSignature, SignatureExpired) as e:
            raise IdentityError("bad_tx") from e
        return LoginTransaction(**data)

    async def complete_login(self, *, code: str, state: str, tx_cookie: str | None,
                             request_id: str | None = None) -> tuple[NewSession, str]:
        tx = self.read_login_tx(tx_cookie)
        if not hmac.compare_digest(tx.state, state):
            raise IdentityError("state_mismatch")
        claims = await self._idp.exchange_code(code=code, code_verifier=tx.code_verifier, nonce=tx.nonce,
                                               redirect_uri=self.redirect_uri)
        allowed = claims.groups & self._s.allowed_groups
        if not allowed:
            async with self._db.tx("app_api") as conn:
                await record_audit(conn, "login_denied", actor_id=None, outcome="denied", request_id=request_id)
            raise LoginDenied(claims.email)
        role = Role.ADMIN if self._s.oidc_admin_group in claims.groups else Role.USER
        async with self._db.tx("app_api") as conn:
            user_id, ws_id = await self._upsert_user(conn, claims.subject, claims.email, role)
            new = await self._create_session(conn, user_id, ws_id, claims.email, role)
            await record_audit(conn, "login", actor_id=user_id, workspace_id=ws_id, request_id=request_id)
        return new, tx.return_to

    async def _upsert_user(self, conn: Conn, subject: str, email: str, role: Role) -> tuple[UUID, UUID]:
        cur = await conn.execute(
            """INSERT INTO app_user(idp_subject, email, role, last_login_at) VALUES (%s, %s, %s, now())
               ON CONFLICT (idp_subject) DO UPDATE SET email = EXCLUDED.email, role = EXCLUDED.role,
                   last_login_at = now()
               RETURNING id""", (subject, email, role.value))
        user_id: UUID = (await cur.fetchone())["id"]  # type: ignore[index]
        cur = await conn.execute("SELECT id FROM workspace WHERE personal_owner_id = %s", (user_id,))
        row = await cur.fetchone()
        if row:
            return user_id, row["id"]
        cur = await conn.execute(
            "INSERT INTO workspace(kind, personal_owner_id) VALUES ('personal', %s) RETURNING id", (user_id,))
        ws_id: UUID = (await cur.fetchone())["id"]  # type: ignore[index]
        await conn.execute("INSERT INTO membership(workspace_id, user_id, role) VALUES (%s, %s, 'owner')",
                           (ws_id, user_id))
        return user_id, ws_id

    async def _create_session(self, conn: Conn, user_id: UUID, ws_id: UUID, email: str, role: Role) -> NewSession:
        sid, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        now = datetime.now(UTC)
        idle = now + timedelta(minutes=self._s.session_idle_min)
        absolute = now + timedelta(hours=self._s.session_absolute_h)
        idle = min(idle, absolute)
        cur = await conn.execute(
            """INSERT INTO session(user_id, workspace_id, token_hash, csrf_token_hash, idle_expires_at,
                                   absolute_expires_at) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",
            (user_id, ws_id, sha256(sid), sha256(csrf), idle, absolute))
        session_id: UUID = (await cur.fetchone())["id"]  # type: ignore[index]
        ctx = SessionContext(session_id, user_id, ws_id, email, role, sha256(csrf), idle, absolute)
        return NewSession(ctx, sid, csrf)

    # ------------------------------------------------------------------ session
    async def resolve_session(self, sid: str | None) -> SessionContext:
        if not sid:
            raise AppError(401, "unauthenticated")
        async with self._db.tx("app_api") as conn:
            cur = await conn.execute(
                """SELECT s.id, s.user_id, s.workspace_id, s.csrf_token_hash, s.idle_expires_at,
                          s.absolute_expires_at, s.last_seen_at, u.email, u.role
                   FROM session s JOIN app_user u ON u.id = s.user_id WHERE s.token_hash = %s""", (sha256(sid),))
            row = await cur.fetchone()
            if row is None:
                raise AppError(401, "unauthenticated")
            now = datetime.now(UTC)
            if now >= min(row["idle_expires_at"], row["absolute_expires_at"]):
                raise AppError(401, "session_expired")
            idle = row["idle_expires_at"]
            # Gia hạn tối đa 1 lần/phút (T01-02)
            if now - row["last_seen_at"] >= timedelta(minutes=1):
                idle = min(now + timedelta(minutes=self._s.session_idle_min), row["absolute_expires_at"])
                await conn.execute("UPDATE session SET last_seen_at = %s, idle_expires_at = %s WHERE id = %s",
                                   (now, idle, row["id"]))
        return SessionContext(row["id"], row["user_id"], row["workspace_id"], row["email"], Role(row["role"]),
                              bytes(row["csrf_token_hash"]), idle, row["absolute_expires_at"])

    @staticmethod
    def csrf_valid(ctx: SessionContext, header_value: str | None) -> bool:
        return bool(header_value) and hmac.compare_digest(sha256(header_value or ""), ctx.csrf_token_hash)

    async def logout(self, ctx: SessionContext, request_id: str | None = None) -> None:
        async with self._db.tx("app_api") as conn:
            await conn.execute("DELETE FROM session WHERE id = %s", (ctx.session_id,))
            await record_audit(conn, "logout", actor_id=ctx.user_id, workspace_id=ctx.workspace_id,
                               request_id=request_id)
