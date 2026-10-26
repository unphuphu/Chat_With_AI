"""Embedding "hashing n-gram" cho dev/test – không cần tải mô hình.

Vector 1024 chiều xác định (cùng văn bản → cùng vector), chuẩn hóa L2. Ghi nhận độ trùng từ, cặp từ và
3-gram ký tự (cả dạng bỏ dấu tiếng Việt) – đủ để demo truy xuất theo từ khóa, KHÔNG thay được mô hình
ngữ nghĩa bge-m3 (SAD ADR-007). Đổi `EMBEDDING_PROVIDER=http` để dùng embedding service thật.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections.abc import Sequence
from typing import Literal

from app.ports.embedding import EMBEDDING_DIM

_WORD = re.compile(r"\w+", re.UNICODE)


def strip_accents(s: str) -> str:
    s = s.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def features(text: str) -> list[tuple[str, float]]:
    text = unicodedata.normalize("NFC", text).lower()
    words = _WORD.findall(text)
    feats: list[tuple[str, float]] = []
    for w in words:
        feats.append(("w:" + w, 1.0))
        feats.append(("a:" + strip_accents(w), 0.6))
        padded = f"#{strip_accents(w)}#"
        for i in range(len(padded) - 2):
            feats.append(("c:" + padded[i:i + 3], 0.25))
    for a, b in zip(words, words[1:], strict=False):
        feats.append((f"b:{a} {b}", 0.8))
    return feats


def hash_embed(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    vec = [0.0] * dim
    for feat, weight in features(text):
        h = hashlib.blake2b(feat.encode("utf-8"), digest_size=8).digest()
        idx = int.from_bytes(h[:4], "little") % dim
        sign = 1.0 if h[4] & 1 else -1.0
        vec[idx] += sign * weight
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        vec[0] = 1.0
        return vec
    return [v / norm for v in vec]


class HashingEmbedding:
    def __init__(self, model_id: str = "hashing-ngram@v1") -> None:
        self._model_id = model_id
        self.calls = 0
        self.fail_times = 0  # test: số lần ném lỗi tiếp theo

    @property
    def model_id(self) -> str:
        return self._model_id

    async def embed(self, texts: Sequence[str], *, purpose: Literal["query", "passage"],
                    timeout_s: float) -> list[list[float]]:
        from app.ports.embedding import EmbeddingUnavailable

        self.calls += 1
        if self.fail_times > 0:
            self.fail_times -= 1
            raise EmbeddingUnavailable("simulated failure")
        return [hash_embed(t) for t in texts]
