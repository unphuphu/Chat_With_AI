# T05-02 – Giới hạn tần suất (ALG-09) cho tải file

| Trường | Giá trị |
|---|---|
| Lát | VS-5 – Nhiều file và giới hạn (Lát 2) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T02-04](T02-04_api-nhan-file-vao-lo-alg-01-accept-file-idempote.md) |
| Story | US-002 |
| Tài liệu tham chiếu | BLUEPRINT ALG-09, DD-04; API_DESIGN 2.6 (RateLimit headers) |

## Mục tiêu

Bộ đếm cửa sổ cố định trong PostgreSQL, header `RateLimit-*`, 429 + `Retry-After`.

## Phạm vi file

- `backend/app/infra/ratelimit.py`
- `backend/tests/integration/test_ratelimit.py`

## Các bước gợi ý

1. Dependency `rate_limit(bucket, limit, window)`; dùng cho `PUT …/files` (30/giờ) – bucket `question` gắn ở T09-02.
2. Header `RateLimit-Limit/Remaining/Reset` trên phản hồi thành công.

## Tiêu chí hoàn thành

- [ ] Test: file thứ 31 trong giờ → 429 `rate_limited`, `Retry-After` đúng
- [ ] Test: 2 bản API (2 engine) dùng chung bộ đếm
- [ ] Test: cửa sổ mới → đếm lại từ 1
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k ratelimit
```
