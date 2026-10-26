"""ALG-03 – chia đoạn TRONG từng trang (SAD ADR-008): 500–800 token, chồng lấn ~80 token.

Bất biến: mỗi đoạn thuộc đúng một trang; `token_count` ≤ max; trang rỗng không sinh đoạn.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.modules.ingestion.extractor import PageText

_TOKEN = re.compile(r"\w+|[^\w\s]", re.UNICODE)
_SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+|\n")


class ApproxTokenCounter:
    """Đếm "token" = số từ + dấu câu. Cộng được chính xác (đếm cả đoạn = tổng các câu).

    Tokenizer bge-m3 thật thường cho ~1,2–1,4 token mỗi từ tiếng Việt; khi dùng embedding service thật,
    thay bằng bộ đếm của tokenizer (DATABASE_DESIGN B.2) và giảm CHUNK_*_TOKENS tương ứng.
    """

    def count(self, text: str) -> int:
        return len(_TOKEN.findall(text))


@dataclass(frozen=True)
class ChunkDraft:
    page_number: int
    chunk_index: int
    content: str
    token_count: int


def _units(text: str) -> list[tuple[str, bool]]:
    """Trả (đơn vị, kết thúc đoạn văn?) – tách theo đoạn văn rồi theo câu."""
    out: list[tuple[str, bool]] = []
    for para in text.split("\n\n"):
        sentences = [s.strip() for s in _SENT_SPLIT.split(para) if s.strip()]
        for i, s in enumerate(sentences):
            out.append((s, i == len(sentences) - 1))
    return out


def _hard_split(unit: str, max_tokens: int, counter: ApproxTokenCounter) -> list[str]:
    words = unit.split()
    pieces, cur = [], []
    for w in words:
        cur.append(w)
        if counter.count(" ".join(cur)) >= max_tokens:
            if len(cur) > 1:
                cur.pop()
                pieces.append(" ".join(cur))
                cur = [w]
            else:
                pieces.append(w)
                cur = []
    if cur:
        pieces.append(" ".join(cur))
    return pieces


def chunk_pages(pages: list[PageText], *, target: int, max_tokens: int, overlap: int,
                counter: ApproxTokenCounter | None = None) -> list[ChunkDraft]:
    counter = counter or ApproxTokenCounter()
    chunks: list[ChunkDraft] = []
    idx = 0
    for page in pages:
        if not page.text.strip():
            continue
        units: list[tuple[str, int, bool]] = []
        for u, ends_para in _units(page.text):
            n = counter.count(u)
            if n > max_tokens:
                for piece in _hard_split(u, max_tokens, counter):
                    units.append((piece, counter.count(piece), False))
            else:
                units.append((u, n, ends_para))
        cur: list[tuple[str, int, bool]] = []
        cur_tokens = 0
        new_in_cur = 0

        def emit() -> None:
            nonlocal idx
            content = " ".join(u for u, _, _ in cur).strip()  # noqa: B023 – gọi trong cùng vòng lặp
            if content:
                chunks.append(ChunkDraft(page.page_number, idx, content, counter.count(content)))  # noqa: B023
                idx += 1

        for u, n, ends_para in units:
            at_para_end = bool(cur) and cur[-1][2]
            if cur and (cur_tokens + n > max_tokens or (cur_tokens >= target and at_para_end)):
                emit()
                tail: list[tuple[str, int, bool]] = []
                t = 0
                for item in reversed(cur):
                    if t + item[1] > overlap:
                        break
                    tail.insert(0, item)
                    t += item[1]
                cur, cur_tokens, new_in_cur = tail, t, 0
            cur.append((u, n, ends_para))
            cur_tokens += n
            new_in_cur += 1
            while cur_tokens > max_tokens and len(cur) > 1:  # chồng lấn + câu mới quá dài: bỏ chồng lấn
                removed = cur.pop(0)
                cur_tokens -= removed[1]
        if cur and new_in_cur > 0:
            emit()
    return chunks
