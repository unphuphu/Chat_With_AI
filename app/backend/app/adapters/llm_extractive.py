"""LLM "trích xuất" cho demo khi chưa có nhà cung cấp LLM (OQ-005).

KHÔNG phải mô hình ngôn ngữ: chọn các câu trong <sources> có nhiều từ trùng với câu hỏi nhất, ghép lại và
gắn [S#]. Không đủ từ trùng → "insufficient". Tuân thủ đúng hợp đồng JSON của LlmPort để thay bằng
adapter thật (Anthropic) chỉ bằng cấu hình LLM_PROVIDER.
"""

from __future__ import annotations

import html
import re
import unicodedata
from typing import Any

from app.adapters.embedding_hashing import strip_accents

_SOURCE = re.compile(r'<source id="(S\d+)">\n(.*?)\n</source>', re.S)
_QUESTION = re.compile(r"<question>(.*?)</question>", re.S)
_SENT = re.compile(r"(?<=[.!?…;])\s+|\n+")
_WORD = re.compile(r"\w+", re.UNICODE)

STOP = {
    # tiếng Việt (dạng bỏ dấu)
    "la", "gi", "cua", "va", "cac", "nhung", "co", "khong", "cho", "voi", "trong", "the", "nao", "bao", "nhieu",
    "duoc", "mot", "nay", "do", "khi", "thi", "tai", "theo", "ve", "tu", "den", "o", "ai", "sao", "hay", "nhu",
    "bi", "ra", "vao", "len", "da", "dang", "se", "can", "phai", "nen", "hon", "nhat", "rat", "lam", "neu",
    "hoi", "biet", "toi", "ban", "chung", "ta", "minh", "nguoi", "viec", "thong", "tin", "lieu",
    # tiếng Anh
    "a", "an", "of", "and", "or", "is", "are", "what", "which", "who", "how", "much", "many", "in", "on",
    "for", "to", "does", "with", "by", "about", "from", "this", "that", "be", "it", "as",
}


def _terms(text: str) -> list[str]:
    words = [strip_accents(w) for w in _WORD.findall(unicodedata.normalize("NFC", text).lower())]
    return [w for w in words if w not in STOP and (len(w) > 1 or w.isdigit())]


class ExtractiveLlm:
    name = "extractive"

    def __init__(self, min_overlap: float = 0.5, max_sentences: int = 3) -> None:
        self.min_overlap = min_overlap
        self.max_sentences = max_sentences

    async def complete_json(self, *, system: str, user: str, json_schema: dict[str, Any],
                            max_output_tokens: int, timeout_s: float) -> dict[str, Any]:
        qm = _QUESTION.search(user)
        question = html.unescape(qm.group(1)) if qm else ""
        q_terms = set(_terms(question))
        q_bigrams = set(zip(_terms(question), _terms(question)[1:], strict=False))
        if not q_terms:
            return {"status": "insufficient", "answer": "", "citations": [], "conflict": False}
        scored: list[tuple[float, int, str, str]] = []
        for order, (sid, content) in enumerate(_SOURCE.findall(user)):
            for sent in _SENT.split(html.unescape(content)):
                sent = sent.strip()
                if len(sent) < 15:
                    continue
                terms = _terms(sent)
                tset = set(terms)
                overlap = len(q_terms & tset) / len(q_terms)
                bigram_bonus = 0.15 * len(q_bigrams & set(zip(terms, terms[1:], strict=False)))
                score = overlap + bigram_bonus
                if overlap >= self.min_overlap:
                    scored.append((score, order, sid, sent))
        if not scored:
            return {"status": "insufficient", "answer": "", "citations": [], "conflict": False}
        scored.sort(key=lambda x: (-x[0], x[1]))
        best = scored[0][0]
        chosen: list[tuple[str, str]] = []
        seen: set[str] = set()
        for score, _, sid, sent in scored:
            if score < best * 0.6 or len(chosen) >= self.max_sentences:
                break
            if sent in seen:
                continue
            seen.add(sent)
            chosen.append((sid, sent))
        answer = " ".join(f"{s.rstrip('.')} [{sid}]." for sid, s in chosen)
        citations = list(dict.fromkeys(sid for sid, _ in chosen))
        return {"status": "answered", "answer": answer, "citations": citations, "conflict": False}
