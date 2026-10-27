# AI Chat PDF – bản demo MVP

Hỏi đáp với tài liệu PDF của chính bạn. Mỗi câu trả lời kèm tên tài liệu và số trang để kiểm chứng.
Được triển khai theo [doc/05-implement/PLAN.md](../doc/05-implement/PLAN.md) và các file `tasks/*.md`.

## Chạy demo (một lệnh)

Yêu cầu: Python ≥ 3.12 và Node.js ≥ 20. Không cần Docker hay PostgreSQL.

```bash
cd app
python -m venv backend/.venv
backend/.venv/Scripts/pip install -r backend/requirements.txt   # Linux/macOS: backend/.venv/bin/pip
backend/.venv/Scripts/python.exe run.py --sample                 # lần đầu: sinh PDF mẫu vào sample-pdfs/
```

Sau đó mở <http://localhost:8080>:

1. Trang đăng nhập của IdP giả lập hiện ra → chọn **Nguyễn Lan (P1)**.
2. Kéo thả các file trong `sample-pdfs/` (`hop-dong-A.pdf`, `chinh-sach-ban-hang-2026.pdf`, `bang-gia-Q4.pdf`;
   thử thêm `ho-so-scan-2019.pdf`, `hop-dong-mat-khau.pdf`, `bao-gia.docx` để xem các đường từ chối).
3. Chờ tài liệu chuyển sang **Sẵn sàng** (vài giây), rồi hỏi, ví dụ:
   - "Bên B thanh toán trong vòng bao nhiêu ngày?" → trả lời 30 ngày, nguồn `hop-dong-A.pdf · tr.2`
   - "Giá gói Premium là bao nhiêu?" → hai giá từ hai tài liệu, mỗi giá có nguồn riêng
   - "Đối thủ cạnh tranh tại thị trường Nhật Bản là ai?" → **Chưa đủ thông tin**
4. Bấm nhãn nguồn để mở file gốc đúng trang; xóa tài liệu để thấy nguồn chuyển sang "(đã xóa)".

Người dùng mẫu: `p1` lan.nguyen, `p2` minh.tran (nhóm `aichat-users`), `admin` (nhóm `aichat-admins`),
`outsider` khach (không thuộc nhóm → trang *Bạn chưa được cấp quyền*).

### Dùng Claude thay cho bộ trả lời trích xuất

Mặc định `LLM_PROVIDER=extractive` chạy offline: nó chọn các câu trong tài liệu khớp với câu hỏi, không cần
API key. Để dùng mô hình thật, sửa `app/.env`:

```
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-...
LLM_MODEL=claude-opus-5-5
```

## Cấu trúc

| Thư mục | Nội dung |
|---|---|
| `backend/app/api` | FastAPI router `/api/v1`, CSRF, lỗi RFC 9457, header bảo mật |
| `backend/app/modules` | Nghiệp vụ: identity, documents, ingestion, retrieval, qa, events, audit |
| `backend/app/ports`, `backend/app/adapters` | Cổng/adapter: blob, embedding, LLM, OIDC (import-linter giữ ranh giới) |
| `backend/app/infra` | Settings, CSDL theo vai trò + RLS, job queue, sandbox, circuit breaker, rate limit |
| `backend/worker` | Worker ingest/purge + tác vụ bảo trì định kỳ |
| `backend/devidp` | IdP OIDC giả lập (authorization code + PKCE, RS256) |
| `backend/migrations` | `sql/0001_initial.sql` (= `doc/04-design/schema.sql` v0.3), `seed_dev.sql` |
| `frontend` | SPA React + TypeScript (Vite), theo `doc/04-design/html_design` S01–S11 |
| `devdb` | PostgreSQL 17 + pgvector chạy bằng PGlite (WASM) |
| `contracts/openapi.yaml` | Hợp đồng API; test đối chiếu với OpenAPI sinh từ FastAPI |

## Kiểm thử

```bash
cd app/backend
.venv/Scripts/python.exe -m pytest -q        # 48 test: unit + integration trên PostgreSQL thật (PGlite)
.venv/Scripts/python.exe -m ruff check app worker devidp tests
.venv/Scripts/python.exe -m mypy             # strict
PYTHONUTF8=1 .venv/Scripts/lint-imports      # ranh giới tầng
.venv/Scripts/python.exe scripts/smoke.py    # smoke đầu-cuối trên môi trường đang chạy (run.py)

cd ../frontend
npx tsc -p . && npx vite build
npx playwright test                          # E2E trên Microsoft Edge có sẵn (cần run.py --sample đang chạy)
```

Đặt `TEST_DATABASE_URL` để chạy integration test với PostgreSQL thật thay cho PGlite (CI dùng `pgvector/pgvector:pg17`).

**Thực thi test case có bằng chứng:** có 130 test case trong [doc/07-verification/test_cases](../doc/07-verification/test_cases/README.md).
Mỗi test case ghi report, ảnh chụp và video vào `test_reports/<tên test case>/` ở gốc repo, bằng công cụ trong
`frontend/evidence/`:
- `fixture.ts`: cho test giao diện/API;
- `record-cli.ts`: cho test chạy bằng lệnh;
- `app.ts`: khởi động lại ứng dụng với cấu hình riêng.

Ghi video cần chạy `npx playwright install ffmpeg` một lần.

## Khác biệt so với kế hoạch

Máy phát triển không có Docker và chỉ có Python 3.14, nên một số lựa chọn trong PLAN được thay bằng phương án
chạy được tại chỗ. Kiến trúc (cổng/adapter, RLS, thuật toán ALG-01…ALG-12, hợp đồng API) giữ nguyên.

| Kế hoạch | Bản demo | Ghi chú |
|---|---|---|
| Repo gốc, `uv`/`pnpm`/`make` | `app/`, `pip`/`npm`/`run.py` | Theo yêu cầu "mọi mã nằm trong ./app" |
| docker-compose: PostgreSQL 16, MinIO, mock-oauth2-server | PGlite (PostgreSQL 17.5 WASM + pgvector 0.8), blob thư mục `.data/blobs`, IdP giả lập viết bằng FastAPI | `BlobPort` vẫn là cổng; adapter S3 chưa viết |
| Pool kết nối, API và worker tách tiến trình, `LISTEN/NOTIFY` | `DB_MODE=single`: một kết nối có khóa, worker chạy trong tiến trình API, bus sự kiện trong bộ nhớ | PGlite chỉ nhận một kết nối. Bật `DB_MODE=pool` khi dùng PostgreSQL thật |
| Alembic + SQLAlchemy Core | Bộ chạy migration SQL tối giản + psycopg 3 | Cùng file `0001_initial.sql` |
| Embedding bge-m3 qua dịch vụ HTTP | `hashing-ngram@v1` (1024 chiều, chạy offline) | Có sẵn adapter HTTP (`EMBEDDING_PROVIDER=http`) |
| LLM nhà cung cấp | Mặc định bộ trả lời trích xuất (offline); adapter Anthropic có sẵn | Câu hỏi tiếp nối (T11-05) và cờ mâu thuẫn tự động cần LLM thật |
| Client sinh từ OpenAPI, TanStack Query | Client viết tay trong `frontend/src/api.ts` | Test hợp đồng đảm bảo mọi path trong `openapi.yaml` đều có |
| pdf.js | Trình xem PDF có sẵn của trình duyệt trong iframe (`#page=N`) | |
| Testcontainers | PGlite trong bộ nhớ cho mỗi lần chạy test | |
| Python 3.12 | Python 3.14 | Giới hạn bộ nhớ sandbox trên Windows dùng psutil thay cho rlimit |

Các điểm sửa so với thiết kế, phát hiện khi chạy thật:

- `COPY ... FROM STDIN` không dùng được với bảng có RLS → ghi `chunk` bằng `executemany` INSERT.
- Full-text dùng truy vấn OR các từ có nghĩa thay cho `websearch_to_tsquery` (AND mọi từ, kể cả "là", "bao nhiêu").
- PGlite không gửi `ParameterStatus` khi bắt tay; `devdb/server.mjs` tự chèn vào, nếu không psycopg (bản C) sẽ crash.
- Endpoint file trả `X-Frame-Options: SAMEORIGIN` để SPA nhúng được trình xem PDF.
- Windows: psycopg async cần `SelectorEventLoop` → chạy uvicorn qua `backend/serve.py`.

Trạng thái từng task: xem cột *Trạng thái* trong [PLAN.md](../doc/05-implement/PLAN.md#4-danh-sách-task).
