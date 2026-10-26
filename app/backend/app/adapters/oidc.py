"""OIDC client: Authorization Code + PKCE, kiểm tra ID token bằng JWKS (T01-01, SAD 7.3a).

Không bao giờ ghi token vào log. Lỗi nào cũng chuyển thành IdentityError không chứa dữ liệu nhạy cảm.
"""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt

from app.ports.identity import IdentityError, IdTokenClaims


class OidcClient:
    def __init__(self, issuer: str, client_id: str, client_secret: str, groups_claim: str = "groups",
                 http: httpx.AsyncClient | None = None) -> None:
        self._issuer = issuer.rstrip("/")
        self._client_id = client_id
        self._client_secret = client_secret
        self._groups_claim = groups_claim
        self._http = http or httpx.AsyncClient(timeout=10)
        self._meta: dict[str, Any] | None = None
        self._jwks: tuple[float, dict[str, Any]] | None = None

    async def _metadata(self) -> dict[str, Any]:
        if self._meta is None:
            try:
                r = await self._http.get(f"{self._issuer}/.well-known/openid-configuration")
                r.raise_for_status()
            except httpx.HTTPError as e:
                raise IdentityError("discovery_failed") from e
            self._meta = r.json()
        return self._meta

    async def _jwk_set(self, force: bool = False) -> dict[str, Any]:
        if self._jwks is None or force or time.time() - self._jwks[0] > 3600:
            meta = await self._metadata()
            try:
                r = await self._http.get(meta["jwks_uri"])
                r.raise_for_status()
            except httpx.HTTPError as e:
                raise IdentityError("jwks_failed") from e
            self._jwks = (time.time(), r.json())
        return self._jwks[1]

    async def authorization_url(self, *, state: str, nonce: str, code_challenge: str, redirect_uri: str) -> str:
        meta = await self._metadata()
        q = urlencode({
            "response_type": "code", "client_id": self._client_id, "redirect_uri": redirect_uri,
            "scope": "openid email profile", "state": state, "nonce": nonce,
            "code_challenge": code_challenge, "code_challenge_method": "S256",
        })
        return f"{meta['authorization_endpoint']}?{q}"

    async def exchange_code(self, *, code: str, code_verifier: str, nonce: str, redirect_uri: str) -> IdTokenClaims:
        meta = await self._metadata()
        try:
            r = await self._http.post(meta["token_endpoint"], data={
                "grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri,
                "code_verifier": code_verifier,
            }, auth=(self._client_id, self._client_secret))
        except httpx.HTTPError as e:
            raise IdentityError("token_request_failed") from e
        if r.status_code != 200:
            raise IdentityError("token_rejected")
        id_token = r.json().get("id_token")
        if not id_token:
            raise IdentityError("no_id_token")
        claims = await self._verify(id_token)
        if claims.get("nonce") != nonce:
            raise IdentityError("nonce_mismatch")
        groups = claims.get(self._groups_claim) or []
        if isinstance(groups, str):
            groups = [groups]
        email = claims.get("email") or ""
        return IdTokenClaims(subject=str(claims["sub"]), email=str(email), groups=frozenset(map(str, groups)))

    async def _verify(self, token: str) -> dict[str, Any]:
        try:
            kid = jwt.get_unverified_header(token).get("kid")
        except jwt.PyJWTError as e:
            raise IdentityError("malformed_token") from e
        for force in (False, True):
            jwks = await self._jwk_set(force=force)
            keys = [k for k in jwks.get("keys", []) if kid is None or k.get("kid") == kid]
            if keys:
                break
        else:
            raise IdentityError("unknown_key")
        key = jwt.PyJWK.from_dict(keys[0])
        try:
            decoded: dict[str, Any] = jwt.decode(token, key=key, algorithms=["RS256", "ES256"],
                                                 audience=self._client_id, issuer=self._issuer,
                                                 options={"require": ["exp", "iat", "sub", "aud", "iss"]})
        except jwt.PyJWTError as e:
            raise IdentityError("invalid_token") from e
        return decoded
