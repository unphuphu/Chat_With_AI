"""IdP OIDC giả lập cho dev/test (thay mock-oauth2-server khi không có Docker).

Hỗ trợ: discovery, /authorize (trang chọn người dùng), /token (code + PKCE S256 + client secret), /jwks.
Người dùng mẫu: p1, p2 (nhóm aichat-users), admin (aichat-admins), outsider (không có nhóm).
CHỈ DÙNG CHO PHÁT TRIỂN – không có mật khẩu.
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

ISSUER = os.environ.get("DEVIDP_ISSUER", "http://localhost:8090")
CLIENT_ID = os.environ.get("OIDC_CLIENT_ID", "aichat-dev")
CLIENT_SECRET = os.environ.get("OIDC_CLIENT_SECRET", "dev-secret-change-me")
KEY_FILE = Path(os.environ.get("DEVIDP_KEY_FILE", Path(__file__).resolve().parents[2] / ".data" / "devidp_key.pem"))

USERS: dict[str, dict[str, Any]] = {
    "p1": {"email": "lan.nguyen@congty.vn", "name": "Nguyễn Lan (P1)", "groups": ["aichat-users"]},
    "p2": {"email": "minh.tran@congty.vn", "name": "Trần Minh (P2)", "groups": ["aichat-users"]},
    "admin": {"email": "admin@congty.vn", "name": "Quản trị viên", "groups": ["aichat-admins"]},
    "outsider": {"email": "khach@congty.vn", "name": "Người ngoài nhóm", "groups": []},
}


def _load_key() -> rsa.RSAPrivateKey:
    if KEY_FILE.exists():
        key = serialization.load_pem_private_key(KEY_FILE.read_bytes(), password=None)
        assert isinstance(key, rsa.RSAPrivateKey)
        return key
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEY_FILE.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                           serialization.NoEncryption()))
    return key


KEY = _load_key()
KID = "devidp-1"
CODES: dict[str, dict[str, Any]] = {}

app = FastAPI(title="Dev IdP", docs_url=None, redoc_url=None)


def _jwk() -> dict[str, Any]:
    jwk: dict[str, Any] = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(KEY.public_key()))
    jwk.update({"kid": KID, "use": "sig", "alg": "RS256"})
    return jwk


@app.get("/.well-known/openid-configuration")
def discovery() -> dict[str, Any]:
    return {
        "issuer": ISSUER,
        "authorization_endpoint": f"{ISSUER}/authorize",
        "token_endpoint": f"{ISSUER}/token",
        "jwks_uri": f"{ISSUER}/jwks",
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "code_challenge_methods_supported": ["S256"],
    }


@app.get("/jwks")
def jwks() -> dict[str, Any]:
    return {"keys": [_jwk()]}


@app.get("/authorize", response_class=HTMLResponse)
def authorize(request: Request) -> str:
    p = request.query_params
    if p.get("client_id") != CLIENT_ID or p.get("response_type") != "code" or p.get("code_challenge_method") != "S256":
        raise HTTPException(400, "invalid_request")
    hidden = "".join(f'<input type="hidden" name="{html.escape(k)}" value="{html.escape(v)}">'
                     for k, v in p.items())
    buttons = "".join(
        f'<button name="user" value="{u}" type="submit"><b>{html.escape(d["name"])}</b>'
        f'<span>{html.escape(d["email"])} · nhóm: {", ".join(d["groups"]) or "(không có)"}</span></button>'
        for u, d in USERS.items())
    return f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>Dev IdP – Đăng nhập</title>
<style>body{{font-family:Segoe UI,system-ui,sans-serif;background:#F5F6F8;display:grid;place-items:center;min-height:100vh;margin:0}}
form{{background:#fff;border:1px solid #D7DCE3;border-radius:14px;padding:28px;width:420px;box-shadow:0 4px 12px rgba(16,24,40,.08)}}
h1{{font-size:20px;margin:0 0 4px}}p{{color:#56606E;margin:0 0 16px;font-size:14px}}
button{{display:flex;flex-direction:column;align-items:flex-start;width:100%;text-align:left;margin:8px 0;padding:10px 14px;border:1px solid #A9B3C1;border-radius:10px;background:#fff;cursor:pointer;font:inherit}}
button:hover{{border-color:#1D5BB8;background:#E7EFFB}}span{{font-size:12px;color:#56606E}}</style></head>
<body><form method="post" action="/authorize"><h1>IdP giả lập (chỉ dùng cho dev)</h1>
<p>Chọn tài khoản để đăng nhập vào AI Chat PDF.</p>{hidden}{buttons}</form></body></html>"""


@app.post("/authorize")
def authorize_submit(user: str = Form(), redirect_uri: str = Form(), state: str = Form(), nonce: str = Form(""),
                     code_challenge: str = Form()) -> RedirectResponse:
    if user not in USERS:
        raise HTTPException(400, "unknown user")
    code = secrets.token_urlsafe(24)
    CODES[code] = {"user": user, "redirect_uri": redirect_uri, "nonce": nonce,
                   "code_challenge": code_challenge, "exp": time.time() + 120}
    return RedirectResponse(f"{redirect_uri}?{urlencode({'code': code, 'state': state})}", status_code=302)


@app.post("/token")
async def token(request: Request) -> JSONResponse:
    form = await request.form()
    auth = request.headers.get("authorization", "")
    cid, csecret = form.get("client_id"), form.get("client_secret")
    if auth.lower().startswith("basic "):
        cid, _, csecret = base64.b64decode(auth[6:]).decode().partition(":")
    if cid != CLIENT_ID or csecret != CLIENT_SECRET:
        return JSONResponse({"error": "invalid_client"}, status_code=401)
    data = CODES.pop(str(form.get("code", "")), None)
    if not data or data["exp"] < time.time() or data["redirect_uri"] != form.get("redirect_uri"):
        return JSONResponse({"error": "invalid_grant"}, status_code=400)
    verifier = str(form.get("code_verifier", ""))
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    if challenge != data["code_challenge"]:
        return JSONResponse({"error": "invalid_grant", "error_description": "pkce"}, status_code=400)
    u = USERS[data["user"]]
    now = int(time.time())
    claims = {"iss": ISSUER, "aud": CLIENT_ID, "sub": f"dev|{data['user']}", "iat": now, "exp": now + 300,
              "nonce": data["nonce"], "email": u["email"], "name": u["name"], "groups": u["groups"]}
    id_token = jwt.encode(claims, KEY, algorithm="RS256", headers={"kid": KID})
    return JSONResponse({"access_token": secrets.token_urlsafe(16), "token_type": "Bearer",
                         "expires_in": 300, "id_token": id_token})
