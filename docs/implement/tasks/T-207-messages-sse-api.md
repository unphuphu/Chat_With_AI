# T-207 — Xây API gửi câu hỏi trả luồng SSE

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 2 |
| **Loại** | Backend |
| **User story** | US-C1 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 2 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-202, T-205 |
| **Mở khóa (task chờ task này)** | T-209, T-211, T-212, T-305, T-306 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

`POST /api/v1/conversations/{id}/messages` (API-09) nhận câu hỏi, lưu tin nhắn người dùng, gọi `AnswerService.ask()` và trả `text/event-stream` gồm các sự kiện `status` → `final` (hoặc `error`) theo Implement_plan §6.7. Lỗi trước khi mở luồng trả HTTP JSON thường. Client ngắt kết nối → hủy lời gọi LLM, không lưu tin nhắn trợ lý.

## 2. Bối cảnh

- SAD §3.2.1 bước 1–5, 14 và bảng "Hành vi lỗi trong luồng"; SAD §2.4 API-09; Implement_plan §6.7.
- AD-07: MVP **không phát sự kiện `token`** (dù bảng API-09 của SAD §2.4 có liệt kê) — chỉ `status` và `final`; `final` là kết quả có hiệu lực duy nhất.
- Proxy phải tắt đệm cho đường dẫn này (`proxy_buffering off`, `proxy_read_timeout 120s`) — đã có ở T-002 (Implement_plan §3.2).
- SSE qua `POST` → client dùng `fetch` + `ReadableStream` (T-209), không dùng `EventSource`.

## 3. Phạm vi

**Trong phạm vi**
- Router `backend/app/answering/router.py`, helper SSE `backend/app/platform/sse.py`.
- Kiểm tra trước luồng: phiên, CSRF, vai trò, body, chủ hội thoại, `NO_READY_DOCUMENTS`.
- Nhận `documentIds` trong body và chuyển nguyên cho `ask(scope=…)`; kiểm tra đầy đủ phạm vi + giao diện chọn phạm vi là T-302.
- Phát hiện ngắt kết nối và hủy task.

**Ngoài phạm vi** (để tránh làm thừa)
- Giới hạn tốc độ `429 RATE_LIMITED` (T-306); retry/circuit breaker (T-305).
- Sự kiện telemetry (T-212). Viết lại câu hỏi (T-301).
- Graceful shutdown chờ luồng SSE ≤ 60 s (T-409).

## 4. Thiết kế chi tiết

**Request** (Pydantic, `extra="forbid"`):

```python
class AskRequest(BaseModel):
    question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    documentIds: list[UUID] | None = Field(default=None, max_length=200)   # [Proposed] giới hạn
```

**Thứ tự kiểm trước khi mở luồng** (lỗi → JSON `{ "error": { "code", "message", "requestId" } }`, `Content-Type: application/json`):

| # | Kiểm | Lỗi |
|---|---|---|
| 1 | Phiên hợp lệ | `401 UNAUTHENTICATED` |
| 2 | `X-CSRF-Token` + `Origin` | `403 FORBIDDEN` |
| 3 | Vai trò `MEMBER` (`require_role`) | `403 FORBIDDEN` |
| 4 | Body hợp lệ | `422 VALIDATION_ERROR` `[Proposed]` |
| 5 | Hội thoại tồn tại và thuộc người gọi (`ConversationService.get_owned`) | `404 NOT_FOUND` `[Proposed]` |
| 6 | Có ≥ 1 tài liệu `READY` trong phạm vi (`DocumentService.count_ready(scope)`) | `409 NO_READY_DOCUMENTS` |
| 7 | *(T-306)* giới hạn tốc độ | `429 RATE_LIMITED` |

Sau bước 6: `add_user_message()` + `set_title_if_empty()` (một giao dịch, T-202) → mở luồng.

**Phản hồi luồng:** `200`, header `Content-Type: text/event-stream; charset=utf-8`, `Cache-Control: no-cache`, `X-Accel-Buffering: no`, `X-Request-Id`.

```text
event: status
data: {"stage":"retrieving"}

event: status
data: {"stage":"generating"}

event: final
data: {"messageId":"…","answerType":"ANSWERED","content":"… [1] … [2]","citations":[{"ordinal":1,"documentId":"…","documentName":"Hợp đồng khung đối tác A.pdf","page":12}],"responseTimeMs":8200}
```

- `NOT_FOUND` do Lớp 1: chỉ `status: retrieving` → `final` (không có `generating`); `content: ""`, `citations: []`.
- Lỗi sau khi đã mở luồng: `event: error` + `data: {"code":"UPSTREAM_TIMEOUT"|"UPSTREAM_UNAVAILABLE"|"INTERNAL_ERROR","message":"<thân thiện, tiếng Việt từ catalog lỗi>","requestId":"…"}` rồi đóng luồng. `INTERNAL_ERROR` là mã `[Proposed]` (thống nhất với T-003). Không có `final` sau `error`.
- Mỗi `data` là **một dòng** JSON (`json.dumps(..., ensure_ascii=False, separators=(",", ":"))`), kết thúc bằng `\n\n`.

**Helper SSE:**

```python
def sse_event(event: Literal["status", "final", "error"], data: dict) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, separators=(',', ':'))}\n\n".encode()
```

**Vòng phát + hủy khi ngắt** (phác thảo):

```python
async def stream(request, user, conversation, body, started_at):
    queue: asyncio.Queue[bytes | None] = asyncio.Queue()
    async def on_stage(stage): await queue.put(sse_event("status", {"stage": stage}))
    async def run():
        try:
            r = await answer_service.ask(user=user, conversation=conversation, question=body.question,
                                         scope=body.documentIds, started_at=started_at, on_stage=on_stage)
            await queue.put(sse_event("final", to_final_payload(r)))
        except AppError as e:
            await queue.put(sse_event("error", e.to_payload(request_id)))
        except Exception:
            log.exception("answer_failed")              # không log nội dung
            await queue.put(sse_event("error", internal_error(request_id)))
        finally:
            await queue.put(None)
    task = asyncio.create_task(run())
    watcher = asyncio.create_task(cancel_on_disconnect(request, task, poll_s=0.5))
    try:
        while (chunk := await queue.get()) is not None:
            yield chunk
    finally:
        watcher.cancel()
        if not task.done():
            task.cancel()                               # generator bị đóng do ngắt kết nối
```

- `cancel_on_disconnect`: lặp `await request.is_disconnected()`; `True` → `task.cancel()`. Hủy lan tới `httpx` trong adapter → lời gọi LLM bị hủy; `AnswerService` không bắt `CancelledError` nên không lưu gì (T-205).
- Ghi log `client_disconnected` (có `request_id`, `stage` hiện tại) khi hủy.
- Không gửi heartbeat ở MVP; `proxy_read_timeout 120s` > `ANSWER_TIMEOUT_S` (60 s).

## 5. Các bước thực hiện

1. Viết `platform/sse.py` + test đơn vị định dạng.
2. Thêm `DocumentService.count_ready(scope: list[UUID] | None) -> int` (module `documents`).
3. Viết `answering/router.py` với kiểm tra theo bảng, rồi `StreamingResponse(stream(...), media_type="text/event-stream")`.
4. Viết `to_final_payload()` ánh xạ `AnswerResult` → camelCase như §6.7.
5. Viết `cancel_on_disconnect()`; dùng `FakeLlm(delay_s=…)` (T-007) để test hủy.
6. Đăng ký router trong `main.py`; kiểm route có trong test bảo vệ route (T-109).
7. Test tích hợp qua `httpx.AsyncClient` (ASGI) đọc luồng; test thủ công qua Nginx (`curl -N`) xác nhận `status` đến trước `final` (không bị gom).

## 6. Tiêu chí chấp nhận

- [ ] Câu hỏi hợp lệ → luồng có đúng thứ tự `status(retrieving)`, `status(generating)`, `final`; `final.citations` không rỗng khi `answerType = ANSWERED`.
- [ ] Lớp 1 từ chối → `status(retrieving)` rồi `final` với `answerType = NOT_FOUND`, `citations = []`, không có `generating`.
- [ ] Không bao giờ có sự kiện `token` trong luồng.
- [ ] Lỗi 401/403/404/409/422 trả `Content-Type: application/json` với `{ "error": {...} }`, không có header `text/event-stream`.
- [ ] Không có tài liệu `READY` → `409 NO_READY_DOCUMENTS`, `FakeEmbedding`/`FakeLlm` được gọi 0 lần.
- [ ] LLM quá thời gian → luồng kết thúc bằng `event: error` `code = UPSTREAM_TIMEOUT`, không có `final`, không có tin nhắn trợ lý trong CSDL; câu hỏi người dùng vẫn được lưu.
- [ ] Client đóng kết nối khi đang `generating` → lời gọi `FakeLlm` bị hủy (cờ `cancelled = True`) trong ≤ 1 s; CSDL không có tin nhắn trợ lý cho lượt đó.
- [ ] Qua Nginx local, sự kiện `status` đầu tiên tới client trong ≤ 300 ms sau khi gửi (với `FakeLlm` chậm 3 s).
- [ ] Câu hỏi 2001 ký tự hoặc chỉ khoảng trắng → `422`.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `sse_event` với tiếng Việt có dấu, xuống dòng trong `content` | Một dòng `data`, UTF-8, `\n` được mã hóa trong JSON |
| Integration | Luồng ANSWERED | 3 sự kiện đúng thứ tự, JSON hợp lệ |
| Integration | Luồng NOT_FOUND (Lớp 1 / Lớp 2) | Đúng như mục 6 |
| Integration | Hội thoại của người khác | 404 JSON |
| Integration | Không có tài liệu READY; có `documentIds` chỉ gồm tài liệu `PROCESSING` | 409 |
| Integration | `FakeLlm` ném `UpstreamUnavailable` | `event: error`, `UPSTREAM_UNAVAILABLE` |
| Integration | Ngắt kết nối giữa chừng | Hủy LLM, 0 tin nhắn trợ lý |
| Integration | Body có trường lạ `{"question":"x","foo":1}` | 422 |
| Manual | `curl -N` qua Nginx | Thấy `status` ngay, `final` sau |

## 8. Cấu hình

| Biến | Mặc định | Ghi chú |
|---|---|---|
| `ANSWER_TIMEOUT_S` | `60` | Dùng ở T-205; nhỏ hơn `proxy_read_timeout` 120 s của Nginx |
| `RATE_LIMIT_QUESTIONS_PER_MIN` | `20` `[Default]` | Áp dụng ở T-306, không ở task này |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| SAD §2.4 liệt kê sự kiện `token`; AD-07 tắt ở MVP | Client/QA có thể chờ `token` | Theo AD-07; client bỏ qua sự kiện lạ (T-209); bật lại chỉ khi SP-02 chứng minh an toàn |
| Phát hiện ngắt kết nối phụ thuộc hành vi Starlette/Uvicorn `[Verify]` | Có thể không hủy kịp | Watcher tự thăm dò `is_disconnected()` mỗi 0,5 s; test tích hợp bắt buộc |
| Thời gian chờ tối đa hiển thị cho người dùng `[TBD: OQ-014]` | Không ảnh hưởng API | Giữ `ANSWER_TIMEOUT_S` cấu hình được |
| Mã `VALIDATION_ERROR`, `NOT_FOUND`, `INTERNAL_ERROR` chưa có trong SDD §3.5 | Cần thống nhất | `[Proposed]`, đồng bộ với T-003 |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §3.2 (nginx SSE), §4.1, §6.7, §10.1
- [SAD](../../design/SAD.md) §2.1 (streaming), §2.4 (API-09), §3.2.1, §4.1.1 (CSRF), §4.2 (timeout), §5 AD-07
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.5 (mã lỗi), §3.7 (vòng đời lượt hỏi)
- [User_Stories](../../design/User_Stories.md) US-C1
- Task liên quan: [T-202](./T-202-conversation-apis.md), [T-205](./T-205-answer-service.md), [T-209](./T-209-chat-screen-core.md), [T-302](./T-302-document-scope.md), [T-305](./T-305-upstream-resilience.md), [T-306](./T-306-rate-limiting.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] OpenAPI mô tả phản hồi `text/event-stream` và các mã lỗi trước luồng.
