# T03-02 – Trích văn bản và phân loại lỗi (ALG-03 extract)

| Trường | Giá trị |
|---|---|
| Lát | VS-3 – Xử lý tài liệu (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T02-02](T02-02_sandbox-va-kiem-tra-pdf-khi-nhan-alg-02.md) |
| Story | US-008 |
| Tài liệu tham chiếu | BLUEPRINT ALG-03 (extract, normalize); PRD 3.3 (mã lý do R-01…R-04); SAD 4.1 bước 2–4 |

## Mục tiêu

Trích văn bản theo trang trong sandbox, chuẩn hóa Unicode, phân loại R-01/R-02/R-03.

## Phạm vi file

- `backend/app/modules/ingestion/{extractor.py,normalize.py,domain.py}`
- `backend/tests/fixtures/pdf/` (thêm: PDF scan chỉ có ảnh, PDF tiếng Việt có dấu, PDF 2 cột)
- `backend/tests/unit/test_extractor.py`

## Các bước gợi ý

1. `extract(path) -> list[PageText] | FailureCode` theo ALG-03; số trang từ 1.
2. `normalize`: NFC, nối từ gạch nối cuối dòng, gộp khoảng trắng.
3. R-03 khi tổng ký tự < `MIN_CHARS_PER_PAGE × số trang`.

## Tiêu chí hoàn thành

- [ ] PDF tiếng Việt: văn bản sau normalize ở dạng NFC và chứa đúng câu mẫu
- [ ] PDF scan → R-03; PDF hỏng → R-01; mật khẩu → R-02
- [ ] Số trang trả về đúng thứ tự 1..n
- [ ] Timeout sandbox → ném lỗi tạm thời (không phải FailureCode)
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-unit -k extractor
```
