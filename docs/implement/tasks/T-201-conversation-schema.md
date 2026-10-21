# T-201 — Tạo lược đồ hội thoại, tin nhắn, trích dẫn và đánh giá

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 2 |
| **Loại** | Backend |
| **User story** | US-D1 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 1 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-004 |
| **Mở khóa (task chờ task này)** | T-202, T-205, T-303 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Sau task này CSDL có bốn bảng `conversation`, `message`, `citation`, `feedback` (DDL theo Implement_plan §6.1) cùng chỉ mục và model SQLAlchemy tương ứng, kèm lớp phòng thủ Row Level Security (RLS) cho `conversation`/`message`. Các task API hội thoại (T-202), trả lời (T-205) và đánh giá (T-303) có chỗ để ghi dữ liệu.

## 2. Bối cảnh

- Hội thoại là của riêng từng người (BR-016, BR-017, BRU-005, AC-017). SAD §3.1 quy định: mọi truy vấn hội thoại lọc `owner_id` ở repository; RLS là lớp thứ hai `[Proposed]`.
- `citation` lưu `document_name_snapshot` + `page` để hội thoại cũ vẫn đọc được sau khi tài liệu bị xóa và chunk bị purge (SAD §3.1 "Snapshot trích dẫn"; Blueprint §3.4). Vì vậy `citation.chunk_id` **không** có khóa ngoại tới `chunk` (Implement_plan §6.1, ghi chú).
- `message.tokens_in/out`, `response_time_ms` phục vụ CN-12 và AC-012 (SAD §3.2.1 bước 13).
- Bảng `feedback` được tạo ở đây để migration gọn một lần; API dùng nó ở T-303.

## 3. Phạm vi

**Trong phạm vi**
- Alembic revision mới (sau baseline của T-004) tạo 4 bảng + chỉ mục.
- Alembic revision riêng bật RLS cho `conversation`, `message` (tách riêng để có thể bỏ qua nếu Tech Lead quyết định không dùng ở T-000).
- Model SQLAlchemy 2 (async) cho 4 bảng.
- Helper đặt biến phiên `app.user_id` trong giao dịch.
- Test migration lên/xuống và test RLS.

**Ngoài phạm vi** (để tránh làm thừa)
- API, service, repository nghiệp vụ (T-202, T-205, T-303).
- Dọn dữ liệu hội thoại theo thời hạn lưu giữ (T-407, `[TBD: OQ-019]`).
- Tìm kiếm theo tiêu đề/câu hỏi đầu (T-304).
- Quyền CSDL theo vai trò (`INSERT/SELECT` cho `audit_log`…) — T-405.

## 4. Thiết kế chi tiết

**File cần tạo/sửa** (theo [Implement_plan §3.1](../Implement_plan.md#31-cấu-trúc-repository-monorepo)):

| File | Nội dung |
|---|---|
| `backend/migrations/versions/<rev>_conversation_schema.py` | Tạo 4 bảng + chỉ mục |
| `backend/migrations/versions/<rev>_conversation_rls.py` | Bật RLS + policy |
| `backend/app/conversations/models.py` | `Conversation`, `Message`, `Citation` |
| `backend/app/feedback/models.py` | `Feedback` |
| `backend/app/platform/db.py` (sửa) | `async def set_rls_user(session, user_id: UUID \| None)` |
| `backend/tests/integration/test_conversation_schema.py` | Test migration + RLS |

**DDL** (giữ nguyên Implement_plan §6.1, bổ sung chỉ mục và ràng buộc có nhãn):

```sql
CREATE TABLE conversation (
  id uuid PRIMARY KEY, owner_id uuid NOT NULL REFERENCES app_user(id),
  title text, started_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX conversation_owner_idx ON conversation (owner_id, started_at DESC);

CREATE TABLE message (
  id uuid PRIMARY KEY, conversation_id uuid NOT NULL REFERENCES conversation(id),
  role text NOT NULL CHECK (role IN ('user','assistant')),
  content text NOT NULL, answer_type text CHECK (answer_type IN ('ANSWERED','NOT_FOUND')),
  response_time_ms int, tokens_in int, tokens_out int,
  created_at timestamptz NOT NULL DEFAULT now(),
  -- [Proposed] chỉ tin nhắn trợ lý có answer_type
  CONSTRAINT message_answer_type_ck CHECK ((role = 'assistant') = (answer_type IS NOT NULL))
);
CREATE INDEX message_conversation_idx ON message (conversation_id, created_at);   -- [Proposed]

CREATE TABLE citation (
  id uuid PRIMARY KEY, message_id uuid NOT NULL REFERENCES message(id),
  chunk_id uuid,                                  -- không FK: chunk có thể đã bị purge
  document_id uuid NOT NULL, document_name_snapshot text NOT NULL, page int NOT NULL,
  ordinal int NOT NULL,                           -- số hiệu [1], [2] hiển thị
  CONSTRAINT citation_ordinal_ck CHECK (ordinal >= 1),               -- [Proposed]
  CONSTRAINT citation_message_ordinal_uq UNIQUE (message_id, ordinal) -- [Proposed]
);

CREATE TABLE feedback (
  message_id uuid PRIMARY KEY REFERENCES message(id),
  rating text NOT NULL CHECK (rating IN ('helpful','not_helpful')),
  created_at timestamptz NOT NULL DEFAULT now()
);
```

Ghi chú: mỗi `ordinal` ứng với **một** cặp (tài liệu, trang) đã loại trùng ở T-205, nên một tin nhắn không có hai dòng `citation` cùng `ordinal`. Nếu hai chunk cùng trang được trích, T-205 chỉ lưu một dòng (giữ `chunk_id` của chunk xuất hiện đầu tiên). `ordinal` đánh số **theo từng tin nhắn**, bắt đầu từ 1 `[Proposed]` (xem rủi ro ở T-205).

**RLS** `[Proposed — SAD §3.1]`:

```sql
ALTER TABLE conversation ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation FORCE ROW LEVEL SECURITY;
CREATE POLICY conversation_owner ON conversation
  USING (owner_id = nullif(current_setting('app.user_id', true), '')::uuid
         OR current_setting('app.rls_bypass', true) = 'on');

ALTER TABLE message ENABLE ROW LEVEL SECURITY;
ALTER TABLE message FORCE ROW LEVEL SECURITY;
CREATE POLICY message_owner ON message
  USING (EXISTS (SELECT 1 FROM conversation c WHERE c.id = message.conversation_id)
         OR current_setting('app.rls_bypass', true) = 'on');
```

- `message_owner` dựa vào RLS của `conversation` trong subquery (chỉ thấy hội thoại của mình).
- `app.rls_bypass = 'on'` chỉ dùng cho Worker/job hệ thống (dọn dữ liệu T-407, báo cáo nếu cần) qua `SET LOCAL`; API **không bao giờ** đặt biến này.
- Lọc `owner_id` ở repository **vẫn bắt buộc** (lớp 1); RLS chỉ là lớp 2.

**Helper:**

```python
async def set_rls_user(session: AsyncSession, user_id: UUID | None) -> None:
    """Gọi đầu mỗi giao dịch truy cập conversation/message. SET LOCAL hết hiệu lực khi commit."""
    await session.execute(text("SELECT set_config('app.user_id', :uid, true)"),
                          {"uid": str(user_id) if user_id else ""})
```

**Model:** khai báo đúng tên cột như DDL; `Message.citations` quan hệ một-nhiều `order_by=Citation.ordinal`; `Conversation.messages` `order_by=Message.created_at`. Không khai báo `relationship` từ `Citation` tới `Chunk`.

## 5. Các bước thực hiện

1. Tạo revision `conversation_schema` (`down_revision` = head của T-004); viết `upgrade()` theo DDL trên, `downgrade()` xóa theo thứ tự `feedback → citation → message → conversation`.
2. Tạo revision `conversation_rls`; `downgrade()` gồm `DROP POLICY` + `DISABLE ROW LEVEL SECURITY`.
3. Viết model SQLAlchemy trong `conversations/models.py`, `feedback/models.py`; đăng ký vào metadata để Alembic autogenerate không báo khác biệt.
4. Thêm `set_rls_user()` vào `platform/db.py`; ghi docstring về `app.rls_bypass`.
5. Viết test tích hợp (Testcontainers PostgreSQL + pgvector).
6. Chạy `make migrate` lên head, xuống base, lên lại.

## 6. Tiêu chí chấp nhận

- [ ] `alembic upgrade head` tạo đủ 4 bảng, các cột/kiểu đúng Implement_plan §6.1; `alembic downgrade -1` hai lần đưa lược đồ về đúng trạng thái sau T-004.
- [ ] `alembic check` (hoặc autogenerate) không phát hiện khác biệt giữa model và lược đồ.
- [ ] Chèn `citation` với `chunk_id` không tồn tại trong `chunk` thành công (không FK).
- [ ] Chèn `message(role='user', answer_type='ANSWERED')` bị từ chối; `message(role='assistant', answer_type=NULL)` bị từ chối.
- [ ] Với RLS bật: phiên đặt `app.user_id = A` chỉ `SELECT` được hội thoại/tin nhắn của A (0 dòng của B); không đặt `app.user_id` → 0 dòng; `app.rls_bypass='on'` → thấy tất cả.
- [ ] `EXPLAIN` truy vấn `WHERE owner_id = :u ORDER BY started_at DESC LIMIT 50` dùng `conversation_owner_idx`.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Integration | upgrade → downgrade → upgrade | Không lỗi; bảng tồn tại/không tồn tại đúng lúc |
| Integration | Chèn đủ chuỗi conversation → message → citation → feedback | Thành công; `feedback` thứ hai cùng `message_id` vi phạm PK |
| Integration | `citation.ordinal = 0` | Vi phạm `citation_ordinal_ck` |
| Integration | Hai `citation` cùng `(message_id, ordinal)` | Vi phạm unique |
| Integration | RLS: user A, user B, không đặt user, bypass | Như mục 6 |
| Integration | `feedback.rating = 'neutral'` | Vi phạm CHECK |

## 8. Cấu hình

Không thêm biến môi trường. Dùng `DATABASE_URL` ([Implement_plan §3.3](../Implement_plan.md#33-biến-môi-trường)). Lưu ý: RLS chỉ có tác dụng với `FORCE` khi ứng dụng kết nối bằng chính vai trò sở hữu bảng; vai trò CSDL tách riêng là việc của T-405.

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| RLS là `[Proposed]`, có thể bị bỏ ở T-000 | Nếu bỏ, mất lớp phòng thủ thứ hai cho AC-017 | Revision RLS tách riêng; nếu bỏ thì không merge revision đó, giữ test lọc `owner_id` ở T-202 |
| Quên `set_rls_user()` trong giao dịch | Truy vấn trả 0 dòng (an toàn nhưng gây lỗi chức năng) | T-202 đặt trong dependency phiên DB của route hội thoại; test tích hợp bắt lỗi này |
| Thời hạn lưu giữ hội thoại `[TBD: OQ-019]` | Cần xóa theo lô sau này | Không có `ON DELETE CASCADE`; T-407 xóa theo thứ tự con → cha |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §3.1, §4.1, §6.1
- [SAD](../../design/SAD.md) §3.1 (cách ly dữ liệu, snapshot trích dẫn), §2.3 (lưu giữ)
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.4 Information View
- [User_Stories](../../design/User_Stories.md) US-D1
- Task liên quan: [T-004](./T-004-db-migrations-baseline.md), [T-202](./T-202-conversation-apis.md), [T-205](./T-205-answer-service.md), [T-303](./T-303-answer-feedback.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Migration có `downgrade()` chạy được và được review bởi Tech Lead.
