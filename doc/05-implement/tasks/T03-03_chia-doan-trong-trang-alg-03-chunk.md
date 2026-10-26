# T03-03 – Chia đoạn trong trang (ALG-03 chunk)

| Trường | Giá trị |
|---|---|
| Lát | VS-3 – Xử lý tài liệu (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T03-02](T03-02_trich-van-ban-va-phan-loai-loi-alg-03-extract.md) |
| Story | US-005, US-021 |
| Tài liệu tham chiếu | BLUEPRINT ALG-03 (chunk); SAD ADR-008; DATABASE_DESIGN B.2 |

## Mục tiêu

Chia văn bản thành đoạn 500–800 token, chồng lấn 80 token, không bao giờ vượt ranh giới trang.

## Phạm vi file

- `backend/app/modules/ingestion/chunker.py`
- `backend/app/modules/ingestion/tokenizer.py` (tokenizer bge-m3 qua `tokenizers`, tải sẵn trong image)
- `backend/tests/unit/test_chunker.py` (có property test bằng hypothesis)

## Các bước gợi ý

1. Thuật toán đúng ALG-03; câu > max bị cắt cứng theo token.
2. `chunk_index` liên tục toàn tài liệu.

## Tiêu chí hoàn thành

- [ ] Property test: mọi đoạn có đúng 1 `page_number`; `token_count ≤ CHUNK_MAX_TOKENS`; ghép các đoạn (bỏ phần chồng lấn) phủ toàn bộ văn bản trang
- [ ] Trang rỗng không sinh đoạn
- [ ] Hiệu năng: 300 trang ~ 600 đoạn trong < 5 s
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-unit -k chunker
```
