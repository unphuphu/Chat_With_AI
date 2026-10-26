"""Sự kiện analytics EVT-01…EVT-11 (PRD 5.2, BLUEPRINT 3.5.3) – không bao giờ chứa nội dung người dùng."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any
from uuid import UUID

from app.infra.db import Conn

ALLOWED: dict[str, frozenset[str]] = {
    "document_upload_started": frozenset({"batch_id", "file_count", "total_bytes"}),
    "document_upload_rejected": frozenset({"batch_id", "reason"}),
    "document_processing_completed": frozenset({"document_id", "page_count", "size_bytes", "duration_ms",
                                                "chunk_count"}),
    "document_processing_failed": frozenset({"document_id", "failure_code", "attempts"}),
    "document_deleted": frozenset({"document_id", "status_at_delete"}),
    "question_submitted": frozenset({"conversation_id", "question_chars", "ready_documents"}),
    "answer_returned": frozenset({"message_id", "status", "latency_ms", "citation_count", "cited_documents",
                                  "has_page_numbers", "gated"}),
    "answer_failed": frozenset({"message_id", "error_code"}),
    "citation_clicked": frozenset({"document_id", "has_page"}),
    "question_retried": frozenset({"message_id", "previous_error_code"}),
    "access_denied": frozenset({"resource_type"}),
}


class AnalyticsPropertyError(ValueError):
    pass


def actor_hash(user_id: UUID | None, key: str) -> bytes | None:
    if user_id is None:
        return None
    return hmac.new(key.encode(), str(user_id).encode(), hashlib.sha256).digest()


async def record_event(conn: Conn, name: str, props: dict[str, Any], *, user_id: UUID | None, key: str) -> None:
    allowed = ALLOWED.get(name)
    if allowed is None:
        raise AnalyticsPropertyError(f"unknown event {name}")
    extra = set(props) - allowed
    if extra:
        raise AnalyticsPropertyError(f"property not allowed: {sorted(extra)}")
    clean = {k: (str(v) if isinstance(v, UUID) else v) for k, v in props.items()}
    await conn.execute(
        "INSERT INTO analytics_event(event_name, actor_hash, properties) VALUES (%s, %s, %s::jsonb)",
        (name, actor_hash(user_id, key), json.dumps(clean)))
