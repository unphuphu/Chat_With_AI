"""IdentityPort – OIDC Authorization Code + PKCE (BLUEPRINT 3.2.2, SAD ADR-011)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class IdentityError(Exception):
    """Đăng nhập thất bại (state/nonce/chữ ký/hết hạn) – không chứa token."""


@dataclass(frozen=True)
class IdTokenClaims:
    subject: str
    email: str
    groups: frozenset[str]


class IdentityPort(Protocol):
    async def authorization_url(self, *, state: str, nonce: str, code_challenge: str, redirect_uri: str) -> str: ...

    async def exchange_code(self, *, code: str, code_verifier: str, nonce: str, redirect_uri: str) -> IdTokenClaims: ...
