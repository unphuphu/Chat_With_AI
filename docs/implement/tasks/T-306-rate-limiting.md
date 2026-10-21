# T-306 — Giới hạn tốc độ theo người dùng và số truy vấn AI đồng thời

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 3 |
| **Loại** | Backend |
| **User story** | US-C5 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 1 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-207 |
| **Mở khóa (task chờ task này)** | T-307 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Mỗi người dùng bị giới hạn số câu hỏi/phút và số tệp tải lên/phút (token bucket), và toàn hệ thống giới hạn số truy vấn AI chạy đồng thời (semaphore). Vượt giới hạn → `429 RATE_LIMITED` trả ngay, trước khi mở SSE và trước khi gọi AI, để bảo vệ hạn mức và chi phí (RSK-006, QAS-14).

## 2. Bối cảnh

- [SAD §4.2](../../design/SAD.md) "Giới hạn tốc độ": mỗi người dùng 20 câu hỏi/phút và 10 tệp tải lên/phút (token bucket tại proxy hoặc middleware API) `[Proposed]`; tổng số truy vấn AI đồng thời tối đa theo cấu hình (semaphore); vượt → `429 RATE_LIMITED`.
- Mã lỗi SDD §3.5: `RATE_LIMITED` 429 — "Thông báo chờ (QAS-14)".
- [Implement_plan §6.7](../Implement_plan.md#67-giao-thức-sse-của-api-09): lỗi 429 xảy ra **trước** khi mở luồng → HTTP thường với JSON lỗi, không mở SSE.
- Giao diện "Bạn đang hỏi hơi nhanh" ở màn 05-F do T-307 làm.
- Quy mô giả định: ≤ ~10 câu hỏi đồng thời ([SAD §0.1](../../design/SAD.md)).

## 3. Phạm vi

**Trong phạm vi**
- `TokenBucketLimiter` theo `user_id` cho 2 loại: `question` (API-09), `upload` (API-02, tính theo số tệp).
- `AiConcurrencyLimiter` (semaphore không chờ) bao toàn bộ phần gọi AI của API-09.
- Header `Retry-After`; metric `rate_limited_total`.

**Ngoài phạm vi** (để tránh làm thừa)
- Hạn mức token tuần `WEEKLY_TOKEN_BUDGET` và cảnh báo 80% (T-404/T-401).
- Giới hạn tại Nginx (`limit_req`) — có thể bổ sung ở T-405 như lớp phòng thủ thô theo IP.
- Retry/circuit breaker với nhà cung cấp (T-305).

## 4. Thiết kế chi tiết

### 4.1 File

| File | Thay đổi |
|---|---|
| `backend/app/platform/rate_limit.py` | **Mới:** `TokenBucketLimiter`, `AiConcurrencyLimiter`, `RateLimited(AppError)` |
| `backend/app/conversations/router.py` | API-09: kiểm `question` bucket + lấy slot semaphore trước khi trả `StreamingResponse` |
| `backend/app/documents/router.py` | API-02: kiểm `upload` bucket |
| `backend/app/main.py` | Khởi tạo limiter (composition root), tiêm qua dependency |
| `backend/app/platform/config.py` | Biến §8 |

### 4.2 Interface

```python
class RateLimited(AppError):   # code="RATE_LIMITED", http_status=429, có retry_after_s
    def __init__(self, retry_after_s: int, kind: Literal["question", "upload", "concurrency"]): ...

class TokenBucketLimiter:
    def __init__(self, capacity: int, per_seconds: float = 60.0, clock=time.monotonic): ...
    def try_acquire(self, key: UUID, tokens: int = 1) -> float | None:
        """Trả None nếu lấy được; ngược lại số giây cần chờ để đủ `tokens`."""

class AiConcurrencyLimiter:
    def __init__(self, max_concurrent: int): ...
    def try_acquire(self) -> AiSlot | None:      # không chờ
        ...
class AiSlot:
    def release(self) -> None: ...                # lũy đẳng
```

- Token bucket: dung lượng = `RATE_LIMIT_QUESTIONS_PER_MIN` (hoặc `..._UPLOADS_PER_MIN`); nạp lại liên tục `capacity / 60` token/giây; ban đầu đầy (cho phép dồn tối đa `capacity` yêu cầu).
- Lưu trong bộ nhớ tiến trình: `dict[user_id, (tokens, last_refill)]`, có `asyncio.Lock`; dọn khóa không dùng > 10 phút `[Proposed]`.

### 4.3 Thứ tự xử lý API-09

1. Xác thực phiên, chủ hội thoại, kiểm tra body, `NO_READY_DOCUMENTS`, `INVALID_SCOPE` (T-302) — lỗi ở đây **không** tiêu token.
2. `question_bucket.try_acquire(user.id)` → thiếu token → `RateLimited(kind="question")`.
3. `slot = ai_limiter.try_acquire()` → không có slot → `RateLimited(kind="concurrency", retry_after_s=2 [Proposed])` (token đã tiêu **không** hoàn lại `[Proposed]`).
4. Mở SSE; `slot.release()` trong `finally` khi phát `final`/`error` **hoặc** client ngắt kết nối.

### 4.4 API-02 (tải lên)

- Trước khi đọc multipart: yêu cầu bucket còn ≥ 1 token, nếu không → `429` cho cả request.
- Mỗi tệp được nhận tiêu 1 token; khi hết token giữa chừng, các tệp còn lại có kết quả riêng `{"name": "...", "status": "REJECTED", "error": "RATE_LIMITED"}` `[Proposed]` (giữ nguyên tắc kết quả **từng tệp** của API-02) — trạng thái/tên trường theo hợp đồng `items` mà T-103 đã chốt.

### 4.5 Phản hồi 429

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 7
Content-Type: application/json

{ "error": { "code": "RATE_LIMITED",
             "message": "Bạn đang hỏi hơi nhanh. Vui lòng đợi vài giây rồi gửi lại câu hỏi.",
             "requestId": "…" } }
```

`Retry-After` = `ceil(giây cần chờ)`, tối thiểu 1. Không ghi `usage_event` (`question_asked` chỉ ghi khi câu hỏi được xử lý). Câu hỏi bị từ chối **không** được lưu vào `message`.

### 4.6 Metric và log

- `rate_limited_total{kind}` (counter; SAD §4.3 có `rate_limited_total`, nhãn `kind` là `[Proposed]`).
- `ai_concurrency_in_use` (gauge) `[Proposed]` — cho SP-01 và cảnh báo.
- Log INFO: `user_id`, `kind`, `retry_after_s`, `request_id`; không có nội dung câu hỏi.

## 5. Các bước thực hiện

1. Thêm biến cấu hình §8 + `.env.example`.
2. Viết `TokenBucketLimiter` với đồng hồ tiêm được + unit test.
3. Viết `AiConcurrencyLimiter` + test giải phóng slot ở mọi đường thoát (thành công, lỗi, hủy).
4. Gắn vào API-09 theo thứ tự §4.3; đảm bảo `release()` nằm trong `finally` của generator SSE.
5. Gắn vào API-02 theo §4.4.
6. Middleware lỗi: `RateLimited` → thêm header `Retry-After`.
7. Đăng ký metric; integration test.
8. Ghi chú vận hành: với N bản API, giới hạn thực tế ≈ N × cấu hình (§9).

## 6. Tiêu chí chấp nhận

- [ ] Với `RATE_LIMIT_QUESTIONS_PER_MIN=20`: câu hỏi thứ 21 trong cùng 1 phút của **một** người dùng → `429 RATE_LIMITED` có `Retry-After` ≥ 1; người dùng khác cùng lúc vẫn hỏi được.
- [ ] Sau khi chờ `Retry-After` giây → câu hỏi kế tiếp được chấp nhận (đồng hồ giả).
- [ ] Phản hồi 429 là JSON thường (không phải `text/event-stream`), không gọi AI, không lưu `message`, không ghi `question_asked`.
- [ ] Yêu cầu lỗi 401/404/409/422 không tiêu token.
- [ ] Với `MAX_CONCURRENT_AI_REQUESTS=2`: 2 SSE đang chạy + yêu cầu thứ 3 → 429 `kind=concurrency`; khi 1 luồng kết thúc (kể cả client ngắt) → yêu cầu mới được nhận.
- [ ] Tải 12 tệp trong một request với giới hạn 10 → 10 tệp được xử lý, 2 tệp có lỗi `RATE_LIMITED` riêng; request mới ngay sau đó → 429.
- [ ] `rate_limited_total{kind="question"}` tăng đúng số lần từ chối.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | Bucket 20/phút: 20 lần `try_acquire` liên tiếp | Đều `None` |
| Unit | Lần 21 | Trả ≈ 3 s (60/20) |
| Unit | Chờ 3 s (đồng hồ giả) | Lấy được 1 token |
| Unit | `try_acquire(tokens=5)` khi còn 3 | Trả thời gian chờ đủ 2 token |
| Unit | Semaphore: acquire ×2, release ×1, release lặp | Đếm đúng, release lũy đẳng |
| Integration | API-09 lần 21 | 429 + `Retry-After`; DB không có message mới |
| Integration | API-09 bị client ngắt giữa chừng | Slot được trả (gauge về 0) |
| Integration | API-02 12 tệp, giới hạn 10 | 10 thành công/lỗi theo tệp + 2 `RATE_LIMITED` |
| E2E | Thông báo "Bạn đang hỏi hơi nhanh" | Xem T-307, T-311 |

## 8. Cấu hình

| Biến | Mặc định | Ghi chú |
|---|---|---|
| `RATE_LIMIT_QUESTIONS_PER_MIN` | `20` `[Default]` | Có trong plan §3.3 |
| `RATE_LIMIT_UPLOADS_PER_MIN` | `10` `[Default]` | Có trong plan §3.3; tính theo số tệp |
| `MAX_CONCURRENT_AI_REQUESTS` | `10` `[Default]` | **Mới** `[Proposed]` tên biến; giá trị **mỗi tiến trình API**; theo giả định ≤ ~10 câu hỏi đồng thời (SAD §0.1), chỉnh khi có OQ-015 và hạn mức nhà cung cấp (OQ-006) |

Môi trường E2E đặt giới hạn nhỏ (vd. `RATE_LIMIT_QUESTIONS_PER_MIN=3`) để kiểm 429.

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Bộ đếm trong bộ nhớ: với 2 bản API, giới hạn thực tế gấp đôi; khởi động lại thì reset | Bảo vệ chi phí lỏng hơn cấu hình | Chấp nhận ở MVP; đặt `MAX_CONCURRENT_AI_REQUESTS` = tổng mong muốn / số bản; nếu cần chính xác, chuyển sang bảng PostgreSQL hoặc Nginx `limit_req` |
| Giá trị 20/10 chỉ là `[Proposed]` | Người dùng thật có thể bị chặn | Theo dõi `rate_limited_total`; chỉnh bằng cấu hình |
| Số người dùng `[TBD: OQ-015]` | Định cỡ semaphore | Dùng mặc định, xem lại ở Sprint 4 |
| Cách xử lý từng tệp khi hết token giữa request là đề xuất | Hợp đồng API-02 | Thống nhất với người làm T-103 |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §3.3, §5.4, §6.7
- [SAD](../../design/SAD.md) §0.1, §4.2 (giới hạn tốc độ), §4.3 (`rate_limited_total`)
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.5 (`RATE_LIMITED`), QAS-14
- [User_Stories](../../design/User_Stories.md) US-C5, §9, §10
- Màn hình: [html_design/05_chat_states.html](../../design/html_design/05_chat_states.html) (khung F), ảnh [chat_ratelimit.png](../../design/images/chat_ratelimit.png)
- Task liên quan: [T-103](./T-103-upload-api.md), [T-207](./T-207-messages-sse-api.md), [T-302](./T-302-document-scope.md), [T-307](./T-307-chat-states.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] `.env.example` có `MAX_CONCURRENT_AI_REQUESTS` kèm chú thích "mỗi tiến trình".
