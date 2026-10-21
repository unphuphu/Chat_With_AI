# T-003 — Dựng khung FastAPI: cấu hình, log, request id, lỗi chung, health

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 0 |
| **Loại** | Backend |
| **User story** | — nền tảng |
| **Ưu tiên** | P0 |
| **Ước lượng** | 1 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-001, T-002 |
| **Mở khóa (task chờ task này)** | T-004, T-006, T-007, T-102, T-404 |
| **Người thực hiện** | _chưa giao_ (BE) |
| **Trạng thái** | To do |

## 1. Mục tiêu

Backend có ứng dụng FastAPI chạy được với: cấu hình tập trung bằng `pydantic-settings`, log JSON không chứa nội dung nhạy cảm, middleware `X-Request-Id`, cơ chế lỗi chung `AppError` → `{ "error": { "code", "message", "requestId" } }`, và hai endpoint API-12 `/health/live`, `/health/ready`. Worker có điểm vào `python -m app.worker` chạy được (vòng lặp rỗng).

## 2. Bối cảnh

- Module `platform` (CMP-10) chịu cấu hình, log, request_id, lỗi, health ([SAD §2.2](../../design/SAD.md#22-tầng-ứng-dụng--logic-nghiệp-vụ-cmp-03cmp-10-cmp-20)).
- Quy ước backend: `AppError(code, http_status, message)`, `X-Request-Id`, log JSON, cấm log nội dung, không đọc `os.environ` rải rác ([Implement_plan §4.1](../Implement_plan.md#41-backend)).
- Trường log chuẩn và health check không phụ thuộc AI ([SAD §4.3](../../design/SAD.md#43-khả-năng-quan-sát-observability)).
- Danh mục mã lỗi: [Blueprint §3.5](../../design/Blueprint_Design.md#35-interface-view).

## 3. Phạm vi

**Trong phạm vi**
- `create_app()`, router gốc `/api/v1` (rỗng), router health.
- `Settings` khai báo **mọi** biến ở Implement_plan §3.3.
- Log JSON (structlog), middleware request id + access log.
- `AppError`, các exception handler (AppError, lỗi validate, 404 route, lỗi không bắt được).
- Kết nối CSDL async (engine + session factory) dùng cho `/health/ready`.
- Cơ chế đăng ký kiểm tra sẵn sàng để task sau thêm (ví dụ hàng đợi ở T-101).
- `app/worker.py` khung.

**Ngoài phạm vi**
- Migration/bảng ([T-004](./T-004-db-migrations-baseline.md)); xác thực ([T-006](./T-006-auth-session-dev-identity.md)).
- `call_upstream()` ([T-305](./T-305-upstream-resilience.md)); OpenTelemetry, `/metrics` ([T-404](./T-404-observability.md)); vòng lặp job thật ([T-101](./T-101-job-queue.md)).

## 4. Thiết kế chi tiết

**Tệp**

```text
backend/app/main.py                 # create_app(), app = create_app()
backend/app/worker.py               # main(): vòng lặp rỗng, bắt SIGTERM
backend/app/platform/config.py      # Settings, get_settings()
backend/app/platform/logging.py     # configure_logging(settings), get_logger()
backend/app/platform/request_id.py  # RequestIdMiddleware, request_id_ctx: ContextVar[str]
backend/app/platform/errors.py      # AppError, ErrorCode, register_error_handlers(app)
backend/app/platform/db.py          # create_engine(), get_session(), Base (SQLAlchemy 2 DeclarativeBase)
backend/app/platform/health.py      # router, ReadinessCheck, register_readiness_check()
backend/app/platform/schemas.py     # ApiModel(BaseModel) với model_config extra="forbid"
backend/tests/unit/test_errors.py, test_request_id.py, test_config.py
backend/tests/integration/test_health.py   # Testcontainers PostgreSQL
```

**Cấu hình**

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")
    APP_ENV: Literal["dev", "ci", "staging", "production"] = "dev"   # [Proposed]
    DATABASE_URL: PostgresDsn
    S3_ENDPOINT: str; S3_BUCKET: str; S3_ACCESS_KEY: SecretStr; S3_SECRET_KEY: SecretStr
    AI_PROVIDER: Literal["fake"] | str = "fake"
    EMBEDDING_MODEL: str = "fake-384"; EMBEDDING_DIM: int = 384
    LLM_MODEL: str | None = None; LLM_REWRITE_MODEL: str | None = None
    AUTH_MODE: Literal["dev", "oidc"] = "dev"
    MAX_UPLOAD_MB: int = 50; MAX_PAGES: int = 500                    # [Default] OQ-013
    ANSWER_TIMEOUT_S: int = 60
    RELEVANCE_THRESHOLD: float = 0.30                                 # [Default] OQ-008
    RETRIEVAL_KV: int = 20; RETRIEVAL_KT: int = 20; RETRIEVAL_K: int = 8; MAX_CHUNKS_PER_DOC: int = 3
    HISTORY_TURNS: int = 6
    RATE_LIMIT_QUESTIONS_PER_MIN: int = 20; RATE_LIMIT_UPLOADS_PER_MIN: int = 10
    WEEKLY_TOKEN_BUDGET: int | None = None
    LOG_LEVEL: str = "INFO"; OTEL_EXPORTER_OTLP_ENDPOINT: str | None = None

@lru_cache
def get_settings() -> Settings: ...
```

Mọi module lấy cấu hình qua `get_settings()` (hoặc dependency FastAPI); cấm `os.environ` ngoài `config.py`. Bí mật dùng `SecretStr` để không lộ khi log `Settings`.

**Lỗi**

```python
class ErrorCode(StrEnum):
    UNAUTHENTICATED = "UNAUTHENTICATED"; FORBIDDEN = "FORBIDDEN"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"; FILE_TOO_LARGE = "FILE_TOO_LARGE"
    NOT_EXTRACTABLE = "NOT_EXTRACTABLE"; NO_READY_DOCUMENTS = "NO_READY_DOCUMENTS"
    UPSTREAM_TIMEOUT = "UPSTREAM_TIMEOUT"; UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    NOT_FOUND = "NOT_FOUND"                 # dùng ở màn 09; chưa có trong SDD §3.5 — [Proposed]
    VALIDATION_ERROR = "VALIDATION_ERROR"   # 422 — [Proposed]
    INTERNAL_ERROR = "INTERNAL_ERROR"       # 500 — [Proposed]

class AppError(Exception):
    def __init__(self, code: ErrorCode, http_status: int, message: str) -> None: ...
```

| Ngoại lệ | HTTP | `code` | `message` (tiếng Việt, thân thiện) |
|---|---|---|---|
| `AppError` | theo đối tượng | theo đối tượng | theo đối tượng |
| `RequestValidationError` | 422 | `VALIDATION_ERROR` | "Dữ liệu gửi lên không hợp lệ." — **không** lặp lại giá trị người dùng nhập |
| `StarletteHTTPException` 404/405 | 404/405 | `NOT_FOUND` | "Không tìm thấy." |
| `Exception` khác | 500 | `INTERNAL_ERROR` | "Đã có lỗi xảy ra. Vui lòng thử lại." — log stacktrace ở mức ERROR, không trả chi tiết |

Body luôn: `{"error": {"code": "...", "message": "...", "requestId": "req_..."}}`, header `X-Request-Id` trùng `requestId`.

**Request id:** nhận `X-Request-Id` từ client/proxy nếu khớp `^[A-Za-z0-9_-]{8,64}$`, ngược lại sinh `req_` + 16 ký tự hex `[Proposed]` (màn 09 hiển thị dạng `req_8f3a21c9`). Lưu vào `ContextVar`, gắn vào mọi log và phản hồi (kể cả lỗi).

**Log:** structlog JSON ra stdout. Một dòng access log mỗi request với trường: `timestamp`, `level`, `service` (`api`/`worker`), `request_id`, `trace_id` (rỗng tới T-404), `user_id` (UUID hoặc null — T-006 điền), `route` (template, ví dụ `/api/v1/documents/{id}`, **không** query string), `status`, `duration_ms`, `error_code`. Không log body, header `Cookie`, `Authorization`, `X-CSRF-Token`.

**Health (API-12, công khai, ngoài `/api/v1`):**

| Endpoint | Hành vi | Phản hồi |
|---|---|---|
| `GET /health/live` | Không I/O | `200 {"status":"ok"}` |
| `GET /health/ready` | Chạy tuần tự mọi `ReadinessCheck` đã đăng ký, mỗi check timeout 2 s `[Proposed]`; check mặc định `db`: `SELECT 1`. **Không** gọi dịch vụ AI | `200 {"status":"ok","checks":{"db":"ok"}}` hoặc `503 {"status":"unavailable","checks":{"db":"fail"}}` |

```python
ReadinessCheck = Callable[[], Awaitable[None]]   # raise khi không sẵn sàng
def register_readiness_check(name: str, check: ReadinessCheck) -> None: ...
```

**OpenAPI:** `create_app()` đặt `openapi_url="/api/v1/openapi.json"`; `docs_url` chỉ bật khi `APP_ENV in {"dev","ci"}` `[Proposed]`.

**Worker:** `app/worker.py` cấu hình log `service=worker`, vòng `while not stopping: await asyncio.sleep(1)`; xử lý SIGTERM/SIGINT để dừng sạch. T-101 thay vòng lặp bằng `JobQueue.claim()`.

## 5. Các bước thực hiện

1. Viết `config.py`; test: thiếu `DATABASE_URL` → lỗi khởi động rõ ràng; `SecretStr` không lộ trong `repr`.
2. Viết `request_id.py` (middleware ASGI thuần để không hỏng streaming SSE về sau).
3. Viết `logging.py` + access log trong middleware; test log ra JSON và không có body.
4. Viết `errors.py` + `register_error_handlers`; test 4 loại ngoại lệ trong bảng.
5. Viết `db.py` (async engine, pool size cấu hình mặc định), `health.py`.
6. Viết `main.py`: `create_app()` gắn middleware, handler, router health, router `/api/v1` rỗng.
7. Viết `worker.py`.
8. Test tích hợp `/health/ready` với Testcontainers PostgreSQL (lên → 200; dừng container → 503).
9. Chạy `make up` và kiểm `curl localhost:8080/health/ready`.

## 6. Tiêu chí chấp nhận

- [ ] `GET /health/live` → 200 `{"status":"ok"}`; `GET /health/ready` → 200 khi CSDL sống, 503 kèm `checks.db="fail"` khi CSDL không truy cập được (≤ 3 s).
- [ ] Một route test ném `AppError(ErrorCode.FORBIDDEN, 403, "...")` trả đúng 403 và body đúng định dạng có `requestId`.
- [ ] Lỗi validate trả 422 `VALIDATION_ERROR`; route không tồn tại trả 404 `NOT_FOUND`; ngoại lệ bất kỳ trả 500 `INTERNAL_ERROR` không chứa stacktrace.
- [ ] Gửi `X-Request-Id: abcdefgh123` → phản hồi và dòng log có cùng giá trị; không gửi → sinh `req_` + 16 hex.
- [ ] Access log là JSON một dòng, đủ các trường liệt kê; test khẳng định body request (chuỗi đánh dấu `SECRET_MARKER`) **không** xuất hiện trong log.
- [ ] `grep -rn "os.environ" backend/app` chỉ ra `platform/config.py` (hoặc không có).
- [ ] `python -m app.worker` chạy, dừng sạch khi nhận SIGTERM (exit 0).
- [ ] CI xanh (ruff, mypy strict, import-linter, pytest).

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `AppError` với mỗi `ErrorCode` | HTTP và `code` đúng; `requestId` có mặt |
| Unit | Body có trường lạ với model `ApiModel` | 422 `VALIDATION_ERROR` |
| Unit | Request id không hợp lệ (`<script>`) | Bị thay bằng id sinh mới |
| Unit | Log capture khi gửi body chứa `SECRET_MARKER` | Chuỗi không có trong log |
| Integration | `/health/ready` với PostgreSQL Testcontainers | 200; sau khi dừng container → 503 |
| Integration | `register_readiness_check("x", fail)` | `/health/ready` 503, `checks.x="fail"` |

## 8. Cấu hình

Đọc mọi biến Implement_plan §3.3. Thêm `[Proposed]` `APP_ENV` (`dev`) — cập nhật `deploy/.env.example` trong cùng PR. `LOG_LEVEL=INFO`, `OTEL_EXPORTER_OTLP_ENDPOINT` trống ở local.

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| SDD §3.5 không có mã cho 404/422/500 | Frontend và test không thống nhất mã | Dùng `NOT_FOUND`, `VALIDATION_ERROR`, `INTERNAL_ERROR` `[Proposed]`; xin Tech Lead bổ sung vào SDD |
| Middleware kiểu `BaseHTTPMiddleware` có thể đệm phản hồi streaming | SSE (T-207) không phát dần | Viết middleware ASGI thuần |
| Pydantic `extra="forbid"` từ chối trường client cũ gửi thêm | Lỗi khi frontend thay đổi | Chấp nhận theo SAD §2.4 ("từ chối trường lạ") |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §3.1, §3.3, §4.1, §10.1 (API-12)
- [SAD](../../design/SAD.md) §2.2, §2.4 (quy ước chung), §4.2 (timeout CSDL), §4.3
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.5 (mô hình lỗi)
- Màn hình: [09_access_denied.html](../../design/html_design/09_access_denied.html) (định dạng mã yêu cầu)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] OpenAPI tại `/api/v1/openapi.json` sinh được và có schema lỗi chung.
