# T-007 — Định nghĩa các port AI/PDF và adapter giả FakeEmbedding, FakeLlm

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 0 |
| **Loại** | Backend |
| **User story** | — nền tảng (US-C1…C4 chạy được với AI giả) |
| **Ưu tiên** | P0 |
| **Ước lượng** | 1 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-003 |
| **Mở khóa (task chờ task này)** | T-104, T-203, T-204, T-206, T-208, T-305 |
| **Người thực hiện** | _chưa giao_ (BE) |
| **Trạng thái** | To do |

## 1. Mục tiêu

Lõi nghiệp vụ có hợp đồng ổn định `LlmPort`, `EmbeddingPort`, `PdfTextPort` (và các kiểu dữ liệu, ngoại lệ đi kèm), cùng adapter giả **xác định** `FakeEmbedding` và `FakeLlm` để mọi luồng ingest/truy xuất/trả lời chạy và kiểm thử được khi chưa có quyết định OQ-006. Chọn adapter bằng `AI_PROVIDER` tại composition root.

## 2. Bối cảnh

- AD-03: AI sau port + cấu hình theo môi trường vì OQ-006 chưa chốt ([SAD §5](../../design/SAD.md#5-nhật-ký-quyết-định-kiến-trúc-architecture-decision-log)); không gửi dữ liệu thật tới AI nào cho tới khi có OQ-006 ([Implement_plan §9.1](../Implement_plan.md#91-quyết-định-cần-có-và-ảnh-hưởng-tới-lập-trình)).
- Hợp đồng nghiệp vụ của port: [Blueprint §3.5](../../design/Blueprint_Design.md#35-interface-view) — `generate` trả `{answerable, content, citedChunkIds[]}`; `rewrite` trả câu hỏi độc lập; `embed` danh sách văn bản → vector cùng số chiều.
- Implement_plan §5.1: `FakeEmbedding` = vector xác định từ hash văn bản; `FakeLlm` = trả JSON trích dẫn chunk đầu tiên hoặc `answerable=false`.
- Lõi không import adapter/SDK; chỉ `app/main.py`, `app/worker.py` khởi tạo adapter ([Implement_plan §3.1](../Implement_plan.md#31-cấu-trúc-repository-monorepo)).

## 3. Phạm vi

**Trong phạm vi**
- `app/ports/llm.py`, `embedding.py`, `pdf_text.py`, `errors.py`.
- `app/adapters/fake/embedding.py` (`FakeEmbedding`), `app/adapters/fake/llm.py` (`FakeLlm`).
- `app/adapters/factory.py`: `build_llm(settings)`, `build_embedding(settings)`; gọi từ `main.py`/`worker.py`.
- Bộ test hợp đồng tái dùng cho adapter thật ở T-208.

**Ngoài phạm vi**
- `FileStorePort` + S3 ([T-102](./T-102-file-store-s3-adapter.md)); `IdentityPort` ([T-006](./T-006-auth-session-dev-identity.md)).
- Adapter `pypdfium2` cho `PdfTextPort` ([T-104](./T-104-ingest-worker.md), dựa trên kết luận [T-008](./T-008-spike-sp03-pdf-extraction.md)).
- Nội dung prompt ([T-206](./T-206-prompt-v1.md)); timeout/retry/circuit breaker `call_upstream()` ([T-305](./T-305-upstream-resilience.md)); adapter AI thật ([T-208](./T-208-real-ai-adapters-reindex.md)).

## 4. Thiết kế chi tiết

**Kiểu dữ liệu và port** (thuần Python, không phụ thuộc SDK):

```python
# app/ports/llm.py
@dataclass(frozen=True)
class PromptChunk:
    ref: str              # định danh mô hình phải trả lại trong citedChunkIds (T-206 chọn nhãn "c1" hay UUID)
    chunk_id: UUID
    document_name: str
    page: int
    text: str

@dataclass(frozen=True)
class LlmPrompt:
    system: str
    user: str
    question: str
    context: tuple[PromptChunk, ...]
    response_schema: Mapping[str, Any]     # JSON schema {answerable, content, citedChunkIds}
    prompt_version: str                    # ví dụ "v1" (T-206)

@dataclass(frozen=True)
class LlmAnswer:
    answerable: bool
    content: str
    cited_chunk_ids: tuple[str, ...]       # giá trị thô từ mô hình; CitationValidator (T-204) kiểm
    tokens_in: int
    tokens_out: int

@dataclass(frozen=True)
class Turn: role: Literal["user", "assistant"]; content: str

@dataclass(frozen=True)
class RewriteResult: text: str; tokens_in: int; tokens_out: int

class LlmPort(Protocol):
    async def generate(self, prompt: LlmPrompt) -> LlmAnswer: ...
    async def rewrite(self, history: Sequence[Turn], question: str) -> RewriteResult: ...

# app/ports/embedding.py
class EmbeddingPort(Protocol):
    model: str                              # ghi vào chunk.embedding_model
    dim: int
    max_batch_size: int
    async def embed(self, texts: Sequence[str]) -> list[list[float]]: ...   # cùng thứ tự, mỗi vector len == dim

# app/ports/pdf_text.py  (interface; adapter ở T-104)
@dataclass(frozen=True)
class PageText: page_no: int; text: str     # page_no bắt đầu từ 1

class PdfTextPort(Protocol):
    def extract_pages(self, pdf_path: Path, *, timeout_s: int) -> list[PageText]: ...

# app/ports/errors.py
class UpstreamTimeout(Exception): ...       # ánh xạ UPSTREAM_TIMEOUT (504)
class UpstreamUnavailable(Exception): ...   # ánh xạ UPSTREAM_UNAVAILABLE (503)
class PdfExtractionError(Exception): ...    # PDF hỏng / mã hóa
class PdfExtractionTimeout(PdfExtractionError): ...
```

Mọi phương thức async phải hủy được (tôn trọng `asyncio.CancelledError`) để T-207 hủy lời gọi khi client ngắt.

**`FakeEmbedding`** (`model = settings.EMBEDDING_MODEL` mặc định `fake-384`, `dim = settings.EMBEDDING_DIM`, `max_batch_size = 64`):
1. Chuẩn hóa: Unicode NFC → chữ thường → bỏ dấu (tương đương `unaccent`, ví dụ dùng `unicodedata` NFD bỏ ký tự kết hợp, `đ→d`) → tách token `\w+`.
2. Feature hashing `[Proposed]`: với mỗi token, `h = int.from_bytes(sha256(token).digest()[:8], "big")`; `idx = h % dim`; dấu `+1` nếu bit 63 của `h` = 0, ngược lại `-1`; cộng vào vector.
3. Chuẩn hóa L2. Văn bản rỗng/không token → vector đơn vị `e_0`.
4. **Không** dùng `hash()` của Python (thay đổi theo tiến trình). Kết quả: cùng văn bản → cùng vector ở mọi tiến trình; văn bản chung nhiều từ → cosine cao, giúp test truy xuất (T-203) có ý nghĩa.

**`FakeLlm`**

```python
class FakeLlm(LlmPort):
    def __init__(self, *, script: Callable[[LlmPrompt], LlmAnswer] | None = None,
                 fail_with: Exception | None = None, delay_s: float = 0.0) -> None: ...
```

| Điều kiện | `generate` trả |
|---|---|
| `fail_with` đặt | ném ngoại lệ đó (để test T-305/T-307: `UpstreamTimeout`, `UpstreamUnavailable`) |
| `script` đặt | kết quả của `script(prompt)` (kịch bản cho T-205, T-213) |
| `prompt.context` rỗng | `LlmAnswer(answerable=False, content="", cited_chunk_ids=(), …)` |
| mặc định | `answerable=True`, `content = "Theo tài liệu: " + 200 ký tự đầu của context[0].text + " [1]"`, `cited_chunk_ids=(context[0].ref,)` |

`rewrite`: mặc định trả nguyên `question` (để T-301 dùng `script`/subclass cho kịch bản nối tiếp). `tokens_in/out` = số từ của `system+user` / `content` (đủ cho test báo cáo token). `delay_s > 0` → `await asyncio.sleep(delay_s)` (test hủy, timeout).

**Factory** (`app/adapters/factory.py`):

```python
def build_embedding(settings: Settings) -> EmbeddingPort: ...   # "fake" → FakeEmbedding; khác → ValueError tới khi T-208
def build_llm(settings: Settings) -> LlmPort: ...               # "fake" → FakeLlm()
```

Khi `AI_PROVIDER=fake` và `APP_ENV in {"staging","production"}` → log cảnh báo một lần khi khởi động (không chặn, vì staging có thể chạy giả trong lúc chờ OQ-006) `[Proposed]`.

## 5. Các bước thực hiện

1. Viết `app/ports/*.py` với dataclass, Protocol, ngoại lệ; docstring nêu bất biến (độ dài vector, thứ tự, hủy được).
2. Viết `FakeEmbedding` + test đơn vị.
3. Viết `FakeLlm` + test đơn vị.
4. Viết `factory.py`; nối vào `create_app()` (lưu vào `app.state`) và `worker.py`.
5. Viết test hợp đồng `tests/contract/test_embedding_port.py`, `test_llm_port.py` tham số hóa theo danh sách adapter (hiện chỉ fake).
6. Kiểm `lint-imports` vẫn xanh (lõi không import `app.adapters`).

## 6. Tiêu chí chấp nhận

- [ ] `FakeEmbedding.embed(["Điều kiện thanh toán"])` trả 1 vector dài `EMBEDDING_DIM`, chuẩn L2 = 1 ± 1e-6, giống hệt giữa 2 tiến trình Python khác nhau.
- [ ] Cosine("điều kiện thanh toán hợp đồng A", "Điều kiện thanh toán") > cosine("điều kiện thanh toán hợp đồng A", "chính sách bảo hành sản phẩm X").
- [ ] `embed([])` trả `[]`; `embed([""])` trả `[e_0]`.
- [ ] `FakeLlm().generate(prompt có 2 chunk)` → `answerable=True`, `cited_chunk_ids == (context[0].ref,)`; context rỗng → `answerable=False`, `cited_chunk_ids == ()`.
- [ ] `FakeLlm(fail_with=UpstreamTimeout())` ném `UpstreamTimeout`; `FakeLlm(delay_s=5)` bị hủy bằng `asyncio.wait_for(…, 0.1)` → `TimeoutError` trong < 0,5 s.
- [ ] `build_llm`/`build_embedding` với `AI_PROVIDER=fake` trả adapter giả; giá trị khác → `ValueError` nêu "chưa hỗ trợ, chờ OQ-006".
- [ ] `lint-imports` xanh; `app.ports` không import gì ngoài thư viện chuẩn.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | Tính xác định của `FakeEmbedding` (chạy `subprocess` thứ hai) | Vector trùng từng phần tử |
| Unit | Bỏ dấu: "Hợp đồng" vs "hop dong" | Vector trùng |
| Unit | Lô 100 văn bản | 100 vector, đúng thứ tự |
| Unit | `FakeLlm` 4 nhánh của bảng | Kết quả đúng bảng |
| Unit | `FakeLlm.rewrite(history, "Còn gói B thì sao?")` | Trả nguyên câu hỏi |
| Contract | Mọi adapter `EmbeddingPort`: `len(v)==dim`, thứ tự giữ nguyên, `model` không rỗng | pass với fake (T-208 thêm adapter thật) |
| Contract | Mọi adapter `LlmPort`: `generate` trả `LlmAnswer` hợp lệ cho prompt mẫu | pass |

## 8. Cấu hình

`AI_PROVIDER=fake` (nhà cung cấp thật sau **OQ-006**), `EMBEDDING_MODEL=fake-384`, `EMBEDDING_DIM=384` `[Default]`; `LLM_MODEL`, `LLM_REWRITE_MODEL` để trống (sau OQ-006/SP-04).

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| `citedChunkIds` là nhãn `c1…cK` (SAD §3.2.1 bước 10) hay UUID (§6.6 "id thuộc tập chunks") | Lệch giữa T-204/T-205/T-206 | Port mang `PromptChunk.ref`; T-206 chốt, T-205 ánh xạ ref → `chunk_id` |
| Hành vi `FakeLlm` quá "dễ" so với AI thật | Test xanh nhưng chất lượng thật kém | Chất lượng đo bằng CMP-17 với AI thật ([T-211](./T-211-eval-harness-v1.md)), không bằng fake |
| Mô hình thật có số chiều khác 384 | Phải migration + reindex | `EMBEDDING_DIM` cấu hình; T-208 xử lý |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §1.2, §3.1, §3.3, §5.1, §6.4, §6.6, §9.1
- [SAD](../../design/SAD.md) §1.2 (Ports & Adapters), §3.2.1 (bước 6, 7, 10), §4.1.5, AD-03, AD-09
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.5 (giao diện ra ngoài)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Docstring của từng port đủ để người viết adapter thật (T-208) không cần đọc mã lõi.
