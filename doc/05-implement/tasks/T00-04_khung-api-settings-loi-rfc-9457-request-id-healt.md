# T00-04 – Khung API: settings, lỗi RFC 9457, request id, health

| Trường | Giá trị |
|---|---|
| Lát | VS-0 – Nền tảng chạy được (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T00-01](T00-01_khoi-tao-monorepo-va-cong-cu.md) |
| Story | – (nền tảng / phi chức năng) |
| Tài liệu tham chiếu | BLUEPRINT 3.6.1, 3.6.6; API_DESIGN 3.5 (mô hình lỗi), 3.6.2, AD-10; openapi.yaml (`Problem`, `ErrorCode`, /healthz, /readyz) |

## Mục tiêu

API FastAPI chạy được với cấu hình kiểm tra lúc khởi động, định dạng lỗi thống nhất và health check.

## Phạm vi file

- `backend/app/main.py` (app factory, composition root)
- `backend/app/infra/settings.py` (pydantic-settings, mọi biến 3.6.6)
- `backend/app/api/errors.py` (ProblemException, handler, ánh xạ 422 FastAPI → `invalid_request`/`empty_question`/`question_too_long`)
- `backend/app/infra/logging.py` (structlog JSON, lọc trường cấm)
- `backend/app/api/middleware.py` (RequestId)
- `backend/app/api/v1/health.py`
- `deploy/docker-compose.dev.yml` (service `api`)

## Các bước gợi ý

1. Settings: giá trị sai kiểu/ngoài khoảng → tiến trình thoát với thông báo rõ.
2. Middleware RequestId: nhận/sinh `X-Request-ID`, gắn vào log context và header phản hồi.
3. Handler: mọi ngoại lệ → `application/problem+json` có `type=https://errors.aichat.local/<code>`, `code`, `request_id`; ngoại lệ lạ → 500 `internal_error`, không lộ stack.
4. Bộ lọc log xóa khóa `question`, `answer`, `content`, `file_name`, `email` (SAD 8.3).
5. `/readyz` kiểm tra `SELECT 1`.

## Tiêu chí hoàn thành

- [ ] Unit test: 3 loại lỗi (ProblemException, validation, ngoại lệ lạ) trả đúng schema `Problem` (validate bằng jsonschema từ openapi.yaml)
- [ ] Unit test bộ lọc log
- [ ] `/healthz` 200, `/readyz` 200 khi có DB và 503 khi không
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-unit -k 'errors or health or logging'
curl -i localhost:8000/api/v1/readyz
```

## Ngoài phạm vi

- Không có xác thực (VS-1)

## Kết quả triển khai

**Done** – Settings, lỗi RFC 9457, request id, `/healthz`, `/readyz`, header bảo mật.
