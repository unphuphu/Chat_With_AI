"""Lưu file trong bộ nhớ – cho unit/integration test."""

from __future__ import annotations

import hashlib
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

from app.ports.blob import BlobUnavailable


class MemoryBlobStore:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, datetime]] = {}
        self.fail = False

    async def put(self, key: str, source: Path, sha256: bytes) -> None:
        if self.fail:
            raise BlobUnavailable("simulated outage")
        data = source.read_bytes()
        if hashlib.sha256(data).digest() != sha256:
            raise BlobUnavailable("checksum mismatch")
        self.objects[key] = (data, datetime.now(UTC))

    async def read(self, key: str) -> AsyncIterator[bytes]:
        if key not in self.objects:
            raise FileNotFoundError(key)
        yield self.objects[key][0]

    async def download_to(self, key: str, target: Path) -> None:
        if self.fail:
            raise BlobUnavailable("simulated outage")
        if key not in self.objects:
            raise FileNotFoundError(key)
        target.write_bytes(self.objects[key][0])

    async def delete(self, key: str) -> None:
        self.objects.pop(key, None)

    async def exists(self, key: str) -> bool:
        return key in self.objects

    async def list_older_than(self, prefix: str, older_than: datetime) -> list[str]:
        return [k for k, (_, t) in self.objects.items() if k.startswith(prefix) and t < older_than]
