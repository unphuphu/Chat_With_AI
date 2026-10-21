# T-002 — Dựng môi trường local bằng docker-compose, nginx và Makefile

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 0 |
| **Loại** | DevOps |
| **User story** | — nền tảng |
| **Ưu tiên** | P0 |
| **Ước lượng** | 1 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-001 |
| **Mở khóa (task chờ task này)** | T-003, T-004 |
| **Người thực hiện** | _chưa giao_ (BE) |
| **Trạng thái** | To do |

## 1. Mục tiêu

Một developer mới clone repo, chạy `cp deploy/.env.example deploy/.env && make up` và có đủ 6 service (`db`, `minio`, `api`, `worker`, `web`, `proxy`) chạy local, truy cập qua `http://localhost:8080`, trong ≤ 30 phút kể cả thời gian tải image (mục tiêu Sprint 0).

## 2. Bối cảnh

- Kiến trúc: một PostgreSQL 16 + pgvector, MinIO (S3), API và Worker cùng một image khác lệnh chạy, SPA tĩnh, reverse proxy Nginx ([Implement_plan §2](../Implement_plan.md#2-kiến-trúc-tóm-tắt-cho-developer), [SAD §2.0](../../design/SAD.md#20-sơ-đồ-container-mức-c4-2)).
- Đường dẫn SSE của API-09 phải tắt đệm ở proxy, nếu không người dùng không thấy sự kiện `status` (Implement_plan §3.2, SAD §3.2.1 bước 1).
- Tải lên phải truyền luồng, không đệm toàn tệp (SAD §3.2.2).
- Dữ liệu thật **không** được dùng ở `dev` ([Blueprint §3.8](../../design/Blueprint_Design.md#38-resource--deployment-view)).

## 3. Phạm vi

**Trong phạm vi**
- `deploy/docker-compose.yml`, `deploy/nginx.conf`, `deploy/.env.example`, `Makefile` ở gốc repo.
- `backend/Dockerfile` (dùng chung cho `api` và `worker`), `frontend/Dockerfile` (build tĩnh, phục vụ bằng nginx).
- Healthcheck cho `db`, `minio`, `api`; volume dữ liệu bền.
- Tạo bucket MinIO khi khởi động.

**Ngoài phạm vi**
- Mã `/health/*` ([T-003](./T-003-fastapi-skeleton.md)), migration ([T-004](./T-004-db-migrations-baseline.md)), dữ liệu seed ([T-006](./T-006-auth-session-dev-identity.md) tạo user dev; PDF mẫu từ [T-009](./T-009-sample-docs-and-eval-questions.md)).
- TLS, header bảo mật (CSP, HSTS) ([T-405](./T-405-security-hardening.md)); triển khai staging ([T-409](./T-409-staging-deployment.md)).

## 4. Thiết kế chi tiết

**`deploy/docker-compose.yml`** (mở rộng phác thảo Implement_plan §3.2; tên image `[Verify]`):

| Service | Image / build | Lệnh | Cổng host | Healthcheck | Phụ thuộc |
|---|---|---|---|---|---|
| `db` | `pgvector/pgvector:pg16` | mặc định | `5432` | `pg_isready -U cwd` | — |
| `minio` | `minio/minio` | `server /data --console-address ":9001"` | `9000`, `9001` | `GET /minio/health/live` | — |
| `minio-init` *(chạy một lần, thoát)* `[Proposed]` | `minio/mc` | `mc alias set local http://minio:9000 $S3_ACCESS_KEY $S3_SECRET_KEY && mc mb -p local/$S3_BUCKET` | — | — | `minio` healthy |
| `api` | `build: ../backend` | `uvicorn app.main:app --host 0.0.0.0 --port 8000` | — (qua proxy) | `GET /health/ready` | `db`, `minio` healthy |
| `worker` | `build: ../backend` | `python -m app.worker` | — | — | `db`, `minio` healthy |
| `web` | `build: ../frontend` | nginx phục vụ `dist/` ở cổng 80 | — | — | — |
| `proxy` | `nginx:stable` | mount `./nginx.conf:/etc/nginx/nginx.conf:ro` | `8080:80` | — | `api`, `web` |

Volume: `pgdata:/var/lib/postgresql/data`, `miniodata:/data`. `env_file: .env` cho `api`, `worker`, `minio-init`. Mọi service `restart: unless-stopped` (trừ `minio-init`). "6 service" trong tiêu chí = 6 service chạy lâu dài; `minio-init` là tác vụ một lần.

**`deploy/nginx.conf`** — các `location`:

```nginx
client_max_body_size 200m;          # [Default] — đặt lại khi OQ-013 chốt (giới hạn tệp × số tệp/lần)

location ~ ^/api/v1/conversations/.+/messages$ {   # API-09 SSE
  proxy_pass http://api:8000;
  proxy_buffering off;
  proxy_read_timeout 120s;
  proxy_set_header X-Request-Id $http_x_request_id;
}
location = /api/v1/documents {                    # API-02: truyền luồng tệp
  proxy_pass http://api:8000;
  proxy_request_buffering off;                     # [Proposed]
}
location /api/   { proxy_pass http://api:8000; }
location /health/ { proxy_pass http://api:8000; }  # local; staging chỉ mạng nội bộ (T-409)
location = /metrics { deny all; }                  # chỉ mạng nội bộ (SAD §4.3)
location /       { proxy_pass http://web:80; }     # SPA
```

Mọi location `/api` đặt `proxy_set_header Host`, `X-Forwarded-For`, `X-Forwarded-Proto`. `web` cấu hình `try_files $uri /index.html` cho route SPA; `Cache-Control: no-cache` cho `index.html`, `public, max-age=31536000, immutable` cho tệp có băm ([SAD §2.1](../../design/SAD.md#21-tầng-frontend--client-cmp-01)).

**`deploy/.env.example`** — đủ mọi biến của [Implement_plan §3.3](../Implement_plan.md#33-biến-môi-trường) với giá trị local:

```dotenv
DATABASE_URL=postgresql+asyncpg://cwd:cwd@db:5432/cwd
S3_ENDPOINT=http://minio:9000
S3_BUCKET=cwd-documents
S3_ACCESS_KEY=cwd-local
S3_SECRET_KEY=cwd-local-secret        # chỉ local; staging/prod lấy từ secret manager
AI_PROVIDER=fake
EMBEDDING_MODEL=fake-384
EMBEDDING_DIM=384
LLM_MODEL=
LLM_REWRITE_MODEL=
AUTH_MODE=dev
MAX_UPLOAD_MB=50                      # [Default] — OQ-013
MAX_PAGES=500                         # [Default] — OQ-013
ANSWER_TIMEOUT_S=60
RELEVANCE_THRESHOLD=0.30              # [Default] — OQ-008
RETRIEVAL_KV=20
RETRIEVAL_KT=20
RETRIEVAL_K=8
MAX_CHUNKS_PER_DOC=3
HISTORY_TURNS=6
RATE_LIMIT_QUESTIONS_PER_MIN=20       # [Default]
RATE_LIMIT_UPLOADS_PER_MIN=10         # [Default]
WEEKLY_TOKEN_BUDGET=
LOG_LEVEL=INFO
OTEL_EXPORTER_OTLP_ENDPOINT=
```

Biến do task sau thêm (ví dụ `APP_ENV`, `SESSION_SECRET` ở T-003/T-006) phải được bổ sung vào tệp này trong cùng PR của task đó. Biến `POSTGRES_*` và `MINIO_ROOT_USER/PASSWORD` của container lấy cùng giá trị local.

**`Makefile`** (gốc repo; `COMPOSE = docker compose -f deploy/docker-compose.yml --env-file deploy/.env`):

| Target | Lệnh |
|---|---|
| `up` | `$(COMPOSE) up -d --build` |
| `down` | `$(COMPOSE) down` |
| `reset` | `$(COMPOSE) down -v` (xóa dữ liệu local) |
| `logs` | `$(COMPOSE) logs -f api worker` |
| `migrate` | `$(COMPOSE) run --rm api alembic upgrade head` |
| `migrate-down` | `$(COMPOSE) run --rm api alembic downgrade -1` |
| `seed` | `$(COMPOSE) run --rm api python -m app.scripts.seed` (script do T-006 tạo; mở rộng nạp PDF ở Sprint 1) |
| `lint` | lệnh lint backend + frontend như CI (T-001) |
| `test` | `cd backend && pytest -q` và `cd frontend && npm test` |
| `ps` | `$(COMPOSE) ps` |

**Dockerfile backend:** `python:3.12-slim`, cài deps từ lockfile, chạy bằng user không phải root, `WORKDIR /app`, không chép `.env` vào image. **Dockerfile frontend:** multi-stage `node:20` (`npm ci && npm run build`) → `nginx:stable` chép `dist/`.

## 5. Các bước thực hiện

1. Viết `backend/Dockerfile` và `frontend/Dockerfile`; cho tới khi T-003/T-005 xong, dùng tệp giữ chỗ (`app/main.py` trả `/health/live`, `index.html` tĩnh) để build được.
2. Viết `deploy/docker-compose.yml` theo bảng; thêm healthcheck và `depends_on: condition: service_healthy`.
3. Viết `deploy/nginx.conf`; chạy `docker compose run --rm proxy nginx -t` để kiểm cú pháp.
4. Viết `deploy/.env.example` đủ biến §3.3; kiểm gitleaks không báo (allowlist tệp ví dụ).
5. Viết `Makefile`; thêm mục "Chạy local" vào `README.md` gốc (4 lệnh của Implement_plan §3.2).
6. Đo thời gian onboarding trên một máy sạch (xóa image): từ clone tới mở được `http://localhost:8080`.

## 6. Tiêu chí chấp nhận

- [ ] `make up` trên máy sạch: `make ps` cho thấy `db`, `minio`, `api`, `worker`, `web`, `proxy` ở trạng thái running/healthy; `minio-init` thoát mã 0.
- [ ] `curl -s localhost:8080/health/live` trả 200; `curl -s localhost:8080/` trả HTML của SPA.
- [ ] Bucket `S3_BUCKET` tồn tại sau `make up` (`mc ls`).
- [ ] `curl -s -o /dev/null -w '%{http_code}' localhost:8080/metrics` trả 403.
- [ ] `nginx -t` pass; location API-09 có `proxy_buffering off` và `proxy_read_timeout 120s`.
- [ ] `deploy/.env.example` chứa 100% biến ở Implement_plan §3.3.
- [ ] `make reset && make up` khôi phục được môi trường sạch.
- [ ] Thời gian onboarding đo ở bước 6 ≤ 30 phút, ghi vào README.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Thủ công | `make up` máy sạch | 6 service chạy; ghi thời gian |
| Thủ công | Dừng `db` (`docker compose stop db`) | `api` healthcheck chuyển unhealthy sau khi T-003 có `/health/ready` |
| Thủ công | `curl -N` tới một route `/api/v1/conversations/x/messages` | Proxy không gom phản hồi (kiểm lại đầy đủ ở T-207) |
| CI | Job tùy chọn `compose-config`: `docker compose config -q` | pass |

## 8. Cấu hình

Toàn bộ biến §3.3 như bảng mục 4. `[Default]`: `MAX_UPLOAD_MB=50`, `MAX_PAGES=500`, `client_max_body_size 200m` (thay khi **OQ-013** chốt); `RELEVANCE_THRESHOLD=0.30` (**OQ-008**); `AUTH_MODE=dev` (**OQ-018**); `AI_PROVIDER=fake` (**OQ-006**).

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| `client_max_body_size` phụ thuộc giới hạn tệp và số tệp/lần (OQ-013) | Tải nhiều tệp lớn bị 413 ở proxy thay vì lỗi từng tệp | `[Default]` 200m; T-103 xác nhận API trả `FILE_TOO_LARGE` từng tệp |
| Image `minio/mc`, `pgvector/pgvector:pg16` đổi tag | `make up` lỗi | Ghim tag cụ thể `[Verify]` khi viết |
| Cổng 5432/9000/8080 bị chiếm trên máy dev | Không khởi động được | Cho phép đổi cổng host qua biến trong `.env` `[Proposed]` |
| Máy Windows: kết thúc dòng CRLF trong script | Container lỗi khi chạy shell | `.gitattributes` `* text=auto eol=lf` cho `*.sh`, `Makefile` |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §2, §3.2, §3.3, §5.1
- [SAD](../../design/SAD.md) §2.0, §2.1, §2.3, §3.2.2, §4.3
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.8

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Một developer khác (không phải người làm) chạy được theo README mà không cần hỏi.
