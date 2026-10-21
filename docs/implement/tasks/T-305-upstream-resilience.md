# T-305 — Xây helper `call_upstream()`: timeout, retry, circuit breaker, metric

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 3 |
| **Loại** | Backend |
| **User story** | US-C5 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 2 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-007, T-207 |
| **Mở khóa (task chờ task này)** | T-307, T-404 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Mọi lời gọi ra ngoài (dịch vụ LLM, embedding, kho tệp, IdP) đi qua một helper chung `call_upstream()` có timeout bắt buộc, retry có giới hạn chỉ cho thao tác lũy đẳng (backoff + jitter, tôn trọng `Retry-After`), circuit breaker theo nhà cung cấp AI và metric. Khi dịch vụ AI chậm/sập, người dùng nhận lỗi `UPSTREAM_TIMEOUT`/`UPSTREAM_UNAVAILABLE` nhanh và rõ thay vì treo.

## 2. Bối cảnh

- Quy ước [Implement_plan §4.1](../Implement_plan.md#41-backend): "Luôn có timeout; retry chỉ cho thao tác lũy đẳng; dùng helper chung `call_upstream()` (timeout + retry + circuit breaker + metric)".
- Thông số [SAD §4.2](../../design/SAD.md): timeout, retry, circuit breaker; hành vi lỗi trong luồng hỏi [SAD §3.2.1](../../design/SAD.md) (embedding thử lại 1 lần → `UPSTREAM_UNAVAILABLE`; LLM thử lại 1 lần nếu 429/5xx).
- Mã lỗi SDD §3.5: `UPSTREAM_TIMEOUT` (504), `UPSTREAM_UNAVAILABLE` (503) — người dùng được hỏi lại, không mất câu hỏi (UI ở T-307).
- Metric SAD §4.3: `upstream_requests_total{provider,outcome}`, `circuit_breaker_state{provider}`.

## 3. Phạm vi

**Trong phạm vi**
- `backend/app/platform/upstream.py`: `call_upstream()`, `RetryPolicy`, `CircuitBreaker`, các lỗi.
- Áp dụng trong adapter: `adapters/fake/*` (để test), adapter AI thật (nếu T-208 đã có), `adapters/s3/`, `adapters/oidc/` (nếu có).
- Ánh xạ lỗi sang `AppError` để T-207 phát `event: error` / HTTP 503/504.
- Kịch bản lỗi cho `FakeLlm`/`FakeEmbedding` (timeout, 429 có `Retry-After`, 503, lỗi kết nối).

**Ngoài phạm vi** (để tránh làm thừa)
- Retry của job queue trong worker (T-101: `min(300 s, 5 s·2^n) ± 20%`, tối đa 5 lần).
- Thử lại do `CitationValidator` sai (thuộc `AnswerService`, T-205).
- Dashboard/cảnh báo "circuit breaker mở > 5 phút" (T-404).
- Giới hạn tốc độ người dùng (T-306).

## 4. Thiết kế chi tiết

### 4.1 Bảng thông số (SAD §4.2)

| Thao tác (`operation`) | `provider` | Timeout | Retry tối đa | Lũy đẳng | Breaker |
|---|---|---|---|---|---|
| `embed_query` (đường hỏi) | `embedding` | kết nối 3 s / tổng 15 s | 2 | Có | Có |
| `embed_batch` (worker) | `embedding` | kết nối 3 s / tổng 15 s | 0 trong helper — retry do job queue (5 lần) | Có | Có |
| `rewrite` | `llm` | 15 s | 0 `[Proposed]` (lỗi → fallback câu gốc, T-301) | Có | Có |
| `generate` | `llm` | 60 s | 1, **chỉ khi chưa nhận được đầu ra** và lỗi là 429/5xx/kết nối | Có (không có tác dụng phụ) | Có |
| `filestore_get/put/delete` | `filestore` | 30 s | 2 cho `get`/`delete`; `put` 0 `[Proposed]` | `get`, `delete` | Không |
| `idp_*` | `idp` | 5 s | 1 cho JWKS/discovery | Có | Không |

Lỗi tạm thời = lỗi kết nối, timeout, HTTP 429, HTTP 5xx. Các 4xx khác **không** retry.

### 4.2 Interface

```python
# app/platform/upstream.py
T = TypeVar("T")

@dataclass(frozen=True)
class RetryPolicy:
    max_retries: int
    base_delay_s: float = 0.5        # [Proposed]
    max_delay_s: float = 4.0         # [Proposed]
    jitter: float = 0.2              # ±20%, cùng tỉ lệ với SAD §2.2

class TransientUpstreamError(Exception):
    def __init__(self, status: int | None, retry_after_s: float | None = None): ...
class PermanentUpstreamError(Exception): ...

class UpstreamTimeout(AppError):      # code="UPSTREAM_TIMEOUT", http_status=504
class UpstreamUnavailable(AppError):  # code="UPSTREAM_UNAVAILABLE", http_status=503

async def call_upstream(
    op: Callable[[], Awaitable[T]], *,
    provider: str, operation: str,
    timeout_s: float, retry: RetryPolicy,
    idempotent: bool, breaker: CircuitBreaker | None,
    deadline: float | None = None,   # monotonic; không retry nếu vượt
) -> T: ...
```

Adapter chuyển ngoại lệ SDK thành `TransientUpstreamError` (kèm `retry_after_s` đọc từ header `Retry-After`) hoặc `PermanentUpstreamError`; **lõi nghiệp vụ không thấy ngoại lệ SDK**.

### 4.3 Thuật toán

```python
async def call_upstream(op, *, provider, operation, timeout_s, retry, idempotent, breaker, deadline=None):
    max_retries = retry.max_retries if idempotent else 0
    for attempt in range(max_retries + 1):
        if breaker and not breaker.allow():
            metrics.upstream(provider, operation, "short_circuit"); raise UpstreamUnavailable()
        try:
            result = await asyncio.wait_for(op(), timeout=timeout_s)
            breaker and breaker.record_success(); metrics.upstream(provider, operation, "success")
            return result
        except (asyncio.TimeoutError, TransientUpstreamError) as e:
            breaker and breaker.record_failure()
            outcome = "timeout" if isinstance(e, asyncio.TimeoutError) else "transient_error"
            metrics.upstream(provider, operation, outcome)
            delay = backoff(attempt, retry, getattr(e, "retry_after_s", None))
            if attempt == max_retries or (deadline and monotonic() + delay >= deadline):
                raise UpstreamTimeout() if outcome == "timeout" else UpstreamUnavailable()
            await asyncio.sleep(delay)
        except PermanentUpstreamError:
            breaker and breaker.record_failure(); metrics.upstream(provider, operation, "error")
            raise UpstreamUnavailable()

def backoff(attempt, retry, retry_after_s):
    if retry_after_s is not None:
        return retry_after_s                          # tôn trọng Retry-After
    d = min(retry.max_delay_s, retry.base_delay_s * 2 ** attempt)
    return d * random.uniform(1 - retry.jitter, 1 + retry.jitter)
```

- `asyncio.CancelledError` (client ngắt SSE) **không** bị bắt: lan ra để hủy lời gọi (T-207).
- `Retry-After` lớn hơn thời gian còn lại của `deadline` → không chờ, ném lỗi ngay.
- `deadline` của đường hỏi = thời điểm bắt đầu + `ANSWER_TIMEOUT_S`.

### 4.4 Circuit breaker (mỗi `provider` AI một bộ, trong bộ nhớ tiến trình)

| Trạng thái | Chuyển khi |
|---|---|
| `closed` → `open` | 5 lỗi **liên tiếp**, **hoặc** tỉ lệ lỗi ≥ 50% trong cửa sổ trượt 30 s với ≥ 10 yêu cầu |
| `open` | Từ chối ngay (`UPSTREAM_UNAVAILABLE`) trong 30 s |
| `open` → `half_open` | Hết 30 s |
| `half_open` | Cho **đúng 1** yêu cầu thử; thành công → `closed` (xóa bộ đếm); lỗi → `open` thêm 30 s |

```python
class CircuitBreaker:
    def __init__(self, provider: str, *, consecutive_failures=5, failure_rate=0.5,
                 window_s=30, min_requests=10, open_s=30, clock=time.monotonic): ...
    def allow(self) -> bool: ...
    def record_success(self) -> None: ...
    def record_failure(self) -> None: ...
    @property
    def state(self) -> Literal["closed", "open", "half_open"]: ...
```

Khởi tạo trong composition root (`main.py`, `worker.py`), tiêm vào adapter. Mỗi tiến trình (API ×2, Worker) có breaker riêng — chấp nhận ở MVP.

### 4.5 Metric và log

| Metric | Nhãn | Ghi chú |
|---|---|---|
| `upstream_requests_total` | `provider`, `outcome` = `success\|timeout\|transient_error\|error\|short_circuit` | SAD §4.3; thêm nhãn `operation` `[Proposed]` |
| `circuit_breaker_state` | `provider` | gauge: 0 = closed, 1 = half_open, 2 = open `[Proposed]` |
| `upstream_request_duration_seconds` | `provider`, `operation` | histogram `[Proposed]`, nguồn cho SP-01 |

Log (JSON) mỗi lần retry/mở breaker: `provider`, `operation`, `attempt`, `outcome`, `status`, `delay_ms`, `request_id`. **Không** log payload/câu hỏi/đoạn văn bản.

## 5. Các bước thực hiện

1. Thêm biến cấu hình §8 vào `Settings` và `.env.example`.
2. Viết `CircuitBreaker` với đồng hồ tiêm được + unit test đủ chuyển trạng thái.
3. Viết `call_upstream`, `backoff` + unit test (đồng hồ/`sleep` giả, `random` cố định seed).
4. Đăng ký metric trong `platform/metrics.py`.
5. Bọc mọi lời gọi trong `FakeLlm`, `FakeEmbedding`, adapter S3, (adapter thật/OIDC nếu đã có) bằng `call_upstream` theo bảng §4.1.
6. Thêm kịch bản lỗi vào adapter giả (`timeout`, `http_429(retry_after=2)`, `http_503`, `conn_error`) dùng chung cơ chế kịch bản FakeLlm của T-213.
7. Integration test API-09 với từng kịch bản: kiểm SSE `error` đúng mã, câu hỏi người dùng vẫn lưu, không lưu tin nhắn trợ lý.
8. Ghi vào README backend: "cấm gọi HTTP ra ngoài không qua `call_upstream`" + kiểm import-linter: `httpx`/SDK AI chỉ được import trong `app.adapters.*`.

## 6. Tiêu chí chấp nhận

- [ ] Mọi lời gọi ra ngoài trong `app/adapters/` đi qua `call_upstream` (review + test grep trong CI `[Proposed]`).
- [ ] `generate` treo quá `ANSWER_TIMEOUT_S` → SSE `event: error` `{"code":"UPSTREAM_TIMEOUT"}` trong ≤ timeout + 1 s.
- [ ] `embed_query` lỗi 503 hai lần rồi thành công → câu trả lời bình thường; lỗi 3 lần → `UPSTREAM_UNAVAILABLE`.
- [ ] 429 có `Retry-After: 2` → lần thử tiếp sau ≥ 2 s (đồng hồ giả); `Retry-After` vượt `deadline` → lỗi ngay, không chờ.
- [ ] 400/401 từ nhà cung cấp → không retry, `UPSTREAM_UNAVAILABLE`.
- [ ] 5 lỗi liên tiếp → breaker `open`; yêu cầu thứ 6 bị từ chối trong < 10 ms không gọi adapter; sau 30 s cho đúng 1 yêu cầu thử.
- [ ] 10 yêu cầu trong 30 s với 5 lỗi xen kẽ (không liên tiếp) → breaker `open`.
- [ ] Client ngắt kết nối giữa lúc retry → lời gọi bị hủy, không retry tiếp.
- [ ] `upstream_requests_total` và `circuit_breaker_state` xuất hiện ở `/metrics` với đúng nhãn.
- [ ] Khi LLM sập: thư viện, xem tệp, lịch sử vẫn hoạt động (suy giảm có kiểm soát — SAD §4.2).

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `backoff(0..3)` seed cố định | 0,5 / 1 / 2 / 4 s ± 20%, không vượt 4 s × 1,2 |
| Unit | `idempotent=False`, lỗi tạm thời | Không retry |
| Unit | Breaker: 4 lỗi + 1 thành công + 4 lỗi | Vẫn `closed` (chuỗi liên tiếp reset) |
| Unit | Breaker: tỉ lệ 50% với 9 yêu cầu | Vẫn `closed` (chưa đủ 10) |
| Unit | Breaker `half_open`: 2 yêu cầu đồng thời | Chỉ 1 được đi qua |
| Unit | `CancelledError` trong `op` | Lan ra ngoài, không ghi `failure` |
| Integration | API-09 + `FakeLlm` kịch bản `timeout` | SSE `error` `UPSTREAM_TIMEOUT`; `message` user có, assistant không |
| Integration | API-09 + `FakeEmbedding` `http_503` ×3 | `UPSTREAM_UNAVAILABLE` |
| Integration | Worker `embed_batch` lỗi tạm thời | Job quay về `queued` theo T-101, không retry trong helper |
| E2E | Trạng thái lỗi AI trên UI | Xem T-307 |

## 8. Cấu hình

Tên biến dưới đây là `[Proposed]` (plan §3.3 chỉ có `ANSWER_TIMEOUT_S`); giá trị theo SAD §4.2.

| Biến | Mặc định |
|---|---|
| `ANSWER_TIMEOUT_S` | `60` (timeout `generate` và `deadline` đường hỏi) |
| `LLM_REWRITE_TIMEOUT_S` | `15` (dùng chung với T-301) |
| `EMBEDDING_CONNECT_TIMEOUT_S`, `EMBEDDING_TIMEOUT_S` | `3`, `15` |
| `FILESTORE_TIMEOUT_S`, `IDP_TIMEOUT_S` | `30`, `5` |
| `UPSTREAM_RETRY_BASE_S`, `UPSTREAM_RETRY_MAX_S` | `0.5`, `4` |
| `CB_CONSECUTIVE_FAILURES`, `CB_FAILURE_RATE`, `CB_WINDOW_S`, `CB_MIN_REQUESTS`, `CB_OPEN_S` | `5`, `0.5`, `30`, `10`, `30` |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Breaker trong bộ nhớ mỗi tiến trình | Mỗi bản API mở/đóng độc lập | Chấp nhận ở MVP (lưu lượng thấp) |
| `ANSWER_TIMEOUT_S` vừa là timeout `generate` vừa là tổng ngân sách | Retry `generate` có thể không còn thời gian | Dùng `deadline`; xem lại sau SP-01 (T-309) |
| Ngưỡng thời gian người dùng chấp nhận `[TBD: OQ-014]` | Timeout có thể phải giảm | Mọi giá trị đọc từ cấu hình |
| Hành vi 429/`Retry-After` khác nhau giữa nhà cung cấp (OQ-006) | Adapter thật | T-208 viết test hợp đồng cho ánh xạ lỗi |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §4.1, §5.4, §6.7
- [SAD](../../design/SAD.md) §3.2.1 (hành vi lỗi), §4.2, §4.3
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.5 (mã lỗi), DR-07
- [User_Stories](../../design/User_Stories.md) US-C5, §9
- Task liên quan: [T-007](./T-007-ports-and-fake-adapters.md), [T-207](./T-207-messages-sse-api.md), [T-301](./T-301-follow-up-rewrite.md), [T-307](./T-307-chat-states.md), [T-404](./T-404-observability.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Biến cấu hình mới có trong `.env.example` kèm chú thích nguồn SAD §4.2.
