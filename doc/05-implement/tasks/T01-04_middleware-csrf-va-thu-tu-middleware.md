# T01-04 – Middleware CSRF và thứ tự middleware

| Trường | Giá trị |
|---|---|
| Lát | VS-1 – Đăng nhập và phiên (Lát 1) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T01-02](T01-02_phien-dang-nhap-va-cookie.md) |
| Story | US-023 |
| Tài liệu tham chiếu | API_DESIGN 3.3 (thứ tự middleware), 2.6 (CSRF); SAD 8.1 (CSRF) |

## Mục tiêu

Mọi request POST/PUT/DELETE có phiên phải có `X-CSRF-Token` hợp lệ.

## Phạm vi file

- `backend/app/api/middleware.py` (CSRF)
- `backend/tests/unit/test_csrf.py`

## Các bước gợi ý

1. So `SHA-256(header)` với `session.csrf_token_hash` bằng so sánh hằng thời gian.
2. Miễn trừ: GET/HEAD, `/auth/login`, `/auth/callback`.
3. Đăng ký thứ tự: RequestId → Telemetry → Session → CSRF → WorkspaceScope → RateLimit.

## Tiêu chí hoàn thành

- [ ] Test: thiếu header → 403 `csrf_invalid`; sai → 403; đúng → qua
- [ ] Test: GET không cần header
- [ ] Test liệt kê mọi route POST/PUT/DELETE trong app và khẳng định đều bị CSRF bảo vệ (chống quên khi thêm route)
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-unit -k csrf
```
