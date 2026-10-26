from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class Role(StrEnum):
    USER = "user"
    ADMIN = "admin"


@dataclass(frozen=True)
class SessionContext:
    session_id: UUID
    user_id: UUID
    workspace_id: UUID
    email: str
    role: Role
    csrf_token_hash: bytes
    idle_expires_at: datetime
    absolute_expires_at: datetime

    @property
    def expires_at(self) -> datetime:
        return min(self.idle_expires_at, self.absolute_expires_at)


@dataclass(frozen=True)
class NewSession:
    context: SessionContext
    sid: str          # giá trị cookie (chỉ trả về một lần, không lưu)
    csrf_token: str   # giá trị cookie đọc được bởi SPA


@dataclass(frozen=True)
class LoginTransaction:
    state: str
    nonce: str
    code_verifier: str
    return_to: str
