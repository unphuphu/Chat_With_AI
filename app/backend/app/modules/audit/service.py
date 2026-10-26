"""Nhật ký kiểm toán – chỉ ID và thời điểm, không có nội dung (NFR-012, T10-01).

Ghi trong cùng transaction với thay đổi nghiệp vụ để không có nhật ký "ma" khi rollback.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from app.infra.db import Conn

AuditAction = Literal["login", "login_denied", "logout", "document_upload", "document_reject",
                      "document_delete", "document_reprocess", "question_asked", "access_denied"]


async def record_audit(conn: Conn, action: AuditAction, *, actor_id: UUID | None,
                       workspace_id: UUID | None = None, target_type: str | None = None,
                       target_id: UUID | None = None, outcome: str = "success",
                       request_id: str | None = None) -> None:
    await conn.execute(
        """INSERT INTO audit_event(actor_id, workspace_id, action, target_type, target_id, outcome, request_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (actor_id, workspace_id, action, target_type, target_id, outcome, request_id))
