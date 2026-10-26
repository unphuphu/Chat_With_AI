"""ALG-03 – trích văn bản theo trang và phân loại lỗi. `extract` chạy TRONG SANDBOX."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class PageText:
    page_number: int  # thứ tự trang trong file, bắt đầu từ 1
    text: str


@dataclass(frozen=True)
class ExtractOutcome:
    pages: list[PageText] | None = None
    failure_code: str | None = None  # "R-01" | "R-02" | "R-03"


_HYPHEN_BREAK = re.compile(r"(\w)-\n(\w)")
_MANY_NL = re.compile(r"\n{3,}")
_SPACES = re.compile(r"[ \t\f\v ]+")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _HYPHEN_BREAK.sub(r"\1\2", text)
    text = _SPACES.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = _MANY_NL.sub("\n\n", text)
    return text.strip()


def extract(path: str, min_chars_per_page: int) -> ExtractOutcome:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(path, strict=False)
        if reader.is_encrypted:
            try:
                ok = bool(reader.decrypt(""))
            except Exception:
                ok = False
            if not ok:
                return ExtractOutcome(failure_code="R-02")
        pages: list[PageText] = []
        for i, page in enumerate(reader.pages):
            try:
                raw = page.extract_text() or ""
            except Exception:
                raw = ""
            pages.append(PageText(i + 1, normalize(raw)))
    except (PdfReadError, ValueError, KeyError, TypeError, OSError):
        return ExtractOutcome(failure_code="R-01")
    if not pages:
        return ExtractOutcome(failure_code="R-01")
    total = sum(len(p.text) for p in pages)
    if total < min_chars_per_page * len(pages):
        return ExtractOutcome(failure_code="R-03")
    return ExtractOutcome(pages=pages)
