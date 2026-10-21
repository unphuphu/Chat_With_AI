# T-005 — Dựng khung React: app shell, tokens.css, AppBar theo vai trò, trang lỗi (màn 09)

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 0 |
| **Loại** | Frontend |
| **User story** | — nền tảng (hỗ trợ US-E1 qua màn 09) |
| **Ưu tiên** | P0 |
| **Ước lượng** | 2 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-001 |
| **Mở khóa (task chờ task này)** | T-006, T-107, T-209, T-304, T-308, T-402 |
| **Người thực hiện** | _chưa giao_ (FE) |
| **Trạng thái** | To do |

## 1. Mục tiêu

SPA React chạy được với router đầy đủ các route của [Implement_plan §6.8](../Implement_plan.md#68-ánh-xạ-màn-hình--route-frontend) (trang rỗng có tiêu đề), app shell có AppBar hiển thị điều hướng **theo vai trò**, bộ biến giao diện `tokens.css` lấy nguyên từ thiết kế HTML, client API dùng chung, và trang lỗi 401/403/404/503 khớp màn 09.

## 2. Bối cảnh

- Frontend bám màn hình trong `docs/design/html_design/`; sao chép biến màu và thành phần từ CSS chung vào `styles/tokens.css` ([Implement_plan §4.2](../Implement_plan.md#42-frontend)).
- 9 tệp HTML dùng chung một khối CSS (khoảng 184 dòng đầu thẻ `<style>` giống hệt nhau); phần riêng của từng màn nằm cuối khối.
- Màn 09 phải không lộ nội dung thư viện, hiển thị mã lỗi và mã yêu cầu để IT truy vết ([User_Stories US-E1](../../design/User_Stories.md#us-e1)).
- Thanh điều hướng: MEMBER thấy Thư viện · Hỏi đáp · Lịch sử; SPONSOR thấy Thư viện · Báo cáo (Implement_plan §6.8).

## 3. Phạm vi

**Trong phạm vi**
- Vite + React 18 + TypeScript strict, React Router, TanStack Query, thư viện i18n.
- `styles/tokens.css` (biến sáng/tối) và `styles/app.css` (lớp dùng chung) `[Proposed]` tách tệp.
- Sprite biểu tượng SVG + component `Icon`.
- `AppLayout`, `AppBar`, cấu hình điều hướng theo vai trò, `RequireRole`.
- `ErrorPage` cho `/error/401|403|404|503` và route lạ `*` → 404.
- `api/client.ts`: fetch dùng chung, parse lỗi chuẩn, xử lý 401/403.
- Trang giữ chỗ: Library, Chat, CitationViewer, History, WeeklyReport, Login (khung).

**Ngoài phạm vi**
- Phiên, gọi `GET /api/v1/auth/session`, nội dung màn đăng nhập, gửi `X-CSRF-Token` ([T-006](./T-006-auth-session-dev-identity.md)).
- Nội dung từng màn ([T-107](./T-107-library-screen.md), [T-209](./T-209-chat-screen-core.md), [T-210](./T-210-citation-viewer-screen.md), [T-304](./T-304-history-screen.md), [T-402](./T-402-weekly-report-screen.md)).
- Vô hiệu hóa "Hỏi đáp" khi chưa có tài liệu `READY` ([T-108](./T-108-empty-library-screen.md)) — chỉ chuẩn bị prop `disabled`.
- Đưa toàn bộ chuỗi vào `vi.json` và ngôn ngữ khác ([T-308](./T-308-i18n.md)).

## 4. Thiết kế chi tiết

**Tệp**

```text
frontend/index.html, vite.config.ts            # dev proxy: /api, /health → http://localhost:8080
frontend/src/main.tsx
frontend/src/app/router.tsx                    # createBrowserRouter
frontend/src/app/providers.tsx                 # QueryClientProvider, i18n
frontend/src/app/AppLayout.tsx                 # skip link + AppBar + <main id="main"><Outlet/></main>
frontend/src/app/AppBar.tsx
frontend/src/app/nav.ts                        # navItemsFor(role)
frontend/src/app/RequireRole.tsx
frontend/src/pages/{Login,Library,Chat,CitationViewer,History,WeeklyReport,ErrorPage}.tsx
frontend/src/components/{Icon,IconSprite,Button,Badge,Banner}.tsx
frontend/src/api/client.ts, errors.ts, types.ts
frontend/src/styles/tokens.css, app.css
frontend/src/i18n/vi.json, index.ts
```

**`tokens.css`:** chép nguyên khối `:root{…}` (sáng), `@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])){…}}` và `:root[data-theme="dark"]{…}` từ [01_login.html](../../design/html_design/01_login.html). Biến: `--bg --surface --surface2 --ink --ink2 --muted --line --line2 --primary --primary-h --on-primary --link --primary-soft --series-1 --grid --ok --ok-bg --warn --warn-bg --err --err-bg --info --info-bg --shadow --focus --r`. Không đổi giá trị.
**`app.css`:** chép các lớp chung (base `body/h1-h3/a/:focus-visible`, `.ic*`, `.sr`, `.skip`, `.appbar*`, `.brand`, `.logo`, `.nav`, `.user*`, `.avatar`, `.page*`, `.card*`, `.btn*`, `.badge*`, `.spin`, `.banner*`, `.input`, `.t`, `.backdrop/.modal/.toast`, `.dropzone`, `.chat…`, `.skel`, media query 860px/640px, `prefers-reduced-motion`). **Bỏ** `.tbd` và `details.notes` (chỉ dùng cho tài liệu thiết kế). CSS riêng của màn (ví dụ `.login*`, `.err-card`) đặt trong CSS module của trang.
**Icon:** sprite gồm các `symbol` `i-upload, i-file, i-trash, i-chat, i-clock, i-chart, i-check, i-alert, i-x, i-send, i-up, i-down, i-plus, i-search, i-ext, i-lock, i-logout, i-refresh, i-info, i-folder, i-back, i-next, i-zoomin, i-zoomout, i-chev, i-wifi-off, i-layers` (viewBox 24). `<Icon name="folder" size="sm|md|lg|xl" />` render `<svg class="ic" aria-hidden="true"><use href="#i-folder"/></svg>`.

**Router** (Implement_plan §6.8):

| Route | Trang | Vai trò được vào | Layout |
|---|---|---|---|
| `/login` | Login | công khai | không AppBar |
| `/library` | Library | MEMBER, SPONSOR, ADMIN | AppLayout |
| `/chat`, `/chat/:conversationId` | Chat | MEMBER | AppLayout |
| `/documents/:id/view` | CitationViewer | MEMBER, SPONSOR, ADMIN | AppLayout |
| `/history` | History | MEMBER | AppLayout |
| `/reports/weekly` | WeeklyReport | SPONSOR, ADMIN | AppLayout |
| `/error/:code` | ErrorPage | công khai | không AppBar |
| `/` | chuyển `/library` | — | — |
| `*` | ErrorPage code=404 | công khai | không AppBar |

Quyền theo ma trận [SAD §4.1.1](../../design/SAD.md#411-xác-thực-và-phân-quyền): xem tệp PDF cho cả ba vai trò; hỏi đáp/lịch sử chỉ MEMBER; báo cáo SPONSOR/ADMIN. `RequireRole({ roles, user, children })`: `user` null → `/login`; sai vai trò → `/error/403`. Ở task này `user` lấy từ một `SessionContext` giữ chỗ (mặc định null); T-006 nối với API-01. Backend vẫn là nơi kiểm quyền thật.

**AppBar** (khớp `<header class="appbar">` của [02_library.html](../../design/html_design/02_library.html), [08_weekly_report.html](../../design/html_design/08_weekly_report.html)):
- Trái: `.brand` → `/library`, ô `.logo` icon `chat`, chữ "Chat với Tài liệu" (`.bn`, ẩn ≤ 640 px). Tên chính thức `[TBD: OQ-016]` → đặt trong `vi.json` (`app.name`).
- Giữa: `<nav class="nav" aria-label="Điều hướng chính">`, mục đang mở có `aria-current="page"`.
- Phải: `.avatar` (2 chữ cái đầu tên, `aria-hidden`), `.user-meta` (tên in đậm + nhãn vai trò; ẩn ≤ 640 px), nút đăng xuất `.out` icon `logout`, `aria-label="Đăng xuất"` — gọi `onLogout` prop (T-006 nối API).

```ts
type Role = 'MEMBER' | 'SPONSOR' | 'ADMIN';
interface NavItem { to: string; labelKey: string; icon: IconName; disabled?: boolean }
function navItemsFor(role: Role): NavItem[];
// MEMBER  → [Thư viện /library folder, Hỏi đáp /chat chat, Lịch sử /history clock]
// SPONSOR → [Thư viện /library folder, Báo cáo /reports/weekly chart]
// ADMIN   → như SPONSOR [Proposed — thiết kế chưa có; chờ PO xác nhận ở T-000]
```

Nhãn vai trò: MEMBER "Nhân viên PTKD", SPONSOR "Sponsor / Quản lý" (theo thiết kế), ADMIN "Quản trị hệ thống" `[Proposed]`. Mục `disabled` render `class="disabled" aria-disabled="true" tabIndex={-1}` như [03_library_empty.html](../../design/html_design/03_library_empty.html).

**ErrorPage (màn 09,** [09_access_denied.html](../../design/html_design/09_access_denied.html), ảnh [denied_403.png](../../design/images/denied_403.png), [denied_401.png](../../design/images/denied_401.png)**):** nền `--bg`, thẻ `.card.err-card` căn giữa (max 480 px, padding 40/32, `box-shadow: var(--shadow)`, chữ căn giữa), icon `ic-xl` màu `--err`, `h1`, đoạn mô tả màu `--ink2`, hàng nút `.acts`, dòng `.ref` cỡ .78rem: "Mã lỗi: `<code>` · Mã yêu cầu: `<code>`". Không có AppBar, không gọi API dữ liệu.

| Code | Icon | Tiêu đề | Mô tả | `code` hiển thị | Nút |
|---|---|---|---|---|---|
| 401 | clock | Phiên đăng nhập đã hết hạn | Vì lý do bảo mật, bạn cần đăng nhập lại. Nội dung bạn đang nhập có thể chưa được lưu. | `UNAUTHENTICATED` | primary "Đăng nhập lại" → `/login?reason=expired` |
| 403 | lock | Bạn không có quyền truy cập | Tài khoản của bạn chưa được cấp quyền dùng chức năng này. Nếu bạn cho rằng đây là nhầm lẫn, hãy liên hệ quản trị viên. | `FORBIDDEN` | primary "Về trang Thư viện" → `/library`; "Liên hệ quản trị viên" (mailto, cấu hình) |
| 404 | search | Không tìm thấy trang | Trang bạn mở không tồn tại hoặc tài liệu/hội thoại đã bị xóa. | `NOT_FOUND` | primary "Về trang Thư viện" |
| 503 | alert | Hệ thống tạm thời không khả dụng | Chúng tôi đang gặp sự cố. Vui lòng thử lại sau ít phút. | `UPSTREAM_UNAVAILABLE` | primary "Thử lại" (reload) |

Mã yêu cầu lấy từ query `?rid=` `[Proposed]` (client API điền khi chuyển hướng); không có thì ẩn phần "Mã yêu cầu". Code lạ → hiển thị 404.

**Client API**

```ts
export class ApiError extends Error { code: string; status: number; requestId?: string }
export async function apiFetch<T>(path: string, init?: RequestInit & { json?: unknown }): Promise<T>;
// - same-origin, credentials: 'same-origin', tiền tố /api/v1
// - phản hồi lỗi → parse {error:{code,message,requestId}} → ném ApiError
// - 401 → navigate('/login?reason=expired') ; 403 → navigate(`/error/403?rid=${requestId}`)
// - hook beforeRequest để T-006 gắn X-CSRF-Token cho POST/PUT/DELETE
```

**Truy cập:** link "Bỏ qua tới nội dung" (`.skip`) trỏ `#main`; mọi nút icon có `aria-label`; focus nhìn thấy (`:focus-visible` trong CSS).

## 5. Các bước thực hiện

1. `npm create vite` (react-ts) trong `frontend/` giữ cấu hình lint của T-001; thêm react-router, @tanstack/react-query, i18next + react-i18next `[Proposed]`.
2. Trích CSS chung từ HTML thiết kế vào `tokens.css`/`app.css`; trích sprite SVG vào `IconSprite.tsx` (render một lần trong `AppLayout` và `ErrorPage`).
3. Viết `nav.ts`, `AppBar.tsx`, `AppLayout.tsx`, `RequireRole.tsx`.
4. Viết `router.tsx` theo bảng; trang giữ chỗ hiển thị `<h1>` tiêu đề trang (từ `vi.json`).
5. Viết `ErrorPage.tsx` theo bảng 4 trạng thái.
6. Viết `api/client.ts`, `errors.ts`.
7. Viết test Vitest + Testing Library; chụp màn `/error/403` và `/error/401` so với ảnh thiết kế ở 1280 px.

## 6. Tiêu chí chấp nhận

- [ ] `npm run dev` mở được mọi route ở bảng; `/` chuyển `/library`; `/khong-ton-tai` hiển thị trang 404.
- [ ] AppBar với `role=MEMBER` có đúng 3 mục (Thư viện, Hỏi đáp, Lịch sử); `role=SPONSOR` có đúng 2 mục (Thư viện, Báo cáo); mục của route hiện tại có `aria-current="page"`.
- [ ] Ở độ rộng ≤ 640 px, tên ứng dụng và `.user-meta` bị ẩn; không có cuộn ngang.
- [ ] `/error/401`, `/error/403`, `/error/404`, `/error/503` hiển thị đúng icon, tiêu đề, mô tả, mã lỗi, nút theo bảng; `?rid=req_x` hiển thị "Mã yêu cầu: req_x".
- [ ] QA so `/error/403` và `/error/401` với `denied_403.png`, `denied_401.png`: bố cục, màu, chữ khớp.
- [ ] `tokens.css` chứa 100% biến của thiết kế với giá trị giống hệt (kiểm bằng script so chuỗi).
- [ ] `apiFetch` nhận 401 → điều hướng `/login?reason=expired`; nhận 403 → `/error/403?rid=…`.
- [ ] Không có chuỗi hiển thị viết cứng trong component mới (dùng `t()`), lint `react/no-danger` sạch.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `navItemsFor('MEMBER'/'SPONSOR'/'ADMIN')` | 3 / 2 / 2 mục đúng thứ tự, đúng `to` |
| Unit | `AppBar` render với route `/history` | Mục "Lịch sử" có `aria-current="page"` |
| Unit | `AppBar` mục `disabled` | `aria-disabled="true"`, `tabIndex=-1` |
| Unit | `ErrorPage` từng code + code lạ | Nội dung theo bảng; code lạ → 404 |
| Unit | `RequireRole` user null / sai vai trò | Chuyển `/login` / `/error/403` |
| Unit | `apiFetch` mock 401, 403, 500 | Điều hướng đúng; 500 ném `ApiError` có `requestId` |
| Thủ công | So ảnh thiết kế màn 09 | Khớp |

## 8. Cấu hình

Không có biến backend. Frontend: email liên hệ quản trị viên `VITE_SUPPORT_EMAIL` `[Proposed]` (thiết kế dùng `it-support@example.com` làm ví dụ). Dev proxy trỏ `http://localhost:8080` (T-002).

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Điều hướng của ADMIN chưa có trong thiết kế | Có thể làm sai ý PO | Dùng như SPONSOR `[Proposed]`, cô lập trong `navItemsFor` |
| Tên sản phẩm chính thức `[TBD: OQ-016]` | Đổi nhãn sau | Đặt trong `vi.json` |
| Trình duyệt hỗ trợ, mức WCAG `[TBD: OQ-020]` | Phạm vi kiểm thử UI | Mặc định Chrome/Edge/Firefox bản mới; WCAG 2.1 AA (SAD §2.1) |
| Thiết kế dùng `#hash` (`#401`, `#expired`) cho biến thể | Không hợp với React Router | Dùng route `/error/:code` và query `?reason=` `[Proposed]` |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §3.1, §4.2, §6.8
- [SAD](../../design/SAD.md) §2.1, §4.1.1
- [User_Stories](../../design/User_Stories.md) US-E1, §1.3, §8
- Màn hình: [09_access_denied.html](../../design/html_design/09_access_denied.html), [02_library.html](../../design/html_design/02_library.html) (AppBar MEMBER), [08_weekly_report.html](../../design/html_design/08_weekly_report.html) (AppBar SPONSOR), [03_library_empty.html](../../design/html_design/03_library_empty.html) (mục bị vô hiệu)
- Ảnh: [denied_403.png](../../design/images/denied_403.png), [denied_401.png](../../design/images/denied_401.png), [library.png](../../design/images/library.png), [report.png](../../design/images/report.png)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Ảnh chụp `/error/401`, `/error/403` đính kèm PR.
