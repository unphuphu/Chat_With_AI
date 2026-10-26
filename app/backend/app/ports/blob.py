"""BlobPort – lưu file PDF gốc (BLUEPRINT 3.2.2)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from typing import Protocol
from uuid import UUID


class BlobUnavailable(Exception):
    """Kho lưu trữ không phản hồi (→ 503 storage_unavailable)."""


def document_key(workspace_id: UUID, document_id: UUID) -> str:
    return f"ws/{workspace_id}/doc/{document_id}.pdf"


def parse_document_key(key: str) -> tuple[UUID, UUID] | None:
    parts = key.split("/")
    if len(parts) != 4 or parts[0] != "ws" or parts[2] != "doc" or not parts[3].endswith(".pdf"):
        return None
    try:
        return UUID(parts[1]), UUID(parts[3][:-4])
    except ValueError:
        return None


class BlobPort(Protocol):
    async def put(self, key: str, source: Path, sha256: bytes) -> None: ...
    def read(self, key: str) -> AsyncIterator[bytes]: ...  # async generator
    async def download_to(self, key: str, target: Path) -> None: ...
    async def delete(self, key: str) -> None: ...  # idempotent
    async def exists(self, key: str) -> bool: ...
    async def list_older_than(self, prefix: str, older_than: datetime) -> list[str]: ...
