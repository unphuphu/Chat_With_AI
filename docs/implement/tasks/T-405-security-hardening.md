# T-405 — Gia cố bảo mật trước phát hành

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 4 |
| **Loại** | Backend / DevOps |
| **User story** | US-E1, US-E2 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 2 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-109 |
| **Mở khóa (task chờ task này)** | T-410 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Hệ thống đạt các biện pháp bảo mật của SAD §4.1 trước khi lên staging/production: header bảo mật (CSP, HSTS, `nosniff`…), cờ cookie đúng, test tự động chứng minh log không chứa nội dung, quét phụ thuộc và bí mật trong CI, vai trò CSDL của ứng dụng chỉ có `INSERT/SELECT` trên `audit_log`, và biên bản rà soát việc nhận tệp PDF.

## 2. Bối cảnh

- SAD §2.1 (CSP nghiêm ngặt, không `dangerouslySetInnerHTML`), §4.1.1 (cookie `HttpOnly; Secure; SameSite=Lax`, CSRF + kiểm `Origin`), §4.1.2 (TLS, HSTS ≥ 1 năm), §4.1.3 (bí mật, `gitleaks`), §4.1.4 (bảo vệ khi nhận PDF), §4.1.6 (`audit_log` chỉ ghi thêm), §4.1.7 (mối đe dọa).
- Quy tắc không được vi phạm số (3) ([Implement_plan §0](../Implement_plan.md#0-đọc-nhanh-5-phút)): không log nội dung tài liệu/câu hỏi/câu trả lời. Rủi ro "lộ nội dung qua log" ở [§9.2](../Implement_plan.md#92-rủi-ro-kỹ-thuật) giao cho task này.
- [T-109](./T-109-route-auth-guard-test.md) đã đảm bảo mọi route nghiệp vụ trả 401 khi không có phiên (AC-018); task này bổ sung kiểm tra theo vai trò (403) và các lớp phòng thủ còn lại. Kết quả là đầu vào của hồ sơ tuân thủ [T-406](./T-406-compliance-package.md).

## 3. Phạm vi

**Trong phạm vi**
- Header bảo mật ở Nginx (SPA + API) và middleware API (phòng thủ lớp 2).
- Rà soát/sửa cờ cookie phiên và CSRF; kiểm `Origin` cho `POST/PUT/DELETE`.
- Chặn khởi động với `AUTH_MODE=dev` ngoài môi trường dev.
- Test quét log/`usage_event`/`audit_log` bằng chuỗi canary.
- Quét phụ thuộc (Python + npm) và xác nhận `gitleaks` trong CI; quét toàn bộ lịch sử git một lần.
- Tách vai trò CSDL: chủ sở hữu lược đồ (chạy migration) và vai trò ứng dụng; `REVOKE UPDATE, DELETE, TRUNCATE` trên `audit_log`.
- Rà soát nhận tệp theo SAD §4.1.4 + test bổ sung cho lỗ hổng tìm thấy.

**Ngoài phạm vi** (để tránh làm thừa)
- Kiểm thử xâm nhập bởi bên thứ ba; quét mã độc ClamAV (`[Proposed — TBD: OQ-006/IT]`).
- Adapter OIDC thật (`[TBD: OQ-018]`); WAF.
- Hồ sơ tuân thủ dữ liệu AI (T-406).

## 4. Thiết kế chi tiết

**File cần tạo/sửa**

| File | Thay đổi |
|---|---|
| `deploy/nginx.conf` | `add_header … always` cho các header dưới; HSTS chỉ trong khối `server` TLS (staging/prod) |
| `backend/app/platform/security_headers.py` | `SecurityHeadersMiddleware` cho phản hồi API |
| `backend/app/access/session.py` (T-006) | xác nhận cờ cookie; `require_same_origin()` cho thao tác ghi |
| `backend/app/platform/config.py` | kiểm tra lúc khởi động: `AUTH_MODE=dev` chỉ khi `APP_ENV=dev` |
| `backend/migrations/versions/xxxx_app_role_grants.py` | tạo/cấp quyền vai trò |
| `backend/tests/integration/security/test_no_content_in_logs.py` | test canary |
| `backend/tests/integration/security/test_security_headers.py`, `test_audit_log_grants.py`, `test_role_matrix.py`, `test_upload_hardening.py` | test |
| `.github/workflows/ci.yml` | job `pip-audit`, `npm audit`, xác nhận `gitleaks` |
| `docs/implement/security/T-405-review.md` `[Proposed]` | biên bản rà soát (checklist mục 4 cuối) |

**Header** (Nginx cho mọi phản hồi; API middleware cho `/api/*`):

| Header | Giá trị |
|---|---|
| `Content-Security-Policy` | `default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; worker-src 'self' blob:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'` `[Proposed]` (`worker-src blob:` cho pdf.js — `[Verify]` khi build) |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` (chỉ qua HTTPS) |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `same-origin` `[Proposed]` |
| `X-Frame-Options` | `DENY` (trình duyệt cũ; tương đương `frame-ancestors`) |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` `[Proposed]` |
| `Cache-Control` (API JSON) | `no-store` `[Proposed]` |

Ghi chú CSP: React đặt `style` qua CSSOM nên không vi phạm `style-src 'self'`; **cấm** thẻ `<style>`/`<script>` nội tuyến trong `index.html` (Vite build ra tệp riêng). Không dùng `'unsafe-inline'`/`'unsafe-eval'`.

**Cookie** (SAD §4.1.1): phiên `HttpOnly; Secure; SameSite=Lax; Path=/`; cookie CSRF (double-submit) `Secure; SameSite=Lax; Path=/` (không `HttpOnly` để SPA đọc). Xoay id phiên khi đăng nhập, xóa khi đăng xuất. `Origin` của `POST/PUT/DELETE` phải bằng `PUBLIC_ORIGIN`, sai → `403 FORBIDDEN`.

**Vai trò CSDL** `[Proposed]` tên vai trò:

```sql
-- chạy bởi vai trò chủ sở hữu (migration)
CREATE ROLE cwd_app LOGIN;            -- mật khẩu từ secret manager, không nằm trong migration
GRANT USAGE ON SCHEMA public TO cwd_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO cwd_app;
REVOKE UPDATE, DELETE, TRUNCATE ON audit_log FROM cwd_app;
GRANT SELECT, INSERT ON audit_log TO cwd_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO cwd_app;
```

Migration chạy bằng `MIGRATION_DATABASE_URL` (chủ sở hữu); API/Worker dùng `DATABASE_URL` (`cwd_app`). Phân vùng `usage_event` tạo mới (T-407) phải được cấp quyền cho `cwd_app` trong cùng câu lệnh tạo.

**Test canary (log không chứa nội dung):** chuỗi duy nhất `CANARY-<uuid4>` được đặt vào (a) văn bản PDF mẫu, (b) tên tệp, (c) câu hỏi, (d) nội dung câu trả lời của `FakeLlm`. Chạy luồng: tải lên → xử lý → hỏi → đánh giá → xem báo cáo → xóa. Bắt mọi bản ghi log (capture handler structlog + stdout/stderr ở mức INFO và WARNING), toàn bộ `usage_event.properties`, `audit_log.target`, thuộc tính span (exporter in-memory, T-404), nhãn `/metrics`. Khẳng định: không nơi nào chứa canary (b) ở dạng đầy đủ, không nơi nào chứa (a), (c), (d).

**Ma trận vai trò** (`test_role_matrix.py`, bổ sung cho T-109) theo SAD §4.1.1: SPONSOR gọi `POST /conversations/{id}/messages` → 403; MEMBER gọi `GET /reports/weekly` → 403; SPONSOR `DELETE /documents/{id}` → 403; ADMIN xem hội thoại người khác → 404/403 (không lộ tồn tại); mọi 403 ghi `access_denied`.

**Quét phụ thuộc:** `pip-audit -r` (hoặc trên lockfile) và `npm audit --omit=dev --audit-level=high`; lỗ hổng mức High/Critical làm fail CI; ngoại lệ ghi trong `security/allowlist.yaml` `[Proposed]` kèm lý do + ngày hết hạn ≤ 30 ngày. Chạy `gitleaks detect --log-opts="--all"` một lần trên toàn lịch sử, ghi kết quả vào biên bản.

**Checklist rà soát nhận tệp** (SAD §4.1.4) — mỗi mục ghi "Đạt / Không đạt + bằng chứng (test/đoạn code)":
1. Kiểm phần mở rộng **và** 5 byte `%PDF-` (T-103).
2. Giới hạn kích thước đếm khi truyền luồng, dừng ngay khi vượt `MAX_UPLOAD_MB`; Nginx `client_max_body_size` khớp.
3. Giới hạn `MAX_PAGES` kiểm trong worker trước khi trích toàn bộ.
4. Tiến trình con trích văn bản: timeout 120 s, giới hạn bộ nhớ (`RLIMIT_AS`/cgroup), không có biến môi trường bí mật, không truy cập mạng ra ngoài `[Verify]` cách cô lập mạng trên hạ tầng.
5. Khóa đối tượng `documents/{uuid}.pdf` sinh phía máy chủ; tên gốc chỉ ở cột `name`.
6. `GET /documents/{id}/file`: `Content-Type: application/pdf`, `Content-Disposition: inline` với tên đã mã hóa RFC 5987, `nosniff`.
7. Tên tệp/câu trả lời hiển thị qua React text node / Markdown đã làm sạch; không `dangerouslySetInnerHTML` (lint rule `react/no-danger` = error).

## 5. Các bước thực hiện

1. Thêm header vào `nginx.conf` + `SecurityHeadersMiddleware`; build SPA và mở mọi màn (01–09) với CSP bật, sửa vi phạm (console không có lỗi CSP).
2. Rà soát cookie/CSRF/`Origin`; thêm kiểm tra khởi động `APP_ENV`/`AUTH_MODE`.
3. Viết migration vai trò; chuyển compose/staging sang hai chuỗi kết nối; chạy toàn bộ test với `cwd_app`.
4. Viết test canary, ma trận vai trò, header, quyền `audit_log`, nhận tệp.
5. Thêm job quét phụ thuộc vào CI; chạy `gitleaks` trên toàn lịch sử.
6. Làm checklist nhận tệp, sửa điểm không đạt (tạo ticket nếu > 0,5 ngày), viết biên bản rà soát và gửi Tech Lead duyệt.

## 6. Tiêu chí chấp nhận

- [ ] `curl -sI https://<staging>/` và `/api/v1/auth/session` có đủ header ở bảng mục 4; HSTS `max-age ≥ 31536000`.
- [ ] Mở 9 màn hình trên bản build với CSP bật: 0 lỗi CSP trong console (E2E Playwright lắng nghe `securitypolicyviolation`).
- [ ] Cookie phiên có `HttpOnly`, `Secure`, `SameSite=Lax`; `POST` với `Origin` lạ → 403; thiếu `X-CSRF-Token` → 403.
- [ ] API khởi động với `APP_ENV=staging` và `AUTH_MODE=dev` → thoát với lỗi cấu hình rõ ràng.
- [ ] Test canary pass: 0 lần xuất hiện canary trong log, `usage_event`, `audit_log`, span, metric.
- [ ] Kết nối bằng `cwd_app`: `UPDATE audit_log …` và `DELETE FROM audit_log` → `permission denied`; `INSERT`/`SELECT` thành công.
- [ ] CI có job quét phụ thuộc fail khi có lỗ hổng High/Critical chưa được miễn trừ; `gitleaks` toàn lịch sử: 0 phát hiện (hoặc đã xử lý và ghi biên bản).
- [ ] Ma trận vai trò SAD §4.1.1: 100% ô "—"/"✗" có test trả 403 (hoặc 404 cho tài nguyên của người khác).
- [ ] Biên bản rà soát nhận tệp: 7/7 mục "Đạt" hoặc có ticket được Tech Lead chấp nhận; biên bản chuyển cho T-406.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Integration | Phản hồi API bất kỳ | Có `nosniff`, `Cache-Control: no-store` |
| Integration | `POST /api/v1/documents` với `Origin: https://evil.example` | 403 `FORBIDDEN` |
| Integration | Luồng đầy đủ với canary | Không lộ canary |
| Integration | `cwd_app` UPDATE/DELETE/TRUNCATE `audit_log` | Bị từ chối |
| Integration | Tệp `.pdf` có nội dung PNG | `UNSUPPORTED_FORMAT` |
| Integration | Tệp `MAX_UPLOAD_MB + 1` MB | `FILE_TOO_LARGE`, đối tượng S3 không được tạo |
| Integration | PDF `MAX_PAGES + 1` trang | Bị từ chối (theo hành vi T-103/T-104) |
| Integration | Tên tệp `../../x"<img src=x onerror=alert(1)>.pdf` | Khóa S3 là UUID; `Content-Disposition` an toàn; UI hiển thị nguyên văn, không thực thi |
| Integration | PDF làm tiến trình trích treo | Bị kết thúc sau 120 s, tài liệu `FAILED` |
| E2E | Duyệt 9 màn với CSP | 0 vi phạm |
| CI | Thêm gói có CVE High (nhánh thử) | Job quét fail |

## 8. Cấu hình

| Biến | Giá trị | Ghi chú |
|---|---|---|
| `AUTH_MODE` | `dev` / `oidc` | [Implement_plan §3.3](../Implement_plan.md#33-biến-môi-trường); `oidc` khi có OQ-018 |
| `APP_ENV` `[Proposed]` | `dev` \| `ci` \| `staging` \| `prod` | Dùng cho kiểm tra khởi động |
| `PUBLIC_ORIGIN` `[Proposed]` | `http://localhost:8080` `[Default]` | So khớp `Origin` |
| `MIGRATION_DATABASE_URL` `[Proposed]` | chủ sở hữu lược đồ | Chỉ cho bước migration; bí mật từ secret manager |
| `DATABASE_URL` | vai trò `cwd_app` | |
| `MAX_UPLOAD_MB`, `MAX_PAGES` | `50`, `500` `[Default]` | `[TBD: OQ-013]` |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Cookie `Secure` trên `http://localhost` | Trình duyệt có thể không gửi cookie ở local | Trình duyệt hiện đại coi `localhost` là ngữ cảnh an toàn `[Verify]`; nếu không, chỉ tắt `Secure` khi `APP_ENV=dev` |
| `audit_log` giữ 12 tháng (SAD §2.3) nhưng `cwd_app` không có `DELETE` | Không dọn được bằng job ứng dụng | Dọn bằng vai trò chủ sở hữu theo quy trình vận hành (xem T-407) |
| pdf.js cần `blob:`/worker | CSP chặn viewer | Bổ sung tối thiểu `worker-src 'self' blob:`; ghi vào biên bản |
| Cách cô lập mạng tiến trình con phụ thuộc hạ tầng | Mục 4 checklist có thể chưa đạt ở VM | Ghi rủi ro trong biên bản, chuyển IT/Bảo mật ở T-406 |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §0, §4.1, §4.2, §5.5 (T-405), §7.1 (Bảo mật), §9.2
- [SAD](../../design/SAD.md) §2.1, §2.3, §4.1.1–§4.1.7
- [User_Stories](../../design/User_Stories.md) US-E1, US-E2
- Màn hình: [html_design/09_access_denied.html](../../design/html_design/09_access_denied.html)
- Task liên quan: [T-006](./T-006-auth-session-dev-identity.md), [T-103](./T-103-upload-api.md), [T-104](./T-104-ingest-worker.md), [T-109](./T-109-route-auth-guard-test.md), [T-404](./T-404-observability.md), [T-406](./T-406-compliance-package.md), [T-407](./T-407-retention-cleanup.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Biên bản rà soát được Tech Lead duyệt và đính kèm vào hồ sơ T-406.
