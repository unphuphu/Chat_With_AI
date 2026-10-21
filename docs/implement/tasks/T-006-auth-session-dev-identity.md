# T-006 — Xác thực: IdentityPort, DevIdentity, phiên cookie, CSRF, require_role và màn đăng nhập (01)

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 0 |
| **Loại** | Fullstack |
| **User story** | US-E1 (nền tảng) |
| **Ưu tiên** | P0 |
| **Ước lượng** | 2 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-003, T-004, T-005 |
| **Mở khóa (task chờ task này)** | T-103, T-109, T-202 |
| **Người thực hiện** | _chưa giao_ (BE + FE) |
| **Trạng thái** | To do |

## 1. Mục tiêu

Người dùng dev đăng nhập qua màn 01, nhận phiên cookie phía máy chủ và vào được app; mọi route nghiệp vụ không có phiên trả `401 UNAUTHENTICATED`; thao tác ghi thiếu/sai `X-CSRF-Token` bị từ chối; `require_role()` chặn vai trò sai bằng `403 FORBIDDEN` và ghi `audit_log`. Thay `DevIdentity` bằng OIDC sau này **không** phải sửa module nghiệp vụ.

## 2. Bối cảnh

- AD-04: cookie phiên phía máy chủ thay vì JWT trong trình duyệt; OIDC Authorization Code + PKCE với IdP `[TBD: OQ-018]`; dev dùng `DevIdentity` ([SAD §4.1.1](../../design/SAD.md#411-xác-thực-và-phân-quyền), [Implement_plan §1.2](../Implement_plan.md#12-các-quyết-định-coi-như-đã-chốt-cho-việc-code)).
- Phiên: id ngẫu nhiên 256-bit, bảng `session` (T-004), cookie `HttpOnly; Secure; SameSite=Lax`, hết hạn tuyệt đối 12 giờ, rảnh 60 phút `[Proposed]`, xoay id khi đăng nhập ([SAD §2.3](../../design/SAD.md#23-tầng-hạ-tầng-dữ-liệu)).
- CSRF: `SameSite=Lax` + `X-CSRF-Token` (double-submit) cho mọi `POST/PUT/DELETE` + kiểm `Origin`.
- "Từ chối mặc định": mọi router khai báo phụ thuộc xác thực; T-109 duyệt toàn bộ route (AC-018).
- Kiểm quyền ở tầng service, không chỉ router ([Implement_plan §4.1](../Implement_plan.md#41-backend)).

## 3. Phạm vi

**Trong phạm vi**
- `IdentityPort`, adapter `DevIdentity` (`app/adapters/dev_identity/`).
- Module `access`: phiên, `current_user()`, `require_role()`, `ensure_role()`, kiểm CSRF + Origin.
- API-01: `GET /api/v1/auth/session`, `POST /api/v1/auth/logout`, cộng luồng đăng nhập `GET /api/v1/auth/login` và `GET /api/v1/auth/callback`.
- Ghi `audit_log`: `login_success`, `login_failed`, `logout`, `access_denied`.
- Script `python -m app.scripts.seed` tạo user dev (dùng bởi `make seed`).
- Frontend: màn 01, `SessionProvider`, nối `RequireRole` và nút đăng xuất của AppBar, gắn `X-CSRF-Token` trong `apiFetch`.

**Ngoài phạm vi**
- Adapter OIDC thật (sau OQ-018, cùng `IdentityPort`); tài khoản cục bộ Argon2id.
- Sự kiện telemetry `access_denied` vào `usage_event` ([T-110](./T-110-telemetry-documents-access.md)).
- Test duyệt toàn bộ route ([T-109](./T-109-route-auth-guard-test.md)); dọn phiên hết hạn ([T-407](./T-407-retention-cleanup.md)); header bảo mật ([T-405](./T-405-security-hardening.md)).

## 4. Thiết kế chi tiết

**Port và adapter**

```python
# app/ports/identity.py
@dataclass(frozen=True)
class IdentityClaims:
    subject: str          # khớp app_user.external_subject
    display_name: str

class IdentityPort(Protocol):
    def authorization_url(self, *, state: str, nonce: str, code_challenge: str, redirect_uri: str) -> str: ...
    async def authenticate(self, *, code: str, state: str, nonce: str, code_verifier: str,
                           redirect_uri: str) -> IdentityClaims: ...   # sai → raise AuthenticationFailed

# app/adapters/dev_identity/adapter.py
class DevIdentity(IdentityPort):
    """authorization_url trả thẳng redirect_uri?code=<subject>&state=<state>; authenticate trả claims của subject."""
```

`DevIdentity` chỉ được khởi tạo khi `AUTH_MODE=dev`; `create_app()` **từ chối khởi động** nếu `AUTH_MODE=dev` và `APP_ENV in {"staging","production"}`.

**Danh sách được cấp quyền:** người dùng phải có dòng trong `app_user` (khớp `external_subject`). Đăng nhập thành công ở IdP nhưng không có dòng → từ chối ("Tài khoản chưa được cấp quyền"). Ai quản lý danh sách `[TBD: OQ-018]`. Seed dev:

| `external_subject` | `display_name` | `role` |
|---|---|---|
| `dev-member` | Nguyễn Văn An | MEMBER |
| `dev-member-2` | Lê Thị Bình | MEMBER (để test cách ly hội thoại ở Sprint 2) |
| `dev-sponsor` | Trần Minh | SPONSOR |
| `dev-admin` | Quản trị Dev | ADMIN |
| *(không seed)* `dev-denied` | — | — (để test từ chối) |

**API**

| Endpoint | Công khai? | Hành vi |
|---|---|---|
| `GET /api/v1/auth/login?returnTo=/library[&devSubject=dev-member]` | có | Sinh `state`, `nonce`, `code_verifier` (PKCE), lưu trong cookie ký `cwd_login` (HttpOnly, 10 phút) `[Proposed]`; `302` tới `IdentityPort.authorization_url(...)`. `devSubject` chỉ có tác dụng khi `AUTH_MODE=dev` |
| `GET /api/v1/auth/callback?code&state` | có | Kiểm `state` với cookie; `authenticate()`; tra `app_user`; không có → audit `login_failed`, `302 /login?reason=denied`; lỗi IdP → `302 /login?reason=error`; thành công → xóa phiên cũ (nếu có cookie), tạo phiên mới, đặt cookie, audit `login_success`, `302 returnTo` |
| `GET /api/v1/auth/session` | có | Phiên hợp lệ → `200 {"user":{"id","displayName","role"},"csrfToken","expiresAt"}`; không → `401 UNAUTHENTICATED` |
| `POST /api/v1/auth/logout` | cần phiên + CSRF | Xóa dòng `session`, xóa cookie, audit `logout`, `204` |

`returnTo` chỉ nhận đường dẫn tương đối bắt đầu bằng `/` và không bắt đầu bằng `//` (chống open redirect), mặc định `/library`.

**Cookie:** `cwd_session` = `session.id` (`HttpOnly; Secure; SameSite=Lax; Path=/`). `Secure` tắt khi `APP_ENV=dev` vì localhost là HTTP `[Proposed]`. CSRF: `session.csrf_token` (32 byte ngẫu nhiên) trả trong body API-01 và cookie không-HttpOnly `cwd_csrf` (double-submit).

**Module `access`**

```python
@dataclass(frozen=True)
class CurrentUser: id: UUID; display_name: str; role: Role   # Role = Literal["MEMBER","SPONSOR","ADMIN"]

async def current_user(request: Request) -> CurrentUser: ...
    # đọc cwd_session → SELECT session JOIN app_user; hết hạn tuyệt đối (expires_at < now)
    # hoặc rảnh (last_seen_at < now - 60 phút) → xóa phiên, raise AppError(UNAUTHENTICATED, 401, ...)
    # cập nhật last_seen_at tối đa 1 lần/phút [Proposed]; gắn user_id vào context log
async def verify_csrf(request: Request, user: CurrentUser = Depends(current_user)) -> None: ...
    # áp dụng POST/PUT/PATCH/DELETE: header X-CSRF-Token == session.csrf_token (so sánh hằng thời gian)
    # và Origin (nếu có) == origin của app → sai: AppError(FORBIDDEN, 403, ...)
def require_role(*roles: Role) -> Callable[..., Awaitable[CurrentUser]]: ...   # dependency FastAPI
def ensure_role(user: CurrentUser, *roles: Role) -> None: ...                  # gọi trong service
```

`require_role`/`ensure_role` sai vai trò → ghi `audit_log(action='access_denied', target=<route template>, result='forbidden')` rồi `403 FORBIDDEN`. Thiếu phiên → `audit_log(action='access_denied', result='unauthenticated', user_id=null)`. Router nghiệp vụ tạo bằng helper `protected_router(prefix)` = `APIRouter(dependencies=[Depends(current_user), Depends(verify_csrf)])`; route công khai liệt kê trong hằng `PUBLIC_ROUTES` (đúng 5 mục: 3 route `/auth/login|callback|session`, `/health/live`, `/health/ready`) để T-109 dùng. Route tài liệu API (`/api/v1/openapi.json`, `/docs`) chỉ bật ở `dev/ci` và được T-109 loại trừ riêng `[Proposed]`.

**Frontend — màn 01** ([01_login.html](../../design/html_design/01_login.html), ảnh [login.png](../../design/images/login.png), [login_expired.png](../../design/images/login_expired.png)):
- Bố cục: `main.login` lưới căn giữa toàn màn (padding 24/16) → `.card.login-card` (max 440 px, padding 36/32, `box-shadow: var(--shadow)`). Từ trên xuống: ô logo 48×48 bo 13 px nền `--primary` icon `chat`; `h1` "Chat với Tài liệu" căn giữa; `.sub` "Đăng nhập để hỏi đáp trên tài liệu PDF của đội."; vùng thông báo `role="alert"` (ẩn khi không có `reason`); nút `.btn.btn-primary` rộng 100% icon `lock` "Đăng nhập bằng tài khoản công ty" → `window.location = /api/v1/auth/login?returnTo=…`; `.login-note` icon `info` "Chỉ người dùng được cấp quyền mới truy cập được. Nội dung tài liệu được xử lý theo chính sách dữ liệu của tổ chức."; `.help` "Không đăng nhập được? Liên hệ IT" (mailto).
- Trạng thái theo `?reason=`:

| `reason` | Banner | Tiêu đề | Nội dung |
|---|---|---|---|
| *(không có)* | — | — | — |
| `expired` | `.banner.warn` icon `alert` | Phiên đăng nhập đã hết hạn | Vì lý do bảo mật, vui lòng đăng nhập lại để tiếp tục. |
| `denied` | `.banner.err` icon `lock` | Tài khoản chưa được cấp quyền | Tài khoản của bạn đăng nhập thành công nhưng chưa nằm trong danh sách được phép. Liên hệ IT để được cấp quyền. |
| `error` | `.banner.err` icon `alert` | Không thể kết nối dịch vụ đăng nhập | Vui lòng thử lại sau ít phút. |

- Khi `import.meta.env.VITE_AUTH_MODE === 'dev'` `[Proposed]`: dưới nút chính hiện nhóm "Tài khoản dev" với 4 nút nhỏ (`dev-member`, `dev-sponsor`, `dev-admin`, `dev-denied`) gọi `/api/v1/auth/login?devSubject=…`. Không render ở build khác.
- `SessionProvider`: gọi `GET /api/v1/auth/session` khi khởi động (TanStack Query `['session']`); 401 → user null. Đã đăng nhập mà mở `/login` → chuyển `/library`. `apiFetch` gắn `X-CSRF-Token` cho phương thức ghi. Nút đăng xuất: `POST /auth/logout` → xóa cache → `/login`.

## 5. Các bước thực hiện

1. Viết `IdentityPort`, `DevIdentity`, test đơn vị adapter.
2. Viết repository phiên (`create`, `get_with_user`, `touch`, `delete`) và `SessionService` (TTL 12 giờ/60 phút).
3. Viết `current_user`, `verify_csrf`, `require_role`, `ensure_role`, `protected_router`, `PUBLIC_ROUTES`.
4. Viết router `auth` 4 endpoint; ghi audit trong cùng giao dịch với thay đổi phiên.
5. Viết `app/scripts/seed.py` (lũy đẳng: `INSERT … ON CONFLICT (external_subject) DO NOTHING`).
6. Thêm route mẫu nội bộ cho test (`GET /api/v1/_test/member` dùng `require_role("MEMBER")`, chỉ đăng ký khi `APP_ENV in {"dev","ci"}`) `[Proposed]`.
7. Frontend: `pages/Login.tsx`, `SessionProvider`, nối `RequireRole`, AppBar (tên, vai trò, đăng xuất), `apiFetch` CSRF.
8. Test tích hợp backend + test Vitest; QA so màn 01 với ảnh.

## 6. Tiêu chí chấp nhận

- [ ] `make seed` rồi bấm "Đăng nhập" (dev-member) → về `/library`, AppBar hiện "Nguyễn Văn An · Nhân viên PTKD" và 3 mục điều hướng; dev-sponsor → 2 mục.
- [ ] `curl /api/v1/auth/session` không cookie → `401` body `{"error":{"code":"UNAUTHENTICATED",…}}`; route mẫu bảo vệ không cookie → 401.
- [ ] `dev-denied` → quay về `/login?reason=denied` hiển thị banner đỏ "Tài khoản chưa được cấp quyền"; `audit_log` có `login_failed`.
- [ ] Cookie `cwd_session` có `HttpOnly`, `SameSite=Lax` (và `Secure` khi `APP_ENV≠dev`); id phiên đổi sau mỗi lần đăng nhập.
- [ ] `POST /auth/logout` thiếu `X-CSRF-Token` hoặc sai → 403 `FORBIDDEN`; đúng → 204, dòng `session` bị xóa, gọi lại API → 401.
- [ ] `Origin: https://evil.example` trên POST → 403.
- [ ] Phiên có `last_seen_at` cũ hơn 60 phút hoặc `expires_at` đã qua → 401 và dòng phiên bị xóa.
- [ ] Route mẫu `require_role("MEMBER")` gọi bằng dev-sponsor → 403 `FORBIDDEN` + `audit_log(action='access_denied')`.
- [ ] `returnTo=//evil.example` hoặc `https://…` → chuyển `/library`.
- [ ] `AUTH_MODE=dev` + `APP_ENV=production` → API không khởi động.
- [ ] Màn 01 với `?reason=expired` khớp [login_expired.png](../../design/images/login_expired.png); không có `reason` khớp [login.png](../../design/images/login.png) (bỏ qua nhóm nút dev).

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `DevIdentity.authorization_url` / `authenticate` | URL chứa `code=<subject>&state`; claims đúng |
| Unit | `ensure_role` đúng/sai | Không ném / `AppError(FORBIDDEN)` |
| Unit | Kiểm `returnTo` (`/a`, `//x`, `http://x`, rỗng) | `/a`, `/library`, `/library`, `/library` |
| Integration | Luồng login → session → logout (Testcontainers PG) | 302, 200, 204; DB đúng |
| Integration | CSRF thiếu/sai/đúng; Origin lạ | 403/403/204; 403 |
| Integration | Phiên hết hạn tuyệt đối và rảnh (đặt thời gian giả) | 401, dòng bị xóa |
| Integration | `state` không khớp cookie ở callback | `302 /login?reason=error`, không tạo phiên |
| Unit (FE) | `Login` với 3 giá trị `reason` | Banner đúng lớp, tiêu đề, nội dung |
| Unit (FE) | `apiFetch` POST | Header `X-CSRF-Token` có giá trị từ session |
| E2E | Đăng nhập dev → thấy `/library` → đăng xuất | Thực hiện đầy đủ ở [T-111](./T-111-e2e-sprint1.md) |

## 8. Cấu hình

`AUTH_MODE=dev` (`oidc` khi **OQ-018** chốt). Thêm `[Proposed]` vào `deploy/.env.example`: `SESSION_SECRET` (ký cookie `cwd_login`; bí mật thật từ secret manager), `SESSION_ABSOLUTE_HOURS=12`, `SESSION_IDLE_MINUTES=60` (SAD §2.3 `[Proposed]`, chờ **OQ-019**), `APP_ORIGIN=http://localhost:8080` (kiểm `Origin`). Frontend: `VITE_AUTH_MODE=dev`.

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| IdP chưa chọn `[TBD: OQ-018]` (SSO hay tài khoản riêng) | Adapter thật chưa viết được | `DevIdentity`; `IdentityPort` theo OIDC Code + PKCE để thêm adapter sau |
| Ai quản lý danh sách người dùng/vai trò `[TBD: OQ-018]`, ma trận quyền `[TBD: OQ-011]` | Cách cấp vai trò | Bảng `app_user` + seed; đổi quyền tập trung ở `ensure_role` |
| DevIdentity lọt vào staging/prod | Ai cũng đăng nhập được | Chặn khởi động theo `APP_ENV`; T-405 rà lại |
| API-01 không nêu rõ phản hồi khi chưa đăng nhập | Frontend/test lệch | `401` `[Proposed]`; frontend coi 401 là "chưa đăng nhập" |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §1.2, §4.1, §4.2, §6.1 (`app_user`, `session`), §6.8, §10.1 (API-01)
- [SAD](../../design/SAD.md) §2.3 (phiên, lưu giữ), §2.4 (quy ước xác thực), §4.1.1, §4.1.6, AD-04
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.5 (API-01, `IdentityPort.authenticate`, mã lỗi)
- [User_Stories](../../design/User_Stories.md) US-E1
- Màn hình: [01_login.html](../../design/html_design/01_login.html); ảnh [login.png](../../design/images/login.png), [login_expired.png](../../design/images/login_expired.png)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Log không chứa giá trị cookie, `csrf_token`, `code`, `state`; `.env.example` cập nhật biến mới.
