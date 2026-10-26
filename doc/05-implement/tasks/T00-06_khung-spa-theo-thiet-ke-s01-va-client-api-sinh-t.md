# T00-06 – Khung SPA theo thiết kế S01 và client API sinh từ OpenAPI

| Trường | Giá trị |
|---|---|
| Lát | VS-0 – Nền tảng chạy được (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T00-01](T00-01_khoi-tao-monorepo-va-cong-cu.md) |
| Story | – (nền tảng / phi chức năng) |
| Tài liệu tham chiếu | doc/04-design/html_design/S01_main_empty.html, S09–S11; API_DESIGN 3.1, 3.2 (view model), 3.5; BLUEPRINT 2.4, 2.5 (UX, WCAG 2.2 AA) |

## Mục tiêu

Giao diện khung hai khu vực đúng thiết kế, design tokens dùng chung, kiểu TypeScript sinh từ `openapi.yaml`.

## Phạm vi file

- `frontend/src/styles/tokens.css` (lấy từ CSS trong html_design)
- `frontend/src/app/{AppShell,routes}.tsx`
- `frontend/src/features/{documents,chat}/` (component rỗng theo S01)
- `frontend/src/shared/api/schema.d.ts` (openapi-typescript)
- `frontend/src/shared/api/client.ts` (fetch, `X-CSRF-Token`, ánh xạ Problem)
- `frontend/src/shared/i18n/vi.json` (mọi chuỗi + `errors.<code>` từ API_DESIGN 3.6.3)
- `frontend/src/pages/{AccessDenied,LoginError}.tsx`
- nginx dev phục vụ SPA + proxy `/api` (service `web`)

## Các bước gợi ý

1. Sao chép design tokens (sáng/tối) và các class cơ sở từ html_design.
2. Dựng AppShell + DocumentPanel trống + ChatPanel trống (ô hỏi khóa) giống S01.
3. Script `pnpm gen:api` sinh kiểu từ `doc/04-design/openapi.yaml`.
4. Client: đọc cookie `csrf_token`, gắn header cho POST/PUT/DELETE; lỗi → `ApiError{code,status,detail,requestId}`.
5. TanStack Query provider; route `/access-denied`, `/login-error`.

## Tiêu chí hoàn thành

- [ ] Ảnh chụp màn hình (Playwright) của `/` khớp bố cục S01 ở 1440×900 (so sánh thủ công, đính kèm PR)
- [ ] axe-core không có vi phạm mức serious/critical trên `/`
- [ ] Unit test client: gắn CSRF header, ánh xạ Problem → ApiError
- [ ] Không có chuỗi tiếng Việt hard-code trong component (lint rule hoặc grep trong CI)
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
pnpm -C frontend gen:api && pnpm -C frontend test && pnpm -C frontend build
```

## Ngoài phạm vi

- Không gọi API thật ngoài /healthz

## Kết quả triển khai

**Done** – SPA Vite + React + TS theo S01; client viết tay `src/api.ts` (không sinh từ OpenAPI) – test hợp đồng đối chiếu `contracts/openapi.yaml`.
