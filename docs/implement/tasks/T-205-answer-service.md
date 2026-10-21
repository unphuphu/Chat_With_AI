# T-205 — Xây AnswerService điều phối trả lời

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 2 |
| **Loại** | Backend |
| **User story** | US-C1, US-C2, US-C3, US-C4 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 3 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-201, T-203, T-204, T-206 |
| **Mở khóa (task chờ task này)** | T-207, T-301 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

`AnswerService.ask()` nhận một câu hỏi trong một hội thoại và trả kết quả cuối `ANSWERED` (có trích dẫn đã kiểm) hoặc `NOT_FOUND`, theo đúng pseudo-code Implement_plan §6.6: embed → truy xuất lai → Lớp 1 → LLM → Lớp 2 (thử lại 1 lần) → ánh xạ trích dẫn → lưu **một giao dịch** (tin nhắn trợ lý + trích dẫn + token + thời gian phản hồi).

## 2. Bối cảnh

- SAD §3.2.1 bước 5–13; Blueprint §3.6.2, §3.6.4 (DD-06); AD-07: không phát `token`, chỉ `status` + `final`.
- Bất biến (Blueprint §3.5): `ANSWERED` ⇒ `citations` không rỗng, mọi trích dẫn trỏ tới chunk đã truy xuất; `NOT_FOUND` ⇒ `citations` rỗng.
- `citation.document_name_snapshot` giữ tên tại thời điểm trả lời (SAD §3.1).
- Module `answering` không truy cập SQL trực tiếp (SAD §2.2) → lưu qua `ConversationService.record_answer()`.
- Viết lại câu hỏi nối tiếp (`LlmPort.rewrite`) thuộc T-301 (Sprint 3); task này để sẵn điểm mở rộng.

## 3. Phạm vi

**Trong phạm vi**
- `backend/app/answering/service.py` (`AnswerService`), `backend/app/answering/citations.py` (`map_citations`, `render_markers`).
- `ConversationService.record_answer()` + repository trong `backend/app/conversations/`.
- Timeout cơ bản cho lời gọi AI; ánh xạ lỗi sang `UPSTREAM_TIMEOUT`/`UPSTREAM_UNAVAILABLE`.
- Wiring trong composition root `backend/app/main.py`.

**Ngoài phạm vi** (để tránh làm thừa)
- HTTP/SSE, lưu tin nhắn người dùng, kiểm `NO_READY_DOCUMENTS` (T-207).
- `rewrite` (T-301); retry 429/5xx + circuit breaker qua `call_upstream()` (T-305); giới hạn tốc độ (T-306).
- Sự kiện `question_asked`/`answer_returned` (T-212 thêm vào giao dịch `record_answer`). Metric Prometheus (T-404).

## 4. Thiết kế chi tiết

```python
Stage = Literal["retrieving", "generating"]

@dataclass(frozen=True)
class CitationView:   ordinal: int; document_id: UUID; document_name: str; page: int
@dataclass(frozen=True)
class AnswerResult:
    message_id: UUID; answer_type: Literal["ANSWERED", "NOT_FOUND"]
    content: str; citations: list[CitationView]; response_time_ms: int

class AnswerService:
    def __init__(self, *, embedding: EmbeddingPort, llm: LlmPort, retrieval: RetrievalService,
                 policy: NotFoundPolicy, validator: CitationValidator,
                 conversations: ConversationService, documents: DocumentService,
                 settings: Settings, clock: Callable[[], float] = time.monotonic): ...

    async def ask(self, *, user: CurrentUser, conversation: Conversation, question: str,
                  scope: list[UUID] | None, started_at: float,
                  on_stage: Callable[[Stage], Awaitable[None]]) -> AnswerResult
```

`started_at` = thời điểm API nhận yêu cầu (T-207 truyền `time.monotonic()`), để `response_time_ms` tính cả các bước trước.

**Luồng `ask()`** (bám Implement_plan §6.6):

```python
await on_stage("retrieving")
query = question                       # T-301: thay bằng rewrite(history, question) khi có lịch sử
qvec = (await with_timeout(self.embedding.embed([query]), EMBED_TIMEOUT_S))[0]
r = await self.retrieval.search(qvec, query, scope)          # 2 truy vấn song song (T-203)

if self.policy.should_refuse(r.best_vector_score, has_text_match=r.has_text_match):
    return await self._persist_not_found(...)                # Lớp 1: KHÔNG gọi LLM

hits = await self.retrieval.with_neighbors(self.retrieval.fuse(r.vector_hits, r.text_hits))
chunks = [ContextChunk(ref=f"c{i}", ...) for i, h in enumerate(hits, start=1)]

await on_stage("generating")
out = await with_timeout(self.llm.generate(build_prompt(question, chunks)), ANSWER_TIMEOUT_S)
v = self.validator.validate(out, chunks)
if not v.ok and v.failure != ValidationFailure.NOT_ANSWERABLE:
    out2 = await with_timeout(self.llm.generate(build_prompt(question, chunks, reminder=True)), ANSWER_TIMEOUT_S)
    tokens += out2 tokens; out, v = out2, self.validator.validate(out2, chunks)
if not v.ok:
    return await self._persist_not_found(...)                # Lớp 2
citations, content = map_citations(out, chunks)
citations = await self._drop_no_longer_ready(citations)      # [Proposed] tài liệu bị xóa trong lúc sinh
if not citations:
    return await self._persist_not_found(...)
return await self._persist_answered(content, citations, ...)
```

- `build_prompt` lấy **câu hỏi gốc** (không phải `query` đã viết lại) — như §6.6.
- Đầu ra LLM không parse được JSON → adapter ném `LlmAnswerInvalid` (lỗi port mới `[Proposed]` trong `app/ports/errors.py`, T-007 chưa có — T-208 thêm); AnswerService coi như `UNKNOWN_ID` (được thử lại 1 lần) `[Proposed]`.
- `with_timeout`: `asyncio.timeout()`; `TimeoutError` → `AppError("UPSTREAM_TIMEOUT", 504)`; `UpstreamUnavailable` (lỗi port, T-007) → `AppError("UPSTREAM_UNAVAILABLE", 503)`. Không lưu tin nhắn trợ lý khi lỗi.
- `asyncio.CancelledError` (client ngắt, T-207) **phải lan ra ngoài**, không bắt, không lưu gì.

**Ánh xạ trích dẫn** (`citations.py`, thuần hàm):

1. Duyệt `out.cited_chunk_ids` theo thứ tự, bỏ id trùng; mỗi `ref` → `ContextChunk`.
2. Gom theo cặp `(document_id, page)`: cặp mới → `ordinal` kế tiếp (bắt đầu 1, **theo từng tin nhắn** `[Proposed]`); giữ `chunk_id` của chunk đầu tiên trong cặp.
3. Trong `content`, thay mỗi đánh dấu `[cN]` (regex `\[c(\d+)\]`) bằng `[ordinal]` của cặp chứa `cN`; đánh dấu trỏ tới `ref` không nằm trong `cited_chunk_ids` → xóa; gộp đánh dấu trùng liền nhau (`[1][1]` → `[1]`).
4. `document_name_snapshot` = `ContextChunk.document_name` (tên lấy từ `document.name` lúc truy xuất).

Ví dụ: `cited=["c3","c1","c4"]`, `c3`=(A,12), `c1`=(A,14), `c4`=(A,12) → ordinal 1=(A,12, chunk c3), 2=(A,14); nội dung "…cuối cùng [c4]." → "…cuối cùng [1]."

**Lưu một giao dịch** — `ConversationService.record_answer()`:

```python
async def record_answer(self, *, conversation_id: UUID, user_id: UUID,
                        answer_type: Literal["ANSWERED", "NOT_FOUND"], content: str,
                        citations: list[CitationDraft], response_time_ms: int,
                        tokens_in: int, tokens_out: int) -> UUID   # message_id
```

Một `async with session.begin()`: `set_rls_user` → `INSERT message(role='assistant', …)` → `INSERT citation` (n dòng) → (T-212: `analytics.emit(...)`) → commit. `NOT_FOUND`: `content = ""` `[Proposed]` (giao diện hiển thị khối riêng từ i18n), `tokens_in/out` = tổng mọi lần gọi `generate` (0 nếu Lớp 1), `citations = []`.

**Log/trace** (không văn bản): `question_length`, `scope_size`, `best_vector_score`, `has_text_match`, `layer1_refused`, `context_chunks`, `validation_failure`, `retried`, `answer_type`, `citation_count`, `tokens_in/out`, `prompt_version`, thời lượng từng bước (`embed`, `retrieve`, `generate`, `validate`).

## 5. Các bước thực hiện

1. Viết `citations.py` + test đơn vị (ánh xạ, loại trùng, thay đánh dấu).
2. Viết `ConversationService.record_answer()` + repository `insert_assistant_message_with_citations()`.
3. Viết `AnswerService` theo luồng trên; thêm `DocumentService.ready_ids(ids) -> set[UUID]` cho `_drop_no_longer_ready` nếu chưa có.
4. Wiring trong `main.py`: khởi tạo `NotFoundPolicy(settings.RELEVANCE_THRESHOLD)`, `CitationValidator()`, adapter theo `AI_PROVIDER`.
5. Viết test tích hợp với `FakeEmbedding` + `FakeLlm` (tham số `script`, `delay_s`, `fail_with` của T-007: trích dẫn hợp lệ, id lạ, `answerable=false`, chậm, lỗi) và PostgreSQL thật.
6. Kiểm log không chứa câu hỏi/câu trả lời (fixture bắt log + assert).

## 6. Tiêu chí chấp nhận

- [ ] Lớp 1 từ chối → kết quả `NOT_FOUND`, `FakeLlm.generate` được gọi **0 lần**, `on_stage("generating")` không được gọi.
- [ ] Đầu ra hợp lệ ngay lần đầu → `generate` gọi đúng 1 lần, kết quả `ANSWERED`, ≥ 1 trích dẫn.
- [ ] Lần 1 `UNKNOWN_ID`, lần 2 hợp lệ → `ANSWERED`, `generate` gọi 2 lần, `tokens_in/out` = tổng 2 lần.
- [ ] Hai lần đều sai → `NOT_FOUND`, `citations = []`; `answerable=false` → `NOT_FOUND` sau **1** lần gọi.
- [ ] Mọi `ANSWERED` được lưu có ≥ 1 dòng `citation`; mọi `citation.chunk_id` thuộc tập chunk đã truy xuất của lượt hỏi đó.
- [ ] Hai chunk cùng (tài liệu, trang) được trích → một `ordinal`; `ordinal` liên tục 1..n; `content` chỉ còn đánh dấu `[n]` với n ∈ 1..n.
- [ ] Tin nhắn + trích dẫn + `response_time_ms` + `tokens_in/out` ghi trong **một** giao dịch: lỗi khi chèn `citation` → không còn dòng `message` trợ lý nào.
- [ ] LLM vượt `ANSWER_TIMEOUT_S` → `AppError UPSTREAM_TIMEOUT`, không có tin nhắn trợ lý; hủy task giữa chừng → không có tin nhắn trợ lý.
- [ ] Tài liệu chuyển `DELETED` trong lúc sinh → trích dẫn của nó bị loại; không còn trích dẫn → `NOT_FOUND`.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `map_citations`: ví dụ ở mục 4 | Ordinal 1=(A,12), 2=(A,14); nội dung đổi đúng |
| Unit | Đánh dấu `[c7]` không có trong `cited_chunk_ids` | Bị xóa khỏi `content` |
| Unit | `cited=["c2","c2"]` | Một trích dẫn |
| Integration | Câu hỏi không khớp từ khóa, điểm vector thấp (Fake) | `NOT_FOUND`, 0 lần `generate` |
| Integration | FakeLlm trích chunk của 2 tài liệu | 2 trích dẫn, 2 `documentId` khác nhau (AC-009 luồng) |
| Integration | FakeLlm `invalid_ids` 2 lần | `NOT_FOUND`, `generate` 2 lần |
| Integration | FakeLlm chậm 5 s, `ANSWER_TIMEOUT_S=1` | `UPSTREAM_TIMEOUT` |
| Integration | Hủy task sau `on_stage("generating")` | `CancelledError` lan ra; 0 tin nhắn trợ lý |
| Integration | Lỗi chèn `citation` (giả lập) | Rollback toàn bộ |
| Integration | Bắt log toàn bộ luồng | Không chứa chuỗi câu hỏi, nội dung trả lời hay văn bản chunk |

## 8. Cấu hình

| Biến | Mặc định | Ghi chú |
|---|---|---|
| `ANSWER_TIMEOUT_S` | `60` | Timeout `generate` (SAD §4.2) |
| `RELEVANCE_THRESHOLD` | `0.30` `[Default]` | `[TBD: OQ-008]`, T-310 |
| `RETRIEVAL_*`, `MAX_CHUNKS_PER_DOC`, `EMBEDDING_MODEL` | xem T-203 | |
| `AI_PROVIDER` | `fake` | Thật sau OQ-006 (T-208) |
| Timeout embedding đường hỏi | 15 s | SAD §4.2; hằng số tạm, chuyển vào cấu hình của `call_upstream()` ở T-305 |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Màn 04 đánh số trích dẫn **liên tục trong cả hội thoại** (lượt 2 có [3] và dùng lại [1]); plan chỉ có `citation.ordinal` theo tin nhắn | Số hiệu khác thiết kế | `[Proposed]` đánh số theo tin nhắn; PO/thiết kế xác nhận. Nếu cần đánh số theo hội thoại: chỉ đổi `map_citations` (đọc trích dẫn trước đó của hội thoại) |
| Tin nhắn người dùng đã lưu (T-207) nhưng lượt hỏi lỗi | Lịch sử có câu hỏi không có trả lời | Chấp nhận; T-307 xử lý "Gửi lại" |
| Hủy đúng lúc giao dịch vừa commit | Tin nhắn đã lưu nhưng không gửi được `final` | Chấp nhận; lần tải lại hội thoại sẽ thấy câu trả lời |
| Ngưỡng chưa hiệu chỉnh `[TBD: OQ-008]` | Tỷ lệ `NOT_FOUND` sai cao/thấp | T-310 |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §2 (luồng hỏi), §4.1, §6.6
- [SAD](../../design/SAD.md) §2.2, §3.1, §3.2.1, §4.1.5, §4.2, §5 AD-07
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.5, §3.6.2, §3.6.4
- [User_Stories](../../design/User_Stories.md) US-C1…C4
- Màn hình: [html_design/04_chat.html](../../design/html_design/04_chat.html)
- Task liên quan: [T-203](./T-203-hybrid-retrieval.md), [T-204](./T-204-notfound-policy-citation-validator.md), [T-206](./T-206-prompt-v1.md), [T-207](./T-207-messages-sse-api.md), [T-212](./T-212-telemetry-qa.md), [T-301](./T-301-follow-up-rewrite.md), [T-305](./T-305-upstream-resilience.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] `import-linter` pass: `answering` không import `app.adapters.*` hay SDK AI.
