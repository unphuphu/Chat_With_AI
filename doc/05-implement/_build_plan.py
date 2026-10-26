import io, os, re, sys
OUT = sys.argv[1]
TASK_DIR = os.path.join(OUT, "tasks")
os.makedirs(TASK_DIR, exist_ok=True)

# ----------------------------------------------------------------------------- slices
SLICES = [
 ("VS-0", "Nền tảng chạy được", "Repo, CI, docker-compose, schema CSDL, API khung, SPA khung",
  "`make up` → mở http://localhost:8080 thấy khung giao diện S01; `GET /api/v1/readyz` = ready; CI xanh", [], "Lát 1"),
 ("VS-1", "Đăng nhập và phiên", "OIDC với IdP giả lập, phiên, CSRF, workspace cá nhân, /me",
  "Đăng nhập bằng mock IdP → thấy email ở header; người ngoài nhóm → S09; đăng xuất", ["US-023", "US-C03"], "Lát 1"),
 ("VS-2", "Tải lên một PDF", "Lô tải lên, kiểm tra file trong sandbox, lưu object storage, danh sách tài liệu",
  "Kéo thả 1 PDF → thấy tiến độ → dòng 'Đang xử lý' trong danh sách", ["US-001", "US-006"], "Lát 1"),
 ("VS-3", "Xử lý tài liệu", "Hàng đợi job, trích văn bản, chia đoạn theo trang, embedding, ghi chỉ mục, SSE",
  "Tài liệu tự chuyển 'Sẵn sàng' không cần tải lại trang; PDF scan → 'Thất bại' + lý do", ["US-005", "US-007", "US-008", "US-025"], "Lát 1"),
 ("VS-4", "Hỏi đáp có trích dẫn", "Truy xuất kết hợp, LLM qua adapter, kiểm tra trích dẫn, hội thoại, giao diện chat",
  "Hỏi một câu → câu trả lời có [1] và nhãn 'tên file · tr.X'; hỏi tiếp trong cùng phiên. **Hết lát 1 (walking skeleton)**",
  ["US-012", "US-013", "US-014", "US-020"], "Lát 1"),
 ("VS-5", "Nhiều file và giới hạn", "Tải nhiều file, mọi đường từ chối, hạn mức, idempotency, giới hạn tần suất tải lên",
  "Chọn 12 file → không tải file nào; 10 file → tải song song 3; mất mạng → 'Tải lại' không tạo trùng", ["US-002", "US-003", "US-004"], "Lát 2"),
 ("VS-6", "Chất lượng câu trả lời", "Chưa đủ thông tin, tổng hợp nhiều tài liệu, số trang, bộ đánh giá RAG",
  "Câu hỏi ngoài tài liệu → 'Chưa đủ thông tin'; báo cáo MET-002…005 từ bộ đánh giá", ["US-016", "US-017", "US-021"], "Lát 2"),
 ("VS-7", "Xóa tài liệu", "Xóa mềm + xóa đoạn trong một transaction, dọn file gốc ≤ 24 h",
  "Xóa tài liệu → không còn được trích dẫn ngay; file gốc biến mất khỏi MinIO sau job purge", ["US-010", "US-011"], "Lát 2"),
 ("VS-8", "Cách ly và bảo mật", "Bộ test phân quyền mọi endpoint, RLS, header bảo mật, quét bí mật/phụ thuộc",
  "Bộ test 2 workspace xanh 100%; báo cáo quét bảo mật không còn High/Critical", ["US-024"], "Lát 2"),
 ("VS-9", "Lỗi, giới hạn và phiên", "Circuit breaker, 503/504, giới hạn câu hỏi, xử lý lỗi phía giao diện, hết phiên",
  "Tắt LLM giả → thẻ lỗi + 'Gửi lại'; hỏi 11 câu/phút → đếm ngược; hết phiên → S11, giữ nháp", ["US-025", "US-026"], "Lát 2"),
 ("VS-10", "Vận hành và đo lường", "Nhật ký kiểm toán, analytics, giám sát, tác vụ bảo trì, đóng gói triển khai, load test",
  "Dashboard Grafana có số liệu; k6 20 người dùng đạt p90 ≤ 15 s; báo cáo launch gate G-01…G-09", ["NFR-012", "PRD 5.2"], "Lát 2"),
 ("VS-11", "Tính năng P1", "Xử lý lại, gửi lại câu hỏi, mâu thuẫn, trình xem PDF, câu hỏi tiếp nối",
  "Từng tính năng P1 theo AC của story", ["US-009", "US-015", "US-018", "US-022", "US-027"], "Lát 3"),
 ("SPIKE", "Thử nghiệm kỹ thuật", "SPIKE-01…04 (SAD 12) – chạy song song, kết quả cập nhật cấu hình/ADR",
  "Báo cáo spike có số liệu và đề xuất", [], "Song song"),
]

# ----------------------------------------------------------------------------- tasks
# (id, slice, title, size, status, deps, refs, goal, files, steps, done, verify, out)
T = []
def task(id, sl, title, size, status, deps, refs, goal, files, steps, done, verify, out=None):
    T.append(dict(id=id, sl=sl, title=title, size=size, status=status, deps=deps, refs=refs, goal=goal,
                  files=files, steps=steps, done=done, verify=verify, out=out or []))

# ---------------- VS-0
task("T00-01", "VS-0", "Khởi tạo monorepo và công cụ", "S", "Ready", [],
 ["BLUEPRINT 3.1 (cấu trúc thư mục)", "BLUEPRINT 3.3 (quy tắc tầng)", "SAD ADR-002, ADR-003"],
 "Tạo cấu trúc repo theo BLUEPRINT 3.1 và bộ lệnh chuẩn để mọi task sau dùng chung.",
 ["`backend/` (pyproject.toml với uv, ruff, mypy strict, pytest, import-linter)", "`backend/app/{api/v1,modules,ports,adapters,infra}/__init__.py`, `backend/worker/`",
  "`embedding-service/` (pyproject riêng)", "`frontend/` (Vite + React 18 + TypeScript strict, vitest, eslint, prettier)", "`Makefile`, `.editorconfig`, `.gitignore`, `.pre-commit-config.yaml`", "`README.md` (cách chạy)"],
 ["Tạo cây thư mục đúng BLUEPRINT 3.1 (chỉ file rỗng/`__init__.py`).", "Cấu hình `ruff` (line 110), `mypy --strict` cho `app/`, `pytest` với marker `integration`, `e2e`.",
  "Thêm `.importlinter` với 5 hợp đồng ở BLUEPRINT 3.3 (sẽ xanh vì chưa có mã).",
  "Tạo Makefile: `lint`, `typecheck`, `test-unit`, `test-int`, `e2e`, `up`, `down`, `fmt`.", "Frontend: `pnpm create vite` template react-ts, bật `strict`, thêm vitest."],
 ["`make lint typecheck test-unit` chạy thành công trên repo trống", "`pnpm -C frontend build` thành công", "`lint-imports` chạy và xanh", "README mô tả yêu cầu máy (Python 3.12, Node 20, Docker) và các lệnh make"],
 ["make lint typecheck test-unit", "pnpm -C frontend build && pnpm -C frontend test"],
 ["Không viết mã nghiệp vụ", "Không cấu hình CI (T00-07)"])

task("T00-02", "VS-0", "docker-compose môi trường dev", "S", "Ready", ["T00-01"],
 ["SAD 9.1 (Phương án B – nội bộ)", "BLUEPRINT 3.6.6 (biến môi trường)", "DATABASE_DESIGN A.0"],
 "Một lệnh `make up` dựng đủ hạ tầng dev: PostgreSQL 16 + pgvector, MinIO, IdP OIDC giả lập.",
 ["`deploy/docker-compose.dev.yml`", "`deploy/postgres/init/00_roles.sql` (6 vai trò ở đầu schema.sql, mật khẩu dev)", "`.env.example`", "`Makefile` (up/down/psql/logs)"],
 ["Service `db`: image `pgvector/pgvector:pg16`, volume, healthcheck `pg_isready`; script init tạo vai trò.",
  "Service `minio` + job tạo bucket `aichat-docs` (tắt versioning – SAD 8.2).",
  "Service `idp`: `ghcr.io/navikt/mock-oauth2-server` cấu hình claim `groups` = [`aichat-users`] cho user `p1`, không có nhóm cho user `outsider`.",
  "`.env.example` liệt kê mọi biến ở BLUEPRINT 3.6.6 với giá trị dev; bí mật để `change-me`."],
 ["`make up` khởi động 3 service healthy trong ≤ 60 s", "`make psql` vào được bằng `app_migrator`; `SELECT extversion FROM pg_extension WHERE extname='vector'` ≥ 0.8", "Bucket tồn tại, versioning tắt", "Discovery `http://localhost:8090/default/.well-known/openid-configuration` trả JSON"],
 ["make up && docker compose -f deploy/docker-compose.dev.yml ps", "make psql -c \"select extversion from pg_extension where extname='vector'\""],
 ["Không chứa service ứng dụng (thêm ở T00-04, T00-06)"])

task("T00-03", "VS-0", "Migration 0001 từ schema.sql và fixture CSDL cho test", "M", "Ready", ["T00-02"],
 ["doc/04-design/schema.sql v0.3", "doc/04-design/seed_dev.sql", "DATABASE_DESIGN A.9"],
 "Áp dụng schema thiết kế bằng Alembic và có fixture Testcontainers để mọi test tích hợp dùng PostgreSQL thật.",
 ["`backend/migrations/` (alembic.ini, env.py)", "`backend/migrations/versions/0001_initial.py` (thực thi nội dung schema.sql)", "`backend/tests/conftest.py` (fixture `pg` dùng testcontainers `pgvector/pgvector:pg16`)", "`backend/tests/integration/test_schema.py`"],
 ["Copy `schema.sql` vào `backend/migrations/sql/0001_initial.sql`; `upgrade()` đọc và thực thi; `downgrade()` drop schema.",
  "Fixture tạo vai trò (như init script), chạy `alembic upgrade head`, chạy `seed_dev.sql` với `SET app.env='dev'`.",
  "Viết test: (a) seed chạy được; (b) chèn `chunk` cho tài liệu PROCESSING rồi COMMIT → lỗi `check_violation`; (c) chuyển READY→PROCESSING → lỗi; (d) `app_api` với `app.workspace_id` của P1 không thấy tài liệu của P2; (e) `app_api` không đặt workspace → 0 hàng."],
 ["`alembic upgrade head` rồi `downgrade base` rồi `upgrade head` thành công", "5 test tích hợp ở bước 3 xanh", "Mọi lỗi phát hiện khi chạy schema trên PostgreSQL thật được sửa **cả** ở `doc/04-design/schema.sql` (ghi chú trong PR)"],
 ["make test-int -k schema"],
 ["Không viết repository/ORM model (task sau)"])

task("T00-04", "VS-0", "Khung API: settings, lỗi RFC 9457, request id, health", "M", "Ready", ["T00-01"],
 ["BLUEPRINT 3.6.1, 3.6.6", "API_DESIGN 3.5 (mô hình lỗi), 3.6.2, AD-10", "openapi.yaml (`Problem`, `ErrorCode`, /healthz, /readyz)"],
 "API FastAPI chạy được với cấu hình kiểm tra lúc khởi động, định dạng lỗi thống nhất và health check.",
 ["`backend/app/main.py` (app factory, composition root)", "`backend/app/infra/settings.py` (pydantic-settings, mọi biến 3.6.6)", "`backend/app/api/errors.py` (ProblemException, handler, ánh xạ 422 FastAPI → `invalid_request`/`empty_question`/`question_too_long`)",
  "`backend/app/infra/logging.py` (structlog JSON, lọc trường cấm)", "`backend/app/api/middleware.py` (RequestId)", "`backend/app/api/v1/health.py`", "`deploy/docker-compose.dev.yml` (service `api`)"],
 ["Settings: giá trị sai kiểu/ngoài khoảng → tiến trình thoát với thông báo rõ.", "Middleware RequestId: nhận/sinh `X-Request-ID`, gắn vào log context và header phản hồi.",
  "Handler: mọi ngoại lệ → `application/problem+json` có `type=https://errors.aichat.local/<code>`, `code`, `request_id`; ngoại lệ lạ → 500 `internal_error`, không lộ stack.",
  "Bộ lọc log xóa khóa `question`, `answer`, `content`, `file_name`, `email` (SAD 8.3).", "`/readyz` kiểm tra `SELECT 1`."],
 ["Unit test: 3 loại lỗi (ProblemException, validation, ngoại lệ lạ) trả đúng schema `Problem` (validate bằng jsonschema từ openapi.yaml)", "Unit test bộ lọc log", "`/healthz` 200, `/readyz` 200 khi có DB và 503 khi không"],
 ["make test-unit -k 'errors or health or logging'", "curl -i localhost:8000/api/v1/readyz"],
 ["Không có xác thực (VS-1)"])

task("T00-05", "VS-0", "Hạ tầng CSDL: engine theo vai trò và phạm vi workspace", "M", "Ready", ["T00-03", "T00-04"],
 ["BLUEPRINT 3.2.3 (bất biến), 3.3", "SAD 5.1 (vai trò CSDL)", "DATABASE_DESIGN A.10 (PgBouncer, LISTEN)"],
 "Mọi truy cập dữ liệu tài liệu đi qua `workspace_scope()` – không thể vô tình truy vấn ngoài phạm vi.",
 ["`backend/app/infra/db.py`", "`backend/tests/integration/test_db_scope.py`"],
 ["Async engine (psycopg 3) theo URL vai trò (`DATABASE_URL_API`, `_WORKER`, `_MAINTENANCE`), pool 10.",
  "Context manager `workspace_scope(session, ws_id)` mở transaction và `SET LOCAL app.workspace_id`.",
  "Helper `scoped_execute` ném `WorkspaceScopeMissing` nếu gọi trên bảng có RLS khi chưa đặt scope (kiểm tra `current_setting`).",
  "Phiên kết nối đặt `TimeZone=UTC`."],
 ["Test: trong scope P1 đọc được tài liệu P1, không thấy P2", "Test: gọi helper không có scope → `WorkspaceScopeMissing`", "Test: `SET LOCAL` không rò sang transaction kế tiếp trên cùng kết nối pool"],
 ["make test-int -k db_scope"],
 ["Không viết repository nghiệp vụ"])

task("T00-06", "VS-0", "Khung SPA theo thiết kế S01 và client API sinh từ OpenAPI", "M", "Ready", ["T00-01"],
 ["doc/04-design/html_design/S01_main_empty.html, S09–S11", "API_DESIGN 3.1, 3.2 (view model), 3.5", "BLUEPRINT 2.4, 2.5 (UX, WCAG 2.2 AA)"],
 "Giao diện khung hai khu vực đúng thiết kế, design tokens dùng chung, kiểu TypeScript sinh từ `openapi.yaml`.",
 ["`frontend/src/styles/tokens.css` (lấy từ CSS trong html_design)", "`frontend/src/app/{AppShell,routes}.tsx`", "`frontend/src/features/{documents,chat}/` (component rỗng theo S01)", "`frontend/src/shared/api/schema.d.ts` (openapi-typescript)", "`frontend/src/shared/api/client.ts` (fetch, `X-CSRF-Token`, ánh xạ Problem)", "`frontend/src/shared/i18n/vi.json` (mọi chuỗi + `errors.<code>` từ API_DESIGN 3.6.3)", "`frontend/src/pages/{AccessDenied,LoginError}.tsx`", "nginx dev phục vụ SPA + proxy `/api` (service `web`)"],
 ["Sao chép design tokens (sáng/tối) và các class cơ sở từ html_design.", "Dựng AppShell + DocumentPanel trống + ChatPanel trống (ô hỏi khóa) giống S01.",
  "Script `pnpm gen:api` sinh kiểu từ `doc/04-design/openapi.yaml`.", "Client: đọc cookie `csrf_token`, gắn header cho POST/PUT/DELETE; lỗi → `ApiError{code,status,detail,requestId}`.",
  "TanStack Query provider; route `/access-denied`, `/login-error`."],
 ["Ảnh chụp màn hình (Playwright) của `/` khớp bố cục S01 ở 1440×900 (so sánh thủ công, đính kèm PR)", "axe-core không có vi phạm mức serious/critical trên `/`", "Unit test client: gắn CSRF header, ánh xạ Problem → ApiError", "Không có chuỗi tiếng Việt hard-code trong component (lint rule hoặc grep trong CI)"],
 ["pnpm -C frontend gen:api && pnpm -C frontend test && pnpm -C frontend build"],
 ["Không gọi API thật ngoài /healthz"])

task("T00-07", "VS-0", "Pipeline CI", "S", "Ready", ["T00-03", "T00-04", "T00-06"],
 ["BLUEPRINT QA-10, QA-12", "API_DESIGN AC-06 (oasdiff)", "SAD 8.1 (bí mật)"],
 "Mỗi pull request được kiểm tra tự động đủ các cổng chất lượng của dự án.",
 ["`.github/workflows/ci.yml` (hoặc tương đương nội bộ)", "`backend/scripts/check_openapi.py`"],
 ["Job backend: ruff, mypy, lint-imports, pytest unit, pytest integration (Testcontainers).", "Job frontend: eslint, tsc, vitest, build.",
  "Job contract: validate `openapi.yaml` (openapi-spec-validator + kiểm tra ví dụ); sinh OpenAPI từ FastAPI và so bằng `oasdiff breaking` (chỉ endpoint đã hiện thực).",
  "Job bảo mật: gitleaks, `pip-audit`, `pnpm audit --prod` (fail ở High/Critical).", "Cache uv/pnpm; tổng thời gian mục tiêu < 10 phút."],
 ["CI chạy xanh trên nhánh chính", "PR cố ý thêm bí mật giả → job gitleaks fail", "PR cố ý đổi kiểu trường trong FastAPI khác openapi.yaml → job contract fail"],
 ["(trên CI) toàn bộ workflow xanh"],
 ["Không triển khai tự động (T10-05)"])

# ---------------- VS-1
task("T01-01", "VS-1", "IdentityPort và adapter OIDC (Authorization Code + PKCE)", "M", "Ready", ["T00-04"],
 ["BLUEPRINT 3.2.2 (`IdentityPort`), 3.6.6", "SAD 7.3a (luồng đăng nhập), ADR-011", "API_DESIGN AD-02"],
 "Lớp nói chuyện với IdP độc lập với nhà cung cấp, kiểm thử với mock-oauth2-server.",
 ["`backend/app/ports/identity.py`", "`backend/app/adapters/oidc_authlib.py`", "`backend/app/modules/identity/domain.py` (`IdTokenClaims`, `Role`)", "`backend/tests/integration/test_oidc_adapter.py`"],
 ["`authorization_url(state, nonce, code_challenge)`; `exchange_code(code, code_verifier, nonce)` kiểm tra chữ ký JWKS (cache 1 h), `iss`, `aud`, `exp`, `nonce`.",
  "Đọc claim nhóm theo cấu hình `OIDC_GROUPS_CLAIM` (mặc định `groups`).", "Ánh xạ lỗi IdP → `IdentityError` (không lộ token vào log)."],
 ["Test với mock IdP: đổi code thành công trả `IdTokenClaims` có groups", "Test: nonce sai → `IdentityError`; token hết hạn → `IdentityError`", "Không có token/secret trong log (kiểm tra caplog)"],
 ["make test-int -k oidc"],
 ["Chưa tạo phiên (T01-02)", "Cấu hình IdP doanh nghiệp thật chờ OQ-102 – chỉ là cấu hình, không đổi mã"])

task("T01-02", "VS-1", "Phiên đăng nhập và cookie", "M", "Ready", ["T00-05", "T01-01"],
 ["BLUEPRINT 3.7.3, DD-01", "SAD 8.1 (phiên, CSRF)", "schema.sql `session`", "API_DESIGN 3.6.3 (`session_expired`)"],
 "Tạo/xác thực/hết hạn phiên an toàn; dependency `resolve_session` cho mọi endpoint cần đăng nhập.",
 ["`backend/app/modules/identity/{service.py,repository.py}`", "`backend/app/api/deps.py` (`resolve_session` → `SessionContext`)", "`backend/tests/integration/test_session.py`"],
 ["Sinh `sid` và `csrf_token` 32 byte (secrets), lưu SHA-256; cookie `sid` HttpOnly/Secure/SameSite=Lax/Path=/; `csrf_token` Secure/SameSite=Strict.",
  "Gia hạn `idle_expires_at` tối đa 1 lần/phút (ghi DB); hết hạn → 401 `session_expired`; không có cookie → 401 `unauthenticated`.",
  "`SessionContext` gắn vào `request.state`."],
 ["Test: phiên hợp lệ → context đúng user/workspace", "Test: quá idle 2 h hoặc absolute 10 h (giả lập thời gian) → 401 `session_expired`", "Test: 100 request trong 1 phút → chỉ 1 lần UPDATE `last_seen_at`", "Test: DB chỉ chứa băm, không chứa token gốc"],
 ["make test-int -k session"])

task("T01-03", "VS-1", "Endpoint /auth/* và /me", "M", "Ready", ["T01-02"],
 ["openapi.yaml `/auth/login`, `/auth/callback`, `/auth/logout`, `/me`", "SAD 7.3a", "USER_STORIES US-023 AC", "html_design S09, S10"],
 "Luồng đăng nhập/đăng xuất đầy đủ: người thuộc nhóm vào được, người ngoài nhóm bị chặn.",
 ["`backend/app/api/v1/auth.py`, `me.py`", "`backend/app/modules/identity/service.py` (upsert user, tạo workspace cá nhân + membership)", "`backend/app/modules/audit/service.py` (bản tối thiểu: `record(action, …)`)", "`backend/tests/integration/test_auth_flow.py`"],
 ["`/auth/login`: cookie tạm `oidc_tx` đã ký (state, nonce, code_verifier, return_to), 10 phút; `return_to` chỉ chấp nhận đường dẫn bắt đầu `/`.",
  "`/auth/callback`: nhóm `aichat-users`/`aichat-admins` → upsert `app_user`, tạo `workspace(kind=personal, personal_owner_id)` lần đầu, tạo phiên, 302 `return_to`; không thuộc nhóm → audit `login_denied`, 302 `/access-denied`; lỗi state/nonce → 302 `/login-error`.",
  "`/auth/logout`: xóa phiên (cascade hội thoại), xóa cookie, audit `logout`.", "`/me`: user, role, `documents_used/limit` (từ `vw_workspace_quota`), `session_expires_at`, `limits` từ settings."],
 ["Test E2E API với mock IdP: user `p1` đăng nhập → `/me` 200 đúng email", "User `outsider` → 302 `/access-denied`, có `audit_event` `login_denied`", "`return_to=https://evil.example` bị bỏ qua", "Đăng nhập lần 2 không tạo workspace thứ hai", "Phản hồi `/me` khớp schema `Me` trong openapi.yaml"],
 ["make test-int -k auth_flow"])

task("T01-04", "VS-1", "Middleware CSRF và thứ tự middleware", "S", "Ready", ["T01-02"],
 ["API_DESIGN 3.3 (thứ tự middleware), 2.6 (CSRF)", "SAD 8.1 (CSRF)"],
 "Mọi request POST/PUT/DELETE có phiên phải có `X-CSRF-Token` hợp lệ.",
 ["`backend/app/api/middleware.py` (CSRF)", "`backend/tests/unit/test_csrf.py`"],
 ["So `SHA-256(header)` với `session.csrf_token_hash` bằng so sánh hằng thời gian.", "Miễn trừ: GET/HEAD, `/auth/login`, `/auth/callback`.", "Đăng ký thứ tự: RequestId → Telemetry → Session → CSRF → WorkspaceScope → RateLimit."],
 ["Test: thiếu header → 403 `csrf_invalid`; sai → 403; đúng → qua", "Test: GET không cần header", "Test liệt kê mọi route POST/PUT/DELETE trong app và khẳng định đều bị CSRF bảo vệ (chống quên khi thêm route)"],
 ["make test-unit -k csrf"])

task("T01-05", "VS-1", "SPA: phiên, header người dùng, trang lỗi đăng nhập", "M", "Ready", ["T00-06", "T01-03"],
 ["API_DESIGN 3.4.3, 3.7.4, CA-03", "html_design S09, S10, S11", "BLUEPRINT DD-10 (nháp trong sessionStorage)"],
 "Người dùng đăng nhập, thấy email, đăng xuất; hết phiên được chuyển đăng nhập mà không mất nháp.",
 ["`frontend/src/shared/session/useSessionGuard.ts`", "`frontend/src/app/Topbar.tsx`", "`frontend/src/pages/SessionExpired.tsx`", "`frontend/e2e/auth.spec.ts` (Playwright + mock IdP)"],
 ["Khởi động: gọi `/me`; 401 → chuyển `/api/v1/auth/login?return_to=<path>`.", "Bắt 401 `session_expired` toàn cục → lưu nháp `aichat.draft` vào sessionStorage → hiện S11 → chuyển đăng nhập sau 5 s.",
  "Topbar: avatar chữ cái, email, nút Đăng xuất (POST /auth/logout)."],
 ["E2E: đăng nhập `p1` → thấy email ở header", "E2E: `outsider` → trang S09", "E2E: xóa phiên trong DB → thao tác tiếp → S11 → đăng nhập lại → nháp câu hỏi khôi phục"],
 ["make e2e -- auth.spec.ts"])

# ---------------- VS-2
task("T02-01", "VS-2", "BlobPort và adapter S3/MinIO", "S", "Ready", ["T00-02", "T00-04"],
 ["BLUEPRINT 3.2.2 (`BlobPort`), 3.5.2 (khóa object)", "SAD 6.2 (timeout, thử lại)"],
 "Lưu/đọc/xóa file PDF qua interface, có bản in-memory cho unit test.",
 ["`backend/app/ports/blob.py`", "`backend/app/adapters/blob_s3.py` (aioboto3 hoặc minio-py async)", "`backend/app/adapters/blob_memory.py`", "`backend/tests/integration/test_blob_s3.py`"],
 ["`put(key, stream, sha256)` với SSE (`ServerSideEncryption` khi cấu hình), kiểm tra checksum; `get_stream`; `delete` idempotent; `list(prefix, older_than)` cho ALG-10.",
  "Timeout 30 s, thử lại 3 lần với lỗi mạng/5xx.", "Khóa `ws/{workspace_id}/doc/{document_id}.pdf` sinh bằng hàm duy nhất `document_key()`."],
 ["Test với MinIO: put→get trả đúng byte; delete 2 lần không lỗi; list theo tuổi", "Unit test: adapter memory có cùng hành vi (chạy chung bộ test hợp đồng cho 2 adapter)"],
 ["make test-int -k blob"])

task("T02-02", "VS-2", "Sandbox và kiểm tra PDF khi nhận (ALG-02)", "M", "Ready", ["T00-04"],
 ["BLUEPRINT ALG-02, 3.6.5 (sandbox), DD-02, QA-07", "SAD 4.1 bước 1"],
 "Kiểm tra định dạng, số trang, mật khẩu trong tiến trình con bị giới hạn, trả `InspectionResult`.",
 ["`backend/app/infra/sandbox.py`", "`backend/app/modules/documents/pdf_inspector.py`", "`backend/tests/fixtures/pdf/` (hợp lệ, docx đổi đuôi, mã hóa mật khẩu, mã hóa mật khẩu rỗng, 301 trang, hỏng, PDF bom nén nhỏ)", "`backend/tests/unit/test_pdf_inspector.py`"],
 ["`sandbox.run(fn, args, timeout_s, mem_mb)`: multiprocessing `spawn`, `RLIMIT_AS`, `RLIMIT_CPU`, không kế thừa socket; trả kết quả hoặc `SandboxTimeout`/`SandboxCrashed`.",
  "Semaphore 2 + chờ tối đa 30 s → `SandboxBusy` (→ 503 `server_busy`).", "Thuật toán đúng ALG-02 (byte `%PDF-`, `decrypt('')`, đếm trang).", "Sinh fixture bằng script `tests/fixtures/pdf/make_fixtures.py` (không commit file lớn)."],
 ["Mỗi fixture cho đúng kết quả (`ok`/`not_pdf`/`encrypted`/`too_many_pages`)", "PDF mật khẩu rỗng → ok", "Hàm treo giả lập → `SandboxTimeout` trong ≤ timeout + 1 s, tiến trình cha vẫn chạy", "Hàm cấp phát 2 GB → `SandboxCrashed`"],
 ["make test-unit -k 'sandbox or pdf_inspector'"],
 ["Chỉ chạy trên Linux/container (CI); trên Windows dev đánh dấu skip có lý do"])

task("T02-03", "VS-2", "API tạo lô tải lên và hạn mức (ALG-01 create_batch)", "S", "Ready", ["T01-03"],
 ["BLUEPRINT ALG-01", "openapi.yaml `POST /upload-batches`, `UploadBatch`, `QuotaProblem`", "DATABASE_DESIGN A.5 (`vw_workspace_quota`)"],
 "Đặt chỗ cho lô tải lên, chặn vượt số file/lần và hạn mức tài liệu.",
 ["`backend/app/modules/documents/{quota.py,service.py,repository.py}`", "`backend/app/api/v1/upload_batches.py` (POST)", "`backend/tests/integration/test_create_batch.py`"],
 ["Khóa hàng `workspace` FOR UPDATE; tính `used`; tạo `upload_batch` (TTL `BATCH_TTL_S`).", "Lỗi: `too_many_files` (> `MAX_FILES_PER_BATCH`), `quota_exceeded` kèm `remaining`."],
 ["Test: 10 file → 201, `slots=10`; 11 file → 422 `too_many_files`, không tạo lô", "Test: đã có 95 tài liệu, xin 10 → 422 `quota_exceeded`, `remaining=5`", "Test đồng thời: 2 request song song mỗi cái 6 file khi còn 10 chỗ → đúng 1 thành công", "Phản hồi khớp schema openapi"],
 ["make test-int -k create_batch"])

task("T02-04", "VS-2", "API nhận file vào lô (ALG-01 accept_file, idempotent)", "M", "Ready", ["T02-01", "T02-02", "T02-03"],
 ["BLUEPRINT ALG-01 (pha 0–4)", "API_DESIGN AD-06", "openapi.yaml `PUT /upload-batches/{batch_id}/files/{client_file_id}`"],
 "Nhận một PDF, kiểm tra, lưu object, tạo tài liệu PROCESSING + job ingest; gửi lại cùng `client_file_id` không tạo trùng.",
 ["`backend/app/api/v1/upload_batches.py` (PUT)", "`backend/app/modules/documents/service.py` (`accept_file`)", "`backend/app/infra/jobs.py` (`enqueue` tối thiểu + `pg_notify('job_enqueued')`)", "`backend/tests/integration/test_accept_file.py`"],
 ["Pha 0 tra `(batch_id, client_file_id)` → 200 nếu có.", "Pha 1 stream ra file tạm, dừng khi vượt `MAX_FILE_MB` → `too_large`; gọi inspector.",
  "Pha 2 transaction ngắn trừ chỗ đặt (cả khi bị từ chối); pha 3 `blob.put`; pha 4 INSERT … ON CONFLICT + job + audit `document_upload`.", "Xóa file tạm trong `finally`."],
 ["Test: PDF hợp lệ → 201 `PROCESSING`, có object trong MinIO, có job QUEUED", "Test: gửi lại cùng `client_file_id` → 200 cùng `id`, không thêm job/chỗ đặt", "Test: `.docx` → 422 `not_pdf`, không có object, `remaining_slots` giảm 1", "Test: lô hết hạn → 404 `batch_expired`; hết chỗ → 409 `batch_full`", "Test: MinIO tắt → 503 `storage_unavailable`, không có document"],
 ["make test-int -k accept_file"])

task("T02-05", "VS-2", "API danh sách tài liệu", "S", "Ready", ["T02-04"],
 ["openapi.yaml `GET /documents`, `DocumentList`", "DATABASE_DESIGN A.5 (`vw_document_list`)"],
 "Trả tài liệu chưa xóa của workspace, mới nhất trước, kèm hạn mức.",
 ["`backend/app/api/v1/documents.py` (GET list)", "`backend/tests/integration/test_list_documents.py`"],
 ["Đọc `vw_document_list` trong `workspace_scope`, sắp `uploaded_at DESC`; `retryable` từ view.", "Không trả `storage_key`, `sha256`, `workspace_id`, `batch_id`."],
 ["Test: 3 trạng thái hiện đúng; tài liệu đã xóa không hiện", "Test: phản hồi không chứa trường cấm (kiểm tra khóa JSON)", "Test: user P2 không thấy tài liệu P1"],
 ["make test-int -k list_documents"])

task("T02-06", "VS-2", "SPA: vùng tải lên một file và danh sách tài liệu", "M", "Ready", ["T01-05", "T02-05"],
 ["html_design S01, S02, S03", "API_DESIGN CA-01 (phần 1 file), 3.7.1, 3.7.3", "USER_STORIES US-001, US-006 AC"],
 "Kéo thả/chọn 1 PDF, thấy tiến độ, thấy dòng tài liệu với trạng thái.",
 ["`frontend/src/features/documents/{UploadDropzone,DocumentList,DocumentRow,QuotaBadge}.tsx`", "`frontend/src/features/documents/useUploadQueue.ts` (bản 1 file)", "`frontend/src/shared/api/upload.ts` (XHR có `onprogress`)", "`frontend/e2e/upload-single.spec.ts`"],
 ["Tạo lô 1 file → PUT với `client_file_id = crypto.randomUUID()` → invalidate `['documents']`, `['me']`.", "DocumentRow: biểu tượng + chữ trạng thái, meta (trang · dung lượng · thời gian `vi-VN`), nút xóa (chưa hoạt động – VS-7).",
  "Trạng thái trống E-01 như S01."],
 ["E2E: chọn 1 PDF → thanh tiến độ xuất hiện ≤ 300 ms → dòng 'Đang xử lý'", "Unit test DocumentRow cho 3 trạng thái (snapshot + có chữ trạng thái)", "axe-core không có lỗi serious"],
 ["pnpm -C frontend test && make e2e -- upload-single.spec.ts"])

# ---------------- VS-3
task("T03-01", "VS-3", "Hàng đợi job và vòng lặp worker (ALG-11)", "M", "Ready", ["T00-05"],
 ["BLUEPRINT ALG-11, 3.7.1, DE-16", "SAD ADR-006, 3.2 (tác vụ)", "schema.sql `job`"],
 "Worker lấy job an toàn khi nhiều bản chạy song song, có heartbeat, thử lại với backoff.",
 ["`backend/app/infra/jobs.py` (`enqueue`, `claim`, `heartbeat`, `complete`, `retry`, `fail`, `cancel`)", "`backend/worker/main.py` (vòng lặp, `INGEST_CONCURRENCY`, `LISTEN job_enqueued` chờ 5 s, tắt gọn)", "`backend/tests/integration/test_jobs.py`"],
 ["SQL claim đúng ALG-11; heartbeat gia hạn `locked_until` mỗi 2 phút.", "`retry(job, backoff)` đặt `QUEUED`, `run_after`; quá `INGEST_MAX_ATTEMPTS` → `fail`.", "Handler đăng ký theo `job.kind`; nối trace bằng `trace_parent`."],
 ["Test: 2 worker cùng lúc với 10 job → mỗi job chạy đúng 1 lần", "Test: worker chết (không heartbeat) → job được claim lại sau `locked_until`, `attempts` tăng", "Test: retry đặt `run_after` đúng backoff 30 s/120 s", "Test: SIGTERM → job đang chạy được trả về QUEUED"],
 ["make test-int -k jobs"])

task("T03-02", "VS-3", "Trích văn bản và phân loại lỗi (ALG-03 extract)", "M", "Ready", ["T02-02"],
 ["BLUEPRINT ALG-03 (extract, normalize)", "PRD 3.3 (mã lý do R-01…R-04)", "SAD 4.1 bước 2–4"],
 "Trích văn bản theo trang trong sandbox, chuẩn hóa Unicode, phân loại R-01/R-02/R-03.",
 ["`backend/app/modules/ingestion/{extractor.py,normalize.py,domain.py}`", "`backend/tests/fixtures/pdf/` (thêm: PDF scan chỉ có ảnh, PDF tiếng Việt có dấu, PDF 2 cột)", "`backend/tests/unit/test_extractor.py`"],
 ["`extract(path) -> list[PageText] | FailureCode` theo ALG-03; số trang từ 1.", "`normalize`: NFC, nối từ gạch nối cuối dòng, gộp khoảng trắng.", "R-03 khi tổng ký tự < `MIN_CHARS_PER_PAGE × số trang`."],
 ["PDF tiếng Việt: văn bản sau normalize ở dạng NFC và chứa đúng câu mẫu", "PDF scan → R-03; PDF hỏng → R-01; mật khẩu → R-02", "Số trang trả về đúng thứ tự 1..n", "Timeout sandbox → ném lỗi tạm thời (không phải FailureCode)"],
 ["make test-unit -k extractor"])

task("T03-03", "VS-3", "Chia đoạn trong trang (ALG-03 chunk)", "M", "Ready", ["T03-02"],
 ["BLUEPRINT ALG-03 (chunk)", "SAD ADR-008", "DATABASE_DESIGN B.2"],
 "Chia văn bản thành đoạn 500–800 token, chồng lấn 80 token, không bao giờ vượt ranh giới trang.",
 ["`backend/app/modules/ingestion/chunker.py`", "`backend/app/modules/ingestion/tokenizer.py` (tokenizer bge-m3 qua `tokenizers`, tải sẵn trong image)", "`backend/tests/unit/test_chunker.py` (có property test bằng hypothesis)"],
 ["Thuật toán đúng ALG-03; câu > max bị cắt cứng theo token.", "`chunk_index` liên tục toàn tài liệu."],
 ["Property test: mọi đoạn có đúng 1 `page_number`; `token_count ≤ CHUNK_MAX_TOKENS`; ghép các đoạn (bỏ phần chồng lấn) phủ toàn bộ văn bản trang", "Trang rỗng không sinh đoạn", "Hiệu năng: 300 trang ~ 600 đoạn trong < 5 s"],
 ["make test-unit -k chunker"])

task("T03-04", "VS-3", "Embedding service và EmbeddingPort", "M", "Ready (giả định)", ["T00-01"],
 ["BLUEPRINT 3.6.5 (`POST /embed`), DE-14", "SAD ADR-007", "DATABASE_DESIGN B.2, B.7"],
 "Service tạo vector `bge-m3` 1024 chiều và adapter gọi nó; adapter giả xác định cho test.",
 ["`embedding-service/app.py` (FastAPI, nạp mô hình khi khởi động, token `EMBEDDING_TOKEN`)", "`embedding-service/Dockerfile` (tải mô hình lúc build)", "`backend/app/ports/embedding.py`", "`backend/app/adapters/{embedding_http.py,embedding_fake.py}`", "`deploy/docker-compose.dev.yml` (service `embedding`, tùy chọn profile `full`)"],
 ["`/embed`: 1–32 văn bản, trả vector chuẩn hóa L2; 413 khi > 32; `/healthz`.", "Adapter HTTP: timeout 30 s (passage) / 2 s (query), thử lại lỗi 5xx.",
  "Fake: vector từ hash nội dung (xác định, chuẩn hóa) để test truy xuất không cần mô hình.", "`EMBEDDING_MODEL_ID=bge-m3@v1`."],
 ["Test service (đánh dấu `slow`, chạy trên CI hằng đêm): 2 câu đồng nghĩa có cosine > 2 câu không liên quan", "Unit test adapter fake: cùng input → cùng vector, chuẩn L2 = 1", "Thiếu/sai token → 401"],
 ["make test-unit -k embedding", "docker compose --profile full up embedding && curl -X POST …/embed"],
 ["Đo thông lượng là việc của SPIKE-02 (TS-02)"])

task("T03-05", "VS-3", "Pipeline ingest và ghi chỉ mục (ALG-04)", "M", "Ready", ["T03-01", "T03-03", "T03-04", "T02-01"],
 ["BLUEPRINT ALG-04, 3.4.3", "DATABASE_DESIGN A.7 (trigger bất biến)"],
 "Job `ingest_document` biến tài liệu PROCESSING thành READY (có đoạn + vector) hoặc FAILED với mã lý do.",
 ["`backend/app/modules/ingestion/pipeline.py`", "`backend/worker/handlers/ingest.py`", "`backend/tests/integration/test_ingest.py`"],
 ["Đúng ALG-04: scope workspace, tải file, extract, chunk, embed theo lô 32, transaction cuối khóa hàng + kiểm tra `deleted_at`, `COPY` đoạn, READY, `pg_notify('document_status')`.",
  "Lỗi phân loại → `mark_failed(R-0x)`; lỗi tạm thời → retry; hết lượt → R-04."],
 ["Test (fake embedding): PDF mẫu → READY, số đoạn > 0, mọi đoạn có `embedding_model='bge-m3@v1'`", "PDF scan → FAILED R-03, không có đoạn", "Embedding lỗi 3 lần → FAILED R-04", "Chạy lại job đã READY một phần (giả lập worker chết trước COMMIT) → kết quả giống chạy 1 lần", "Có thông báo NOTIFY khi đổi trạng thái"],
 ["make test-int -k ingest"])

task("T03-06", "VS-3", "SSE: phát trạng thái tài liệu tới giao diện", "M", "Ready", ["T03-05", "T02-06"],
 ["BLUEPRINT 3.4.2, DD-12", "openapi.yaml `/events`", "API_DESIGN CA-03", "html_design S03 (toast)"],
 "Giao diện tự cập nhật trạng thái tài liệu và hiện thông báo khi Sẵn sàng/Thất bại.",
 ["`backend/app/modules/events/{bus.py,sse.py}`", "`backend/app/api/v1/events.py`", "`frontend/src/shared/sse/useSse.ts`", "`frontend/src/shared/ui/Toast.tsx`", "`backend/tests/integration/test_sse.py`", "`frontend/e2e/processing.spec.ts`"],
 ["EventBus: 1 kết nối `LISTEN document_status` mỗi bản API; map `ws → set[Queue]`; queue đầy 100 → đóng kết nối.", "`/events`: `retry: 5000`, `: ping` mỗi 25 s, sự kiện `document.status_changed`, `quota.changed`.",
  "SPA: `onopen` → invalidate documents; sự kiện → cập nhật cache + toast tự ẩn 5 s, vùng `aria-live`."],
 ["Test: NOTIFY cho ws A chỉ tới client của ws A", "Test: ping xuất hiện trong 26 s", "E2E: tải PDF → dòng tự chuyển 'Sẵn sàng' không tải lại trang, toast hiện rồi tự ẩn", "E2E: PDF scan → 'Thất bại' + lý do R-03 như S03"],
 ["make test-int -k sse && make e2e -- processing.spec.ts"])

# ---------------- VS-4
task("T04-01", "VS-4", "Truy xuất kết hợp và cổng ngưỡng (ALG-05)", "M", "Ready", ["T03-05"],
 ["BLUEPRINT ALG-05", "DATABASE_DESIGN B.4, B.5", "SAD ADR-009"],
 "Từ câu hỏi trả top-8 đoạn trong workspace (vector + full-text, RRF) và cờ `below_gate`.",
 ["`backend/app/modules/retrieval/{service.py,hybrid_sql.py,domain.py}`", "`backend/tests/integration/test_retrieval.py`"],
 ["Câu SQL đúng ALG-05 (lọc `workspace_id`, `embedding_model`), `SET LOCAL hnsw.ef_search`, `hnsw.iterative_scan`.", "Embed câu hỏi (timeout 2 s); trả `RetrievalResult`."],
 ["Test (fake embedding, nội dung có từ khóa): câu hỏi chứa mã hợp đồng tìm đúng đoạn qua nhánh full-text", "Test: không bao giờ trả đoạn của workspace khác (2 workspace có cùng nội dung)", "Test: không có đoạn liên quan → `below_gate=True`", "`EXPLAIN` trên 10.000 đoạn giả dùng `idx_chunk_embedding_hnsw` và `idx_chunk_tsv_gin` (ghi plan vào PR)"],
 ["make test-int -k retrieval"])

task("T04-02", "VS-4", "LlmPort, adapter giả và adapter nhà cung cấp", "M", "Ready (giả định)", ["T00-04"],
 ["BLUEPRINT 3.2.2 (`LlmPort`), DE-13, DD-07", "SAD ADR-007, 6.2", "PRD NFR-011"],
 "Gọi LLM qua interface trả JSON đúng schema; mặc định dùng adapter giả để phát triển và test.",
 ["`backend/app/ports/llm.py` (lỗi chuẩn hóa)", "`backend/app/adapters/llm_fake.py` (kịch bản: answered/insufficient/invalid/timeout/5xx)", "`backend/app/adapters/llm_anthropic.py` (`LLM_MODEL=claude-sonnet-5-5`, structured output theo schema `LlmAnswer`)", "`backend/tests/unit/test_llm_contract.py`"],
 ["`complete_json(system, user, schema, max_output_tokens, timeout_s)`; ánh xạ 429/5xx/timeout/JSON sai sang lỗi chuẩn.", "Adapter thật chỉ bật khi có `LLM_API_KEY`; không ghi prompt/phản hồi vào log.",
  "Contract test: payload gửi đi chỉ chứa prompt hệ thống, câu hỏi và nội dung đoạn có nhãn S1…S8 – không có `document_id`, tên file, số trang, email."],
 ["Unit test adapter giả cho 5 kịch bản", "Contract test NFR-011 xanh cho cả 2 adapter (adapter thật dùng HTTP mock)", "Adapter thật chạy được với key thử nghiệm (thủ công, ghi kết quả vào PR) – bỏ qua nếu chưa có quyền (OQ-005)"],
 ["make test-unit -k llm"],
 ["Chọn nhà cung cấp chính thức chờ OQ-005 – chỉ thêm adapter khác nếu được yêu cầu"])

task("T04-03", "VS-4", "Sinh câu trả lời và kiểm tra trích dẫn (ALG-06)", "M", "Ready", ["T04-01", "T04-02"],
 ["BLUEPRINT ALG-06, DD-11", "SAD ADR-010, 4.3, 7.4", "USER_STORIES US-013, US-016, US-020 AC"],
 "Dựng prompt, gọi LLM trong ngân sách thời gian, chỉ chấp nhận trích dẫn hợp lệ, đánh số [n].",
 ["`backend/app/modules/qa/{prompt.py,answerer.py,validator.py}`", "`backend/tests/unit/test_answerer.py`"],
 ["`PROMPT_SYSTEM` phiên bản 1 (đúng nội dung ALG-06), hằng `PROMPT_VERSION`.", "Kiểm tra: mã S# hợp lệ, xóa mã lạ, không còn trích dẫn → INSUFFICIENT, đổi S# → [n] theo thứ tự xuất hiện.",
  "Ngân sách: timeout lần đầu `LLM_TIMEOUT_S`; thử lại chỉ khi lỗi trong `LLM_RETRY_WINDOW_S` và còn ≥ 2 s; sửa JSON 1 lần nếu còn ngân sách."],
 ["Test: LLM trích S9 (không tồn tại) → bị loại; chỉ còn mã lạ → INSUFFICIENT", "Test: `[S3] … [S1]` → `[1] … [2]` và citations đúng thứ tự", "Test (đồng hồ giả): lỗi 429 ở 1 s → thử lại với timeout = 15 − 1 − 1,5; lỗi ở 4 s → không thử lại", "Test: đường xấu nhất ≤ 15 s"],
 ["make test-unit -k answerer"])

task("T04-04", "VS-4", "Hội thoại và API đặt câu hỏi (ALG-08 cơ bản)", "M", "Ready", ["T04-03", "T01-04"],
 ["BLUEPRINT ALG-08", "openapi.yaml `/conversations/current`, `POST /conversations/{id}/messages`, `Answer`", "schema.sql `conversation`, `message`, `citation`"],
 "Người dùng đặt câu hỏi, nhận `Answer`; hội thoại giữ khi tải lại trang.",
 ["`backend/app/modules/qa/{service.py,repository.py}`", "`backend/app/api/v1/conversations.py`", "`backend/tests/integration/test_ask.py`"],
 ["`GET /conversations/current` tạo nếu chưa có cho phiên.", "`POST …/messages`: kiểm tra hội thoại thuộc phiên; 409 `no_ready_documents`; INSERT … ON CONFLICT; commit trước khi gọi LLM (DD-06); lưu answer + citations (bản chụp tên tài liệu).",
  "Gửi lại cùng `client_request_id` sau ANSWERED/INSUFFICIENT → trả kết quả cũ, không gọi LLM.", "Audit `question_asked`."],
 ["Test (LLM giả): câu trả lời có citations khớp tài liệu/trang", "Test: không có tài liệu Sẵn sàng → 409", "Test: gửi lại cùng id → LLM giả chỉ được gọi 1 lần", "Test: hội thoại của phiên khác → 404", "Test: tải lại `/conversations/current` trả đủ tin nhắn"],
 ["make test-int -k ask"])

task("T04-05", "VS-4", "SPA: khung chat, câu trả lời và nhãn nguồn", "M", "Ready", ["T04-04", "T03-06"],
 ["html_design S04", "API_DESIGN CA-02 (phần cơ bản), CA-04, 3.7.2", "BLUEPRINT DE-02"],
 "Ô hỏi, danh sách tin nhắn, câu trả lời có [n] bấm được và nhãn 'tên file · tr.X'.",
 ["`frontend/src/features/chat/{Composer,MessageList,MessageItem,CitationChip,AnswerText}.tsx`", "`frontend/src/features/chat/useAsk.ts`", "`frontend/e2e/ask.spec.ts`"],
 ["Composer: khóa khi không có tài liệu Sẵn sàng (lý do bằng chữ), bộ đếm 2.000, Enter gửi, Shift+Enter xuống dòng, giữ nháp.", "AnswerText tách `[n]` bằng regex, không bao giờ dựng HTML từ câu trả lời.",
  "Trạng thái 'Đang soạn câu trả lời' ≤ 300 ms; tự cuộn xuống tin mới; vùng `aria-live`."],
 ["Unit test AnswerText: `[1]` có citation → nút; `[9]` không có → văn bản; chuỗi `<script>` hiển thị nguyên văn", "E2E (LLM giả): hỏi → câu trả lời + 2 nhãn nguồn; tải lại trang → hội thoại còn", "axe-core không có lỗi serious"],
 ["pnpm -C frontend test && make e2e -- ask.spec.ts"])

task("T04-06", "VS-4", "Demo lát 1: E2E luồng xuyên suốt", "S", "Ready", ["T04-05", "T01-05"],
 ["USER_STORIES mục 3 (lát 1)", "PRD 2.2 (hành trình)"],
 "Một test E2E chứng minh luồng Đăng nhập → Tải PDF → Sẵn sàng → Hỏi → Trả lời có nguồn chạy được trên docker-compose.",
 ["`frontend/e2e/slice1-journey.spec.ts`", "`docs/demo/slice1.md` (kịch bản demo, ảnh chụp)"],
 ["Chạy toàn bộ stack (embedding thật nếu máy đủ, LLM giả hoặc thật nếu có key).", "Ghi thời gian từng bước."],
 ["E2E xanh trên CI với LLM giả + embedding giả", "Chạy thủ công 1 lần với embedding thật, ghi kết quả vào `docs/demo/slice1.md`", "PO xem demo (ghi ngày vào file)"],
 ["make e2e -- slice1-journey.spec.ts"])

# ---------------- SPIKES
task("TS-01", "SPIKE", "SPIKE-01: chất lượng và độ trễ RAG với LLM ứng viên", "M", "Blocked", ["T04-04", "T06-03"],
 ["SAD 12 (SPIKE-01, TR-01, TR-04)", "PRD NFR-001, NFR-003…005"],
 "Đo MET-002/004/005 và p90 độ trễ trên bộ câu hỏi thật với LLM ứng viên để quyết định ADR-007.",
 ["`eval/reports/spike-01.md`"],
 ["Nạp bộ PDF mẫu (DEP-003), chạy bộ câu hỏi (DEP-005) qua bộ đánh giá T06-03.", "Load 20 người dùng đồng thời (k6 script của T10-06 bản rút gọn).", "So sánh top-k 6/8, ef_search 80/120."],
 ["Báo cáo có bảng MET-002, MET-004, MET-005, NFR-018, p50/p90 và đề xuất giữ/đổi ADR-007, ADR-009"],
 ["python -m eval.run --suite dep005 --out eval/reports/spike-01.json"],
 ["**Chặn bởi:** DEP-003, DEP-005 (bộ PDF, bộ câu hỏi), OQ-005 (quyền dùng LLM)"])

task("TS-02", "SPIKE", "SPIKE-02: thông lượng embedding", "S", "Ready", ["T03-04", "T03-03"],
 ["SAD 12 (SPIKE-02, TR-02), 9.2", "PRD NFR-002"],
 "Xác định CPU 4 vCPU có xử lý file 300 trang ≤ 3 phút không, hay cần GPU.",
 ["`eval/reports/spike-02.md`", "`eval/bench_embedding.py`"],
 ["Đo đoạn/giây với lô 8/16/32 trên 4 vCPU; ước tính file 300 trang (~600 đoạn).", "Nếu có GPU: đo lại."],
 ["Báo cáo có số liệu và khuyến nghị cấu hình (CPU/GPU, số bản) cập nhật SAD 9.2"],
 ["python eval/bench_embedding.py --texts 600 --batch 32"])

task("TS-03", "SPIKE", "SPIKE-03: chất lượng trích văn bản và số trang", "S", "Blocked", ["T03-02"],
 ["SAD 12 (SPIKE-03, TR-03), ADR-015", "PRD NFR-018"],
 "Kiểm tra `pypdf` trên PDF thật: thứ tự chữ, bảng, nhiều cột, số trang, ngưỡng R-03.",
 ["`eval/reports/spike-03.md`"],
 ["Chạy extractor trên DEP-003, chấm tay 30 trang ngẫu nhiên.", "Hiệu chỉnh `MIN_CHARS_PER_PAGE`."],
 ["Báo cáo tỷ lệ trang trích đúng, đề xuất giữ `pypdf` hay mua PyMuPDF"],
 ["python -m eval.extract_report --dir data/dep003"],
 ["**Chặn bởi:** DEP-003 (bộ PDF mẫu được phép dùng)"])

task("TS-04", "SPIKE", "SPIKE-04: hiệu chỉnh ngưỡng τ và top-k", "S", "Blocked", ["T04-01", "T06-03"],
 ["SAD 12 (SPIKE-04)", "DATABASE_DESIGN B.6 (đo recall)"],
 "Chọn `RETRIEVAL_MIN_SIMILARITY` và `RETRIEVAL_TOP_K` tối đa MET-005 mà MET-002 ≥ 80%; đo recall@30 HNSW.",
 ["`eval/reports/spike-04.md`"],
 ["Quét τ 0,30…0,60 bước 0,05; top-k 6/8/10.", "Đo recall@30 theo B.6."],
 ["Bảng kết quả và giá trị đề xuất cập nhật `.env.example` + BLUEPRINT 3.6.6"],
 ["python -m eval.sweep --param tau --from 0.30 --to 0.60 --step 0.05"],
 ["**Chặn bởi:** DEP-005"])

# ---------------- VS-5
task("T05-01", "VS-5", "Hoàn thiện các đường từ chối file và lô", "S", "Ready", ["T02-04"],
 ["USER_STORIES US-002, US-003, US-004 AC, I-01", "PRD E-07, E-08", "openapi.yaml (413/422/404/409)"],
 "Mọi đường lỗi tải lên trả đúng mã, đúng thông điệp, không để rác.",
 ["`backend/tests/integration/test_upload_rejections.py`", "`deploy/nginx/api.conf` (`client_max_body_size MAX_FILE_MB+1m`)"],
 ["Bảng test cho: không phải PDF, đuôi .pdf giả, quá dung lượng (dừng sớm khi stream), > 300 trang, mật khẩu, lô hết hạn, hết chỗ, vượt hạn mức.", "Proxy trả 413 dạng Problem (`too_large`)."],
 ["Mọi dòng trong bảng test xanh; sau mỗi lỗi: không có object mồ côi, không có document, `remaining_slots` đúng", "Upload 25 MB bị dừng trước khi đọc hết body (đo byte đã đọc)"],
 ["make test-int -k upload_rejections"])

task("T05-02", "VS-5", "Giới hạn tần suất (ALG-09) cho tải file", "S", "Ready", ["T02-04"],
 ["BLUEPRINT ALG-09, DD-04", "API_DESIGN 2.6 (RateLimit headers)"],
 "Bộ đếm cửa sổ cố định trong PostgreSQL, header `RateLimit-*`, 429 + `Retry-After`.",
 ["`backend/app/infra/ratelimit.py`", "`backend/tests/integration/test_ratelimit.py`"],
 ["Dependency `rate_limit(bucket, limit, window)`; dùng cho `PUT …/files` (30/giờ) – bucket `question` gắn ở T09-02.", "Header `RateLimit-Limit/Remaining/Reset` trên phản hồi thành công."],
 ["Test: file thứ 31 trong giờ → 429 `rate_limited`, `Retry-After` đúng", "Test: 2 bản API (2 engine) dùng chung bộ đếm", "Test: cửa sổ mới → đếm lại từ 1"],
 ["make test-int -k ratelimit"])

task("T05-03", "VS-5", "SPA: tải nhiều file đầy đủ (CA-01) và thông báo giới hạn", "M", "Ready", ["T02-06", "T05-01"],
 ["API_DESIGN CA-01, 3.7.1", "html_design S02, S08", "USER_STORIES US-002 AC 2–3"],
 "Kiểm tra trước bằng `/me.limits`, tải song song 3, thử lại an toàn, tạo lô mới khi lô hết hạn.",
 ["`frontend/src/features/documents/useUploadQueue.ts` (bản đầy đủ)", "`frontend/src/features/documents/UploadItem.tsx`", "`frontend/e2e/upload-multi.spec.ts`"],
 ["Đúng CA-01: file sai đuôi/quá dung lượng bị chặn ở client; > max file → báo, không tải file nào; pool 3; `Tải lại` dùng lại `client_file_id`; `batch_expired`/`batch_full` → lô mới 1 lần; `server_busy` → chờ `Retry-After` tối đa 2 lần.", "Cảnh báo hạn mức khi còn ≤ 5 chỗ (S08)."],
 ["E2E: 12 file → thông báo, 0 request PUT", "E2E: 5 file trong đó 1 `.docx` → 4 nhận, 1 báo lỗi trên dòng", "E2E: cắt mạng giữa PUT (Playwright `route.abort`) → 'Tải lại' → 1 tài liệu, không trùng", "Tối đa 3 PUT đồng thời (đếm trong test)"],
 ["make e2e -- upload-multi.spec.ts"])

# ---------------- VS-6
task("T06-01", "VS-6", "Đường 'Chưa đủ thông tin' đầy đủ", "S", "Ready", ["T04-04", "T04-05"],
 ["USER_STORIES US-016 AC", "BLUEPRINT ALG-05 (cổng), ALG-06", "html_design S04 (thẻ Chưa đủ thông tin)", "PRD E-11, E-16"],
 "Ba lớp phát hiện thiếu căn cứ hoạt động và hiển thị đúng thiết kế.",
 ["`backend/tests/integration/test_insufficient.py`", "`frontend/src/features/chat/InsufficientAnswer.tsx`"],
 ["Test 3 đường: dưới ngưỡng (LLM không được gọi), LLM trả `insufficient`, LLM trả answered nhưng không có trích dẫn hợp lệ.", "Giao diện: nhãn 'Chưa đủ thông tin', viền nét đứt, không có phần nguồn, gợi ý hành động."],
 ["3 test backend xanh; đường dưới ngưỡng xác nhận 0 lần gọi LLM", "Unit test component + axe", "Câu chào hỏi ('xin chào') → INSUFFICIENT (E-16) với LLM giả kịch bản tương ứng"],
 ["make test-int -k insufficient && pnpm -C frontend test"])

task("T06-02", "VS-6", "Tổng hợp nhiều tài liệu và số trang", "S", "Ready", ["T04-04"],
 ["USER_STORIES US-017, US-021 AC", "BLUEPRINT ALG-06, DD-11", "DATABASE_DESIGN `citation`"],
 "Câu trả lời trích nhiều tài liệu; số trang đúng hoặc null, không bao giờ đoán.",
 ["`backend/tests/integration/test_multi_doc.py`", "`frontend/src/features/chat/CitationChip.tsx` (trường hợp không có trang)"],
 ["Fixture 2 PDF có thông tin bổ sung nhau; LLM giả trích cả hai.", "Đoạn có `page_number` → chip 'tr.X'; trích dẫn không có trang → chỉ tên file."],
 ["Test: citations chứa 2 `document_id` khác nhau, đúng trang của đoạn đã truy xuất", "Test: tài liệu bị đổi tên/xóa sau khi trả lời → `document_name_snapshot` giữ tên cũ", "Unit test chip không trang"],
 ["make test-int -k multi_doc"])

task("T06-03", "VS-6", "Bộ đánh giá RAG (DE-22) và định dạng bộ câu hỏi", "M", "Ready", ["T04-04"],
 ["BLUEPRINT DE-22, QA-11", "PRD 5.1 G-02, NFR-003…005, NFR-018", "BRD DEP-005"],
 "Công cụ chạy bộ câu hỏi qua API staging và tính MET-002…005, NFR-018; chạy hằng đêm.",
 ["`eval/` (package riêng: `run.py`, `metrics.py`, `schema.json` cho bộ câu hỏi)", "`eval/datasets/sample.jsonl` (10 câu minh họa trên PDF tự tạo)", "workflow CI hằng đêm"],
 ["Định dạng câu hỏi: `{id, question, type: in_doc|multi_doc|out_of_doc|followup, expected_docs, expected_pages, reference_answer}`.", "Chấm tự động: tài liệu/trang trích dẫn; tỷ lệ INSUFFICIENT với out_of_doc. Chấm 'đúng nội dung' xuất file CSV để người dùng nghiệp vụ chấm (không dùng LLM tự chấm làm số liệu chính thức).",
  "So sánh với lần chạy trước, cảnh báo khi giảm > 3 điểm %."],
 ["Chạy trên `sample.jsonl` sinh báo cáo JSON + Markdown có đủ chỉ số", "README hướng dẫn BA soạn DEP-005 theo schema", "Job hằng đêm chạy được trên staging (hoặc docker-compose)"],
 ["python -m eval.run --suite sample --out eval/reports/sample.json"])

# ---------------- VS-7
task("T07-01", "VS-7", "API xóa tài liệu (ALG-12)", "S", "Ready", ["T03-05", "T02-05"],
 ["BLUEPRINT ALG-12", "openapi.yaml `DELETE /documents/{id}`", "USER_STORIES US-010, US-011 AC"],
 "Xóa mềm + xóa đoạn + hủy job chờ + enqueue purge trong một transaction.",
 ["`backend/app/modules/documents/service.py` (`soft_delete`)", "`backend/app/api/v1/documents.py` (DELETE)", "`backend/tests/integration/test_delete.py`"],
 ["Đúng ALG-12; audit `document_delete`; NOTIFY `quota.changed`."],
 ["Test: sau DELETE, truy xuất không trả đoạn của tài liệu (US-011 AC)", "Test race: ingest đang chạy tới bước 7 thì DELETE → ingest rollback, 0 đoạn, job CANCELLED (QA-14)", "Test: DELETE lần 2 → 404; tài liệu của người khác → 404"],
 ["make test-int -k delete"])

task("T07-02", "VS-7", "Worker purge và lượt quét (ALG-10)", "S", "Ready", ["T07-01", "T03-01"],
 ["BLUEPRINT ALG-10", "DATABASE_DESIGN A.6 (`fn_pending_purges`, `fn_purge_lag_max_seconds`)", "PRD NFR-013"],
 "Xóa thật file gốc ≤ 24 h, dọn object mồ côi, đo độ trễ purge.",
 ["`backend/worker/handlers/purge.py`", "`backend/worker/schedule.py` (lượt quét mỗi giờ)", "`backend/tests/integration/test_purge.py`"],
 ["Đúng ALG-10; metric `purge_lag_seconds`."],
 ["Test: sau purge, object không còn, `purged_at` có giá trị", "Test: tài liệu bị sót job → lượt quét enqueue lại", "Test: object không có document, tuổi > 1 h → bị xóa; tuổi < 1 h → giữ"],
 ["make test-int -k purge"])

task("T07-03", "VS-7", "SPA: hộp xác nhận xóa và nguồn đã xóa", "S", "Ready", ["T07-01", "T04-05"],
 ["html_design S07, S05 (chip '(đã xóa)')", "API_DESIGN 3.7.3", "PRD E-13, E-19"],
 "Xóa có xác nhận, ẩn dòng lạc quan, nhãn nguồn của tài liệu đã xóa hiển thị '(đã xóa)'.",
 ["`frontend/src/features/documents/DeleteDialog.tsx`", "`frontend/e2e/delete.spec.ts`"],
 ["`role=alertdialog`, focus mặc định nút Hủy, Esc đóng, trả focus về nút xóa.", "Lỗi khác 404 → khôi phục dòng + toast lỗi."],
 ["E2E: xóa → dòng biến mất; hỏi lại câu cũ → không trích tài liệu đã xóa", "E2E: chip của câu trả lời cũ hiện '(đã xóa)' và không bấm được", "Kiểm tra bàn phím: Tab vòng trong hộp thoại"],
 ["make e2e -- delete.spec.ts"])

# ---------------- VS-8
task("T08-01", "VS-8", "Bộ test phân quyền và cách ly toàn hệ thống", "M", "Ready", ["T07-01", "T04-04"],
 ["USER_STORIES US-024 AC", "PRD NFR-010, G-04", "BLUEPRINT QA-06", "API_DESIGN AD-11"],
 "Chứng minh không endpoint nào cho phép truy cập dữ liệu của workspace khác.",
 ["`backend/tests/security/test_isolation.py`", "`backend/tests/security/test_rls_direct.py`"],
 ["Sinh tự động danh sách route từ OpenAPI; với mọi route có tham số ID: dùng ID của workspace A khi đăng nhập B → 404, không lộ dữ liệu.", "Test RLS trực tiếp bằng SQL cho cả `app_api` và `app_worker` (không scope → 0 hàng).", "Test view `vw_document_list` không lộ dữ liệu (security_invoker).", "Test analytics: không có khóa nội dung (CHECK)."],
 ["Mọi route trong OpenAPI được phủ (test fail nếu có route mới chưa khai báo)", "0 rò rỉ; mỗi lần bị từ chối có `audit_event access_denied`"],
 ["make test-int -k security"])

task("T08-02", "VS-8", "Cứng hóa bảo mật HTTP và chuỗi cung ứng", "S", "Ready", ["T00-07"],
 ["SAD 8.1", "API_DESIGN 2.6 (CORS tắt, Cache-Control)", "PRD NFR-009"],
 "Header bảo mật, cookie đúng cờ, không CORS, quét phụ thuộc và bí mật.",
 ["`deploy/nginx/*.conf`", "`backend/app/api/middleware.py` (SecurityHeaders)", "`backend/tests/unit/test_security_headers.py`"],
 ["CSP `default-src 'self'; frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, HSTS ở proxy; `Cache-Control: private, no-store` cho API.", "Không trả `Access-Control-*`."],
 ["Test header trên 3 endpoint", "Quét ZAP baseline (docker) không có cảnh báo High", "pip-audit / pnpm audit không có High/Critical"],
 ["make test-unit -k security_headers"])

# ---------------- VS-9
task("T09-01", "VS-9", "Circuit breaker LLM và ánh xạ 503/504 (ALG-07)", "S", "Ready", ["T04-03"],
 ["BLUEPRINT ALG-07, 3.7.5", "SAD 6.2", "PRD E-06"],
 "Khi LLM lỗi liên tục, trả lỗi ngay thay vì chờ; tự phục hồi.",
 ["`backend/app/infra/circuit.py`", "`backend/tests/unit/test_circuit.py`", "`backend/tests/integration/test_ask_failures.py`"],
 ["Đúng ALG-07; `LlmInvalidOutput` không tính; metric `circuit_breaker_state`.", "Message chuyển FAILED với `error_code`; analytics `answer_failed`."],
 ["Test: 5 lỗi trong 60 s → OPEN, request tiếp trả 503 < 100 ms với `Retry-After`", "Test: sau 30 s chỉ 1 request đi qua (HALF_OPEN)", "Test: LLM giả timeout → 504 `ai_timeout`, message FAILED"],
 ["make test-unit -k circuit && make test-int -k ask_failures"])

task("T09-02", "VS-9", "Giới hạn câu hỏi và đếm ngược trên giao diện", "S", "Ready", ["T05-02", "T04-05"],
 ["BLUEPRINT ALG-09", "html_design S05 (cảnh báo đếm ngược)", "API_DESIGN 3.6.3 `rate_limited`"],
 "10 câu hỏi/phút/người; giao diện đếm ngược và tự mở khóa, không mất nội dung ô hỏi.",
 ["`backend/app/api/v1/conversations.py` (gắn `rate_limit('question',…)`)", "`frontend/src/features/chat/RateLimitNotice.tsx`"],
 ["Gắn dependency; SPA đọc `Retry-After`, khóa nút Gửi, đếm ngược, mở khóa."],
 ["Test API: câu thứ 11 → 429", "E2E: câu thứ 11 → thông báo đếm ngược, nội dung ô hỏi còn nguyên, hết giờ tự mở khóa (đồng hồ giả)"],
 ["make test-int -k ratelimit && make e2e -- ratelimit.spec.ts"])

task("T09-03", "VS-9", "SPA: thẻ lỗi câu trả lời, cảnh báo hết phiên", "S", "Ready", ["T09-01", "T03-06", "T01-05"],
 ["html_design S05, S11", "API_DESIGN 3.4.2, 3.4.3, 3.6.3", "USER_STORIES US-026 AC"],
 "Lỗi câu hỏi hiện đúng chỗ, sự kiện `session.expiring` hiện cảnh báo.",
 ["`frontend/src/features/chat/FailedAnswer.tsx`", "`backend/app/modules/events/session_expiry.py` (phát `session.expiring` trước 5 phút)", "`frontend/e2e/errors.spec.ts`"],
 ["Thẻ lỗi: nhãn 'Chưa trả lời được', thông điệp theo mã, câu hỏi gốc vẫn hiện (nút 'Gửi lại' hoạt động ở T11-02).", "Timeout phía client 20 s → coi như lỗi mạng.", "Toast cảnh báo phiên không chặn thao tác."],
 ["E2E: LLM giả 503 → thẻ lỗi đúng S05", "E2E: cắt mạng khi hỏi → thẻ lỗi, không treo spinner", "Test: phiên còn 5 phút → client nhận `session.expiring` đúng 1 lần"],
 ["make e2e -- errors.spec.ts"])

# ---------------- VS-10
task("T10-01", "VS-10", "Nhật ký kiểm toán đầy đủ", "S", "Ready", ["T07-01", "T04-04", "T01-03"],
 ["PRD NFR-012, NFR-023", "schema.sql `audit_event`", "DATABASE_DESIGN A.7"],
 "Mọi hành động trong danh sách `action` được ghi đúng 1 lần, không có nội dung.",
 ["`backend/app/modules/audit/service.py` (bản đầy đủ, gồm `request_id`)", "`backend/tests/integration/test_audit.py`"],
 ["Rà soát mọi điểm gọi; ghi trong cùng transaction với thay đổi nghiệp vụ.", "Kiểm tra `app_readonly_audit` đọc được, `app_api` không UPDATE/DELETE được."],
 ["Test: mỗi hành động trong 9 `action` sinh đúng 1 hàng", "Test: `app_api` UPDATE `audit_event` → permission denied"],
 ["make test-int -k audit"])

task("T10-02", "VS-10", "Sự kiện analytics EVT-01…EVT-11", "S", "Ready", ["T07-01", "T04-04", "T06-01"],
 ["PRD 5.2", "BLUEPRINT 3.5.3", "DATABASE_DESIGN A.5 (view báo cáo)", "API_DESIGN AD-12"],
 "Ghi 11 sự kiện với thuộc tính đúng, `actor_hash`, không có nội dung; view báo cáo chạy được.",
 ["`backend/app/modules/events/analytics.py`", "`backend/tests/integration/test_analytics.py`"],
 ["Whitelist thuộc tính theo bảng 3.5.3; `actor_hash` = HMAC-SHA256(user_id, `ACTOR_HASH_KEY`).", "EVT-09 `citation_clicked` để lại cho T11-04 (endpoint mở file); task này hiện thực 10 sự kiện còn lại."],
 ["Test: 10 sự kiện (trừ EVT-09) có đúng khóa thuộc tính", "Test: thêm khóa `question` → bị chặn ở ứng dụng và ở CHECK CSDL", "Test: `vw_report_daily_questions` trả số liệu đúng với dữ liệu giả"],
 ["make test-int -k analytics"])

task("T10-03", "VS-10", "Giám sát: trace, metric, dashboard, cảnh báo", "M", "Ready", ["T04-04", "T03-05"],
 ["SAD 8.3", "BLUEPRINT QA-13", "DATABASE_DESIGN A.10 (truy vấn giám sát)"],
 "Có đủ metric, trace và cảnh báo ở SAD 8.3 trên môi trường dev/staging.",
 ["`backend/app/infra/telemetry.py` (OpenTelemetry, prometheus-client)", "`deploy/observability/` (otel-collector, prometheus, grafana dashboards JSON, alert rules)", "`deploy/docker-compose.dev.yml` (profile `obs`)"],
 ["Span cho embed, truy xuất, LLM, kiểm tra trích dẫn, các giai đoạn ingest; trace nối API → job qua `trace_parent`.", "Metric đúng tên SAD 8.3; 3 dashboard; 7 cảnh báo."],
 ["Chạy luồng lát 1 → Grafana hiển thị p50/p90 trả lời, độ sâu hàng đợi, lỗi theo mã R", "Trace một câu hỏi thấy đủ span", "Log không chứa trường cấm (test T00-04 vẫn xanh)"],
 ["docker compose --profile obs up && make e2e -- slice1-journey.spec.ts"])

task("T10-04", "VS-10", "Tác vụ bảo trì định kỳ", "S", "Ready", ["T03-01"],
 ["SAD 3.2 (tác vụ), DATABASE_DESIGN A.10 (kế hoạch bảo trì)", "PRD NFR-023, NFR-024"],
 "Hết hạn phiên, phân vùng nhật ký, dọn dữ liệu cũ chạy tự động bằng vai trò `app_maintenance`.",
 ["`backend/worker/maintenance.py`", "`backend/tests/integration/test_maintenance.py`"],
 ["`expire_sessions` (15 phút, xóa lô quá 1 ngày); `ensure_audit_partition` + `drop_audit_partitions_before` (hằng ngày); xóa `analytics_event` > 180 ngày, `rate_limit_counter` > 2 h, `job` xong > 7 ngày.", "Khóa advisory để chỉ 1 worker chạy mỗi tác vụ."],
 ["Test từng tác vụ với dữ liệu quá hạn/chưa quá hạn", "Test: 2 worker cùng chạy → tác vụ chạy 1 lần", "Phiên hết hạn bị xóa kéo theo hội thoại (NFR-024)"],
 ["make test-int -k maintenance"])

task("T10-05", "VS-10", "Đóng gói và cấu hình triển khai staging", "M", "Ready (giả định)", ["T00-07", "T10-03"],
 ["SAD 9.1, 9.2, ADR-013", "DATABASE_DESIGN A.10 (sao lưu, tham số)"],
 "Image production cho api/worker/embedding/web và cấu hình staging chạy được với một lệnh.",
 ["`backend/Dockerfile`, `embedding-service/Dockerfile`, `frontend/Dockerfile` (multi-stage, user không phải root)", "`deploy/staging/` (compose hoặc manifest theo hạ tầng được chọn)", "`docs/runbook.md` (triển khai, rollback, khôi phục CSDL, xoay vòng bí mật)"],
 ["Rolling update, migration chạy trước như job riêng (expand/contract).", "Bí mật từ secret manager/biến môi trường, không nằm trong image.", "Tài nguyên theo SAD 9.2."],
 ["Triển khai staging từ đầu bằng runbook thành công", "Rollback về bản trước trong ≤ 10 phút (diễn tập, ghi lại)", "Quét image (trivy) không có Critical"],
 ["trivy image aichat-api:latest"],
 ["Hạ tầng production cụ thể chờ OQ-005, OQ-203"])

task("T10-06", "VS-10", "Load test và báo cáo launch gate", "M", "Ready", ["T10-05", "T06-03", "T08-01"],
 ["PRD 5.1 (G-01…G-09), NFR-001, NFR-002, NFR-007", "BLUEPRINT QA-01, QA-02"],
 "Đo hiệu năng trên staging và tổng hợp trạng thái mọi điều kiện ra mắt.",
 ["`perf/k6/ask.js`, `perf/k6/upload.js`", "`docs/launch-gate.md`"],
 ["k6: 20 người dùng ảo hỏi liên tục 10 phút; 10 người tải file 20 MB.", "Điền bảng G-01…G-09 với bằng chứng (link báo cáo test, eval, bảo mật)."],
 ["Báo cáo p50/p90 hỏi đáp và thời gian xử lý file lớn nhất", "`docs/launch-gate.md` có trạng thái từng gate và danh sách việc còn thiếu"],
 ["k6 run perf/k6/ask.js"])

# ---------------- VS-11 P1
task("T11-01", "VS-11", "Xử lý lại tài liệu lỗi tạm thời (US-009)", "S", "Ready", ["T03-05", "T02-06"],
 ["USER_STORIES US-009 AC", "openapi.yaml `POST /documents/{id}/reprocess`", "html_design S03"],
 "Tài liệu Thất bại R-04 xử lý lại được; mã khác không có nút.",
 ["`backend/app/api/v1/documents.py` (reprocess)", "`frontend/src/features/documents/DocumentRow.tsx` (nút Xử lý lại)", "`backend/tests/integration/test_reprocess.py`"],
 ["FAILED R-04 → PROCESSING (xóa `failure_code`), enqueue job, audit `document_reprocess`; khác → 409 `not_retryable`."],
 ["Test: R-04 → 202 và job mới; R-03 → 409; gọi 2 lần → lần 2 409", "E2E: nút chỉ hiện với R-04"],
 ["make test-int -k reprocess"])

task("T11-02", "VS-11", "Gửi lại câu hỏi bị lỗi (US-027)", "S", "Ready", ["T09-03", "T04-04"],
 ["USER_STORIES US-027 AC", "BLUEPRINT ALG-08 (FAILED → PENDING), 3.7.2", "API_DESIGN 3.4.2 (409 → thăm dò)"],
 "Bấm 'Gửi lại' chạy lại đúng câu hỏi với cùng `client_request_id`.",
 ["`backend/app/modules/qa/service.py` (nhánh FAILED/PENDING quá hạn, `idempotency_mismatch`)", "`frontend/src/features/chat/useAsk.ts` (retry, polling khi 409)", "`backend/tests/integration/test_resend.py`"],
 ["Đúng ALG-08; analytics `question_retried`.", "SPA: 409 `request_in_progress` → thăm dò `/conversations/current` mỗi 2 s tối đa 20 s."],
 ["Test: FAILED → gửi lại → ANSWERED, `attempt=2`", "Test: cùng id khác nội dung → 422 `idempotency_mismatch`", "E2E: LLM giả lỗi lần 1, thành công lần 2 → thẻ lỗi thành câu trả lời"],
 ["make test-int -k resend"])

task("T11-03", "VS-11", "Nêu mâu thuẫn giữa tài liệu (US-018)", "S", "Ready", ["T06-02"],
 ["USER_STORIES US-018 AC", "BLUEPRINT ALG-06 (`conflict`)", "html_design S04 (khối mâu thuẫn)"],
 "Khi các nguồn khác nhau, câu trả lời liệt kê từng giá trị kèm nguồn.",
 ["`backend/app/modules/qa/prompt.py` (đảm bảo chỉ dẫn mâu thuẫn)", "`frontend/src/features/chat/ConflictNotice.tsx`", "`eval/datasets/sample.jsonl` (thêm cặp mâu thuẫn)"],
 ["Truyền `conflict` từ `LlmAnswer` ra `Answer` (thêm trường tùy chọn `conflict: boolean` vào openapi.yaml – thay đổi không phá vỡ).", "Giao diện hiển thị khối cảnh báo như S04."],
 ["Cập nhật openapi.yaml + kiểm tra hợp đồng xanh", "Test với LLM giả `conflict=true` → khối hiển thị", "Bộ đánh giá có ≥ 2 câu mâu thuẫn"],
 ["make test-int -k conflict"])

task("T11-04", "VS-11", "Trình xem PDF tại trang (US-022)", "M", "Blocked", ["T04-05"],
 ["USER_STORIES US-022 AC", "openapi.yaml `GET /documents/{id}/file`", "html_design S06", "API_DESIGN AD-12"],
 "Bấm nhãn nguồn mở PDF gốc đúng trang trong lớp phủ.",
 ["`backend/app/api/v1/documents.py` (file stream, 410, EVT-09)", "`frontend/src/features/viewer/PdfViewerOverlay.tsx` (pdf.js tải lười)"],
 ["Stream qua API (`Cache-Control: private, no-store`, `Content-Disposition` inline).", "Overlay `aria-modal`, Esc đóng, trả focus; mở trang X hoặc trang 1."],
 ["E2E: bấm [1] → mở đúng trang", "Tài liệu đã xóa → thông báo 'Tài liệu đã bị xóa'", "Bundle chính không tăng (pdf.js ở chunk riêng)"],
 ["make e2e -- viewer.spec.ts"],
 ["**Chặn bởi:** OQ-014 (mở trong ứng dụng hay không)"])

task("T11-05", "VS-11", "Câu hỏi tiếp nối hiểu ngữ cảnh (US-015)", "M", "Blocked", ["T04-04", "T06-03"],
 ["USER_STORIES US-015 AC", "BLUEPRINT ALG-06 (câu hỏi tiếp nối, `FEATURE_FOLLOWUP`)"],
 "Viết lại câu hỏi tiếp nối thành câu độc lập trước khi truy xuất.",
 ["`backend/app/modules/qa/rewriter.py`", "`eval/datasets/sample.jsonl` (10 cặp followup)"],
 ["Gọi LLM (100 token, 2 s) với 3 lượt gần nhất; tính vào ngân sách 15 s; bật bằng cờ."],
 ["≥ 8/10 cặp đúng ngữ cảnh trên bộ đánh giá", "Tắt cờ → hành vi như cũ"],
 ["python -m eval.run --suite followup"],
 ["**Chặn bởi:** OQ-012"])

# ----------------------------------------------------------------------------- helpers
def slug(s):
    s = s.lower()
    rep = {"à":"a","á":"a","ạ":"a","ả":"a","ã":"a","â":"a","ầ":"a","ấ":"a","ậ":"a","ẩ":"a","ẫ":"a","ă":"a","ằ":"a","ắ":"a","ặ":"a","ẳ":"a","ẵ":"a",
           "è":"e","é":"e","ẹ":"e","ẻ":"e","ẽ":"e","ê":"e","ề":"e","ế":"e","ệ":"e","ể":"e","ễ":"e","ì":"i","í":"i","ị":"i","ỉ":"i","ĩ":"i",
           "ò":"o","ó":"o","ọ":"o","ỏ":"o","õ":"o","ô":"o","ồ":"o","ố":"o","ộ":"o","ổ":"o","ỗ":"o","ơ":"o","ờ":"o","ớ":"o","ợ":"o","ở":"o","ỡ":"o",
           "ù":"u","ú":"u","ụ":"u","ủ":"u","ũ":"u","ư":"u","ừ":"u","ứ":"u","ự":"u","ử":"u","ữ":"u","ỳ":"y","ý":"y","ỵ":"y","ỷ":"y","ỹ":"y","đ":"d"}
    s = "".join(rep.get(c, c) for c in s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:48].rstrip("-")

FILES = {t["id"]: f"{t['id']}_{slug(t['title'])}.md" for t in T}
STORY_RE = re.compile(r"US-\d{3}|US-C0\d|NFR-\d{3}")
SIZE_TXT = {"S": "S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp", "M": "M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp"}

STORIES = {
 "T01-01": ["US-023"], "T01-02": ["US-023"], "T01-03": ["US-023", "US-C01", "US-C03"], "T01-04": ["US-023"], "T01-05": ["US-023", "US-C03"],
 "T02-01": ["US-001"], "T02-02": ["US-003", "US-004"], "T02-03": ["US-002"], "T02-04": ["US-001"], "T02-05": ["US-006"], "T02-06": ["US-001", "US-006"],
 "T03-01": ["US-005"], "T03-02": ["US-008"], "T03-03": ["US-005", "US-021"], "T03-04": ["US-005"], "T03-05": ["US-005", "US-008"], "T03-06": ["US-007", "US-025"],
 "T04-01": ["US-013", "US-017"], "T04-02": ["US-012"], "T04-03": ["US-013", "US-016", "US-020"], "T04-04": ["US-012", "US-014"],
 "T04-05": ["US-012", "US-014", "US-020", "US-025"], "T04-06": ["US-001", "US-005", "US-006", "US-012", "US-013", "US-020", "US-023"],
 "T05-01": ["US-002", "US-003", "US-004"], "T05-02": ["US-002"], "T05-03": ["US-002", "US-003", "US-004", "US-026"],
 "T06-01": ["US-016"], "T06-02": ["US-017", "US-021"], "T06-03": ["US-013", "US-016", "US-017", "US-021"],
 "T07-01": ["US-010", "US-011"], "T07-02": ["US-011"], "T07-03": ["US-010", "US-011"],
 "T08-01": ["US-024"], "T08-02": ["US-024"],
 "T09-01": ["US-026"], "T09-02": ["US-026"], "T09-03": ["US-025", "US-026"],
 "T10-01": ["US-C02"],
 "T11-01": ["US-009"], "T11-02": ["US-027"], "T11-03": ["US-018"], "T11-04": ["US-022"], "T11-05": ["US-015"],
 "TS-01": ["US-013", "US-016"], "TS-02": ["US-005"], "TS-03": ["US-021"], "TS-04": ["US-016"],
}

def task_md(t):
    sl = next(s for s in SLICES if s[0] == t["sl"])
    deps = ", ".join(f"[{d}]({FILES[d]})" for d in t["deps"]) or "–"
    blockers = [o for o in t["out"] if o.startswith("**Chặn bởi:**")]
    out = [o for o in t["out"] if not o.startswith("**Chặn bởi:**")]
    L = [f"# {t['id']} – {t['title']}", "",
         "| Trường | Giá trị |", "|---|---|",
         f"| Lát | {sl[0]} – {sl[1]} ({sl[5]}) |",
         f"| Kích thước | {SIZE_TXT[t['size']]} |",
         f"| Trạng thái | **{t['status']}** |",
         f"| Phụ thuộc | {deps} |",
         f"| Story | {', '.join(STORIES.get(t['id'], [])) or '– (nền tảng / phi chức năng)'} |",
         f"| Tài liệu tham chiếu | {'; '.join(t['refs'])} |", ""]
    if blockers:
        L += ["> " + b for b in blockers] + [""]
    L += ["## Mục tiêu", "", t["goal"], "",
          "## Phạm vi file", ""] + [f"- {f}" for f in t["files"]] + ["",
          "## Các bước gợi ý", ""] + [f"{i}. {s}" for i, s in enumerate(t["steps"], 1)] + ["",
          "## Tiêu chí hoàn thành", ""] + [f"- [ ] {d}" for d in t["done"]] + [
          "- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`",
          "- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log", "",
          "## Kiểm chứng", "", "```bash"] + t["verify"] + ["```", ""]
    if out:
        L += ["## Ngoài phạm vi", ""] + [f"- {o}" for o in out] + [""]
    return "\n".join(L)

for t in T:
    io.open(os.path.join(TASK_DIR, FILES[t["id"]]), "w", encoding="utf-8", newline="\n").write(task_md(t))

# ----------------------------------------------------------------------------- PLAN.md
def story_tasks():
    m = {}
    for t in T:
        for x in STORIES.get(t["id"], []):
            m.setdefault(x, []).append(t["id"])
    return m

counts = {}
for t in T:
    counts.setdefault(t["sl"], []).append(t)

slice_rows = "\n".join(
    f"| **{s[0]}** {s[1]} | {s[5]} | {s[2]} | {', '.join(s[4]) or '–'} | {s[3]} | {', '.join(f'[{t['id']}](tasks/{FILES[t['id']]})' for t in counts.get(s[0], []))} |"
    for s in SLICES)

task_rows = "\n".join(
    f"| [{t['id']}](tasks/{FILES[t['id']]}) | {t['title']} | {t['sl']} | {t['size']} | {t['status']} | {', '.join(t['deps']) or '–'} |" for t in T)

st = story_tasks()
def skey(s):
    p, n = s.split("-", 1)
    return (p, n)
all_stories = [f"US-{i:03d}" for i in range(1, 28)]
trace_rows = "\n".join(f"| {s} | {', '.join(sorted(set(st.get(s, []))) ) or '**chưa có** – xem ghi chú'} |" for s in all_stories)

n_ready = sum(1 for t in T if t["status"].startswith("Ready"))
n_blocked = sum(1 for t in T if t["status"] == "Blocked")

edges = []
for t in T:
    for d in t["deps"]:
        edges.append(f"    {d.replace('-', '_')} --> {t['id'].replace('-', '_')}")
mermaid_slices = """flowchart LR
    VS0[VS-0 Nền tảng] --> VS1[VS-1 Đăng nhập]
    VS0 --> VS2[VS-2 Tải 1 PDF]
    VS1 --> VS2
    VS2 --> VS3[VS-3 Xử lý tài liệu]
    VS3 --> VS4[VS-4 Hỏi đáp có trích dẫn]
    VS4 --> M1{{Mốc 1: demo lát 1}}
    M1 --> VS5[VS-5 Nhiều file]
    M1 --> VS6[VS-6 Chất lượng]
    M1 --> VS7[VS-7 Xóa]
    M1 --> VS9[VS-9 Lỗi & giới hạn]
    VS7 --> VS8[VS-8 Cách ly]
    VS5 & VS6 & VS8 & VS9 --> VS10[VS-10 Vận hành]
    VS10 --> M2{{Mốc 2: launch gate MVP}}
    M2 -.P1 nếu kịp.-> VS11[VS-11 Tính năng P1]
    SP[SPIKE-01…04] -.kết quả cập nhật cấu hình.-> VS6
"""

PLAN = f"""# Kế hoạch triển khai – MVP AI Chat với tài liệu PDF

| Trường | Giá trị |
|---|---|
| Mã tài liệu | PLAN-AICHAT-001 · v0.1 |
| Ngày | 2026-10-24 |
| Đầu vào | [SAD](../04-design/SAD.md) v0.4 · [USER_STORIES](../03-analysis/USER_STORIES.md) v0.1 · [BLUEPRINT](../04-design/BLUEPRINT.md) v0.3 · [API_DESIGN](../04-design/API_DESIGN.md) + [openapi.yaml](../04-design/openapi.yaml) · [DATABASE_DESIGN](../04-design/DATABASE_DESIGN.md) + [schema.sql](../04-design/schema.sql) · [html_design](../04-design/html_design/index.html) |
| Số task | {len(T)} ({n_ready} sẵn sàng, {n_blocked} bị chặn) trong {len(SLICES)} nhóm |

## 1. Cách chia

- **Lát dọc (vertical slice):** mỗi lát đi xuyên giao diện → API → CSDL/worker và kết thúc bằng một thứ **demo được** (cột "Demo" ở mục 3). Riêng VS-0 là nền tảng bắt buộc, nhưng cũng kết thúc bằng một ứng dụng chạy được.
- **Thứ tự theo USER_STORIES mục 3:** lát 1 (VS-0…VS-4) dựng luồng xuyên suốt *Tải PDF → Xử lý → Hỏi → Trả lời có nguồn* sớm nhất để đo chất lượng AI thật (rủi ro RSK-001); lát 2 (VS-5…VS-10) hoàn thiện mọi story P0 và điều kiện ra mắt; lát 3 (VS-11) là P1.
- **Task cho agent:** mỗi task là một pull request, kích thước S (≤ ~200 dòng, 1–2 vòng lặp) hoặc M (~200–400 dòng, 2–4 vòng lặp), có danh sách file, các bước, tiêu chí hoàn thành kiểm tra được và lệnh kiểm chứng. Không có task L – task nào lớn hơn phải tách trước khi làm.
- **Không chờ quyết định bên ngoài:** phần phụ thuộc câu hỏi mở được làm sau *port/adapter* với bản giả (IdP giả lập, LLM giả, embedding giả). Đổi sang nhà cung cấp thật chỉ là cấu hình hoặc thêm adapter.

## 2. Bản đồ lát

```mermaid
{mermaid_slices}```

**Mốc 1 – demo lát 1** (sau T04-06): PO xem luồng xuyên suốt; chạy SPIKE-01 sớm nhất có thể.
**Mốc 2 – launch gate** (sau T10-06): PRD 5.1 G-01…G-09.

## 3. Các lát

| Lát | Giai đoạn | Nội dung | Story | Demo / tiêu chí lát | Task |
|---|---|---|---|---|---|
{slice_rows}

## 4. Danh sách task

| Task | Tiêu đề | Lát | Cỡ | Trạng thái | Phụ thuộc |
|---|---|---|---|---|---|
{task_rows}

**Trạng thái:** *Ready* = làm được ngay; *Ready (giả định)* = làm được với giá trị đề xuất/bản giả, cần PO/IT-Security xác nhận trước production; *Blocked* = chờ câu hỏi mở hoặc dữ liệu (ghi trong task).

## 5. Đồ thị phụ thuộc task

```mermaid
flowchart LR
{chr(10).join(edges)}
```

**Thứ tự gợi ý khi chỉ có một agent:** T00-01 → T00-02 → T00-03 → T00-04 → T00-05 → T00-06 → T00-07 → T01-01 → T01-02 → T01-04 → T01-03 → T01-05 → T02-01 → T02-02 → T02-03 → T02-04 → T02-05 → T02-06 → T03-01 → T03-02 → T03-03 → T03-04 → TS-02 → T03-05 → T03-06 → T04-01 → T04-02 → T04-03 → T04-04 → T04-05 → T04-06 (**Mốc 1**) → T06-03 → T06-01 → T06-02 → T07-01 → T07-02 → T07-03 → T05-01 → T05-02 → T05-03 → T09-01 → T09-02 → T09-03 → T08-01 → T08-02 → T10-01 → T10-02 → T10-03 → T10-04 → T10-05 → T10-06 (**Mốc 2**) → T11-01 → T11-02 → T11-03.

**Song song khi có nhiều agent:** sau T00-01, nhánh frontend (T00-06) và backend (T00-02…T00-05) chạy song song; T02-01, T02-02, T03-04, T04-02 không phụ thuộc nhau và có thể làm cùng lúc; TS-02 chạy ngay khi có T03-03, T03-04.

## 6. Quy trình làm một task (cho agent)

1. **Đọc** file task và các mục "Tài liệu tham chiếu". Thiết kế là nguồn chuẩn: tên bảng/cột theo `schema.sql`, endpoint và schema theo `openapi.yaml`, thuật toán theo `BLUEPRINT` ALG-xx, giao diện theo `html_design`.
2. **Kiểm tra phụ thuộc** đã xong (tiêu chí hoàn thành của task trước đã tick).
3. **Viết test trước** từ "Tiêu chí hoàn thành", rồi hiện thực tới khi xanh.
4. **Chạy lệnh "Kiểm chứng"** và `make lint typecheck`.
5. **Tick** các ô trong file task, ghi ngắn vào cuối file: ngày, PR, quyết định nhỏ đã đưa ra.
6. **Nếu thiết kế sai hoặc thiếu:** không tự đổi hành vi đã đặc tả. Sửa ở mức tối thiểu để task chạy, ghi rõ trong PR và mở mục "Đề xuất sửa tài liệu" (tài liệu + mục + đề xuất). Lỗi rõ ràng trong `schema.sql`/`openapi.yaml` phát hiện khi chạy thật thì sửa cả tài liệu trong cùng PR.
7. **Dừng và hỏi** khi: task cần quyết định nằm trong danh sách câu hỏi mở; thay đổi vượt phạm vi file đã liệt kê nhiều hơn 3 file; hoặc sau 3 vòng lặp vẫn không xanh.

### Quy ước chung

| Hạng mục | Quy ước |
|---|---|
| Backend | Python 3.12, uv, FastAPI, SQLAlchemy 2 Core (async, psycopg 3), Pydantic v2, ruff, mypy strict, pytest (+ Testcontainers, hypothesis) |
| Frontend | React 18 + TypeScript strict, Vite, TanStack Query, vitest, Playwright + axe-core, pnpm |
| Lệnh | `make up` · `make lint` · `make typecheck` · `make test-unit` · `make test-int` · `make e2e` (định nghĩa ở T00-01) |
| Nhánh / PR | `task/<ID>-<slug>`; tiêu đề PR bắt đầu bằng ID task; một task một PR |
| Bản giả | `llm_fake`, `embedding_fake`, `blob_memory`, mock-oauth2-server – mặc định trong test và dev |
| Dữ liệu thật | Không commit PDF thật của doanh nghiệp; fixture sinh bằng script |
| Definition of Done | USER_STORIES mục 8.2 + tiêu chí trong từng task |

## 7. Những gì đang bị chặn và cách xử lý

| Phụ thuộc | Task bị ảnh hưởng | Trong lúc chờ |
|---|---|---|
| OQ-005 nhà cung cấp LLM | T04-02 (adapter thật), TS-01 | Dùng `llm_fake`; adapter Anthropic chỉ bật khi có khóa |
| OQ-001, OQ-102 IdP và cách cấp quyền | T01-01…T01-03 (chỉ phần cấu hình) | Phát triển với mock-oauth2-server; đổi IdP = đổi cấu hình |
| OQ-003, OQ-006, OQ-009 ngưỡng | Mọi task dùng giới hạn | Dùng giá trị D-01…D-13 trong `.env.example` |
| DEP-003, DEP-005 PDF mẫu, bộ câu hỏi | TS-01, TS-03, TS-04, chỉ số chất lượng ở G-02 | Fixture tự tạo + `eval/datasets/sample.jsonl` |
| OQ-012 | T11-05 | Không làm |
| OQ-014 | T11-04 | Không làm. Endpoint `GET /documents/{id}/file` và sự kiện EVT-09 nằm trong T11-04; nếu PO chốt "không mở trong ứng dụng" thì vẫn tách phần endpoint ra làm (người dùng cần tải file gốc để kiểm chứng) |
| OQ-202, OQ-203 | T10-05 (production) | Chỉ dựng staging |
| US-019 (P2, OQ-018) | Không có task | Ngoài MVP |

## 8. Truy vết story → task

| Story | Task |
|---|---|
{trace_rows}

**Ghi chú:** US-019 (P2) không có task theo USER_STORIES mục 3 ("Sau MVP"). Story đề xuất: US-C01 (cấp quyền qua nhóm IdP) nằm trong T01-03; US-C02 (tra cứu nhật ký) qua vai trò `app_readonly_audit` trong T10-01; US-C03 (đăng xuất) trong T01-03, T01-05; US-C04, US-C05 chưa có task.

## 9. Rủi ro của kế hoạch

| Rủi ro | Ảnh hưởng | Giảm thiểu |
|---|---|---|
| Chất lượng RAG tiếng Việt không đạt (TR-01) | Phải đổi mô hình/chiến lược sau khi đã xây xong | Lát 1 kết thúc sớm; TS-01 ngay sau Mốc 1; tham số RAG là cấu hình |
| Embedding CPU chậm (TR-02) | NFR-002 không đạt | TS-02 chạy sớm (chỉ cần T03-03, T03-04) |
| Agent hiểu sai thiết kế | Làm lại | Mỗi task trỏ tới mục tài liệu cụ thể; test viết từ tiêu chí trước khi code |
| Schema chưa chạy trên PostgreSQL thật | Lỗi ở T00-03 | T00-03 là task thứ 3; sửa cả tài liệu |
| Sandbox chỉ chạy trên Linux | Dev trên Windows không chạy được test sandbox | Chạy trong container/CI; test đánh dấu skip có lý do |
"""
io.open(os.path.join(OUT, "PLAN.md"), "w", encoding="utf-8", newline="\n").write(PLAN)
print("tasks", len(T), "ready", n_ready, "blocked", n_blocked)
missing = [s for s in all_stories if s not in st]
print("stories without tasks:", missing)
