# T01-03 – Endpoint /auth/* và /me

| Trường | Giá trị |
|---|---|
| Lát | VS-1 – Đăng nhập và phiên (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T01-02](T01-02_phien-dang-nhap-va-cookie.md) |
| Story | US-023, US-C01, US-C03 |
| Tài liệu tham chiếu | openapi.yaml `/auth/login`, `/auth/callback`, `/auth/logout`, `/me`; SAD 7.3a; USER_STORIES US-023 AC; html_design S09, S10 |

## Mục tiêu

Luồng đăng nhập/đăng xuất đầy đủ: người thuộc nhóm vào được, người ngoài nhóm bị chặn.

## Phạm vi file

- `backend/app/api/v1/auth.py`, `me.py`
- `backend/app/modules/identity/service.py` (upsert user, tạo workspace cá nhân + membership)
- `backend/app/modules/audit/service.py` (bản tối thiểu: `record(action, …)`)
- `backend/tests/integration/test_auth_flow.py`

## Các bước gợi ý

1. `/auth/login`: cookie tạm `oidc_tx` đã ký (state, nonce, code_verifier, return_to), 10 phút; `return_to` chỉ chấp nhận đường dẫn bắt đầu `/`.
2. `/auth/callback`: nhóm `aichat-users`/`aichat-admins` → upsert `app_user`, tạo `workspace(kind=personal, personal_owner_id)` lần đầu, tạo phiên, 302 `return_to`; không thuộc nhóm → audit `login_denied`, 302 `/access-denied`; lỗi state/nonce → 302 `/login-error`.
3. `/auth/logout`: xóa phiên (cascade hội thoại), xóa cookie, audit `logout`.
4. `/me`: user, role, `documents_used/limit` (từ `vw_workspace_quota`), `session_expires_at`, `limits` từ settings.

## Tiêu chí hoàn thành

- [ ] Test E2E API với mock IdP: user `p1` đăng nhập → `/me` 200 đúng email
- [ ] User `outsider` → 302 `/access-denied`, có `audit_event` `login_denied`
- [ ] `return_to=https://evil.example` bị bỏ qua
- [ ] Đăng nhập lần 2 không tạo workspace thứ hai
- [ ] Phản hồi `/me` khớp schema `Me` trong openapi.yaml
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k auth_flow
```
