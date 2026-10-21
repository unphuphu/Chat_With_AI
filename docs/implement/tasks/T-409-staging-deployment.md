# T-409 — Triển khai staging: rolling deploy, graceful shutdown, migration, rollback

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 4 |
| **Loại** | DevOps |
| **User story** | — nền tảng (DoD "Demo được trên staging"; launch gate chạy trên staging) |
| **Ưu tiên** | P0 |
| **Ước lượng** | 2 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-404 |
| **Mở khóa (task chờ task này)** | T-408, T-410 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Có môi trường staging giống production (SAD §4.2 "triển khai tham chiếu"), triển khai được một phiên bản bất kỳ bằng một lệnh, theo kiểu cuốn chiếu không gián đoạn (≥ 2 bản API, chờ luồng SSE ≤ 60 s khi dừng), chạy migration theo Expand/Contract trước khi đổi mã, và quay lui về phiên bản trước đã được diễn tập. Bí mật lấy từ secret manager.

## 2. Bối cảnh

- SAD §4.2: 1 máy chủ/VM: reverse proxy, API ×2, Worker ×1–2; PostgreSQL + kho tệp là dịch vụ quản lý hoặc có sao lưu; `restart: unless-stopped`; rolling + `health/ready`; graceful shutdown chờ SSE ≤ 60 s; Worker dừng nhận việc mới rồi hoàn tất việc đang chạy; Expand/Contract; giữ ảnh container phiên bản trước để quay lui. SAD AD-10 (container, 1 VM).
- SAD §4.1.2 (TLS ≥ 1.2, HSTS), §4.1.3 (bí mật từ secret manager, không trong ảnh/mã/log). Blueprint §3.8: staging dùng bộ tài liệu mẫu/đã ẩn thông tin (DEP-001); dữ liệu thật **không** dùng ở dev.
- Đầu vào: compose/nginx của [T-002](./T-002-docker-compose-local-env.md), observability của [T-404](./T-404-observability.md), header bảo mật của [T-405](./T-405-security-hardening.md).

## 3. Phạm vi

**Trong phạm vi**
- Cấu hình staging (`deploy/staging/`), build + đẩy ảnh có tag git SHA trong CI.
- Script triển khai, migration, quay lui; graceful shutdown cho API (SSE) và Worker.
- Kiểm tra tương thích migration (mã N-1 chạy trên lược đồ N).
- Smoke test sau triển khai; diễn tập rollback có biên bản.
- Gắn kênh nhận cảnh báo (T-404) trên staging.

**Ngoài phạm vi** (để tránh làm thừa)
- Production và HA nhiều node/Kubernetes (AD-10).
- Sao lưu/khôi phục (T-408).
- Chọn nhà cung cấp AI (T-208, OQ-006): staging chạy `AI_PROVIDER=fake` cho tới khi OQ-006 được duyệt.

## 4. Thiết kế chi tiết

**File cần tạo/sửa** `[Proposed]` đường dẫn trong `deploy/`:

| File | Nội dung |
|---|---|
| `deploy/staging/docker-compose.staging.yml` | `proxy`, `api-1`, `api-2`, `worker-1`, (`worker-2` tùy chọn), `otel-collector`, `prometheus`; `restart: unless-stopped`; ảnh `…/cwd-backend:${IMAGE_TAG}`, `…/cwd-web:${IMAGE_TAG}`; không ánh xạ cổng CSDL/metric ra host |
| `deploy/staging/nginx.staging.conf` | TLS, HSTS, `upstream api { server api-1:8000 max_fails=1 fail_timeout=5s; server api-2:8000 max_fails=1 fail_timeout=5s; }`, `proxy_next_upstream error timeout http_503` (chỉ cho yêu cầu không phải POST hỏi), giữ khối SSE `proxy_buffering off; proxy_read_timeout 120s` |
| `deploy/scripts/deploy.sh` | `deploy.sh <git-sha>` |
| `deploy/scripts/rollback.sh` | `rollback.sh` → triển khai lại SHA trước (đọc `deploy/staging/.last_successful`) |
| `deploy/scripts/smoke.sh` | smoke test sau triển khai |
| `deploy/scripts/fetch_secrets.sh` | lấy bí mật từ secret manager vào biến môi trường của tiến trình compose (không ghi đĩa ở dạng rõ hoặc ghi vào tmpfs, quyền 600) |
| `backend/app/main.py` | trạng thái "đang dừng": khi nhận SIGTERM → `/health/ready` trả 503 ngay; theo dõi số luồng SSE đang mở |
| `backend/app/worker.py` | SIGTERM → ngừng `claim()`, chờ việc đang chạy xong tối đa `WORKER_SHUTDOWN_TIMEOUT_S`, rồi thoát |
| `.github/workflows/ci.yml` | job `build-images` (tag SHA), job `migration-compat` |
| `docs/implement/runbooks/deploy.md` `[Proposed]` | runbook + biên bản diễn tập rollback |

**Trình tự `deploy.sh <sha>`**

1. `fetch_secrets.sh`; kiểm ảnh `<sha>` tồn tại trong registry.
2. **Migration (expand)**: chạy container một lần `alembic upgrade head` với `MIGRATION_DATABASE_URL`; lỗi → dừng, không đổi mã.
3. **API cuốn chiếu**, lần lượt `api-1` rồi `api-2`:
   a. Gửi SIGTERM cho bản cũ (`docker compose stop -t 75 api-1`) → bản cũ trả `ready=503`, Nginx thôi gửi yêu cầu mới (passive check), Uvicorn ngừng nhận kết nối, chờ yêu cầu/luồng SSE đang chạy ≤ `SHUTDOWN_GRACE_S` (60 s), sau đó đóng.
   b. Khởi động bản mới `IMAGE_TAG=<sha> docker compose up -d --no-deps api-1`.
   c. Chờ `/health/ready` = 200 (tối đa 60 s, thăm dò 2 s); quá hạn → dừng triển khai, chạy `rollback.sh`.
4. **Worker**: SIGTERM bản cũ (`stop -t <WORKER_SHUTDOWN_TIMEOUT_S + 15>`), bản mới lên. Việc bị cắt ngang được vòng quét "mồ côi" (T-101) đưa về `queued`; handler lũy đẳng.
5. `smoke.sh`; đạt → ghi `<sha>` vào `.last_successful`; không đạt → `rollback.sh`.
6. **Contract** (dọn cột/bảng cũ) chỉ trong bản phát hành **sau**, khi không còn mã nào dùng phần cũ.

**Graceful shutdown API** `[Proposed]` chi tiết: `uvicorn --timeout-graceful-shutdown 60`; handler `lifespan` đặt cờ `shutting_down=True`; `/health/ready` đọc cờ → 503; luồng SSE đang mở được phép chạy tới `final` hoặc tới hạn 60 s (`ANSWER_TIMEOUT_S` = 60 nên hầu hết luồng kết thúc trước hạn); luồng bị cắt → client nhận lỗi mạng và hiển thị trạng thái "mất kết nối" của T-307 (câu hỏi được giữ để gửi lại). `stop -t 75` lớn hơn 60 s để Docker không SIGKILL sớm.

**Quy tắc Expand/Contract** (checklist review PR có migration):
- Chỉ thêm (bảng, cột cho phép NULL hoặc có mặc định, chỉ mục `CONCURRENTLY` khi bảng lớn); không đổi tên/xóa cột trong cùng bản với mã mới.
- Mọi migration có `downgrade()` hoặc ghi chú `# irreversible: <lý do>`.
- Job CI `migration-compat`: dựng CSDL ở `head`, chạy test tích hợp của **mã `main` trước đó** (N-1) → phải pass `[Proposed]`.

**Smoke test (`smoke.sh`)**: `/health/live`, `/health/ready` = 200; trang `/` trả `index.html` với `Cache-Control: no-cache` và header CSP; đăng nhập (dev hoặc OIDC test user) → `GET /api/v1/auth/session` 200; `GET /api/v1/documents` 200; hỏi 1 câu trên tài liệu mẫu → sự kiện `final`; `GET /api/v1/reports/weekly` với tài khoản SPONSOR 200; `/metrics` qua proxy 404.

**Bí mật** (SAD §4.1.3): `DATABASE_URL`, `MIGRATION_DATABASE_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, khóa ký phiên, bí mật OIDC, khóa API AI — chỉ lấy từ secret manager của nền tảng `[TBD: hạ tầng]`; không có trong ảnh (`docker history` sạch), repo, log; mỗi môi trường một bộ; xoay vòng = cập nhật secret + `deploy.sh` cùng SHA (không build lại).

## 5. Các bước thực hiện

1. Chuẩn bị VM staging (Docker, TLS certificate, DNS), CSDL PostgreSQL 16 + pgvector (dịch vụ quản lý hoặc container có volume + sao lưu — chốt cùng T-408), bucket S3 riêng tư, secret manager.
2. Thêm job CI build/đẩy ảnh `cwd-backend`, `cwd-web` tag SHA.
3. Viết compose + nginx staging; bật TLS/HSTS; chặn `/metrics`.
4. Cài đặt graceful shutdown API (cờ, readiness 503) và Worker (ngừng claim); test tích hợp.
5. Viết `deploy.sh`, `rollback.sh`, `smoke.sh`, `fetch_secrets.sh`.
6. Thêm job `migration-compat` vào CI.
7. Triển khai bản đầu; nạp tài liệu mẫu DEP-001 (`make seed` tương đương), tạo tài khoản MEMBER/SPONSOR/ADMIN thử.
8. Gắn kênh nhận cảnh báo của T-404; kích hoạt thử cảnh báo (1)/(3).
9. **Diễn tập rollback**: triển khai SHA B (có migration expand) → `rollback.sh` về SHA A **không** downgrade lược đồ → smoke pass; ghi thời gian và kết quả vào biên bản.
10. **Thử không gián đoạn**: trong lúc `deploy.sh`, chạy script tải nhẹ (k6/Locust: 1 câu hỏi/2 s + `GET /documents` 5/s) → ghi số lỗi.

## 6. Tiêu chí chấp nhận

- [ ] `deploy/scripts/deploy.sh <sha>` triển khai staging từ đầu đến cuối không thao tác tay, kết thúc bằng smoke pass.
- [ ] Trong lúc triển khai với tải nhẹ: 0 lỗi 5xx cho `GET`, 0 luồng SSE bị cắt khi luồng kết thúc trong ≤ 60 s kể từ SIGTERM.
- [ ] Gửi SIGTERM cho một bản API: `/health/ready` của bản đó trả 503 trong ≤ 1 s; tiến trình thoát trong ≤ 60 s sau khi luồng SSE cuối kết thúc.
- [ ] Worker nhận SIGTERM khi đang `ingest_document`: không nhận việc mới; việc hiện tại hoặc hoàn tất, hoặc được đưa về `queued` và hoàn tất sau khi bản mới chạy (tài liệu cuối cùng `READY`, không chunk trùng).
- [ ] Job CI `migration-compat` chạy trên mọi PR có migration và pass.
- [ ] Diễn tập rollback thành công trong ≤ 15 phút `[Proposed]`, không downgrade lược đồ; biên bản lưu trong runbook.
- [ ] `docker history` của ảnh và `git grep` repo không chứa bí mật; `.env` staging không được commit.
- [ ] Staging dùng TLS ≥ 1.2, có HSTS; cổng 5432, metric, MinIO console không truy cập được từ ngoài VM.
- [ ] Cảnh báo thử nghiệm được nhận ở kênh đã cấu hình.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Integration | API nhận SIGTERM giữa luồng SSE (FakeLlm trễ 5 s) | Luồng nhận `final`; `/health/ready` = 503 trong lúc chờ |
| Integration | API nhận SIGTERM, luồng SSE quá 60 s | Đóng luồng; client nhận lỗi mạng, tin nhắn trợ lý không lưu |
| Integration | Worker nhận SIGTERM khi đang xử lý | Ngừng `claim()`; việc hoàn tất hoặc về `queued` |
| CI | `migration-compat` với migration xóa cột (cố ý) | Fail |
| Thủ công (staging) | `deploy.sh` + tải nhẹ | Theo AC |
| Thủ công (staging) | `rollback.sh` | Smoke pass, bản A chạy trên lược đồ mới |
| Thủ công (staging) | Quét cổng từ ngoài VM | Chỉ 443 (và 80 chuyển hướng) mở |

## 8. Cấu hình

| Biến | Giá trị staging | Ghi chú |
|---|---|---|
| `IMAGE_TAG` `[Proposed]` | git SHA | |
| `SHUTDOWN_GRACE_S` `[Proposed]` | `60` | SAD §4.2 |
| `WORKER_SHUTDOWN_TIMEOUT_S` `[Proposed]` | `150` `[Default]` | > timeout trích PDF 120 s |
| `APP_ENV` | `staging` | T-405 |
| `AUTH_MODE` | `oidc` khi có OQ-018; nếu chưa có, cần ngoại lệ được Tech Lead duyệt cho `dev` trên staging nội bộ | `[TBD: OQ-018]` |
| `AI_PROVIDER` | `fake` cho tới khi OQ-006 duyệt | [Implement_plan §9.1](../Implement_plan.md#91-quyết-định-cần-có-và-ảnh-hưởng-tới-lập-trình) |
| `MAX_UPLOAD_MB`, `MAX_PAGES`, `RELEVANCE_THRESHOLD`, … | như [§3.3](../Implement_plan.md#33-biến-môi-trường) | Thay `[Default]` khi OQ chốt |
| Bí mật | từ secret manager | SAD §4.1.3 |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| OQ-018 chưa có IdP → staging phải chạy `AUTH_MODE=dev`, xung đột với kiểm tra khởi động của T-405 | Không triển khai được hoặc staging thiếu xác thực thật | Ngoại lệ có thời hạn (`APP_ENV=staging-dev` `[Proposed]`) + giới hạn mạng nội bộ; ghi vào launch gate là chưa đạt |
| Hạ tầng staging (VM, secret manager, registry) chưa có `[TBD]` | Chặn task | Tech Lead yêu cầu sớm từ đầu Sprint 4 |
| Nginx OSS không có health check chủ động | Có thể gửi yêu cầu tới bản đang dừng | Readiness 503 + `max_fails`/`proxy_next_upstream`; dừng từng bản một |
| `proxy_next_upstream` với POST hỏi có thể gửi lặp | Câu hỏi bị xử lý 2 lần | Không bật `next_upstream` cho `POST` (`non_idempotent` tắt — mặc định Nginx) |
| OQ-017 (khả dụng) | Có thể đòi HA cao hơn 1 VM | Giữ AD-10; xem lại khi OQ-017 chốt |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §3.2, §3.3, §4.5 (Demo trên staging), §5.5 (T-409), §8
- [SAD](../../design/SAD.md) §4.1.2, §4.1.3, §4.2 (triển khai, migration, quay lui), AD-10
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.8 (môi trường)
- Task liên quan: [T-002](./T-002-docker-compose-local-env.md), [T-101](./T-101-job-queue.md), [T-207](./T-207-messages-sse-api.md), [T-307](./T-307-chat-states.md), [T-404](./T-404-observability.md), [T-405](./T-405-security-hardening.md), [T-408](./T-408-backup-restore-drill.md), [T-410](./T-410-launch-gate-uat.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Runbook triển khai/rollback được một thành viên khác (không phải người viết) làm theo thành công.
