"""ALG-02 – kiểm tra file PDF khi nhận. Hàm `inspect` chạy TRONG SANDBOX (tiến trình con)."""

from __future__ import annotations

from pathlib import Path

from app.modules.documents.domain import InspectionResult


def inspect(path: str, max_bytes: int, max_pages: int) -> InspectionResult:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    p = Path(path)
    if p.stat().st_size > max_bytes:
        return InspectionResult(False, reject_code="too_large")
    with p.open("rb") as f:
        if f.read(5) != b"%PDF-":
            return InspectionResult(False, reject_code="not_pdf")
    try:
        reader = PdfReader(str(p), strict=False)
        if reader.is_encrypted:
            try:
                ok = bool(reader.decrypt(""))
            except Exception:
                ok = False
            if not ok:
                return InspectionResult(False, reject_code="encrypted")
        n = len(reader.pages)
    except (PdfReadError, ValueError, KeyError, TypeError, OSError):
        return InspectionResult(False, reject_code="not_pdf")
    if n == 0:
        return InspectionResult(False, reject_code="not_pdf")
    if n > max_pages:
        return InspectionResult(False, reject_code="too_many_pages")
    return InspectionResult(True, page_count=n)
