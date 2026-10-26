# T01-02 – Phiên đăng nhập và cookie

| Trường | Giá trị |
|---|---|
| Lát | VS-1 – Đăng nhập và phiên (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T00-05](T00-05_ha-tang-csdl-engine-theo-vai-tro-va-pham-vi-work.md), [T01-01](T01-01_identityport-va-adapter-oidc-authorization-code.md) |
| Story | US-023 |
| Tài liệu tham chiếu | BLUEPRINT 3.7.3, DD-01; SAD 8.1 (phiên, CSRF); schema.sql `session`; API_DESIGN 3.6.3 (`session_expired`) |

## Mục tiêu

Tạo/xác thực/hết hạn phiên an toàn; dependency `resolve_session` cho mọi endpoint cần đăng nhập.

## Phạm vi file

- `backend/app/modules/identity/{service.py,repository.py}`
- `backend/app/api/deps.py` (`resolve_session` → `SessionContext`)
- `backend/tests/integration/test_session.py`

## Các bước gợi ý

1. Sinh `sid` và `csrf_token` 32 byte (secrets), lưu SHA-256; cookie `sid` HttpOnly/Secure/SameSite=Lax/Path=/; `csrf_token` Secure/SameSite=Strict.
2. Gia hạn `idle_expires_at` tối đa 1 lần/phút (ghi DB); hết hạn → 401 `session_expired`; không có cookie → 401 `unauthenticated`.
3. `SessionContext` gắn vào `request.state`.

## Tiêu chí hoàn thành

- [ ] Test: phiên hợp lệ → context đúng user/workspace
- [ ] Test: quá idle 2 h hoặc absolute 10 h (giả lập thời gian) → 401 `session_expired`
- [ ] Test: 100 request trong 1 phút → chỉ 1 lần UPDATE `last_seen_at`
- [ ] Test: DB chỉ chứa băm, không chứa token gốc
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k session
```
