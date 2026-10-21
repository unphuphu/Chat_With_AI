# T-101 — Xây dựng hàng đợi việc `JobQueue` trên PostgreSQL (`SKIP LOCKED`)

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 1 |
| **Loại** | Backend |
| **User story** | US-A3 (nền tảng cho xử lý tài liệu, xóa, thử lại) |
| **Ưu tiên** | P0 |
| **Ước lượng** | 2 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-004 |
| **Mở khóa (task chờ task này)** | T-103, T-104, T-106, T-112, T-407 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Có một hàng đợi việc bền vững nằm trong bảng `job` của PostgreSQL: service nghiệp vụ `enqueue()` **trong cùng giao dịch** với thay đổi dữ liệu; tiến trình Worker `claim()` việc bằng `FOR UPDATE SKIP LOCKED`, gọi handler đã đăng ký, `complete()` hoặc `fail()` với lùi thời gian có nhiễu; việc "mồ côi" tự được đưa về hàng đợi.

## 2. Bối cảnh

- SAD AD-06: không dùng Redis/RabbitMQ; hàng đợi là bảng `job` (DDL ở [SAD §3.1](../../design/SAD.md#31-chiến-lược-mô-hình-dữ-liệu-cốt-lõi), đã tạo ở T-004).
- Thiết kế worker: [SAD §2.2](../../design/SAD.md#22-tầng-ứng-dụng--logic-nghiệp-vụ-cmp-03cmp-10-cmp-20) (bảng "Worker bất đồng bộ") và [Implement_plan §6.3](../Implement_plan.md#63-hàng-đợi-việc).
- Người dùng chính: `ingest_document` (T-104), `purge_document` (T-106), thử lại (T-112), `reindex_all` (T-208), dọn dẹp (T-407).
- Phục vụ BR-003 (trạng thái xử lý luôn tiến triển, không "kẹt" âm thầm — CN-08).

## 3. Phạm vi

**Trong phạm vi**
- Module `backend/app/jobs/`: `JobQueue`, mô hình `Job`, lỗi `TransientJobError`/`PermanentJobError`, sổ đăng ký handler.
- Vòng lặp worker trong `backend/app/worker.py` (composition root): claim → dispatch → complete/fail; quét mồ côi mỗi phút; tắt nhẹ nhàng (SIGTERM).
- Đồng thời N việc/worker (mặc định 2).
- Test tích hợp với PostgreSQL thật (Testcontainers).

**Ngoài phạm vi**
- Handler nghiệp vụ cụ thể (T-104, T-106, T-208, T-407).
- Metric `job_queue_depth`, `job_age_seconds`, `jobs_failed_total` và nối `trace_id` (T-404) — chỉ chừa chỗ: `payload` cho phép khóa `trace_id`.
- `LISTEN/NOTIFY` (để sau, plan §6.3).

## 4. Thiết kế chi tiết

**File cần tạo/sửa**

| File | Nội dung |
|---|---|
| `backend/app/jobs/__init__.py` | Xuất `JobQueue`, `Job`, `register_handler`, lỗi |
| `backend/app/jobs/models.py` | `Job` (dataclass/Pydantic): `id, type, payload, status, attempts, max_attempts, run_after, locked_by, locked_at, last_error` |
| `backend/app/jobs/queue.py` | Lớp `JobQueue` |
| `backend/app/jobs/registry.py` | Sổ đăng ký handler theo `type` |
| `backend/app/jobs/errors.py` | `TransientJobError`, `PermanentJobError` |
| `backend/app/jobs/backoff.py` | `compute_delay(attempts) -> timedelta` |
| `backend/app/worker.py` | Vòng lặp worker, khởi tạo adapter, đăng ký handler |
| `backend/tests/integration/jobs/test_queue.py`, `backend/tests/unit/jobs/test_backoff.py` | Test |

**Chữ ký**

```python
class JobQueue:
    async def enqueue(self, session: AsyncSession, type: str, payload: dict,
                      *, run_after: datetime | None = None, max_attempts: int = 5) -> UUID: ...
        # KHÔNG tự commit: dùng session của use case gọi tới (cùng giao dịch với document/audit_log)
    async def claim(self, worker_id: str) -> Job | None: ...        # giao dịch riêng, ngắn
    async def complete(self, job_id: UUID) -> None: ...             # status='succeeded'
    async def fail(self, job: Job, error: Exception) -> FailOutcome: ...  # RETRY_SCHEDULED | EXHAUSTED
    async def sweep_orphans(self, older_than: timedelta = timedelta(minutes=15)) -> int: ...

JobHandler = Callable[[dict], Awaitable[None]]
OnExhausted = Callable[[dict, str], Awaitable[None]]   # vd. T-104 đặt document FAILED + failure_reason

def register_handler(type: str, handler: JobHandler, *, on_exhausted: OnExhausted | None = None) -> None: ...
```

**SQL claim** (nguyên văn [Implement_plan §6.3](../Implement_plan.md#63-hàng-đợi-việc)):

```sql
UPDATE job SET status = 'running', locked_by = :worker, locked_at = now(), attempts = attempts + 1
WHERE id = (
  SELECT id FROM job
  WHERE status = 'queued' AND run_after <= now()
  ORDER BY run_after
  FOR UPDATE SKIP LOCKED
  LIMIT 1
)
RETURNING *;
```

**SQL fail / sweep**

```sql
-- lỗi tạm thời, còn lượt
UPDATE job SET status='queued', run_after = now() + :delay, locked_by=NULL, locked_at=NULL, last_error=:err
WHERE id=:id;
-- hết lượt hoặc lỗi vĩnh viễn
UPDATE job SET status='failed', locked_by=NULL, locked_at=NULL, last_error=:err WHERE id=:id;
-- quét mồ côi (mỗi 60 s)
UPDATE job SET status='queued', locked_by=NULL, locked_at=NULL
WHERE status='running' AND locked_at < now() - interval '15 minutes';
```

**Quy tắc**
- Trạng thái job: `queued → running → succeeded | queued (thử lại) | failed`.
- Backoff: `delay = min(300 s, 5 s · 2^attempts) × uniform(0.8, 1.2)` (± 20%). `attempts` là số đã tăng khi claim.
- `TransientJobError` (429/5xx/timeout từ dịch vụ ngoài) → thử lại nếu `attempts < max_attempts`; ngược lại `failed` + gọi `on_exhausted`.
- `PermanentJobError` và mọi exception khác ngoài dự kiến → `failed` ngay + `on_exhausted` (không thử lại lỗi lập trình) `[Proposed]`.
- `type` không có handler → `failed`, `last_error='UNKNOWN_JOB_TYPE'`.
- **Hợp đồng lũy đẳng:** mọi handler phải chạy lại an toàn (cùng payload chạy 2 lần → không sinh dữ liệu trùng). Quét mồ côi có thể khiến một việc chạy hai lần; đây là thiết kế "at-least-once".
- `last_error` chỉ chứa mã lỗi + tên exception, **không** chứa nội dung tài liệu; cắt tối đa 1.000 ký tự `[Proposed]`.
- Worker rảnh: ngủ 1–2 s (ngẫu nhiên) rồi claim lại.
- SIGTERM: ngừng claim việc mới, chờ việc đang chạy xong (tối đa thời gian cấu hình), rồi thoát (SAD §4.2).
- `worker_id` = `"{hostname}:{pid}:{slot}"`.

## 5. Các bước thực hiện

1. Viết `backoff.compute_delay()` + test đơn vị (biên 300 s, nhiễu trong ±20%).
2. Viết `Job`, `errors.py`, `registry.py` (đăng ký trùng `type` → `ValueError`).
3. Viết `JobQueue.enqueue()` nhận `AsyncSession` của bên gọi; chèn `job(id=uuid4(), status='queued', run_after=now() hoặc tham số)`.
4. Viết `claim()` bằng SQL trên trong một giao dịch ngắn, commit ngay sau `RETURNING`.
5. Viết `complete()`, `fail()` (phân loại lỗi, tính `delay`, gọi `on_exhausted` trong giao dịch riêng sau khi đánh dấu `failed`).
6. Viết `sweep_orphans()`; worker chạy mỗi 60 s.
7. Viết `backend/app/worker.py`: đọc settings, tạo adapter, đăng ký handler, chạy `WORKER_CONCURRENCY` coroutine claim song song, xử lý SIGTERM. Log JSON có `job_id`, `job_type`, `attempts`, `outcome`, `duration_ms`.
8. Viết test tích hợp (mục 7); thêm biến vào `deploy/.env.example`.

## 6. Tiêu chí chấp nhận

- [ ] Hai worker chạy đồng thời trên 100 job: mỗi job được xử lý đúng 1 lần ở trạng thái `succeeded`, không job nào bị hai worker nhận cùng lúc.
- [ ] `enqueue()` trong một giao dịch bị rollback → không còn dòng `job` nào.
- [ ] Handler ném `TransientJobError` → job về `queued`, `run_after` lùi trong khoảng `[0,8·d; 1,2·d]` với `d = min(300, 5·2^attempts)` giây.
- [ ] Sau `max_attempts` (5) lần lỗi tạm thời → job `failed` và `on_exhausted` được gọi đúng 1 lần.
- [ ] Job `running` có `locked_at` cũ hơn 15 phút được `sweep_orphans()` đưa về `queued`; job `running` mới hơn không bị đụng.
- [ ] Job có `run_after` trong tương lai không bị claim.
- [ ] Worker nhận SIGTERM khi đang xử lý: việc đang chạy hoàn tất, không claim thêm việc.
- [ ] Không có import `app.adapters.*` trong `app/jobs/` (import-linter xanh).

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `compute_delay(1..10)` lặp 1.000 lần | Luôn trong ±20% của `min(300, 5·2^n)`; không vượt 360 s |
| Unit | Đăng ký trùng `type` | `ValueError` |
| Integration | 2 worker × 100 job, handler ghi `job_id` vào bảng tạm | 100 dòng, không trùng |
| Integration | Enqueue rồi rollback | `SELECT count(*) FROM job` = 0 |
| Integration | Handler lỗi tạm thời 5 lần | `status='failed'`, `attempts=5`, `on_exhausted` gọi 1 lần |
| Integration | `PermanentJobError` ở lần 1 | `failed`, `attempts=1` |
| Integration | Job `running`, `locked_at = now() - 16 phút` | Về `queued` sau `sweep_orphans()` |
| Integration | `type='unknown'` | `failed`, `last_error='UNKNOWN_JOB_TYPE'` |

## 8. Cấu hình

| Biến | Mặc định | Ghi chú |
|---|---|---|
| `DATABASE_URL` | plan §3.3 | Dùng chung |
| `WORKER_CONCURRENCY` | `2` `[Proposed]` | SAD §2.2 "mặc định 2 việc/worker"; chưa có trong plan §3.3 — thêm vào `.env.example` |
| `JOB_ORPHAN_TIMEOUT_MIN` | `15` `[Proposed]` | SAD §2.2 |
| `JOB_MAX_ATTEMPTS` | `5` `[Proposed]` | SAD §2.2 |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Handler dài hơn 15 phút (PDF rất lớn) bị quét mồ côi trong khi vẫn chạy | Chạy trùng | Timeout trích PDF 120 s (T-104) giữ handler ngắn; handler lũy đẳng |
| Bảng `job` (SAD §3.1) không có `created_at` | T-404 khó tính `job_age_seconds` | Ghi chú cho T-404; nếu cần, thêm cột bằng migration expand `[Proposed]` |
| Bảng `job` tăng dần | Truy vấn chậm dần | Chỉ mục một phần `job_ready_idx`; dọn job `succeeded` cũ ở T-407 |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §3.1, §4.1, §6.3
- [SAD](../../design/SAD.md) §2.2 (Worker), §3.1 (DDL `job`), §4.2 (graceful shutdown), AD-06
- [User_Stories](../../design/User_Stories.md) US-A3
- Task liên quan: [T-004](./T-004-db-migrations-baseline.md), [T-104](./T-104-ingest-worker.md), [T-106](./T-106-delete-document-purge.md), [T-112](./T-112-retry-failed-document.md), [T-407](./T-407-retention-cleanup.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] README ngắn trong docstring `app/jobs/__init__.py` nêu hợp đồng lũy đẳng cho người viết handler.
