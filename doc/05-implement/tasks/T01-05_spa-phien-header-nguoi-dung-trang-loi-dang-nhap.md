# T01-05 – SPA: phiên, header người dùng, trang lỗi đăng nhập

| Trường | Giá trị |
|---|---|
| Lát | VS-1 – Đăng nhập và phiên (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T00-06](T00-06_khung-spa-theo-thiet-ke-s01-va-client-api-sinh-t.md), [T01-03](T01-03_endpoint-auth-va-me.md) |
| Story | US-023, US-C03 |
| Tài liệu tham chiếu | API_DESIGN 3.4.3, 3.7.4, CA-03; html_design S09, S10, S11; BLUEPRINT DD-10 (nháp trong sessionStorage) |

## Mục tiêu

Người dùng đăng nhập, thấy email, đăng xuất; hết phiên được chuyển đăng nhập mà không mất nháp.

## Phạm vi file

- `frontend/src/shared/session/useSessionGuard.ts`
- `frontend/src/app/Topbar.tsx`
- `frontend/src/pages/SessionExpired.tsx`
- `frontend/e2e/auth.spec.ts` (Playwright + mock IdP)

## Các bước gợi ý

1. Khởi động: gọi `/me`; 401 → chuyển `/api/v1/auth/login?return_to=<path>`.
2. Bắt 401 `session_expired` toàn cục → lưu nháp `aichat.draft` vào sessionStorage → hiện S11 → chuyển đăng nhập sau 5 s.
3. Topbar: avatar chữ cái, email, nút Đăng xuất (POST /auth/logout).

## Tiêu chí hoàn thành

- [ ] E2E: đăng nhập `p1` → thấy email ở header
- [ ] E2E: `outsider` → trang S09
- [ ] E2E: xóa phiên trong DB → thao tác tiếp → S11 → đăng nhập lại → nháp câu hỏi khôi phục
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make e2e -- auth.spec.ts
```

## Kết quả triển khai

**Done** – Header người dùng, đăng xuất, trang S09/S10/S11, lưu nháp khi hết phiên.
