# T-208 — Viết adapter AI thật và công việc reindex_all ⛔

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 2 (dời sang sprint sau nếu OQ-006 chưa có kết quả) |
| **Loại** | Backend |
| **User story** | US-C1, US-E2 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 2 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-007, OQ-006 |
| **Mở khóa (task chờ task này)** | T-309, T-406 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do — ⛔ **bị chặn bởi OQ-006** (chính sách dữ liệu AI) |

## 1. Mục tiêu

Hệ thống gọi được dịch vụ LLM và embedding **thật** (do OQ-006 cho phép) qua `LlmPort`/`EmbeddingPort`, chọn bằng cấu hình `AI_PROVIDER` mà không đổi lõi nghiệp vụ; và có công việc `reindex_all` để vector hóa lại toàn bộ thư viện khi đổi mô hình embedding.

## 2. Bối cảnh

- AD-03, DD-07: AI nằm sau port + cấu hình; đổi nhà cung cấp không đổi kiến trúc (SAD §0.2, §1.1 D2).
- OQ-006 quyết định: có được gửi nội dung ra ngoài không, nơi xử lý (data residency), thời gian lưu, "không dùng để huấn luyện" (SAD §4.1.5). **Chưa có OQ-006 thì không gửi dữ liệu thật tới bất kỳ dịch vụ AI nào** (Implement_plan §9.1).
- DR-04 / SAD §3.1: mỗi chunk lưu `embedding_model`; đổi mô hình = `reindex_all` rồi mới chuyển cấu hình.
- Sau task này mới chạy được: SP-01 với độ trễ thật (T-309), hồ sơ tuân thủ (T-406), CMP-17 với AI thật (T-211/T-310).

## 3. Phạm vi

**Trong phạm vi**
- Adapter `LlmPort` (`generate`, `rewrite`) và `EmbeddingPort` (`embed`) cho nhà cung cấp được duyệt.
- Chọn adapter trong composition root theo `AI_PROVIDER`; kiểm cấu hình khi khởi động.
- Bộ test hợp đồng port chạy chung cho `FakeLlm`/`FakeEmbedding` và adapter thật (qua mock HTTP).
- Handler `reindex_all` + lệnh enqueue + quy trình vận hành.

**Ngoài phạm vi** (để tránh làm thừa)
- Timeout/retry/circuit breaker chung `call_upstream()` (T-305) — adapter chỉ đặt timeout HTTP cơ bản.
- Chọn nhà cung cấp/mô hình bằng số liệu chất lượng (SP-04, dùng CMP-17) và ký hồ sơ tuân thủ (T-406).
- Reindex không gián đoạn (hai cột vector song song) — ngoài MVP.

## 4. Thiết kế chi tiết

**Hợp đồng port** (định nghĩa ở T-007; adapter phải tuân thủ đúng):

| Hàm | Đầu vào | Đầu ra | Lỗi phải ném |
|---|---|---|---|
| `LlmPort.generate(req: LlmPrompt)` | `system`, `user`, `response_schema` (T-206) | `LlmAnswer(answerable, content, cited_chunk_ids, tokens_in, tokens_out)` | `UpstreamTimeout`, `UpstreamUnavailable` (429/5xx/kết nối, kèm `retry_after`), `LlmAnswerInvalid` (không parse/không khớp schema) |
| `LlmPort.rewrite(history, question)` | ≤ `HISTORY_TURNS` lượt (`Turn`) + câu hỏi | `RewriteResult` (câu hỏi độc lập + token) | Như trên (dùng ở T-301) |
| `EmbeddingPort.embed(texts: list[str])` | 1..n văn bản | `list[list[float]]`, mỗi vector đúng `EMBEDDING_DIM` | Như trên; sai số chiều → `EmbeddingDimensionMismatch` |

`LlmAnswerInvalid` và `EmbeddingDimensionMismatch` là lỗi port **mới** `[Proposed]` (T-007 mới có `UpstreamTimeout`, `UpstreamUnavailable`) — thêm vào `app/ports/errors.py`; `retry_after` là thuộc tính `[Proposed]` của `UpstreamUnavailable`. `rewrite` trả `RewriteResult(text, tokens_in, tokens_out)` theo T-007.

Quy tắc adapter: chỉ adapter được import SDK/HTTP client của nhà cung cấp (`import-linter`); **không có công cụ/function calling** cho LLM (SAD §4.1.5); bật structured output (JSON schema) nếu nhà cung cấp hỗ trợ, nếu không thì JSON mode + kiểm bằng Pydantic; lấy `tokens_in/out` từ phản hồi; không log prompt/đầu ra; không gửi tên người dùng.

**File:**

```text
backend/app/adapters/<provider>/        # ví dụ openai_like/ (Implement_plan §3.1) — tên theo OQ-006
├─ llm.py          # class <Provider>Llm(LlmPort)
├─ embedding.py    # class <Provider>Embedding(EmbeddingPort)
└─ errors.py       # ánh xạ mã HTTP → lỗi port
backend/app/ingestion/reindex.py        # handler reindex_all
backend/tests/contract/test_llm_port.py, test_embedding_port.py
```

**Chọn adapter** (`app/main.py`, `app/worker.py`):

```python
def build_ai(settings) -> tuple[LlmPort, EmbeddingPort]:
    match settings.AI_PROVIDER:
        case "fake": return FakeLlm(...), FakeEmbedding(dim=settings.EMBEDDING_DIM)
        case "<provider>": return ProviderLlm(settings), ProviderEmbedding(settings)
        case other: raise ConfigError(f"AI_PROVIDER không hỗ trợ: {other}")
```

Kiểm khi khởi động: `EMBEDDING_DIM` khớp số chiều cột `chunk.embedding` (đọc `atttypmod`); `AI_PROVIDER != fake` mà thiếu `LLM_MODEL`/`EMBEDDING_MODEL`/khóa API → không khởi động. `/health/ready` **không** gọi dịch vụ AI (SAD §2.4).

**Tiêu chí chọn nhà cung cấp/mô hình** (không định danh nhà cung cấp — SAD §6, §4.1.5; quyết định cuối do OQ-006 + SP-04):

| Tiêu chí | Cách kiểm |
|---|---|
| Chính sách dữ liệu: không dùng để huấn luyện, thời gian lưu, vùng xử lý | Hợp đồng/cấu hình tài khoản; IT/Bảo mật duyệt `[TBD: OQ-006]` |
| Chất lượng tiếng Việt (và ngôn ngữ OQ-009) | CMP-17 trên bộ câu hỏi OQ-008 (SP-04) |
| Đầu ra có cấu trúc (JSON schema) | Thử với `schema.json` của T-206; tỷ lệ `LlmAnswerInvalid` |
| Độ trễ `generate` 3–10 s, embedding 0,1–0,5 s | SP-01 (T-309), ngân sách SAD §3.2.1 |
| Embedding đa ngữ, ≤ 2.000 chiều (HNSW `vector`) hoặc dùng `halfvec` `[Verify]` | Tài liệu mô hình |
| Giá, hạn mức (token/phút), tương thích `WEEKLY_TOKEN_BUDGET` | Bảng giá; CN-12 |
| Có phương án tự lưu trữ cùng port | Adapter tương thích máy chủ suy luận nội bộ |

**`reindex_all`** (loại việc có sẵn trong SAD §2.2):

- Payload: `{"target_model": "...", "target_dim": N}`; enqueue bằng lệnh `python -m app.ingestion.reindex --target-model … --target-dim …` (hoặc `make reindex`) `[Proposed]`.
- Handler: duyệt tài liệu `READY` theo lô; với mỗi tài liệu, đọc các chunk có `embedding_model <> target_model`, embed theo lô `EMBEDDING_BATCH_SIZE`, rồi **một giao dịch/tài liệu** cập nhật `embedding`, `embedding_model`. Lũy đẳng: chạy lại bỏ qua chunk đã đúng model; tài liệu `DELETED` giữa chừng bị bỏ qua. Ghi log tiến độ (số tài liệu/chunk, không văn bản).
- Quy trình vận hành `[Proposed]` (MVP chấp nhận cửa sổ bảo trì):
  1. Cùng số chiều: chạy `reindex_all` → khi xong, đổi `EMBEDDING_MODEL` và khởi động lại API/Worker. Trong lúc chạy, truy xuất chỉ thấy chunk còn model cũ → báo trước cho người dùng.
  2. Khác số chiều: migration expand đổi cột `embedding` sang `vector(M)` (xóa chỉ mục HNSW, xóa vector cũ, đặt `embedding_model='pending'`) → đổi cấu hình → `reindex_all` → tạo lại HNSW. Hỏi đáp trả `NOT_FOUND` cho tới khi xong → chỉ làm trước khi có người dùng thật.

## 5. Các bước thực hiện

**Trong lúc bị chặn (làm được ngay, không gửi dữ liệu ra ngoài):**
1. Viết test hợp đồng port, chạy với `FakeLlm`/`FakeEmbedding`.
2. Viết khung adapter cho API dạng HTTP phổ biến, test bằng mock transport (`httpx.MockTransport`/`respx`): 200, 429 có `Retry-After`, 500, timeout, JSON hỏng, sai số chiều.
3. Viết `reindex_all` + test tích hợp với `FakeEmbedding` hai "model" (`fake-384` → `fake-384b`).
4. Chuẩn bị bảng so sánh ứng viên theo tiêu chí ở mục 4 (không gọi thử bằng tài liệu thật).

**Sau khi OQ-006 có kết quả:**
5. Hoàn thiện adapter cho nhà cung cấp được duyệt; cấu hình vùng xử lý và "không huấn luyện".
6. Nạp khóa API từ secret manager (SAD §4.1.3) cho staging; chạy smoke test `-m real_ai` với PDF mẫu không nhạy cảm (T-009).
7. Chạy `reindex_all` trên staging; chạy CMP-17 (T-211) và bàn giao số liệu cho T-309, T-406.

## 6. Tiêu chí chấp nhận

- [ ] Test hợp đồng port pass cho cả adapter giả và adapter thật (mock HTTP): đầu ra đúng kiểu; 429/5xx → `UpstreamUnavailable`; timeout → `UpstreamTimeout`; JSON hỏng → `LlmAnswerInvalid`; sai số chiều → `EmbeddingDimensionMismatch`.
- [ ] Đổi `AI_PROVIDER` giữa `fake` và nhà cung cấp thật không cần sửa mã ngoài `adapters/` và composition root (kiểm bằng `import-linter`).
- [ ] Prompt gửi đi không chứa tên/ID người dùng; log không chứa prompt hay đầu ra (test bắt log).
- [ ] `reindex_all` chạy hai lần liên tiếp cho kết quả giống nhau; mọi chunk của tài liệu `READY` có `embedding_model = target_model`; chunk của tài liệu `DELETED` không được xử lý.
- [ ] `EMBEDDING_DIM` khác số chiều cột → API/Worker từ chối khởi động với thông báo rõ.
- [ ] (Sau OQ-006) Smoke test thật: 1 câu hỏi mẫu trả `ANSWERED` có trích dẫn hợp lệ trên staging.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Contract | `generate` với `schema.json` T-206 | `LlmAnswer` hợp lệ |
| Contract | Mock 429 `Retry-After: 2` | `UpstreamUnavailable(retry_after=2)` |
| Contract | Mock chậm hơn timeout | `UpstreamTimeout` |
| Contract | Mock trả văn bản không phải JSON | `LlmAnswerInvalid` |
| Contract | `embed` 3 văn bản | 3 vector, đúng chiều |
| Integration | `reindex_all` 3 tài liệu, một bị xóa giữa chừng | 2 tài liệu chuyển model; không lỗi |
| Integration | Khởi động với `EMBEDDING_DIM` sai | Thoát với `ConfigError` |
| Smoke (`real_ai`, sau OQ-006) | Hỏi 1 câu trên PDF mẫu | `ANSWERED` + trích dẫn |

## 8. Cấu hình

| Biến | Mặc định | Ghi chú |
|---|---|---|
| `AI_PROVIDER` | `fake` | Giá trị thật `[TBD: OQ-006]` |
| `LLM_MODEL`, `LLM_REWRITE_MODEL` | — | Sau OQ-006/SP-04 |
| `EMBEDDING_MODEL`, `EMBEDDING_DIM` | `fake-384`, `384` `[Default]` | Đổi = `reindex_all` |
| `AI_API_BASE_URL`, `AI_API_KEY`, `AI_REGION` | — | `[Proposed]` biến mới; `AI_API_KEY` chỉ từ secret manager, không vào `.env.example` giá trị thật |
| `EMBEDDING_BATCH_SIZE` | `64` | `[Proposed]` theo giới hạn nhà cung cấp |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| OQ-006 chưa có kết quả | Không có AI thật: không đo MET-002, SP-01, không ký AC-020 | Toàn bộ luồng chạy với Fake; làm các bước 1–4 |
| OQ-006 cấm gửi ra ngoài | Phải tự lưu trữ mô hình → chi phí/hạ tầng tăng | Cùng port; adapter cho máy chủ suy luận nội bộ; đo lại bằng CMP-17 |
| `chunk` có `UNIQUE (document_id, page, chunk_index)` và một cột `vector(N)` | Không thể giữ song song vector hai model → reindex cần cửa sổ bảo trì | Quy trình ở mục 4; xem lại nếu cần reindex khi đã có người dùng |
| Mô hình > 2.000 chiều `[Verify]` | HNSW `vector` không dùng được | Chọn mô hình ≤ 2.000 chiều hoặc `halfvec` |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §1.2, §3.1 (quy tắc phụ thuộc), §3.3, §6.1 (ghi chú `embedding_model`), §9.1
- [SAD](../../design/SAD.md) §0.2, §2.2 (`reindex_all`), §3.1, §4.1.3, §4.1.5, §4.2, §6, §7 SP-04
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.5 (giao diện ra ngoài), §3.8 (DD-07)
- [User_Stories](../../design/User_Stories.md) US-C1, US-E2
- Task liên quan: [T-007](./T-007-ports-and-fake-adapters.md), [T-206](./T-206-prompt-v1.md), [T-211](./T-211-eval-harness-v1.md), [T-305](./T-305-upstream-resilience.md), [T-309](./T-309-spike-sp01-latency.md), [T-406](./T-406-compliance-package.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Có văn bản kết quả OQ-006 đính kèm PR; cấu hình "không huấn luyện" và vùng xử lý được ghi lại cho T-406.
