"""Gọi embedding service nội bộ (`POST /embed`, BLUEPRINT 3.6.5)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import httpx

from app.ports.embedding import EmbeddingUnavailable


class HttpEmbedding:
    def __init__(self, base_url: str, token: str, model_id: str) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, headers={"Authorization": f"Bearer {token}"})
        self._model_id = model_id

    @property
    def model_id(self) -> str:
        return self._model_id

    async def embed(self, texts: Sequence[str], *, purpose: Literal["query", "passage"],
                    timeout_s: float) -> list[list[float]]:
        last: Exception | None = None
        for _ in range(2):
            try:
                r = await self._client.post("/embed", json={"texts": list(texts), "purpose": purpose},
                                            timeout=timeout_s)
                if r.status_code >= 500:
                    last = EmbeddingUnavailable(f"status {r.status_code}")
                    continue
                r.raise_for_status()
                vectors: list[list[float]] = r.json()["vectors"]
                return vectors
            except httpx.HTTPError as e:
                last = e
        raise EmbeddingUnavailable(str(last))

    async def aclose(self) -> None:
        await self._client.aclose()
