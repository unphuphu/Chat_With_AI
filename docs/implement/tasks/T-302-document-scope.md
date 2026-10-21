# T-302 — Cho phép giới hạn phạm vi câu hỏi vào tài liệu được chọn

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 3 |
| **Loại** | Fullstack |
| **User story** | US-C7 |
| **Ưu tiên** | P1 |
| **Ước lượng** | 2 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-203, T-209 |
| **Mở khóa (task chờ task này)** | T-311 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Người dùng chọn một hoặc vài tài liệu "Sẵn sàng" trên màn 04 để giới hạn phạm vi; API-09 nhận `documentIds`, kiểm tra hợp lệ và chỉ truy xuất trong các tài liệu đó, nên câu trả lời chỉ trích dẫn tài liệu đã chọn (AC-014). Mặc định là "Toàn bộ thư viện".

## 2. Bối cảnh

- BR-014 / **AC-014**: "Khi chọn chỉ tài liệu Y, câu trả lời chỉ trích dẫn tài liệu Y, kể cả khi tài liệu khác cũng có thông tin liên quan."
- API-09 `POST /api/v1/conversations/{id}/messages` body `{ "question": string (1..2000), "documentIds?": uuid[] }` ([SAD §2.4](../../design/SAD.md)).
- Thuật toán DD-06 bước 1: phạm vi = tài liệu `READY` ∩ `documentIds` ([Blueprint §3.6.4](../../design/Blueprint_Design.md)). SQL truy xuất đã có điều kiện `(:scope_is_null OR c.document_id = ANY(:scope))` ([Implement_plan §6.5](../Implement_plan.md#65-truy-xuất-lai)) — T-203.
- Thiết kế: [04_chat.html](../../design/html_design/04_chat.html), ảnh [chat_scope.png](../../design/images/chat_scope.png).
- Lọc phạm vi hẹp có thể làm HNSW trả thiếu kết quả — chiến lược chọn ở T-309 (SP-01).

## 3. Phạm vi

**Trong phạm vi**
- Backend: kiểm tra `documentIds` trong API-09 trước khi mở SSE; truyền `scope` xuống `AnswerService.ask()` → `RetrievalService`.
- Backend: `DocumentService.filter_ready(ids)` (module `documents` sở hữu bảng `document`).
- Frontend: nút "Phạm vi" + popover chọn tài liệu + dòng chip trên ô nhập; gửi `documentIds` theo lựa chọn.
- Truyền `scoped_documents` cho sự kiện `question_asked` (thuộc tính đã định nghĩa ở PRD §5.2; sự kiện ghi ở T-212).

**Ngoài phạm vi** (để tránh làm thừa)
- Lưu phạm vi vào CSDL theo hội thoại (không có trong thiết kế).
- Tìm kiếm trong popover, nhóm tài liệu, phân quyền theo tài liệu (OQ-011, ngoài MVP).
- Tối ưu HNSW khi lọc (T-309).

## 4. Thiết kế chi tiết

### 4.1 Hợp đồng API-09 (bổ sung)

```json
POST /api/v1/conversations/{id}/messages
{ "question": "Điều kiện thanh toán là gì?",
  "documentIds": ["7b0c…", "a41e…"] }
```

| Giá trị `documentIds` | Ý nghĩa |
|---|---|
| Không gửi hoặc `null` | Toàn bộ thư viện (mọi tài liệu `READY` tại thời điểm hỏi) |
| Mảng 1..100 UUID, không trùng `[Proposed]` giới hạn 100 | Chỉ các tài liệu này |
| `[]` | Lỗi `422 INVALID_SCOPE` `[Proposed]` |

Thứ tự kiểm tra (đều trước khi mở SSE, trả HTTP thường theo [Implement_plan §6.7](../Implement_plan.md#67-giao-thức-sse-của-api-09)):

1. Phiên (`401 UNAUTHENTICATED`), chủ hội thoại (theo T-202/T-207).
2. Pydantic: `question` 1..2000 ký tự; `documentIds` là UUID hợp lệ, không trùng, ≤ 100 phần tử → sai định dạng trả lỗi kiểm tra đầu vào chung của T-003.
3. Thư viện không có tài liệu `READY` nào → `409 NO_READY_DOCUMENTS` (SDD §3.5).
4. Có `documentIds`: `ready = DocumentService.filter_ready(ids)`. Nếu `ready != set(ids)` (id không tồn tại, `DELETED`, `UPLOADED`, `PROCESSING`, `FAILED`, `NOT_EXTRACTABLE`) → **`422 INVALID_SCOPE`** `[Proposed — mã mới, bổ sung vào danh mục SDD §3.5]`:

```json
{ "error": { "code": "INVALID_SCOPE",
             "message": "Một số tài liệu trong phạm vi không còn sẵn sàng. Vui lòng chọn lại.",
             "requestId": "…" } }
```

Lý do từ chối thay vì âm thầm lấy giao: nếu người dùng chọn Y nhưng Y vừa bị xóa, trả lời trên phần còn lại (hoặc "không tìm thấy") sẽ gây hiểu nhầm. Không tiết lộ thêm thông tin vì thư viện dùng chung (ASM-002).

### 4.2 Backend

```python
# app/documents/service.py
class DocumentService:
    async def filter_ready(self, ids: Sequence[UUID]) -> set[UUID]:
        """Trả tập id có status='READY'. Một truy vấn: SELECT id FROM document
        WHERE id = ANY(:ids) AND status = 'READY'."""

# app/conversations/schemas.py
class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: constr(min_length=1, max_length=2000)
    document_ids: conlist(UUID, min_length=1, max_length=100) | None = Field(None, alias="documentIds")

# app/answering/service.py
async def ask(self, conversation, question: str, scope: frozenset[UUID] | None) -> Answer: ...
```

- Router API-09 gọi `filter_ready` **trước** khi tạo `StreamingResponse`; ném `AppError("INVALID_SCOPE", 422, …)`.
- `scope` truyền nguyên vào `retrieval.vector(qvec, scope)` và `retrieval.text(query, scope)`; SQL vẫn lọc `d.status = 'READY'` (phòng tài liệu bị xóa giữa lúc kiểm tra và truy vấn — QAS-06).
- Bất biến kiểm thêm trong `AnswerService` (phòng thủ): mọi `citation.document_id ∈ scope` khi `scope` khác `None`; vi phạm → log lỗi + trả `NOT_FOUND` `[Proposed]`.
- `question_asked.scoped_documents`: `null` khi toàn thư viện, ngược lại danh sách UUID (không có tên tệp).

### 4.3 Frontend — bộ chọn phạm vi (màn 04)

**Vị trí:** bên phải thanh tiêu đề hội thoại (`.chat-head`), cùng hàng với `<h1>` tiêu đề hội thoại.

| Thành phần | Mô tả (bám `04_chat.html`) |
|---|---|
| Nút mở | `button.btn.btn-sm`, icon `layers` + nhãn + icon `chev`; `aria-expanded`, `aria-controls="scopePop"` |
| Nhãn nút | Toàn bộ: **"Phạm vi: toàn bộ thư viện (N)"** · Một phần: **"Phạm vi: K tài liệu"** (N = số tài liệu `READY`) |
| Popover | `role="group"`, `aria-label="Chọn tài liệu để giới hạn phạm vi câu hỏi"`; rộng 340 px (tối đa 90vw), neo phải, cách nút 6 px, bo 12 px, viền `--line2`, `--shadow`; danh sách cuộn khi dài (`max-height: 360px` `[Proposed]`) |
| Mục đầu | Checkbox "**Toàn bộ thư viện**" + dòng phụ muted "Mặc định · các tài liệu “Sẵn sàng”" |
| Mục tài liệu | Checkbox + tên tài liệu + dòng phụ "{pageCount} trang"; **chỉ tài liệu `READY`**, sắp theo tên `[Proposed]` |
| Chân popover | Chữ muted "Chỉ hiện tài liệu đã “Sẵn sàng”." + nút `btn-primary btn-sm` **"Xong"** |
| Chip trên ô nhập | Icon `layers` + "**Đang hỏi trên: toàn bộ thư viện (N tài liệu)**" hoặc "**Đang hỏi trên: {tên1}, {tên2}**" |

**Hành vi**
- Mặc định mọi checkbox được chọn = toàn bộ thư viện → gửi **không có** `documentIds` (tài liệu mới `READY` sau đó cũng được dùng).
- Bỏ chọn một phần → nhãn/chip đổi; gửi `documentIds` = các id đang chọn.
- Chọn đủ tất cả **hoặc** bỏ hết → tự quay về "Toàn bộ thư viện" (mọi ô được chọn lại), như script thiết kế.
- Bấm "Toàn bộ thư viện" → chọn lại tất cả.
- Đóng popover: nút "Xong", phím `Esc` (trả focus về nút mở), bấm ra ngoài.
- Nguồn dữ liệu: `GET /api/v1/documents?status=READY` (TanStack Query `['documents', {status:'READY'}]`), đọc hết các trang bằng `cursor`.
- Phạm vi giữ trong state theo `conversationId` (trong bộ nhớ); hội thoại mới mặc định toàn bộ thư viện `[Proposed]`.
- Khi danh sách tải lại mà tài liệu đã chọn không còn `READY` → bỏ khỏi lựa chọn; nếu không còn gì → về toàn bộ thư viện.
- Nhận `422 INVALID_SCOPE` → giữ câu hỏi trong ô nhập, làm mới danh sách tài liệu, hiện banner `warn` với `message` từ API `[Proposed]`.
- Nút "Chọn tài liệu" trong khung "Không tìm thấy" (màn 05-A) mở popover này.
- Mọi chuỗi lấy từ `i18n/vi.json` (khóa `chat.scope.*`, xem T-308).

```ts
// frontend/src/pages/Chat/scope.ts
export type Scope = { kind: 'all' } | { kind: 'some'; documentIds: string[] };
export function toRequest(scope: Scope): { documentIds?: string[] };
export function scopeLabel(scope: Scope, readyCount: number, t: TFunction): string;
```

File FE: `frontend/src/pages/Chat/ScopePicker.tsx`, `ScopeChip.tsx`, `scope.ts`, test `ScopePicker.test.tsx`.

## 5. Các bước thực hiện

1. Thêm `INVALID_SCOPE` vào bảng mã lỗi trong `platform/errors.py` (+ ghi chú `[Proposed]` cho Tech Lead cập nhật SDD §3.5).
2. Viết `DocumentService.filter_ready` + integration test với đủ 6 trạng thái.
3. Cập nhật `AskRequest` và router API-09 theo thứ tự kiểm tra §4.1; truyền `scope` vào `AnswerService.ask`.
4. Kiểm phòng thủ citation ⊂ scope trong `AnswerService`.
5. FE: `scope.ts` (thuần, có unit test) → `ScopePicker` → `ScopeChip` → nối vào gửi câu hỏi của T-209.
6. Xử lý `422 INVALID_SCOPE` trên FE.
7. So khớp giao diện với `chat_scope.png`; kiểm bàn phím (Tab, Space, Esc).

## 6. Tiêu chí chấp nhận

- [ ] Gửi không có `documentIds` → truy xuất trên toàn bộ tài liệu `READY` (hành vi như Sprint 2).
- [ ] `documentIds=[Y]` → mọi trích dẫn trong `final` có `documentId = Y` dù X cũng chứa thông tin liên quan (**AC-014**).
- [ ] `documentIds` chứa id không tồn tại / `DELETED` / `PROCESSING` / `NOT_EXTRACTABLE` / `FAILED` → `422 INVALID_SCOPE`, không mở SSE, không gọi AI, không lưu tin nhắn.
- [ ] `documentIds=[]`, id trùng, > 100 phần tử, hoặc không phải UUID → 422, không gọi AI.
- [ ] Popover chỉ liệt kê tài liệu `READY`; nhãn nút và chip đổi đúng 2 dạng chữ ở §4.3.
- [ ] Bỏ hết hoặc chọn đủ → quay về "Toàn bộ thư viện" và request không có `documentIds`.
- [ ] `Esc` đóng popover và trả focus về nút; `aria-expanded` phản ánh trạng thái.
- [ ] `question_asked.scoped_documents` là `null` hoặc danh sách UUID, không chứa tên tệp.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit (BE) | `AskRequest` với `[]`, trùng id, 101 id, chuỗi không phải UUID | Lỗi kiểm tra |
| Unit (FE) | `scope.ts`: chọn 2/3, 3/3, 0/3 | `some[2]`, `all`, `all`; `toRequest(all)` = `{}` |
| Unit (FE) | `ScopePicker`: Esc, bấm ngoài, "Xong" | Đóng, focus về nút |
| Integration | `filter_ready` với tài liệu ở 6 trạng thái | Chỉ id `READY` |
| Integration | API-09 X, Y đều chứa "thanh toán", scope `[Y]` (FakeLlm) | Mọi citation thuộc Y |
| Integration | API-09 scope chứa id vừa `DELETED` | 422 `INVALID_SCOPE`, không có bản ghi `message` mới |
| Integration | Xóa Y giữa lúc kiểm tra và truy vấn (giả lập) | SQL lọc `READY` → không trả chunk của Y |
| E2E | AC-014 trên UI | Xem T-311 |

## 8. Cấu hình

Không thêm biến môi trường. Giới hạn 100 id/lần hỏi là hằng số trong schema `[Proposed]`; dùng `RETRIEVAL_KV`, `RETRIEVAL_KT`, `RETRIEVAL_K`, `MAX_CHUNKS_PER_DOC` sẵn có.

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| `INVALID_SCOPE` là mã mới, SDD §3.5 chưa có; DD-06 mô tả "giao" (intersection) thay vì từ chối | Hợp đồng API | Dùng `[Proposed]`; Tech Lead xác nhận và cập nhật SDD |
| Phạm vi hẹp làm HNSW trả < `kv` | "Không tìm thấy" sai khi chọn 1 tài liệu | `SET LOCAL hnsw.ef_search = 100`; chiến lược quét theo T-309 |
| Thư viện ~500 tài liệu, `limit` tối đa 200 | Popover dài, nhiều trang | Đọc hết bằng `cursor`; cân nhắc ô tìm trong popover sau MVP (cần PO) |
| Phân quyền theo tài liệu (OQ-011) | Kiểm tra `filter_ready` phải thêm ACL | Gom kiểm tra vào một hàm để mở rộng |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §5.4, §6.5, §6.7
- [SAD](../../design/SAD.md) §2.3 (lọc phạm vi), §2.4 (API-09), §3.1 (nhất quán trạng thái)
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.5, §3.6.4 bước 1
- [User_Stories](../../design/User_Stories.md) US-C7
- Màn hình: [html_design/04_chat.html](../../design/html_design/04_chat.html), ảnh [chat_scope.png](../../design/images/chat_scope.png)
- Task liên quan: [T-203](./T-203-hybrid-retrieval.md), [T-209](./T-209-chat-screen-core.md), [T-212](./T-212-telemetry-qa.md), [T-309](./T-309-spike-sp01-latency.md), [T-311](./T-311-e2e-sprint3.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Mã `INVALID_SCOPE` được Tech Lead chấp thuận và có trong OpenAPI (mục lỗi của API-09).
