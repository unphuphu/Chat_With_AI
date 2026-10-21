# T-204 — Viết NotFoundPolicy và CitationValidator (thuần domain)

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 2 |
| **Loại** | Backend |
| **User story** | US-C3, US-C4 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 1,5 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-007 |
| **Mở khóa (task chờ task này)** | T-205 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Có hai lớp domain không I/O, test đơn vị đầy đủ, hiện thực hai lớp kiểm soát chống bịa: **Lớp 1** `NotFoundPolicy` quyết định từ chối trước khi gọi LLM; **Lớp 2** `CitationValidator` quyết định đầu ra LLM có trích dẫn hợp lệ hay không. Đây là nơi duy nhất chứa hai quy tắc này.

## 2. Bối cảnh

- Quy tắc không được vi phạm số 1 (Implement_plan §0): câu trả lời `ANSWERED` luôn có ≥ 1 trích dẫn hợp lệ. BRU-001, BRU-003, BR-010, BR-011, AC-010, AC-011.
- SAD §3.2.1 bước 9 (Lớp 1) và bước 11 (Lớp 2); Blueprint §3.6.4 bước 5, 7 (DD-06); AD-07.
- Quy tắc chính xác: Implement_plan §6.6 — `is_valid(out, chunks)` là `True` **khi và chỉ khi** `out.answerable is True`, `out.cited_chunk_ids` không rỗng, và **mọi** id thuộc tập `chunks`.
- Lớp domain không đọc cấu hình, không log, không gọi port — ngưỡng được tiêm qua constructor (SAD §2.4 phân lớp).

## 3. Phạm vi

**Trong phạm vi**
- `NotFoundPolicy`, `CitationValidator`, kiểu `ValidationResult`/`ValidationFailure`, kiểu `ContextChunk` dùng chung với T-205/T-206.
- Test đơn vị, gồm **toàn bộ ca bắt buộc** của Implement_plan §6.6.

**Ngoài phạm vi** (để tránh làm thừa)
- Gọi LLM, thử lại, ánh xạ trích dẫn sang (tài liệu, trang), lưu CSDL (T-205).
- Xây prompt (T-206). Metric `citation_validation_failures_total` (T-205 tăng, T-404 xuất).
- Hiệu chỉnh `RELEVANCE_THRESHOLD` (T-310, `[TBD: OQ-008]`).

## 4. Thiết kế chi tiết

**File:** `backend/app/answering/domain/{__init__.py, context.py, not_found_policy.py, citation_validator.py}`; test `backend/tests/unit/answering/test_not_found_policy.py`, `test_citation_validator.py`.

```python
# context.py
@dataclass(frozen=True)
class ContextChunk:
    ref: str              # "c1".."cK" — nhãn đưa vào prompt (SAD §3.2.1 bước 10)
    chunk_id: UUID
    document_id: UUID
    document_name: str
    page: int
    text: str
```

```python
# not_found_policy.py — Lớp 1
class NotFoundPolicy:
    def __init__(self, relevance_threshold: float):
        if not 0.0 <= relevance_threshold <= 1.0:
            raise ValueError("relevance_threshold phải trong [0, 1]")
        self._t = relevance_threshold

    def should_refuse(self, best_vector_score: float | None, *, has_text_match: bool) -> bool:
        """True = trả NOT_FOUND, KHÔNG gọi LLM.
        Từ chối khi và chỉ khi: (không có điểm vector HOẶC điểm < ngưỡng) VÀ không có khớp từ khóa."""
        below = best_vector_score is None or best_vector_score < self._t
        return below and not has_text_match
```

```python
# citation_validator.py — Lớp 2
class ValidationFailure(StrEnum):
    NOT_ANSWERABLE = "not_answerable"      # out.answerable is False
    EMPTY_CITATIONS = "empty_citations"    # answerable True nhưng danh sách rỗng
    UNKNOWN_ID = "unknown_id"              # có ít nhất một id không thuộc tập chunks

@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failure: ValidationFailure | None
    unknown_ids: tuple[str, ...] = ()

class CitationValidator:
    def validate(self, out: LlmAnswer, chunks: Sequence[ContextChunk]) -> ValidationResult: ...
    def is_valid(self, out: LlmAnswer, chunks: Sequence[ContextChunk]) -> bool:
        return self.validate(out, chunks).ok
```

`LlmAnswer` là kiểu đầu ra của `LlmPort.generate` định nghĩa ở T-007 (`answerable: bool`, `content: str`, `cited_chunk_ids: tuple[str, ...]`, `tokens_in`, `tokens_out`). "Id" trong `cited_chunk_ids` là **nhãn `ref`** (`"c3"`) của `ContextChunk`, không phải UUID `[Proposed]` — nhãn ngắn giảm lỗi mô hình chép sai UUID; T-205 đổi `ref` → `chunk_id`.

**Quy tắc `validate()` (thứ tự kiểm):**

1. `out.answerable is not True` → `NOT_ANSWERABLE`.
2. `len(out.cited_chunk_ids) == 0` → `EMPTY_CITATIONS`.
3. `allowed = {c.ref for c in chunks}`; `unknown = [i for i in out.cited_chunk_ids if i not in allowed]`; `unknown` không rỗng → `UNKNOWN_ID` (kèm `unknown_ids`, chỉ là nhãn, không phải nội dung).
4. Ngược lại `ok=True`.

- So khớp **chính xác** (phân biệt hoa thường, không cắt khoảng trắng). Chuẩn hóa nếu cần là việc của adapter (T-007/T-208).
- Id trùng (`["c1","c1"]`) với `c1` hợp lệ → `ok=True` `[Proposed]`; loại trùng khi ánh xạ (T-205).
- Validator **không** kiểm `content` có rỗng hay có đánh dấu `[cN]` — ngoài quy tắc §6.6.
- Cách T-205 dùng `failure`: `NOT_ANSWERABLE` → `NOT_FOUND` ngay; `EMPTY_CITATIONS`/`UNKNOWN_ID` → thử lại 1 lần với nhắc nhở, vẫn sai → `NOT_FOUND`.

## 5. Các bước thực hiện

1. Tạo package `answering/domain/`; viết `ContextChunk`.
2. Viết `NotFoundPolicy` + test (bảng mục 7).
3. Viết `CitationValidator` + test, gồm 5 ca bắt buộc của Implement_plan §6.6.
4. Thêm test dạng thuộc tính (Hypothesis `[Proposed]`): với mọi tập `chunks` và danh sách id sinh ngẫu nhiên, `is_valid` = `True` ⇔ `answerable` ∧ danh sách không rỗng ∧ tập id ⊆ tập `ref`.
5. Thêm hợp đồng `import-linter`: `app.answering.domain` không import `sqlalchemy`, `httpx`, `app.adapters`, `app.platform.config`.

## 6. Tiêu chí chấp nhận

- [ ] 5 ca bắt buộc của Implement_plan §6.6 có test riêng và cho kết quả đúng: id lạ → sai; danh sách rỗng → sai; `answerable=false` → sai; trùng id hợp lệ → đúng; một id hợp lệ + một id lạ → **sai**.
- [ ] `NotFoundPolicy` từ chối khi và chỉ khi (điểm `None` hoặc `< ngưỡng`) **và** không có khớp từ khóa; điểm **bằng** ngưỡng không bị từ chối.
- [ ] Ngưỡng ngoài `[0, 1]` → `ValueError` khi khởi tạo.
- [ ] Coverage dòng của `answering/domain/` = 100%.
- [ ] Package `answering/domain` không có import I/O (kiểm bằng `import-linter` trong CI).

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | Policy: `best=None`, `text=False` | `True` (từ chối) |
| Unit | Policy: `best=None`, `text=True` | `False` |
| Unit | Policy: `best=0.10`, `t=0.30`, `text=False` | `True` |
| Unit | Policy: `best=0.10`, `t=0.30`, `text=True` | `False` |
| Unit | Policy: `best=0.30`, `t=0.30`, `text=False` | `False` (biên) |
| Unit | Policy: `best=0.85`, `text=False` | `False` |
| Unit | Policy: `t=1.2` hoặc `t=-0.1` | `ValueError` |
| Unit | Validator: `answerable=True`, `["c9"]`, chunks `c1..c3` | `ok=False`, `UNKNOWN_ID`, `unknown_ids=("c9",)` |
| Unit | Validator: `answerable=True`, `[]` | `ok=False`, `EMPTY_CITATIONS` |
| Unit | Validator: `answerable=False`, `["c1"]` | `ok=False`, `NOT_ANSWERABLE` |
| Unit | Validator: `answerable=True`, `["c1","c1"]` | `ok=True` |
| Unit | Validator: `answerable=True`, `["c1","c9"]` | `ok=False`, `UNKNOWN_ID` |
| Unit | Validator: `answerable=True`, `["c1","c2"]` | `ok=True` |
| Unit | Validator: `"C1"` hoặc `" c1"` khi chunk có `c1` | `ok=False` (so khớp chính xác) |
| Unit | Validator: `chunks` rỗng, `["c1"]` | `ok=False`, `UNKNOWN_ID` |
| Unit | Thuộc tính (Hypothesis) | Tương đương công thức ở bước 4 |

## 8. Cấu hình

Domain không đọc cấu hình. Composition root (`app/main.py`) khởi tạo `NotFoundPolicy(settings.RELEVANCE_THRESHOLD)`; `RELEVANCE_THRESHOLD = 0.30` `[Default]`, **hiệu chỉnh bằng bộ kiểm thử** `[TBD: OQ-008]` (T-310).

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Plan §6.6 liệt kê ca "trùng id" nhưng không nêu kỳ vọng | Hai cách hiểu | Chọn `ok=True` `[Proposed]` vì mọi id đều thuộc tập đã truy xuất; Tech Lead xác nhận khi review |
| Pseudo-code §6.6 thử lại với **mọi** đầu ra không hợp lệ, kể cả `answerable=false` | Gọi LLM thêm một lần không cần thiết khi mô hình đã nói "không đủ thông tin" | Validator trả `failure` để T-205 chỉ thử lại với `EMPTY_CITATIONS`/`UNKNOWN_ID` `[Proposed]` |
| Blueprint §3.6.4 bước 5 chỉ nói "điểm cao nhất < ngưỡng"; SAD/plan thêm điều kiện "không có khớp từ khóa" | Hai mô tả khác nhau | Theo SAD §3.2.1 bước 9 và plan §6.6 (có điều kiện từ khóa) |
| Validator chỉ bảo đảm trích dẫn trỏ tới đoạn đã truy xuất, không bảo đảm diễn giải đúng (Blueprint §3.6.4) | MET-002 vẫn có thể thấp | Đo bằng CMP-17 (T-211) |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §0 (quy tắc không được vi phạm), §6.6, §7.1
- [SAD](../../design/SAD.md) §2.4 (phân lớp), §3.2.1 bước 9, 11; §5 AD-07
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.5 (bất biến hợp đồng API-09), §3.6.4
- [User_Stories](../../design/User_Stories.md) US-C3, US-C4
- Task liên quan: [T-007](./T-007-ports-and-fake-adapters.md), [T-205](./T-205-answer-service.md), [T-206](./T-206-prompt-v1.md), [T-310](./T-310-threshold-calibration.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Hai reviewer (trong đó có Tech Lead) duyệt PR vì đây là guardrail cốt lõi của BRU-001/BRU-003.
