# T-212 — Ghi sự kiện telemetry hỏi đáp

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 2 |
| **Loại** | Backend |
| **User story** | US-C1, US-D1 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 0,5 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-207 |
| **Mở khóa (task chờ task này)** | T-401 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Bảng `usage_event` ghi đủ ba sự kiện `conversation_started`, `question_asked`, `answer_returned` với thuộc tính đúng PRD §5.2, **không** chứa nội dung câu hỏi/câu trả lời, ghi cùng giao dịch với thay đổi nghiệp vụ — làm nguồn cho báo cáo tuần (T-401, AC-021, MET-003).

## 2. Bối cảnh

- PRD §5.2 (thuộc tính từng sự kiện); Implement_plan §10.2 (sự kiện → task); SAD §3.2.1 bước 13; SAD §3.1 "Dữ liệu phân tích tách khỏi nội dung".
- Khung `emit()` + mô hình thuộc tính theo danh sách trắng đã có ở T-110 (`app/analytics/events.py`): `async def emit(session, name, *, user_id, **props)`; trường lạ → lỗi.
- Không log nội dung (Implement_plan §0 quy tắc 3; OQ-006).

## 3. Phạm vi

**Trong phạm vi**
- Thêm 3 giá trị `EventName` + 3 mô hình thuộc tính.
- Gọi `emit()` ở `ConversationService.create()` (T-202), `add_user_message()` (T-202, qua T-207) và `record_answer()` (T-205).
- Hàm `detect_language()` tối giản cho thuộc tính `language` `[Proposed]`.

**Ngoài phạm vi** (để tránh làm thừa)
- `answer_feedback_submitted` (T-303), `conversation_resumed` (T-304), `weekly_usage_report_generated` (T-401).
- Metric Prometheus `answers_total`… (T-404). Báo cáo tuần (T-401).

## 4. Thiết kế chi tiết

**File:** `backend/app/analytics/events.py` (sửa), `backend/app/analytics/language.py` (mới), `backend/app/conversations/service.py` (sửa); test `backend/tests/unit/analytics/test_qa_events.py`, `backend/tests/integration/test_qa_telemetry.py`.

```python
class EventName(StrEnum):
    ...
    CONVERSATION_STARTED = "conversation_started"
    QUESTION_ASKED       = "question_asked"
    ANSWER_RETURNED      = "answer_returned"

class ConversationStartedProps(EventProps):          # extra="forbid"
    conversation_id: UUID

class QuestionAskedProps(EventProps):
    conversation_id: UUID
    question_length: int                              # số ký tự sau strip, 1..2000
    scoped_documents: list[UUID] | None               # null = toàn bộ thư viện
    language: Literal["vi", "en", "unknown"]          # [Proposed]

class AnswerReturnedProps(EventProps):
    conversation_id: UUID
    response_time_ms: int
    citation_count: int
    answer_type: Literal["answered", "not_found"]     # chữ thường theo PRD
```

`user_id` ghi vào cột `usage_event.user_id` (không lặp trong `properties`), như T-110.

**Điểm ghi:**

| Sự kiện | Ở đâu | Giao dịch | Khi nào |
|---|---|---|---|
| `conversation_started` | `ConversationService.create()` | Cùng `INSERT conversation` | Mỗi `POST /api/v1/conversations` thành công |
| `question_asked` | `ConversationService.add_user_message()` | Cùng `INSERT message(role='user')` | Sau khi qua mọi kiểm tra trước luồng của T-207 |
| `answer_returned` | `ConversationService.record_answer()` | Cùng `INSERT message(role='assistant')` + `citation` | Chỉ khi có kết quả cuối (`ANSWERED`/`NOT_FOUND`) |

- `question_asked` ghi khi lưu câu hỏi (bước 4 SAD §3.2.1) thay vì bước 13 `[Proposed]`: câu hỏi lỗi AI hay client ngắt kết nối **vẫn** được đếm (đúng nghĩa "số câu hỏi đã đặt" của MET-003). Hệ quả: `count(question_asked) ≥ count(answer_returned)`; chênh lệch = lượt lỗi/hủy.
- Lỗi `401/403/404/409/422/429` trước luồng → **không** ghi `question_asked`.
- `answer_type` ánh xạ `ANSWERED → "answered"`, `NOT_FOUND → "not_found"`; `citation_count` = số dòng `citation` đã lưu (sau loại trùng).
- `detect_language(text)` `[Proposed]`: có ký tự đặc trưng tiếng Việt (ă â đ ê ô ơ ư hoặc dấu thanh kết hợp sau NFD) → `"vi"`; chỉ chữ Latin ASCII → `"en"`; còn lại → `"unknown"`. Danh sách ngôn ngữ chính thức `[TBD: OQ-009]` — thay bằng bộ phát hiện tốt hơn ở T-308 nếu cần.

## 5. Các bước thực hiện

1. Thêm `EventName` + 3 mô hình thuộc tính vào `events.py`; đăng ký trong `PROPERTY_MODELS`.
2. Viết `language.py` + test.
3. Thêm lời gọi `emit()` vào 3 hàm service theo bảng, **bên trong** giao dịch sẵn có.
4. Viết test tích hợp: luồng hỏi đầy đủ qua API-09 với FakeLlm (ANSWERED, NOT_FOUND, lỗi AI, client ngắt) rồi đếm sự kiện.
5. Thêm test "không có nội dung": quét `properties` của mọi sự kiện sinh trong test, khẳng định không chứa chuỗi câu hỏi/câu trả lời/tên tài liệu.

## 6. Tiêu chí chấp nhận

- [ ] Một lượt hỏi thành công sinh đúng 1 `question_asked` + 1 `answer_returned`; tạo hội thoại sinh đúng 1 `conversation_started`.
- [ ] Thuộc tính đúng tập PRD §5.2 (cộng `language` theo PRD); thêm trường lạ → `ValidationError` (test đơn vị).
- [ ] `properties` không chứa văn bản câu hỏi, câu trả lời, `quote` hay tên tài liệu (test quét chuỗi).
- [ ] Lỗi AI hoặc client ngắt kết nối: có `question_asked`, **không** có `answer_returned`.
- [ ] `409 NO_READY_DOCUMENTS`/`404`/`422`: không có `question_asked`.
- [ ] Rollback giao dịch `record_answer` (lỗi chèn `citation`) → không còn `answer_returned` của lượt đó.
- [ ] `answer_returned.response_time_ms` bằng `message.response_time_ms`; `citation_count` bằng số dòng `citation` của tin nhắn.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `detect_language("Điều kiện thanh toán?")` | `"vi"` |
| Unit | `detect_language("What are the payment terms?")` | `"en"` |
| Unit | `detect_language("12345 ???")` | `"unknown"` |
| Unit | `QuestionAskedProps(..., question="x")` | `ValidationError` (trường lạ) |
| Integration | Lượt ANSWERED với 2 trích dẫn | `answer_type="answered"`, `citation_count=2` |
| Integration | Lượt NOT_FOUND Lớp 1 | `answer_type="not_found"`, `citation_count=0` |
| Integration | `FakeLlm(fail_with=UpstreamTimeout())` | 1 `question_asked`, 0 `answer_returned` |
| Integration | `documentIds=[Y]` | `scoped_documents=[Y]`; không có → `null` |
| Integration | Quét `usage_event.properties` sau toàn bộ test | Không chứa nội dung |

## 8. Cấu hình

Không có biến mới. Phân vùng `usage_event` theo tháng đã có ở T-004/T-407.

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| SAD §3.2.1 bước 13 ghi cả hai sự kiện ở cuối; task này ghi `question_asked` ở bước 4 `[Proposed]` | Số "câu hỏi" trong báo cáo gồm cả lượt lỗi | Ghi rõ định nghĩa trong T-401; Sponsor xác nhận khi xem báo cáo |
| Thuộc tính `language` cần danh sách ngôn ngữ `[TBD: OQ-009]` | Giá trị có thể chưa chuẩn | Heuristic tối giản; thay ở T-308 |
| PRD ghi tên sự kiện là "đề xuất làm việc" | Có thể đổi tên | Tên nằm trong `EventName` một chỗ |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §0, §4.1 (giao dịch), §10.2
- [SAD](../../design/SAD.md) §3.1, §3.2.1 bước 4 và 13, §4.3 (sự kiện sản phẩm)
- [PRD](../../requirements/PRD.md) §5.2
- [User_Stories](../../design/User_Stories.md) US-C1, US-D1, US-F2
- Task liên quan: [T-110](./T-110-telemetry-documents-access.md), [T-202](./T-202-conversation-apis.md), [T-205](./T-205-answer-service.md), [T-207](./T-207-messages-sse-api.md), [T-401](./T-401-weekly-report-api.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Định nghĩa đếm `question_asked` được ghi vào docstring của `QuestionAskedProps` để T-401 dùng.
