# T-404 — Gắn observability: tracing, metric, log, cảnh báo

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 4 |
| **Loại** | DevOps |
| **User story** | — nền tảng (vận hành, launch gate "cảnh báo hoạt động") |
| **Ưu tiên** | P0 |
| **Ước lượng** | 3 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-003, T-305 |
| **Mở khóa (task chờ task này)** | T-409 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

API và Worker xuất trace OpenTelemetry (nối liền yêu cầu tải lên → việc lập chỉ mục qua `job.payload`), xuất đủ danh mục metric Prometheus của SAD §4.3 tại `/metrics` chỉ trong mạng nội bộ, log JSON có đủ trường chuẩn, và 7 cảnh báo ban đầu được định nghĩa, kiểm thử và gắn kênh nhận.

## 2. Bối cảnh

- SAD §4.3 (Log, Metric, Tracing, danh mục metric tối thiểu, 7 cảnh báo `[Proposed]`), SAD §4.2 (timeout/circuit breaker — metric do `call_upstream()` của [T-305](./T-305-upstream-resilience.md) sinh).
- T-003 đã có log JSON + `X-Request-Id`; task này bổ sung `trace_id`, `service`, `duration_ms`, `error_code` và chuẩn hóa.
- Launch gate ([Implement_plan §8](../Implement_plan.md#8-launch-gate-điều-kiện-lên-production)): "cảnh báo hoạt động". Rủi ro "lộ nội dung qua log" ([§9.2](../Implement_plan.md#92-rủi-ro-kỹ-thuật)): metric/trace/log **không** chứa nội dung.

## 3. Phạm vi

**Trong phạm vi**
- `app/platform/tracing.py`, `app/platform/metrics.py`, chuẩn hóa `app/platform/logging.py`.
- Span cho HTTP, từng bước luồng hỏi, lời gọi ra ngoài, mỗi việc worker; lan truyền `traceparent` qua `job.payload`.
- Toàn bộ metric trong danh mục SAD §4.3 (bảng mục 4) + metric bổ sung tối thiểu để cảnh báo (4) và (7) hoạt động.
- `/metrics` cho API (cổng 8000, chặn ở Nginx) và Worker (cổng riêng); cấu hình OTel Collector + Prometheus cho local (profile tùy chọn) và mẫu cho staging.
- File luật cảnh báo + test luật (`promtool test rules`).

**Ngoài phạm vi** (để tránh làm thừa)
- Chọn/cài công cụ hiển thị (Grafana…) và kho log tập trung của tổ chức `[TBD]` (SAD §6) — chỉ cung cấp định dạng chuẩn và file cấu hình mẫu.
- Dashboard hoàn chỉnh (chỉ một dashboard JSON tối thiểu nếu còn thời gian — không bắt buộc).
- Cơ chế sao lưu (T-408 sinh metric cho cảnh báo 7).

## 4. Thiết kế chi tiết

**File cần tạo/sửa**

| File | Nội dung |
|---|---|
| `backend/app/platform/tracing.py` | `setup_tracing(service: Literal["api","worker"]) -> None`; `inject_trace(payload: dict) -> dict`; `extract_trace(payload: dict) -> Context` |
| `backend/app/platform/metrics.py` | Khai báo **mọi** metric (một nơi duy nhất), `metrics_app()` (ASGI), `start_worker_metrics_server(port)` |
| `backend/app/platform/logging.py` | Processor thêm `service`, `trace_id`, `span_id`; danh sách trường cho phép |
| `backend/app/platform/db_metrics.py` | `refresh_db_gauges()` — cập nhật gauge từ CSDL mỗi 30 s `[Proposed]` (chạy trong Worker) |
| `backend/app/jobs/queue.py` (T-101) | `enqueue()` gọi `inject_trace()`; vòng worker gọi `extract_trace()` |
| `backend/app/answering/service.py` (T-205) | span + `answer_pipeline_duration_seconds` từng `stage` |
| `backend/app/main.py`, `backend/app/worker.py` | gọi `setup_tracing`, mount `/metrics`, middleware HTTP metric |
| `deploy/nginx.conf` | `location = /metrics { deny all; return 404; }` |
| `deploy/observability/otel-collector.yaml`, `prometheus.yml`, `alerts.yml`, `alerts_test.yml` | `[Proposed]` đường dẫn |
| `deploy/docker-compose.yml` | service `otel-collector`, `prometheus` dưới `profiles: ["observability"]` |

**Tracing**

| Span | Thuộc tính cho phép | Cấm |
|---|---|---|
| `HTTP {method} {route}` (auto-instrument FastAPI) | `http.route`, `http.status_code`, `request_id` | query string, body |
| `answer.rewrite`, `answer.embed`, `answer.retrieve`, `answer.generate`, `answer.validate` | `chunks.count`, `answer.type`, `retry` | câu hỏi, câu trả lời, văn bản chunk |
| `upstream.{provider}.{op}` (trong `call_upstream()`) | `provider`, `outcome`, `attempt` | payload |
| `job.{type}` (worker) | `job.id`, `job.attempt`, `document.id` | tên tệp |
| SQLAlchemy (auto) | câu SQL **đã tham số hóa** | giá trị tham số (`db.statement` chỉ chứa placeholder) |

Lan truyền sang Worker `[Proposed — khóa payload]`:

```python
def inject_trace(payload: dict) -> dict:
    carrier: dict[str, str] = {}
    propagate.inject(carrier)                       # W3C traceparent
    return {**payload, "traceparent": carrier.get("traceparent")}

# worker
ctx = extract_trace(job.payload)                    # rỗng → span gốc mới
with tracer.start_as_current_span(f"job.{job.type}", context=ctx): ...
```

Lấy mẫu 100% (SAD §4.3). `OTEL_EXPORTER_OTLP_ENDPOINT` trống → không xuất (local), không lỗi.

**Metric** (đủ danh mục SAD §4.3 — tên giữ nguyên):

| Metric | Loại | Nơi ghi |
|---|---|---|
| `http_request_duration_seconds{route,status}` | histogram | middleware HTTP (dùng **route template**, không dùng path thật) |
| `answer_pipeline_duration_seconds{stage}` | histogram | `AnswerService`; `stage` ∈ `rewrite, embed, retrieve, generate, validate, total` |
| `answers_total{type}` | counter | `AnswerService`; `type` ∈ `answered, not_found, error` |
| `citation_validation_failures_total` | counter | `CitationValidator` lần sai |
| `llm_tokens_total{direction}`, `embedding_tokens_total` | counter | adapter AI / `AnswerService`; `direction` ∈ `in, out` |
| `upstream_requests_total{provider,outcome}`, `circuit_breaker_state{provider}` | counter / gauge | `call_upstream()` (T-305) — kiểm tra đã có, gắn vào registry chung |
| `job_queue_depth{type}`, `job_age_seconds`, `jobs_failed_total{type}` | gauge / gauge / counter | `refresh_db_gauges()`; `jobs_failed_total` tại `JobQueue.fail()` khi hết lượt |
| `documents_by_status{status}` | gauge | `refresh_db_gauges()` |
| `db_connections_in_use`, `db_query_duration_seconds` | gauge / histogram | pool SQLAlchemy event hooks |
| `rate_limited_total` | counter | T-306 khi trả `429` |
| `access_denied_total{reason}` | counter | nơi ghi `access_denied` (T-110); `reason` ∈ `unauthenticated, unauthorized` |
| `documents_processing_oldest_seconds` `[Proposed]` | gauge | `refresh_db_gauges()` — cần cho cảnh báo (4) "tài liệu PROCESSING > 30 phút" |

Nhãn chỉ có tập giá trị hữu hạn (không `user_id`, không `document_id`). Mỗi container API chạy 1 tiến trình Uvicorn `[Proposed]` để không cần chế độ multiprocess của `prometheus_client`.

```sql
-- refresh_db_gauges()
SELECT type, count(*) FROM job WHERE status = 'queued' GROUP BY type;
SELECT coalesce(extract(epoch FROM now() - min(run_after)), 0) FROM job WHERE status = 'queued';
SELECT status, count(*) FROM document GROUP BY status;
SELECT coalesce(extract(epoch FROM now() - min(uploaded_at)), 0) FROM document WHERE status = 'PROCESSING';
```

**Log** — trường chuẩn (SAD §4.3): `timestamp`, `level`, `service`, `request_id`, `trace_id`, `user_id`, `route`, `status`, `duration_ms`, `error_code`. Một dòng "access log" mỗi yêu cầu. Processor cuối cùng loại bỏ khóa không thuộc danh sách cho phép ở mức INFO (`question`, `content`, `text`, `filename`… bị bỏ) `[Proposed]`.

**Cảnh báo ban đầu** (`deploy/observability/alerts.yml`):

| # | Tên | Biểu thức (rút gọn) | `for` |
|---|---|---|---|
| 1 | `High5xxRate` | `sum(rate(http_request_duration_seconds_count{status=~"5.."}[5m])) / sum(rate(http_request_duration_seconds_count[5m])) > 0.02` | 5m |
| 2 | `AnswerLatencyP90High` | `histogram_quantile(0.9, sum by (le) (rate(answer_pipeline_duration_seconds_bucket{stage="total"}[15m]))) > ANSWER_P90_ALERT_S` | 15m |
| 3 | `CircuitBreakerOpen` | `max by (provider) (circuit_breaker_state) == 2` (0 đóng, 1 nửa mở, 2 mở `[Proposed]`) | 5m |
| 4 | `JobQueueStuck` | `job_age_seconds > 600 or documents_processing_oldest_seconds > 1800` | 1m |
| 5 | `WeeklyTokenBudget80` | `sum(increase(llm_tokens_total[7d])) + sum(increase(embedding_tokens_total[7d])) >= 0.8 * WEEKLY_TOKEN_BUDGET` | 10m |
| 6 | `DbDiskHigh` | `% đĩa CSDL > 80%` — từ exporter của nền tảng/dịch vụ CSDL quản lý `[TBD: hạ tầng]` | 10m |
| 7 | `BackupFailed` | `time() - backup_last_success_timestamp_seconds > 26*3600` (metric do T-408 ghi qua textfile/pushgateway `[Proposed]`) | 5m |

`ANSWER_P90_ALERT_S` = ngưỡng OQ-014 `[TBD: OQ-014]`, `[Default]` 15 (SDD QAS-01). Ngưỡng và hạn mức được sinh vào file luật từ biến cấu hình lúc triển khai (template), không viết cứng trong code.

## 5. Các bước thực hiện

1. Thêm phụ thuộc `opentelemetry-sdk`, `opentelemetry-exporter-otlp`, `opentelemetry-instrumentation-fastapi`, `-sqlalchemy`, `-httpx`, `prometheus-client` (`[Verify]` phiên bản, giấy phép Apache-2.0).
2. Viết `tracing.py`; gọi trong `main.py`/`worker.py`; test exporter in-memory.
3. Sửa `JobQueue.enqueue()`/vòng worker để lan truyền `traceparent`; test nối trace tải lên → `job.ingest_document`.
4. Viết `metrics.py` với toàn bộ metric; middleware HTTP; mount `/metrics` trên API; `start_worker_metrics_server(WORKER_METRICS_PORT)` trong worker.
5. Gắn metric vào `AnswerService`, `CitationValidator`, adapter AI, `JobQueue.fail()`, rate limiter, `access_denied`; xác nhận metric của `call_upstream()` dùng registry chung.
6. Viết `refresh_db_gauges()` chạy mỗi `DB_GAUGE_INTERVAL_S` trong worker.
7. Chuẩn hóa processor log (trường chuẩn + danh sách cho phép); cập nhật test log của T-003.
8. Chặn `/metrics` trên Nginx; thêm Collector + Prometheus vào compose (profile `observability`).
9. Viết `alerts.yml` + `alerts_test.yml`, chạy `promtool test rules` trong CI; gắn kênh nhận (email/chat của đội vận hành `[TBD]`) trên staging ở T-409.

## 6. Tiêu chí chấp nhận

- [ ] `curl http://api:8000/metrics` (trong mạng compose) trả đủ **mọi** tên metric ở bảng mục 4; `curl http://localhost:8080/metrics` qua Nginx trả `404`.
- [ ] Worker phơi metric tại `:WORKER_METRICS_PORT/metrics`, không ánh xạ cổng ra host trong staging.
- [ ] Tải lên 1 PDF → trong Collector/exporter thử nghiệm thấy **một** trace chứa span `HTTP POST /api/v1/documents` và span `job.ingest_document` cùng `trace_id`.
- [ ] Một câu hỏi tạo đủ 5 span `answer.*` (hoặc 4 khi không có lịch sử — không có `rewrite`) và histogram `answer_pipeline_duration_seconds` có mẫu cho các `stage` tương ứng + `total`.
- [ ] Mọi dòng log JSON của API có `timestamp, level, service, request_id, trace_id, route, status, duration_ms`; log lỗi có `error_code`.
- [ ] Test tự động: sau luồng tải lên + hỏi với chuỗi đánh dấu (canary) trong PDF/câu hỏi, chuỗi đó **không** xuất hiện trong log, nhãn metric, thuộc tính span.
- [ ] `promtool test rules` pass cho cả 7 cảnh báo (mỗi cảnh báo có ít nhất 1 ca kích hoạt và 1 ca không kích hoạt).
- [ ] Trên staging: kích hoạt thử cảnh báo (1) và (3) (giả lập AI lỗi) và nhận được thông báo ở kênh đã cấu hình (bằng chứng cho T-410).

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `inject_trace({})` rồi `extract_trace()` | Cùng `trace_id` |
| Unit | `extract_trace({})` (job cũ không có khóa) | Không lỗi, span gốc mới |
| Unit | Processor log với khóa `question` | Khóa bị loại ở INFO |
| Integration | Gọi `/api/v1/documents/{id}` | `http_request_duration_seconds` có `route="/api/v1/documents/{id}"` (template) |
| Integration | 3 việc `queued`, cũ nhất 700 s | `job_queue_depth`, `job_age_seconds ≈ 700` |
| Integration | AI giả trả 503 liên tục | `upstream_requests_total{outcome="error"}` tăng; `circuit_breaker_state` = mở |
| Integration | Canary trong PDF + câu hỏi | Không có trong log/metric/span |
| Rules | `alerts_test.yml` | 7/7 pass |
| Thủ công (staging) | Giả lập AI lỗi 6 phút | Nhận cảnh báo 3 |

## 8. Cấu hình

| Biến | Giá trị | Ghi chú |
|---|---|---|
| `LOG_LEVEL`, `OTEL_EXPORTER_OTLP_ENDPOINT` | `INFO`, trống ở local | [Implement_plan §3.3](../Implement_plan.md#33-biến-môi-trường) |
| `OTEL_SERVICE_NAME` | `cwd-api` / `cwd-worker` `[Proposed]` | Biến chuẩn OTel |
| `WORKER_METRICS_PORT` `[Proposed]` | `9100` `[Default]` | |
| `DB_GAUGE_INTERVAL_S` `[Proposed]` | `30` `[Default]` | |
| `ANSWER_P90_ALERT_S` `[Proposed]` | `15` `[Default]` | `[TBD: OQ-014]` |
| `WEEKLY_TOKEN_BUDGET` | — | Đã có ở §3.3; cảnh báo 80% (CN-12) |

Cập nhật `deploy/.env.example` với các biến mới.

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Công cụ quan sát của tổ chức chưa chọn `[TBD]` | Không biết nơi xuất OTLP/log | Dùng Collector + Prometheus trong compose; chỉ đổi endpoint khi có |
| Danh mục SAD không có metric cho "tài liệu PROCESSING > 30 phút" | Cảnh báo (4) thiếu dữ liệu | Thêm `documents_processing_oldest_seconds` `[Proposed]` (dùng `uploaded_at` vì bảng `document` không có thời điểm bắt đầu xử lý) |
| Cảnh báo (6) phụ thuộc hạ tầng CSDL | Có thể không có exporter | Ghi rõ trong T-409; dùng cảnh báo của dịch vụ CSDL quản lý nếu có |
| Auto-instrument SQLAlchemy ghi giá trị tham số | Lộ nội dung chunk/câu hỏi | Tắt ghi tham số; test canary bắt buộc |
| OQ-014 chưa có | Ngưỡng cảnh báo (2) tạm | `[Default]` 15 s, đổi qua cấu hình |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §3.3, §4.1, §5.5 (T-404), §8, §9.2
- [SAD](../../design/SAD.md) §4.2, §4.3
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.8 (Quan sát CN-09, CN-14)
- Task liên quan: [T-003](./T-003-fastapi-skeleton.md), [T-101](./T-101-job-queue.md), [T-305](./T-305-upstream-resilience.md), [T-405](./T-405-security-hardening.md), [T-408](./T-408-backup-restore-drill.md), [T-409](./T-409-staging-deployment.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Bảng metric + ý nghĩa cảnh báo được ghi vào runbook vận hành (dùng lại ở T-409, T-410).
