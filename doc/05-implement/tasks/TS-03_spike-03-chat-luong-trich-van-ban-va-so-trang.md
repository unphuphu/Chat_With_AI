# TS-03 – SPIKE-03: chất lượng trích văn bản và số trang

| Trường | Giá trị |
|---|---|
| Lát | SPIKE – Thử nghiệm kỹ thuật (Song song) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Partial** |
| Phụ thuộc | [T03-02](T03-02_trich-van-ban-va-phan-loai-loi-alg-03-extract.md) |
| Story | US-021 |
| Tài liệu tham chiếu | SAD 12 (SPIKE-03, TR-03), ADR-015; PRD NFR-018 |

> **Chặn bởi:** DEP-003 (bộ PDF mẫu được phép dùng)

## Mục tiêu

Kiểm tra `pypdf` trên PDF thật: thứ tự chữ, bảng, nhiều cột, số trang, ngưỡng R-03.

## Phạm vi file

- `eval/reports/spike-03.md`

## Các bước gợi ý

1. Chạy extractor trên DEP-003, chấm tay 30 trang ngẫu nhiên.
2. Hiệu chỉnh `MIN_CHARS_PER_PAGE`.

## Tiêu chí hoàn thành

- [ ] Báo cáo tỷ lệ trang trích đúng, đề xuất giữ `pypdf` hay mua PyMuPDF
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
python -m eval.extract_report --dir data/dep003
```

## Kết quả triển khai

**Partial** – Đã kiểm chứng trên PDF mẫu sinh tự động (tiếng Việt NFC, đúng số trang); chưa có bộ PDF thật của người dùng.
