# T-303 — Ghi nhận đánh giá Hữu ích / Không hữu ích cho câu trả lời

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 3 |
| **Loại** | Fullstack |
| **User story** | US-F1 |
| **Ưu tiên** | P1 |
| **Ước lượng** | 1,5 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-201, T-209 |
| **Mở khóa (task chờ task này)** | T-311, T-401 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Dưới mỗi câu trả lời có cặp nút "Hữu ích" / "Không hữu ích"; bấm để đánh giá, bấm nút khác để đổi, bấm lại nút đang chọn để bỏ. Đánh giá được lưu (API-10), giữ nguyên khi tải lại trang và sinh sự kiện `answer_feedback_submitted` làm dữ liệu cho MET-004 (AC-019).

## 2. Bối cảnh

- BR-019 / **AC-019**: "Đánh giá trên một câu trả lời được ghi nhận và xuất hiện trong số liệu MET-004." ([User_Stories US-F1](../../design/User_Stories.md#us-f1)).
- API-10 `PUT /api/v1/messages/{id}/feedback` body `{ "rating": "helpful" | "not_helpful" }` → `204`, ghi đè được ([SAD §2.4](../../design/SAD.md)). Quyền: chủ hội thoại (SDD §3.5; SAD §4.1.1 — chỉ MEMBER đánh giá câu trả lời của mình).
- Bảng `feedback(message_id PK, rating, created_at)` đã tạo ở T-201 ([Implement_plan §6.1](../Implement_plan.md#61-lược-đồ-csdl)).
- Sự kiện PRD §5.2: `answer_feedback_submitted` — `conversation_id, message_id, rating`.
- Thiết kế: [04_chat.html](../../design/html_design/04_chat.html) `.ans-tools`, ảnh [chat.png](../../design/images/chat.png). Báo cáo tuần (T-401) đọc số liệu này.

## 3. Phạm vi

**Trong phạm vi**
- API-10 `PUT` (tạo/ghi đè) và `DELETE` để bỏ đánh giá `[Proposed]`.
- Trả trạng thái đánh giá hiện tại trong chi tiết hội thoại (API-08) để hiển thị lại khi mở hội thoại.
- Nút đánh giá trên màn 04 với `aria-pressed`, cập nhật lạc quan (optimistic) và hoàn tác khi lỗi.
- Sự kiện `answer_feedback_submitted` ghi vào `usage_event` cùng giao dịch.

**Ngoài phạm vi** (để tránh làm thừa)
- Ô nhập lý do/nhận xét (không có trong thiết kế).
- Tổng hợp MET-004 trên báo cáo (T-401/T-402).
- Đánh giá tin nhắn của người khác (không có quyền này trong MVP).

## 4. Thiết kế chi tiết

### 4.1 File

| File | Thay đổi |
|---|---|
| `backend/app/feedback/router.py` | **Mới:** `PUT`, `DELETE /api/v1/messages/{id}/feedback` |
| `backend/app/feedback/service.py` | **Mới:** `FeedbackService` |
| `backend/app/feedback/repository.py` | **Mới:** upsert/delete trên `feedback` |
| `backend/app/conversations/service.py` | `ConversationService.get_owned_assistant_message(message_id, user_id)` |
| `backend/app/conversations/schemas.py` | Thêm `feedback` vào phần tử tin nhắn trợ lý của API-08 |
| `frontend/src/components/FeedbackButtons.tsx` | **Mới** |
| `frontend/src/api/feedback.ts` | **Mới:** `putFeedback`, `deleteFeedback` |

### 4.2 Hợp đồng API

```http
PUT /api/v1/messages/{messageId}/feedback
X-CSRF-Token: …
Content-Type: application/json

{ "rating": "helpful" }
→ 204 No Content
```

```http
DELETE /api/v1/messages/{messageId}/feedback      [Proposed]
X-CSRF-Token: …
→ 204 No Content   (lũy đẳng: chưa có đánh giá vẫn trả 204)
```

| Tình huống | Phản hồi |
|---|---|
| Không có phiên | `401 UNAUTHENTICATED` |
| Thiếu/sai `X-CSRF-Token` | `403 FORBIDDEN` (theo T-006) |
| Vai trò không phải MEMBER (vd. SPONSOR) | `403 FORBIDDEN` + `access_denied` |
| `messageId` không tồn tại, là tin nhắn `user`, hoặc thuộc hội thoại của người khác | `404` — dùng đúng mã và cách xử lý "không tìm thấy tài nguyên" mà T-202 dùng cho hội thoại của người khác (không phân biệt để không lộ sự tồn tại) |
| `rating` khác 2 giá trị, hoặc có trường lạ | Lỗi kiểm tra đầu vào chung (T-003) |

Phần tử tin nhắn trợ lý trong `GET /api/v1/conversations/{id}` bổ sung `[Proposed]`:

```json
{ "id": "…", "role": "assistant", "answerType": "ANSWERED", "content": "…",
  "citations": [ … ], "feedback": "helpful" }
```

`feedback`: `"helpful" | "not_helpful" | null`.

### 4.3 Backend

```python
class FeedbackService:
    async def set(self, user: CurrentUser, message_id: UUID, rating: Rating) -> None: ...
    async def clear(self, user: CurrentUser, message_id: UUID) -> None: ...
```

`set` trong **một giao dịch**:
1. `msg = conversations.get_owned_assistant_message(message_id, user.id)` → không có thì ném lỗi 404.
2. Upsert:
   ```sql
   INSERT INTO feedback (message_id, rating, created_at) VALUES (:mid, :rating, now())
   ON CONFLICT (message_id) DO UPDATE SET rating = EXCLUDED.rating, created_at = now();
   ```
3. `analytics.emit("answer_feedback_submitted", user_id=user.id, properties={"conversation_id": msg.conversation_id, "message_id": msg.id, "rating": rating})` — **chỉ khi** rating mới khác rating cũ (bấm lặp cùng giá trị không sinh sự kiện) `[Proposed]`.

`clear`: `DELETE FROM feedback WHERE message_id = :mid` (sau khi kiểm quyền); không phát sự kiện `[Proposed]` (PRD chỉ định nghĩa `rating` có 2 giá trị). Ghi chú cho T-401: MET-004 nên tính theo **trạng thái cuối** mỗi `message_id` (bảng `feedback` hoặc sự kiện mới nhất theo `message_id`), không cộng dồn mọi sự kiện.

Kiểm quyền ở service (không chỉ router): `require_role(MEMBER)` + lọc `owner_id`.

### 4.4 Frontend — `FeedbackButtons`

Bám `.ans-tools` trong `04_chat.html`:

- Hàng chữ nhỏ màu muted (0,85 rem) dưới khối trích dẫn: nhãn "**Hữu ích?**" + 2 nút `.fb`: icon `up` + "**Hữu ích**", icon `down` + "**Không hữu ích**".
- Nút `.fb`: cao tối thiểu 36 px, nền trong suốt, chữ `--ink2`; hover nền `--surface2`; **đã chọn** (`aria-pressed="true"`): nền `--primary-soft`, chữ `--link`, viền `--primary`.
- Nhóm có `role="group"` và `aria-label="Đánh giá câu trả lời"` `[Proposed]`.
- Chỉ hiện cho tin nhắn `answerType = "ANSWERED"` (khung "Không tìm thấy" ở màn 05 không có nút đánh giá).

| Trạng thái hiện tại | Hành động | Gọi API | Trạng thái mới |
|---|---|---|---|
| Chưa chọn | Bấm "Hữu ích" | `PUT helpful` | Hữu ích được nhấn |
| Hữu ích | Bấm "Không hữu ích" | `PUT not_helpful` | Không hữu ích được nhấn |
| Hữu ích | Bấm lại "Hữu ích" | `DELETE` | Chưa chọn |

- Cập nhật lạc quan ngay khi bấm (phản hồi ≤ 300 ms, Blueprint §2.4); lỗi → trả về trạng thái trước + toast "Chưa lưu được đánh giá. Vui lòng thử lại." `[Proposed]`.
- Bấm liên tiếp: hủy request cũ (`AbortController`), chỉ request cuối có hiệu lực.
- Cập nhật cache `['conversation', id]` sau khi thành công.
- Không chặn đọc/cuộn; không đổi focus.
- Chuỗi trong `vi.json`: `chat.feedback.prompt`, `chat.feedback.helpful`, `chat.feedback.notHelpful`, `chat.feedback.saveError`.

## 5. Các bước thực hiện

1. Viết `FeedbackRepository` (upsert/delete) + integration test.
2. Viết `ConversationService.get_owned_assistant_message`.
3. Viết `FeedbackService` (giao dịch + sự kiện) và router; đăng ký route với phụ thuộc xác thực (T-109 tự kiểm).
4. Bổ sung trường `feedback` vào API-08 (LEFT JOIN qua repository của `conversations` gọi `FeedbackService.get_for_messages(ids)` để giữ ranh giới module).
5. FE: `api/feedback.ts`, `FeedbackButtons` + test; gắn vào tin nhắn trợ lý của T-209.
6. Kiểm với trình đọc màn hình: trạng thái "đã nhấn" được đọc ra.

## 6. Tiêu chí chấp nhận

- [ ] `PUT` hợp lệ → `204`, bảng `feedback` có đúng 1 dòng cho `message_id` với `rating` mới; gọi lại với giá trị khác → vẫn 1 dòng, rating được ghi đè.
- [ ] Mỗi lần rating thay đổi → đúng 1 bản ghi `usage_event` `answer_feedback_submitted` có `conversation_id`, `message_id`, `rating`, `user_id`; không có văn bản câu trả lời.
- [ ] `DELETE` → dòng bị xóa, `204`; gọi `DELETE` lần 2 → vẫn `204`.
- [ ] Người dùng B gửi feedback cho tin nhắn của A → 404, dữ liệu của A không đổi.
- [ ] SPONSOR gọi API-10 → 403; không có phiên → 401; thiếu CSRF → 403.
- [ ] Trên UI: bấm "Hữu ích" → `aria-pressed="true"`; tải lại trang → vẫn được nhấn; bấm lại → `aria-pressed="false"` ở cả 2 nút.
- [ ] Lỗi mạng khi lưu → nút trở về trạng thái trước và có toast.
- [ ] **AC-019:** đánh giá xuất hiện trong dữ liệu nguồn của MET-004 (truy vấn `usage_event`/`feedback`) — kiểm lại ở T-311 và T-401.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit (FE) | Bảng chuyển trạng thái §4.4 (3 hàng) | Gọi đúng hàm API, `aria-pressed` đúng |
| Unit (FE) | API trả 500 | Hoàn tác + toast |
| Unit (FE) | Tin nhắn `NOT_FOUND` | Không render nút |
| Integration | PUT helpful → PUT not_helpful → PUT not_helpful | 1 dòng `feedback`; 2 sự kiện |
| Integration | DELETE khi chưa có | 204 |
| Integration | PUT lên tin nhắn `role='user'` | 404 |
| Integration | User B → tin nhắn của A | 404 |
| Integration | GET conversation sau PUT | `feedback: "not_helpful"` |
| Contract | OpenAPI API-10 | Schema body/response khớp |
| E2E | AC-019 | Xem T-311 |

## 8. Cấu hình

Không thêm biến môi trường.

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| SDD/SAD chỉ có `PUT`; "bấm lại để bỏ" cần `DELETE` `[Proposed]` | Hợp đồng API | Tech Lead xác nhận; cập nhật bảng API |
| Cách đếm MET-004 khi người dùng đổi/bỏ đánh giá chưa định nghĩa | Số liệu báo cáo tuần sai lệch | T-401 tính theo trạng thái cuối mỗi tin nhắn; xác nhận với Sponsor |
| Mục tiêu MET-004 `[TBD: OQ-007]` | Chỉ ảnh hưởng hiển thị mục tiêu ở T-402 | Không chặn task này |
| Có cho đánh giá câu "Không tìm thấy" không | Dữ liệu "không tìm thấy sai" | Thiết kế không có nút → không hiển thị; API vẫn chấp nhận tin nhắn trợ lý bất kỳ |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §5.4, §6.1, §10.2
- [SAD](../../design/SAD.md) §2.4 (API-10), §4.1.1 (ma trận quyền)
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.5
- [User_Stories](../../design/User_Stories.md) US-F1
- PRD §5.2 (`answer_feedback_submitted`)
- Màn hình: [html_design/04_chat.html](../../design/html_design/04_chat.html), ảnh [chat.png](../../design/images/chat.png)
- Task liên quan: [T-201](./T-201-conversation-schema.md), [T-202](./T-202-conversation-apis.md), [T-209](./T-209-chat-screen-core.md), [T-401](./T-401-weekly-report-api.md), [T-311](./T-311-e2e-sprint3.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Người làm T-401 đã được báo quy tắc đếm theo trạng thái cuối.
