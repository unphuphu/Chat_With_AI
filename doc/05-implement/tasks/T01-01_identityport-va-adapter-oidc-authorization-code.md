# T01-01 – IdentityPort và adapter OIDC (Authorization Code + PKCE)

| Trường | Giá trị |
|---|---|
| Lát | VS-1 – Đăng nhập và phiên (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T00-04](T00-04_khung-api-settings-loi-rfc-9457-request-id-healt.md) |
| Story | US-023 |
| Tài liệu tham chiếu | BLUEPRINT 3.2.2 (`IdentityPort`), 3.6.6; SAD 7.3a (luồng đăng nhập), ADR-011; API_DESIGN AD-02 |

## Mục tiêu

Lớp nói chuyện với IdP độc lập với nhà cung cấp, kiểm thử với mock-oauth2-server.

## Phạm vi file

- `backend/app/ports/identity.py`
- `backend/app/adapters/oidc_authlib.py`
- `backend/app/modules/identity/domain.py` (`IdTokenClaims`, `Role`)
- `backend/tests/integration/test_oidc_adapter.py`

## Các bước gợi ý

1. `authorization_url(state, nonce, code_challenge)`; `exchange_code(code, code_verifier, nonce)` kiểm tra chữ ký JWKS (cache 1 h), `iss`, `aud`, `exp`, `nonce`.
2. Đọc claim nhóm theo cấu hình `OIDC_GROUPS_CLAIM` (mặc định `groups`).
3. Ánh xạ lỗi IdP → `IdentityError` (không lộ token vào log).

## Tiêu chí hoàn thành

- [ ] Test với mock IdP: đổi code thành công trả `IdTokenClaims` có groups
- [ ] Test: nonce sai → `IdentityError`; token hết hạn → `IdentityError`
- [ ] Không có token/secret trong log (kiểm tra caplog)
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k oidc
```

## Ngoài phạm vi

- Chưa tạo phiên (T01-02)
- Cấu hình IdP doanh nghiệp thật chờ OQ-102 – chỉ là cấu hình, không đổi mã

## Kết quả triển khai

**Done** – Adapter OIDC (discovery, JWKS, PKCE S256, RS256/ES256); IdP giả lập cho dev.
