# T-202 — Xây API tạo, liệt kê và xem hội thoại

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 2 |
| **Loại** | Backend |
| **User story** | US-D1, US-D2 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 1 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-006, T-201 |
| **Mở khóa (task chờ task này)** | T-207, T-209, T-304 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Người dùng (vai trò `MEMBER`) tạo được hội thoại mới, xem danh sách hội thoại của chính mình và mở chi tiết một hội thoại kèm tin nhắn và trích dẫn — qua API-07/API-08. Không ai đọc được hội thoại của người khác.

## 2. Bối cảnh

- API-07 `POST /api/v1/conversations`, API-08 `GET /api/v1/conversations`, `GET /api/v1/conversations/{id}` (SAD §2.4; Implement_plan §10.1).
- US-D1 (AC-016): hội thoại mới không mang ngữ cảnh hội thoại trước — bảo đảm bằng việc mỗi tin nhắn gắn `conversation_id` và lịch sử chỉ đọc trong cùng hội thoại (T-205/T-301).
- Cách ly theo `owner_id` ở repository (lớp 1) + RLS (lớp 2, T-201) — AC-017, BRU-005. Ma trận quyền SAD §4.1.1: hỏi đáp/hội thoại chỉ `MEMBER`; `SPONSOR`/`ADMIN` không xem hội thoại người khác.
- `ConversationService` là điểm vào cho module khác (SAD §2.2); T-207 và T-205 gọi các hàm ở đây.

## 3. Phạm vi

**Trong phạm vi**
- Router, service, repository của module `conversations`.
- Ba endpoint trên + schema Pydantic phản hồi.
- Hàm service cho T-207: `get_owned()`, `add_user_message()`, `set_title_if_empty()`.
- Trả `quote` (văn bản chunk) trong trích dẫn để màn 06 tô đoạn (T-210) `[Proposed]`.

**Ngoài phạm vi** (để tránh làm thừa)
- `POST /conversations/{id}/messages` (T-207); lưu câu trả lời `record_answer()` (T-205).
- Tìm kiếm `q`, nhóm theo ngày, sự kiện `conversation_resumed` (T-304).
- Sự kiện `conversation_started` (T-212 thêm vào `create()`).
- Xóa hội thoại (không có trong MVP).

## 4. Thiết kế chi tiết

**File:** `backend/app/conversations/{router.py, service.py, repository.py, schemas.py}`; đăng ký router trong `backend/app/main.py`; test ở `backend/tests/integration/test_conversations_api.py`.

**Service:**

```python
class ConversationService:
    async def create(self, user: CurrentUser, title: str | None) -> Conversation
    async def list_owned(self, user: CurrentUser, limit: int, cursor: str | None) -> Page[ConversationSummary]
    async def get_detail(self, user: CurrentUser, conversation_id: UUID) -> ConversationDetail
    async def get_owned(self, user: CurrentUser, conversation_id: UUID) -> Conversation   # 404 nếu không phải chủ
    async def add_user_message(self, conversation: Conversation, content: str) -> Message   # dùng ở T-207
    async def set_title_if_empty(self, conversation: Conversation, question: str) -> None   # [Proposed]
```

- Mọi hàm kiểm vai trò `MEMBER` ở service (không chỉ router) và gọi `set_rls_user(session, user.id)` đầu giao dịch.
- Repository **luôn** có điều kiện `owner_id = :user_id`. Không tồn tại **hoặc** không phải chủ → cùng một lỗi 404 (không lộ sự tồn tại).
- `set_title_if_empty`: nếu `title IS NULL`, đặt `title` = câu hỏi đầu tiên sau khi gộp khoảng trắng, cắt 80 ký tự + "…" `[Proposed]` (màn 04 hiển thị tiêu đề ở đầu khung chat và thanh bên).
- `quote`: lấy qua `RetrievalService.get_chunk_texts(chunk_ids)` (module `retrieval` là module duy nhất được đọc `chunk`, Implement_plan §3.1); trả `null` nếu chunk đã purge hoặc tài liệu `DELETED`.

**API**

| Endpoint | Request | Response thành công | Lỗi |
|---|---|---|---|
| `POST /api/v1/conversations` | `{"title": "string ≤ 200"?}` (trường lạ → 422) | `201 {"id","title","startedAt"}` | 401, 403 (`FORBIDDEN` khi không phải MEMBER hoặc thiếu CSRF), 422 |
| `GET /api/v1/conversations?limit=50&cursor=` | `limit` 1..200, mặc định 50 | `200 {"items":[ConversationSummary], "nextCursor": string\|null}` | 401, 403, 422 |
| `GET /api/v1/conversations/{id}` | — | `200 ConversationDetail` | 401, 403, 404 |

```json
// ConversationSummary — sắp xếp started_at DESC, id DESC
{ "id": "uuid", "title": "Điều kiện thanh toán hợp đồng A", "startedAt": "2026-10-21T03:40:00Z",
  "lastMessageAt": "2026-10-21T03:42:10Z", "messageCount": 4 }

// ConversationDetail — messages theo created_at ASC
{ "id": "uuid", "title": "…", "startedAt": "…",
  "messages": [
    { "id": "uuid", "role": "user", "content": "Điều kiện thanh toán…?", "createdAt": "…" },
    { "id": "uuid", "role": "assistant", "answerType": "ANSWERED", "content": "… [1] … [2]",
      "responseTimeMs": 8200, "createdAt": "…",
      "citations": [ { "ordinal": 1, "documentId": "uuid", "documentName": "Hợp đồng khung đối tác A.pdf",
                       "page": 12, "chunkId": "uuid|null", "quote": "a) Đợt 1: 30%…|null" } ] }
  ] }
```

- `lastMessageAt`, `messageCount` (thanh bên màn 04 hiển thị "4 tin nhắn · 10:42") là trường `[Proposed]`; tính bằng `LEFT JOIN LATERAL (SELECT count(*), max(created_at) FROM message …)`.
- `documentName` lấy từ `citation.document_name_snapshot` (không join `document`).
- `cursor` = base64url của `"{started_at_iso}|{id}"` `[Proposed]`; truy vấn `WHERE (started_at, id) < (:ts, :id)`.
- Mã lỗi 404/422: SDD §3.5 chưa có mã; dùng `NOT_FOUND` (404) và `VALIDATION_ERROR` (422) `[Proposed — thống nhất với khung lỗi T-003]`.

## 5. Các bước thực hiện

1. Viết `schemas.py` (Pydantic v2, `model_config = ConfigDict(extra="forbid")`, alias camelCase).
2. Viết `repository.py`: `insert_conversation`, `list_by_owner(owner_id, limit, cursor)`, `get_by_id_and_owner`, `list_messages_with_citations(conversation_id)`, `insert_user_message`, `update_title_if_null`.
3. Thêm `RetrievalService.get_chunk_texts(ids: list[UUID]) -> dict[UUID, str]` (nếu T-203 chưa có) — `SELECT c.id, c.text FROM chunk c JOIN document d … WHERE c.id = ANY(:ids) AND d.status <> 'DELETED'`.
4. Viết `service.py` theo chữ ký trên; một use case = một giao dịch.
5. Viết `router.py`: phụ thuộc `current_user()` + `require_role("MEMBER")` (T-006); POST yêu cầu `X-CSRF-Token`.
6. Gắn router vào `main.py`; kiểm route mới xuất hiện trong test bảo vệ route (T-109) và trả 401 khi không có phiên.
7. Viết test tích hợp.

## 6. Tiêu chí chấp nhận

- [ ] `POST /api/v1/conversations` trả `201` với `id` UUID mới; bản ghi có `owner_id` = người gọi.
- [ ] `GET /api/v1/conversations` chỉ trả hội thoại của người gọi, sắp xếp mới nhất trước; phân trang đủ 120 bản ghi qua 3 trang `limit=50` không trùng, không thiếu.
- [ ] `GET /api/v1/conversations/{id}` của người khác trả `404 NOT_FOUND`, giống hệt khi `id` không tồn tại (cùng mã, cùng thông điệp).
- [ ] Người dùng vai trò `SPONSOR` gọi 3 endpoint → `403 FORBIDDEN`; không có phiên → `401 UNAUTHENTICATED`.
- [ ] Chi tiết trả `citations` theo `ordinal` tăng dần; trích dẫn của tài liệu đã xóa vẫn có `documentName` (snapshot) và `quote = null`.
- [ ] Gửi trường lạ (`{"title":"x","owner":"…"}`) → `422`.
- [ ] Log của các endpoint không chứa `title` hay nội dung tin nhắn.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | Mã hóa/giải mã `cursor`; cursor hỏng | Khứ hồi đúng; cursor hỏng → 422 |
| Unit | `set_title_if_empty` với câu 300 ký tự, nhiều khoảng trắng | Tiêu đề ≤ 81 ký tự, khoảng trắng đã gộp; không ghi đè tiêu đề có sẵn |
| Integration | A tạo 2 hội thoại, B tạo 1; A gọi danh sách | Đúng 2 mục của A |
| Integration | B gọi chi tiết hội thoại của A | 404 `NOT_FOUND` |
| Integration | Hội thoại có tin nhắn trợ lý `NOT_FOUND` | `citations: []`, `answerType: "NOT_FOUND"` |
| Integration | Tài liệu được trích dẫn chuyển `DELETED`, chunk đã purge | `documentName` còn nguyên, `chunkId` vẫn trả, `quote: null` |
| Integration | POST thiếu `X-CSRF-Token` | 403 |
| Contract | Phản hồi khớp schema OpenAPI | Pass |

## 8. Cấu hình

Không thêm biến. Giới hạn phân trang theo SAD §2.4 (mặc định 50, tối đa 200) — hằng số trong `platform`, không phải ngưỡng nghiệp vụ.

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Trả `quote` (văn bản chunk) là mở rộng hợp đồng API-08 | Thêm dữ liệu tài liệu trong phản hồi (người dùng vẫn có quyền đọc toàn thư viện — ASM-002) | `[Proposed]`; Tech Lead xác nhận khi review; nếu OQ-011 đưa phân quyền theo tài liệu thì lọc `quote` theo quyền |
| Mã lỗi 404/422 chưa có trong SDD §3.5 | Frontend cần mã ổn định | Dùng tên `[Proposed]` ở trên, thống nhất với T-003; cập nhật SDD sau |
| Quyền hỏi đáp của `ADMIN` (SAD §4.1.1 ghi "—") `[TBD: OQ-011]` | ADMIN không tạo được hội thoại | Kiểm vai trò qua một hàm để đổi nhanh |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §4.1, §6.1, §6.8, §10.1
- [SAD](../../design/SAD.md) §2.2, §2.4 (API-07/08), §3.1, §4.1.1
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.5
- [User_Stories](../../design/User_Stories.md) US-D1, US-D2
- Màn hình: [html_design/04_chat.html](../../design/html_design/04_chat.html) (thanh bên), [html_design/07_history.html](../../design/html_design/07_history.html)
- Task liên quan: [T-201](./T-201-conversation-schema.md), [T-207](./T-207-messages-sse-api.md), [T-209](./T-209-chat-screen-core.md), [T-210](./T-210-citation-viewer-screen.md), [T-304](./T-304-history-screen.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Ba route mới nằm trong danh sách kiểm của test bảo vệ route (T-109) và pass.
