"""EmbeddingPort – tạo vector 1024 chiều chuẩn hóa L2 (BLUEPRINT 3.2.2, DATABASE_DESIGN B.2)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, Protocol

EMBEDDING_DIM = 1024


class EmbeddingUnavailable(Exception):
    """Dịch vụ embedding lỗi hoặc quá thời gian."""


class EmbeddingPort(Protocol):
    @property
    def model_id(self) -> str: ...

    async def embed(self, texts: Sequence[str], *, purpose: Literal["query", "passage"],
                    timeout_s: float) -> list[list[float]]: ...


class TokenCounter(Protocol):
    def count(self, text: str) -> int: ...
