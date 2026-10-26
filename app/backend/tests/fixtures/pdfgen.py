"""Sinh PDF mẫu cho test/demo (không commit PDF thật – PLAN quy ước "Dữ liệu thật")."""

from __future__ import annotations

import io
import sys
from pathlib import Path

from fpdf import FPDF
from pypdf import PdfReader, PdfWriter

FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
    Path("/Library/Fonts/Arial Unicode.ttf"),
]


def _font() -> Path:
    for p in FONT_CANDIDATES:
        if p.exists():
            return p
    raise RuntimeError("Không tìm thấy font Unicode (Arial/DejaVu) để sinh PDF tiếng Việt")


def text_pdf(path: Path, pages: list[str], title: str = "") -> Path:
    pdf = FPDF()
    pdf.add_font("U", "", str(_font()))
    pdf.set_font("U", size=12)
    for body in pages:
        pdf.add_page()
        if title:
            pdf.set_font("U", size=14)
            pdf.multi_cell(0, 8, title)
            pdf.set_font("U", size=12)
        pdf.multi_cell(0, 7, body)
    pdf.output(str(path))
    return path


def scan_pdf(path: Path, pages: int = 2) -> Path:
    from PIL import Image, ImageDraw

    pdf = FPDF()
    for _ in range(pages):
        img = Image.new("RGB", (600, 800), "white")
        d = ImageDraw.Draw(img)
        for y in range(60, 760, 24):
            d.rectangle([50, y, 550, y + 10], fill=(80, 80, 80))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        pdf.add_page()
        pdf.image(buf, x=10, y=10, w=190)
    pdf.output(str(path))
    return path


def encrypted_pdf(src: Path, path: Path, user_password: str) -> Path:
    writer = PdfWriter(clone_from=PdfReader(str(src)))
    writer.encrypt(user_password=user_password, owner_password="owner-secret", algorithm="AES-128")
    with path.open("wb") as f:
        writer.write(f)
    return path


CONTRACT_A = [
    "HỢP ĐỒNG CUNG CẤP DỊCH VỤ SỐ HD-2026-001\n\nĐiều 1. Phạm vi: Bên A cung cấp nền tảng phân tích dữ liệu "
    "cho Bên B trong 24 tháng.\n\nĐiều 2. Giá trị hợp đồng là 1.200.000.000 đồng chưa gồm thuế giá trị gia tăng.",
    "Điều 5. Thanh toán: Bên B thanh toán trong vòng 30 ngày kể từ ngày nhận được hóa đơn giá trị gia tăng hợp lệ "
    "và biên bản nghiệm thu.\n\nĐiều 6. Lãi chậm trả: Bên B chịu lãi chậm trả 0,05% mỗi ngày trên số tiền chậm "
    "thanh toán, tối đa 10% giá trị hợp đồng.",
    "Điều 9. Hiệu lực: Hợp đồng có hiệu lực kể từ ngày ký và kéo dài 24 tháng. Điều 10. Bảo hành: Bên A bảo hành "
    "phần mềm trong 12 tháng kể từ ngày nghiệm thu.",
]
POLICY = [
    "CHÍNH SÁCH BÁN HÀNG 2026\n\nMục 1. Đối tượng áp dụng: toàn bộ khách hàng doanh nghiệp.\n\nMục 2. Khách hàng "
    "chiến lược được kéo dài thời hạn thanh toán tối đa 45 ngày, cần phê duyệt của Giám đốc kinh doanh.",
    "Mục 7. Bảng giá: gói Premium có giá 11.900.000 đồng mỗi tháng. Gói Standard có giá 6.500.000 đồng mỗi tháng.",
]
PRICE_LIST = [
    "BẢNG GIÁ QUÝ 4\n\nGói Premium: 12.500.000 đồng mỗi tháng. Gói Standard: 6.500.000 đồng mỗi tháng. "
    "Giá chưa gồm thuế giá trị gia tăng.",
]


def make_all(out: Path, max_pages: int = 5) -> dict[str, Path]:
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "contract": text_pdf(out / "hop-dong-A.pdf", CONTRACT_A),
        "policy": text_pdf(out / "chinh-sach-ban-hang-2026.pdf", POLICY),
        "price": text_pdf(out / "bang-gia-Q4.pdf", PRICE_LIST),
        "scan": scan_pdf(out / "ho-so-scan-2019.pdf"),
        "too_many_pages": text_pdf(out / "qua-nhieu-trang.pdf",
                                   [f"Trang {i + 1}: nội dung kiểm thử giới hạn số trang."
                                    for i in range(max_pages + 1)]),
    }
    files["encrypted"] = encrypted_pdf(files["contract"], out / "hop-dong-mat-khau.pdf", "secret")
    files["encrypted_empty"] = encrypted_pdf(files["contract"], out / "hop-dong-khoa-in.pdf", "")
    (out / "hong.pdf").write_bytes(b"%PDF-1.4\n1 0 obj << /Type /Catalog >> garbage without xref\n")
    files["broken"] = out / "hong.pdf"
    (out / "bao-gia.docx").write_bytes(b"PK\x03\x04" + b"\x00" * 200)
    files["docx"] = out / "bao-gia.docx"
    (out / "gia-mao.pdf").write_bytes(b"PK\x03\x04 khong phai pdf")
    files["fake_pdf"] = out / "gia-mao.pdf"
    return files


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("sample-pdfs")
    for name, p in make_all(target, max_pages=300).items():
        print(f"{name:16} {p}")
