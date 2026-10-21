# T-203 — Xây truy xuất lai (vector + full-text + RRF)

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 2 |
| **Loại** | Backend |
| **User story** | US-C1, US-C2 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 3 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-007, T-104 |
| **Mở khóa (task chờ task này)** | T-205, T-302, T-309 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Module `retrieval` trả được tập đoạn liên quan nhất cho một câu hỏi: hai truy vấn song song (HNSW vector + GIN full-text), chỉ trên tài liệu `READY` trong phạm vi và cùng `embedding_model` hiện hành, hợp nhất bằng RRF, tối đa `MAX_CHUNKS_PER_DOC` đoạn/tài liệu, bổ sung đoạn kề cùng trang; đồng thời **phơi ra điểm vector tốt nhất trước RRF** cho `NotFoundPolicy`.

## 2. Bối cảnh

- SAD §3.2.1 bước 8; Implement_plan §6.5 (SQL mẫu, RRF); Blueprint §3.6.4 bước 1, 3, 4 (DD-06).
- BRU-002/QAS-06: tài liệu không `READY` **không bao giờ** được trả về — `retrieval` luôn `JOIN document` và lọc `status = 'READY'` (SAD §3.1).
- BR-009/AC-009: giới hạn số đoạn mỗi tài liệu để đa dạng nguồn.
- DD-04: chunk không vượt trang → thông tin vắt trang được bù bằng đoạn kề.
- DR-04: chỉ so sánh vector cùng `embedding_model` (SAD §3.1 "Phiên bản embedding").

## 3. Phạm vi

**Trong phạm vi**
- `RetrievalService` với `vector_search`, `text_search`, `fuse` (RRF + cap), `with_neighbors`, `search` (tiện ích gói các bước), `get_chunk_texts` (dùng ở T-202).
- Tham số `scope: list[UUID] | None` (lọc theo phạm vi đã có từ đầu; giao diện chọn phạm vi là T-302).
- Test tích hợp trên PostgreSQL thật (Testcontainers + pgvector).

**Ngoài phạm vi** (để tránh làm thừa)
- Embed câu hỏi (AnswerService gọi `EmbeddingPort`, T-205).
- Quyết định "không tìm thấy" (T-204/T-205).
- Chọn quét lặp hay quét chính xác khi lọc phạm vi hẹp — quyết định bằng SP-01 (T-309).
- Hiệu chỉnh `k`, ngưỡng (T-310).

## 4. Thiết kế chi tiết

**File:** `backend/app/retrieval/{service.py, sql.py, rrf.py, models.py}`; test `backend/tests/unit/test_rrf.py`, `backend/tests/integration/test_retrieval.py`.

```python
@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: UUID; document_id: UUID; document_name: str
    page: int; chunk_index: int; text: str
    score: float | None          # điểm của kênh trả về nó; None với đoạn kề

@dataclass(frozen=True)
class RetrievalResult:
    vector_hits: list[RetrievedChunk]
    text_hits: list[RetrievedChunk]
    best_vector_score: float | None    # max(score) của vector_hits, TRƯỚC RRF; None nếu rỗng
    has_text_match: bool               # len(text_hits) > 0

class RetrievalService:
    async def vector_search(self, qvec: list[float], scope: list[UUID] | None) -> list[RetrievedChunk]
    async def text_search(self, query: str, scope: list[UUID] | None) -> list[RetrievedChunk]
    async def search(self, qvec: list[float], query: str, scope: list[UUID] | None) -> RetrievalResult
    def fuse(self, vector_hits, text_hits) -> list[RetrievedChunk]          # thuần Python
    async def with_neighbors(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]
    async def get_chunk_texts(self, chunk_ids: list[UUID]) -> dict[UUID, str]
```

`search()` chạy `vector_search` và `text_search` bằng `asyncio.gather` trên **hai phiên CSDL riêng** (một phiên không chạy song song hai câu lệnh). AnswerService (T-205) gọi `search()` → đưa `best_vector_score`, `has_text_match` cho `NotFoundPolicy` → nếu không từ chối mới gọi `fuse()` + `with_neighbors()`.

**SQL (a) vector** — Implement_plan §6.5, thêm `d.name`, `c.chunk_index` vào danh sách cột `[Proposed]` (cần cho snapshot tên và đoạn kề):

```sql
SET LOCAL hnsw.ef_search = 100;          -- giá trị từ RETRIEVAL_EF_SEARCH
SET LOCAL statement_timeout = '3s';      -- SAD §4.2: truy xuất 3 s
SELECT c.id, c.document_id, d.name AS document_name, c.page, c.chunk_index, c.text,
       1 - (c.embedding <=> :qvec) AS score
FROM chunk c JOIN document d ON d.id = c.document_id
WHERE d.status = 'READY' AND c.embedding_model = :model
  AND (:scope_is_null OR c.document_id = ANY(:scope))
ORDER BY c.embedding <=> :qvec
LIMIT :kv;
```

**SQL (b) full-text:**

```sql
SET LOCAL statement_timeout = '3s';
SELECT c.id, c.document_id, d.name AS document_name, c.page, c.chunk_index, c.text,
       ts_rank(c.keywords, plainto_tsquery('simple', f_unaccent(:q))) AS score
FROM chunk c JOIN document d ON d.id = c.document_id
WHERE d.status = 'READY'
  AND (:scope_is_null OR c.document_id = ANY(:scope))
  AND c.keywords @@ plainto_tsquery('simple', f_unaccent(:q))
ORDER BY score DESC
LIMIT :kt;
```

- `:model` = `settings.EMBEDDING_MODEL`; `:kv` = `RETRIEVAL_KV`; `:kt` = `RETRIEVAL_KT`; `:scope` truyền kiểu `uuid[]`, `:scope_is_null` = `scope is None`.
- `SET LOCAL` cần giao dịch: mỗi truy vấn chạy trong `async with session.begin():` riêng.
- `f_unaccent` là hàm `IMMUTABLE` tạo ở T-004. Nếu `query` sau khi bỏ dấu không còn từ nào (chỉ dấu câu) → bỏ qua truy vấn (b), trả `[]`.
- Vector truyền qua `pgvector` (đăng ký codec cho asyncpg).

**RRF + cap** (thuần Python, `rrf.py`):

```python
RRF_K = 60   # SAD §2.3

def rrf(vector_hits, text_hits, k=RRF_K) -> list[UUID]:
    score = defaultdict(float)
    for hits in (vector_hits, text_hits):
        for rank, h in enumerate(hits, start=1):
            score[h.chunk_id] += 1 / (k + rank)
    return sorted(score, key=lambda cid: (-score[cid], str(cid)))   # phá hòa ổn định

def cap_per_document(ranked_ids, by_id, max_per_doc) -> list[UUID]: ...
# fuse() = cap_per_document(rrf(...), max_per_doc=MAX_CHUNKS_PER_DOC)[:RETRIEVAL_K]
```

**Đoạn kề** (`with_neighbors`): với mỗi đoạn đã chọn, lấy `chunk_index ± 1` **cùng `document_id` và cùng `page`**, cùng điều kiện `READY` + `embedding_model`:

```sql
SELECT c.id, c.document_id, d.name, c.page, c.chunk_index, c.text
FROM chunk c JOIN document d ON d.id = c.document_id
JOIN unnest(:doc_ids::uuid[], :pages::int[], :idxs::int[]) AS t(document_id, page, chunk_index)
  ON c.document_id = t.document_id AND c.page = t.page
 AND c.chunk_index IN (t.chunk_index - 1, t.chunk_index + 1)
WHERE d.status = 'READY' AND c.embedding_model = :model;
```

Thứ tự kết quả: giữ thứ tự RRF; đoạn kề chèn ngay trước/sau đoạn gốc theo `chunk_index`; loại trùng theo `chunk_id` (giữ vị trí xuất hiện đầu). Đoạn kề có `score = None` và **được** đưa vào ngữ cảnh/trích dẫn như đoạn thường.

**Log** (không có văn bản): `vector_hits`, `text_hits`, `best_vector_score`, `fused`, `with_neighbors`, `duration_ms`, `scope_size`.

## 5. Các bước thực hiện

1. Viết `models.py`, `rrf.py` + test đơn vị RRF/cap trước.
2. Viết `sql.py` (hằng `text()` cho 3 truy vấn) và `service.py`.
3. Đăng ký codec pgvector trong engine (`platform/db.py`) nếu T-004/T-104 chưa làm.
4. Viết fixture tích hợp: tạo tài liệu ở các trạng thái, chunk với vector điều khiển được (vector đơn vị theo trục) và văn bản có/không dấu.
5. Viết test tích hợp theo bảng mục 7; đo thời gian truy vấn trên ~10⁴ chunk sinh tổng hợp để có số tham khảo cho SP-01.
6. Viết `get_chunk_texts` (dùng ở T-202).

## 6. Tiêu chí chấp nhận

- [ ] Chunk của tài liệu `UPLOADED`, `PROCESSING`, `NOT_EXTRACTABLE`, `FAILED`, `DELETED` không bao giờ xuất hiện trong `vector_hits`, `text_hits`, kết quả `fuse()` hay `with_neighbors()`.
- [ ] Chunk có `embedding_model` khác `EMBEDDING_MODEL` không xuất hiện trong `vector_hits` và đoạn kề.
- [ ] Với `scope=[Y]`, mọi đoạn trả về thuộc tài liệu Y; `scope=None` tìm trên toàn bộ `READY`.
- [ ] `fuse()` trả ≤ `RETRIEVAL_K` (8) đoạn và ≤ `MAX_CHUNKS_PER_DOC` (3) đoạn mỗi tài liệu.
- [ ] `best_vector_score` = điểm cosine lớn nhất của `vector_hits` (trước RRF); `None` khi không có hit.
- [ ] Câu hỏi "thanh toan" (không dấu) khớp chunk chứa "thanh toán" qua kênh full-text.
- [ ] Đoạn kề chỉ lấy cùng trang, không vượt sang trang khác; không trùng `chunk_id`.
- [ ] Phạm vi hẹp (1 tài liệu 10 chunk trong 2.000 chunk): `vector_hits` trả đủ 10 đoạn (không "mất" kết quả do HNSW).

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | RRF: id có ở cả hai danh sách hạng 1 | Đứng đầu, điểm = 2/61 |
| Unit | RRF: hòa điểm | Thứ tự ổn định giữa các lần chạy |
| Unit | Cap: 5 hit cùng tài liệu + 2 tài liệu khác | Tối đa 3 của tài liệu đầu, tổng ≤ 8 |
| Unit | Một danh sách rỗng | RRF chỉ theo danh sách còn lại |
| Integration | Tài liệu `DELETED` có vector gần nhất | Không xuất hiện |
| Integration | Hai `embedding_model` cùng tồn tại | Chỉ model hiện hành |
| Integration | `scope` gồm tài liệu `FAILED` | Không trả đoạn của nó |
| Integration | Đoạn kề ở trang khác (`chunk_index` liền kề nhưng `page` khác) | Không được thêm |
| Integration | Phạm vi hẹp với `ef_search=100` | Đủ kết quả; nếu thiếu, ghi nhận cho SP-01 (quét lặp `hnsw.iterative_scan` `[Verify]` pgvector ≥ 0.8) |
| Integration | Câu hỏi chỉ có dấu câu | `text_hits = []`, không lỗi SQL |

## 8. Cấu hình

| Biến | Mặc định | Ghi chú |
|---|---|---|
| `RETRIEVAL_KV`, `RETRIEVAL_KT`, `RETRIEVAL_K`, `MAX_CHUNKS_PER_DOC` | `20`, `20`, `8`, `3` | Implement_plan §3.3; hiệu chỉnh ở T-310 `[TBD: OQ-008]` |
| `EMBEDDING_MODEL` | `fake-384` `[Default]` | Lọc `chunk.embedding_model` |
| `RETRIEVAL_EF_SEARCH` | `100` | `[Proposed]` biến mới cho `hnsw.ef_search` (SAD §2.3: 80–100); thêm vào `.env.example` |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| `plainto_tsquery` nối các từ bằng AND; với cấu hình `simple` (không bỏ stopword) câu hỏi dài hiếm khi khớp toàn bộ | Kênh full-text gần như rỗng → `has_text_match` ít khi đúng, Lớp 1 dựa gần hết vào vector | Giữ SQL chuẩn của plan; đo tỷ lệ `text_hits > 0` trên bộ câu hỏi (T-211); nếu thấp, đề xuất `websearch_to_tsquery`/OR các từ ở T-310 |
| Lọc phạm vi làm HNSW trả thiếu | Mất kết quả khi phạm vi hẹp | Test ở mục 7; quyết định quét lặp/quét chính xác ở SP-01 (T-309) |
| `FakeEmbedding` (T-007) dùng feature hashing theo từ → chỉ phản ánh trùng từ, không phải ngữ nghĩa | Điểm vector và `RELEVANCE_THRESHOLD` với adapter giả không phản ánh chất lượng thật | Test tích hợp dùng vector điều khiển được; chất lượng đo bằng CMP-17 với AI thật |
| Số chiều `vector(N)` và giới hạn 2.000 chiều của HNSW `[Verify]` | Đổi mô hình có thể phải đổi kiểu cột | Xử lý ở T-208 |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §3.1 (quy tắc module), §3.3, §6.1 (ghi chú `embedding_model`, `f_unaccent`), §6.5
- [SAD](../../design/SAD.md) §2.3 (chỉ mục, RRF, lọc phạm vi), §3.1, §3.2.1 bước 8–9, §4.2 (timeout), §7 SP-01
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.6.4 (DD-06), §3.4 (DD-04)
- [User_Stories](../../design/User_Stories.md) US-C1, US-C2
- Task liên quan: [T-104](./T-104-ingest-worker.md), [T-204](./T-204-notfound-policy-citation-validator.md), [T-205](./T-205-answer-service.md), [T-302](./T-302-document-scope.md), [T-309](./T-309-spike-sp01-latency.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] `import-linter` pass: `retrieval` chỉ import `app.ports`, `app.platform`, không import `app.adapters`.
- [ ] Ghi số đo thời gian truy vấn (P50/P90 trên ~10⁴ chunk local) vào mô tả PR để T-309 dùng làm mốc.
