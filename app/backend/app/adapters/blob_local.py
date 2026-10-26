"""Lưu file trên đĩa cục bộ (dev khi không có MinIO/S3). Cùng hợp đồng với blob_memory (test hợp đồng chung)."""

from __future__ import annotations

import asyncio
import hashlib
import os
import shutil
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

from app.ports.blob import BlobUnavailable


class LocalBlobStore:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        p = (self._root / key).resolve()
        if self._root not in p.parents:
            raise ValueError("invalid blob key")
        return p

    async def put(self, key: str, source: Path, sha256: bytes) -> None:
        def _copy() -> None:
            target = self._path(key)
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(".part")
            shutil.copyfile(source, tmp)
            digest = hashlib.sha256(tmp.read_bytes()).digest()
            if digest != sha256:
                tmp.unlink(missing_ok=True)
                raise BlobUnavailable("checksum mismatch")
            os.replace(tmp, target)

        try:
            await asyncio.to_thread(_copy)
        except OSError as e:
            raise BlobUnavailable(str(e)) from e

    async def read(self, key: str) -> AsyncIterator[bytes]:
        path = self._path(key)
        if not path.exists():
            raise FileNotFoundError(key)
        with path.open("rb") as f:
            while chunk := await asyncio.to_thread(f.read, 64 * 1024):
                yield chunk

    async def download_to(self, key: str, target: Path) -> None:
        path = self._path(key)
        if not path.exists():
            raise FileNotFoundError(key)
        await asyncio.to_thread(shutil.copyfile, path, target)

    async def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    async def exists(self, key: str) -> bool:
        return self._path(key).exists()

    async def list_older_than(self, prefix: str, older_than: datetime) -> list[str]:
        base = self._path(prefix) if prefix else self._root
        if not base.exists():
            return []
        out = []
        for p in base.rglob("*.pdf"):
            mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=UTC)
            if mtime < older_than:
                out.append(p.relative_to(self._root).as_posix())
        return out
