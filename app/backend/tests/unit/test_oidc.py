"""UT-015 – xác thực id_token OIDC: sai issuer/audience/nonce/hạn/chữ ký, xoay khóa JWKS (không gọi mạng)."""

from __future__ import annotations

import json
import time

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.adapters.oidc import OidcClient
from app.ports.identity import IdentityError

ISSUER, CLIENT = "http://idp.test", "aichat-dev"


def _key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _jwk(key, kid):
    d = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    return {**d, "kid": kid, "alg": "RS256", "use": "sig"}


def _token(key, kid="k1", **over):
    now = int(time.time())
    claims = {"iss": ISSUER, "aud": CLIENT, "sub": "dev|p1", "email": "lan.nguyen@congty.vn",
              "groups": ["aichat-users"], "nonce": "N", "iat": now, "exp": now + 300, **over}
    return jwt.encode({k: v for k, v in claims.items() if v is not None}, key, algorithm="RS256", headers={"kid": kid})


class Idp:
    """IdP giả: discovery + JWKS (đổi được) + token endpoint trả id_token cho trước."""

    def __init__(self, keys: dict[str, object]):
        self.keys, self.id_token, self.jwks_calls = keys, "", 0

    def handler(self, request: httpx.Request) -> httpx.Response:
        p = request.url.path
        if p.endswith("openid-configuration"):
            return httpx.Response(200, json={"authorization_endpoint": f"{ISSUER}/authorize",
                                             "token_endpoint": f"{ISSUER}/token", "jwks_uri": f"{ISSUER}/jwks"})
        if p == "/jwks":
            self.jwks_calls += 1
            return httpx.Response(200, json={"keys": [_jwk(k, kid) for kid, k in self.keys.items()]})
        if p == "/token":
            return httpx.Response(200, json={"id_token": self.id_token})
        return httpx.Response(404)


def _client(idp: Idp) -> OidcClient:
    return OidcClient(ISSUER, CLIENT, "secret", http=httpx.AsyncClient(transport=httpx.MockTransport(idp.handler)))


async def _login(idp: Idp, token: str, nonce: str = "N"):
    idp.id_token = token
    return await _client(idp).exchange_code(code="c", code_verifier="v", nonce=nonce, redirect_uri="http://x/cb")


async def test_valid_token() -> None:
    k = _key()
    claims = await _login(Idp({"k1": k}), _token(k))
    assert claims.email == "lan.nguyen@congty.vn" and claims.groups == frozenset({"aichat-users"})
    assert claims.subject == "dev|p1"


@pytest.mark.parametrize("over", [{"iss": "http://evil"}, {"aud": "other"}, {"exp": int(time.time()) - 10},
                                  {"sub": None}])
async def test_invalid_claims_rejected(over) -> None:
    k = _key()
    with pytest.raises(IdentityError):
        await _login(Idp({"k1": k}), _token(k, **over))


async def test_wrong_nonce_and_signature() -> None:
    k = _key()
    with pytest.raises(IdentityError, match="nonce_mismatch"):
        await _login(Idp({"k1": k}), _token(k), nonce="khac")
    with pytest.raises(IdentityError):  # ký bằng khóa khác nhưng cùng kid
        await _login(Idp({"k1": k}), _token(_key()))


async def test_jwks_rotation_refetches_once() -> None:
    old, new = _key(), _key()
    idp = Idp({"k1": old})
    client = _client(idp)
    idp.id_token = _token(old)
    await client.exchange_code(code="c", code_verifier="v", nonce="N", redirect_uri="http://x/cb")
    assert idp.jwks_calls == 1
    idp.keys = {"k2": new}  # IdP xoay khóa
    idp.id_token = _token(new, kid="k2")
    claims = await client.exchange_code(code="c", code_verifier="v", nonce="N", redirect_uri="http://x/cb")
    assert claims.email and idp.jwks_calls == 2  # tải lại đúng một lần
