# T-109 — Viết test tự động bảo vệ mọi route (AC-018), chạy trong CI vĩnh viễn

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 1 |
| **Loại** | Backend |
| **User story** | US-E1 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 1 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-006 |
| **Mở khóa (task chờ task này)** | T-405 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Một bộ test duyệt **toàn bộ** route đã đăng ký trong ứng dụng FastAPI và thất bại nếu có route nghiệp vụ nào (a) không khai báo phụ thuộc xác thực, hoặc (b) trả khác `401 UNAUTHENTICATED` khi gọi không có phiên. Mọi route mới thêm sau này tự động bị kiểm — không cần ai nhớ viết test.

## 2. Bối cảnh

- [SAD §4.1.1](../../design/SAD.md#411-xác-thực-và-phân-quyền) "Thực thi từ chối mặc định": bài kiểm tra tự động duyệt toàn bộ route, thất bại nếu thiếu xác thực.
- AC-018 / QAS-04: người chưa xác thực hoặc không được cấp quyền bị từ chối ở **100%** điểm chức năng; launch gate [plan §8](../Implement_plan.md#8-launch-gate-điều-kiện-lên-production): "Test route tự động: 100% route nghiệp vụ từ chối khi chưa xác thực".
- Cơ chế phiên/CSRF/`require_role()`/`current_user()` do [T-006](./T-006-auth-session-dev-identity.md) cung cấp. Mã lỗi Blueprint §3.5: `UNAUTHENTICATED` (401), `FORBIDDEN` (403).

## 3. Phạm vi

**Trong phạm vi**
- Test tĩnh: kiểm cây phụ thuộc (`route.dependant`) của mỗi `APIRoute` có `current_user` (trực tiếp hoặc qua `require_role`).
- Test động: gọi từng route không cookie, với cookie sai, với phiên hết hạn → `401` đúng định dạng lỗi, không lộ dữ liệu.
- Test vai trò: bảng `ROUTE_ROLES` khai báo vai trò được phép; gọi bằng vai trò không được phép → `403 FORBIDDEN`.
- Test ghi không có `X-CSRF-Token` → bị từ chối.
- Danh sách trắng `PUBLIC_ROUTES` có lý do cho từng mục; meta-test chứng minh bộ kiểm phát hiện được route thiếu bảo vệ.
- Đánh dấu `pytest -m security`, chạy ở **mọi PR**, không được `skip`.

**Ngoài phạm vi**
- Chuyển hướng phía SPA về `/login` (E2E ở T-111).
- Header bảo mật, cookie flags (T-405).
- Sự kiện `access_denied` (T-110) — test này chỉ kiểm phản hồi HTTP.

## 4. Thiết kế chi tiết

**File**

| File | Nội dung |
|---|---|
| `backend/tests/security/test_route_auth_guard.py` | Test tĩnh + động |
| `backend/tests/security/route_policy.py` | `PUBLIC_ROUTES`, `ROUTE_ROLES`, bộ sinh tham số đường dẫn/thân giả |
| `backend/tests/security/test_guard_detects_unprotected.py` | Meta-test |
| `.github/workflows/ci.yml` | Bước `pytest -m security` bắt buộc |

**Chính sách**

```python
PUBLIC_ROUTES: dict[tuple[str, str], str] = {
    ("GET",  "/health/live"):            "API-12, probe hạ tầng",
    ("GET",  "/health/ready"):           "API-12, probe hạ tầng",
    ("GET",  "/api/v1/auth/session"):    "API-01, trả trạng thái phiên",
    # + các route đăng nhập/callback của DevIdentity/OIDC do T-006 định nghĩa (ghi rõ tên)
}
ROUTE_ROLES: dict[tuple[str, str], set[str]] = {
    ("POST",   "/api/v1/documents"):                 {"MEMBER", "ADMIN"},
    ("GET",    "/api/v1/documents"):                 {"MEMBER", "SPONSOR", "ADMIN"},
    ("GET",    "/api/v1/documents/{id}"):            {"MEMBER", "SPONSOR", "ADMIN"},
    ("GET",    "/api/v1/documents/{id}/file"):       {"MEMBER", "SPONSOR", "ADMIN"},
    ("DELETE", "/api/v1/documents/{id}"):            {"MEMBER", "ADMIN"},   # [TBD: OQ-011]
    # Sprint sau bổ sung: conversations/messages (MEMBER), reports/weekly (SPONSOR, ADMIN), ...
}
```

**Quy tắc kiểm**
1. Duyệt `app.routes`; với mỗi `APIRoute` × mỗi method (bỏ `HEAD`/`OPTIONS` tự sinh):
   - Nếu `(method, path)` ∈ `PUBLIC_ROUTES` → bỏ qua.
   - Ngược lại phải ∈ `ROUTE_ROLES` → nếu không: **thất bại** "route mới chưa khai báo chính sách vai trò".
2. Tĩnh: duyệt đệ quy `route.dependant.dependencies`; phải gặp `current_user` → nếu không: thất bại kèm tên route.
3. Động không phiên: thay `{id}`/`{...}` bằng `uuid4()`, thân JSON tối thiểu hợp lệ (hoặc `{}`), multipart rỗng cho upload. Kỳ vọng: `status == 401`, `body.error.code == "UNAUTHENTICATED"`, có `requestId`, thân **không** chứa khóa `items`/`content`/`name`.
4. Động với cookie rác và với phiên `expires_at < now()` → `401`.
5. Vai trò: tạo phiên cho từng vai trò không thuộc `ROUTE_ROLES[...]` → `403 FORBIDDEN` (kiểm quyền phải xảy ra **trước** khi xử lý tham số, nên `uuid4()` không tồn tại vẫn ra `403`, không ra `404`).
6. CSRF: với `POST/PUT/DELETE`, phiên hợp lệ nhưng thiếu `X-CSRF-Token` → bị từ chối theo mã T-006 quy định (`403`).
7. Route static file/SPA (nếu backend phục vụ) không thuộc `/api/v1` → không áp dụng; `/metrics` (T-404) nếu xuất hiện phải nằm trong `PUBLIC_ROUTES` với lý do "chỉ mạng nội bộ, chặn ở proxy" và được T-405 kiểm ở proxy.

**Meta-test**: tạo app thử gồm router của ứng dụng + 1 route `GET /api/v1/__unprotected` không có phụ thuộc xác thực → chạy hàm kiểm → khẳng định nó **thất bại** và nêu đúng tên route.

## 5. Các bước thực hiện

1. Viết `route_policy.py` với chính sách cho các route hiện có (Sprint 0–1).
2. Viết hàm `iter_business_routes(app)` và `has_auth_dependency(dependant)`.
3. Viết test tĩnh, test động không phiên/cookie rác/phiên hết hạn.
4. Viết test vai trò và CSRF với phiên tạo trực tiếp trong CSDL test (fixture của T-006).
5. Viết meta-test.
6. Thêm bước CI bắt buộc; ghi hướng dẫn ngắn ở đầu `route_policy.py`: "thêm route mới ⇒ khai báo ở `ROUTE_ROLES` trong cùng PR".

## 6. Tiêu chí chấp nhận

- [ ] Mọi route `/api/v1/*` hiện có (trừ `PUBLIC_ROUTES`) trả `401 UNAUTHENTICATED` khi không có phiên — 100% (AC-018, phần chưa xác thực).
- [ ] Phiên hết hạn và cookie giả → `401`.
- [ ] SPONSOR gọi `POST /api/v1/documents` và `DELETE /api/v1/documents/{id}` → `403 FORBIDDEN` (AC-018, phần không được cấp quyền).
- [ ] Thêm một route mới không có `current_user` → test thất bại với thông điệp nêu tên route (meta-test xanh).
- [ ] Thêm một route mới có xác thực nhưng chưa khai báo `ROUTE_ROLES` → test thất bại.
- [ ] Bước `pytest -m security` là bắt buộc trong CI cho mọi PR; tổng thời gian < 60 s.
- [ ] Phản hồi lỗi không chứa dữ liệu nghiệp vụ.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `has_auth_dependency` với phụ thuộc lồng 2 cấp | `True` |
| Integration | Mọi route, không cookie | `401`, `UNAUTHENTICATED` |
| Integration | Mọi route, phiên hết hạn | `401` |
| Integration | Ma trận vai trò × route | `403` khi không được phép |
| Integration | `DELETE` thiếu CSRF | Bị từ chối |
| Meta | Route `__unprotected` | Bộ kiểm báo lỗi |

## 8. Cấu hình

| Biến | Giá trị trong test | Ghi chú |
|---|---|---|
| `AUTH_MODE` | `dev` | `DevIdentity`; khi chuyển `oidc` (OQ-018) test vẫn phải xanh |
| `DATABASE_URL` | Testcontainers | Phiên test tạo trực tiếp |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| OQ-011 thay đổi ma trận quyền | Sửa `ROUTE_ROLES` | Một chỗ duy nhất; đồng bộ với `can_delete_document` (T-106) |
| OQ-018 thay IdP | Route đăng nhập đổi tên | Cập nhật `PUBLIC_ROUTES` trong PR của adapter OIDC |
| "Không nằm trong danh sách được cấp quyền" (AC-018) phụ thuộc cách IdP/DevIdentity cấp vai trò | Có thể không có phiên để kiểm `403` | T-006 từ chối đăng nhập người không có vai trò; T-111 kiểm E2E |
| Route bị kiểm quyền sau khi tải tài nguyên → trả `404` thay vì `403` | Rò rỉ sự tồn tại tài nguyên | Test bước 5 bắt lỗi này |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §4.3, §4.5, §7.1, §7.2, §8
- [SAD](../../design/SAD.md) §4.1.1, §4.1.7
- [Blueprint_Design](../../design/Blueprint_Design.md) §2.3 (QAS-04), §3.5
- [User_Stories](../../design/User_Stories.md) US-E1
- Task liên quan: [T-006](./T-006-auth-session-dev-identity.md), [T-110](./T-110-telemetry-documents-access.md), [T-111](./T-111-e2e-sprint1.md), [T-405](./T-405-security-hardening.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Mẫu PR (`.github/pull_request_template.md` nếu có) nhắc khai báo `ROUTE_ROLES` cho route mới.
