# T-104 — Viết handler worker `ingest_document`: trích văn bản, chia chunk, embed, đặt `READY`

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 1 |
| **Loại** | Backend |
| **User story** | US-A3, US-A4 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 3 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-007, T-008, T-101, T-102 |
| **Mở khóa (task chờ task này)** | T-107, T-112, T-203 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Mỗi tài liệu `UPLOADED` được Worker xử lý tự động: trích văn bản từng trang trong **tiến trình con có giới hạn thời gian/bộ nhớ**, phát hiện PDF không có chữ (`NOT_EXTRACTABLE`), chuẩn hóa NFC, chia chunk **không vượt trang**, embed theo lô và ghi chunk + đặt `READY` **trong cùng một giao dịch**. Lỗi tạm thời được thử lại; hết lượt → `FAILED` kèm `failure_reason`.

## 2. Bối cảnh

- Pseudo-code chuẩn: [Implement_plan §6.4](../Implement_plan.md#64-xử-lý-tài-liệu-ingest_document).
- Quy trình 7 bước và cô lập tài nguyên: [SAD §2.2](../../design/SAD.md#22-tầng-ứng-dụng--logic-nghiệp-vụ-cmp-03cmp-10-cmp-20); AD-09; DD-04 (chunk không vượt trang → trích dẫn đúng trang, AC-010).
- Ngưỡng `NOT_EXTRACTABLE` lấy từ kết quả SP-03 (`docs/implement/spikes/SP-03.md`, [T-008](./T-008-spike-sp03-pdf-extraction.md)).
- AC-003 (chuyển "sẵn sàng"), AC-004 (PDF scan → "không thể truy vấn"); QAS-02: PDF ≤ 100 trang sẵn sàng P90 ≤ 120 s `[Proposed]`.

## 3. Phạm vi

**Trong phạm vi**
- Adapter `PdfiumTextExtractor` (triển khai `PdfTextPort` của T-007) chạy `pypdfium2` trong tiến trình con.
- `normalize()`, `split_within_page()`, `has_meaningful_text()`, `embed_in_batches()`.
- Handler `ingest_document` + `on_exhausted` (đặt `FAILED`), đăng ký trong `app/worker.py`.
- Kiểm tra `MAX_PAGES` (phần số trang của AC-005).
- Dùng `FakeEmbedding` ở dev/CI.

**Ngoài phạm vi**
- OCR (ngoài MVP, BRD §5.2).
- `call_upstream()` đầy đủ (circuit breaker — T-305); ở đây chỉ timeout + phân loại lỗi tạm thời.
- Sự kiện `document_upload_succeeded/rejected` (T-110 thêm `emit` vào các điểm đánh dấu).
- Adapter embedding thật, `reindex_all` (T-208).

## 4. Thiết kế chi tiết

**File**

| File | Nội dung |
|---|---|
| `backend/app/ingestion/ingest_document.py` | Handler + `on_ingest_exhausted` |
| `backend/app/ingestion/normalize.py` | `normalize(text) -> str` |
| `backend/app/ingestion/chunker.py` | `ChunkDraft`, `split_within_page()` |
| `backend/app/ingestion/quality.py` | `has_meaningful_text(pages) -> bool` |
| `backend/app/ingestion/chunk_repository.py` | `delete_by_document`, `insert_many` |
| `backend/app/adapters/pdfium/extractor.py` | `PdfiumTextExtractor` (cha) |
| `backend/app/adapters/pdfium/child.py` | Điểm vào tiến trình con: `python -m app.adapters.pdfium.child <pdf_path>` |

**Chữ ký**

```python
@dataclass(frozen=True)
class PageText: page_no: int; text: str          # page_no bắt đầu từ 1

class PdfTextPort(Protocol):                      # đã có ở T-007
    async def extract_pages(self, pdf_path: Path, *, timeout_s: int, max_pages: int) -> list[PageText]: ...
# Lỗi: PdfTooManyPages(page_count), PdfExtractTimeout, PdfUnreadable

@dataclass(frozen=True)
class ChunkDraft: page: int; chunk_index: int; text: str

def split_within_page(text: str, page_no: int, *, target_tokens: int = 400, overlap: int = 50) -> list[ChunkDraft]: ...
def has_meaningful_text(pages: list[PageText]) -> bool: ...
async def ingest_document(payload: dict) -> None: ...            # payload = {"document_id": "<uuid>"}
```

**Luồng handler** (theo plan §6.4, bổ sung xử lý lỗi)

```python
async def ingest_document(payload):
    doc = await documents.get(payload["document_id"])
    if doc is None or doc.status not in ("UPLOADED", "PROCESSING"):
        return                                                     # lũy đẳng
    await documents.transition(doc, "PROCESSING")
    with tempfile.TemporaryDirectory() as tmp:                     # tải tệp ra đĩa tạm theo luồng
        path = await download_to(files.open_stream(doc.file_ref), tmp)
        try:
            pages = await pdf_text.extract_pages(path, timeout_s=settings.PDF_EXTRACT_TIMEOUT_S,
                                                 max_pages=settings.MAX_PAGES)
        except PdfTooManyPages:   raise PermanentJobError("TOO_MANY_PAGES")
        except PdfExtractTimeout: raise PermanentJobError("EXTRACTION_TIMEOUT")
        except PdfUnreadable:     raise PermanentJobError("PDF_UNREADABLE")
    if not has_meaningful_text(pages):
        await documents.transition(doc, "NOT_EXTRACTABLE", page_count=len(pages)); return
    drafts = [c for p in pages for c in split_within_page(normalize(p.text), p.page_no)]
    vectors = await embed_in_batches([c.text for c in drafts])    # lỗi 429/5xx/timeout → TransientJobError
    async with session.begin():
        locked = await documents.get_for_update(doc.id)           # SELECT … FOR UPDATE
        if locked.status != "PROCESSING": return                  # đã bị xóa giữa chừng → bỏ, không ghi chunk
        await chunk_repo.delete_by_document(doc.id)
        await chunk_repo.insert_many(doc.id, drafts, vectors, model=settings.EMBEDDING_MODEL)
        await documents.transition(locked, "READY", page_count=len(pages))
```

- `on_ingest_exhausted(payload, last_error)`: nếu tài liệu còn `PROCESSING|UPLOADED` → `FAILED`, `failure_reason = <mã>` (`TOO_MANY_PAGES`, `EXTRACTION_TIMEOUT`, `PDF_UNREADABLE`, `EMBEDDING_UNAVAILABLE`, `INTERNAL_ERROR`) `[Proposed]`. Giao diện ánh xạ mã → câu tiếng Việt (T-107).
- `TOO_MANY_PAGES` là cách `[Proposed]` để đáp ứng AC-005 phần số trang (không có trạng thái "bị từ chối" riêng trong §6.2) — cần Tech Lead/PO xác nhận.

**Tiến trình con** (AD-09, SAD §4.1.4)
- `asyncio.create_subprocess_exec(sys.executable, "-m", "app.adapters.pdfium.child", path)`; `preexec_fn` đặt `resource.setrlimit(RLIMIT_AS, PDF_MEMORY_LIMIT_MB)` và `RLIMIT_CPU`; môi trường tối thiểu (không biến bí mật, không `S3_*`, không `DATABASE_URL`).
- Con đọc PDF, nếu `len(pdf) > max_pages` → thoát mã 3; ngược lại ghi JSON Lines `{"page": n, "text": "…"}` ra stdout; PDF hỏng/mã hóa → mã 4.
- Cha: `asyncio.wait_for(…, timeout_s)`; quá giờ → `kill()` → `PdfExtractTimeout`. Không ghi stderr của con ra log ở INFO (có thể chứa nội dung).

**Quy tắc xử lý văn bản**
- `normalize`: `unicodedata.normalize("NFC")`; bỏ ký tự điều khiển trừ `\n`; nối từ bị gạch nối cuối dòng; gộp xuống dòng đơn trong đoạn thành dấu cách; gộp khoảng trắng.
- `has_meaningful_text` `[Default — thay bằng ngưỡng SP-03]`: `False` nếu tổng ký tự chữ/số < `MIN_TEXT_CHARS` (50) **hoặc** tỷ lệ trang có ≥ 1 ký tự chữ < `MIN_TEXT_PAGE_RATIO` (0,10).
- `split_within_page`: tách theo đoạn → câu; gom tới ~`target_tokens`, chồng lấp `overlap` token **chỉ trong cùng trang**; đếm token xấp xỉ `len(text)/4` `[Proposed]` cho tới khi có tokenizer của mô hình (T-208). Trang rỗng → không sinh chunk. `chunk_index` tăng dần trong từng trang (khớp `UNIQUE(document_id, page, chunk_index)`).
- `embed_in_batches`: lô `EMBEDDING_BATCH_SIZE`; kiểm số chiều vector = `EMBEDDING_DIM`, sai → `PermanentJobError("EMBEDDING_DIM_MISMATCH")`.
- Log: `document_id`, `page_count`, `chunk_count`, `duration_ms` từng bước; **không** log văn bản.

## 5. Các bước thực hiện

1. Đọc `docs/implement/spikes/SP-03.md`; ghi ngưỡng đề xuất vào giá trị mặc định cấu hình.
2. Viết `normalize`, `split_within_page`, `has_meaningful_text` + test đơn vị (có văn bản tiếng Việt tổ hợp NFD).
3. Viết `child.py` và `PdfiumTextExtractor` (timeout, giới hạn bộ nhớ, mã thoát).
4. Viết `chunk_repository` (`insert_many` theo lô 500 dòng `[Proposed]`).
5. Viết handler `ingest_document` + `on_ingest_exhausted`; gọi `DocumentService.transition` (không ghi bảng `document` trực tiếp).
6. Đăng ký `register_handler("ingest_document", ingest_document, on_exhausted=on_ingest_exhausted)` trong `app/worker.py`.
7. Test tích hợp với PostgreSQL + MinIO + `FakeEmbedding`; cập nhật `.env.example`.

## 6. Tiêu chí chấp nhận

- [ ] PDF văn bản 10 trang → `READY`, `page_count=10`, mọi chunk có `page` ∈ [1..10], `embedding_model = EMBEDDING_MODEL`, không chunk nào chứa văn bản của 2 trang.
- [ ] PDF chỉ chứa ảnh scan → `NOT_EXTRACTABLE`, 0 chunk (AC-004 phần xử lý).
- [ ] Không bao giờ quan sát được `READY` mà số chunk = 0 (kiểm bằng truy vấn trong test đồng thời).
- [ ] Chạy handler 2 lần cho cùng tài liệu → số chunk không đổi (lũy đẳng).
- [ ] PDF làm tiến trình con chạy quá `PDF_EXTRACT_TIMEOUT_S` → con bị kill, tài liệu `FAILED`, `failure_reason=EXTRACTION_TIMEOUT`, worker vẫn sống.
- [ ] PDF > `MAX_PAGES` → `FAILED`, `failure_reason=TOO_MANY_PAGES`.
- [ ] `FakeEmbedding` ném lỗi tạm thời 2 lần rồi thành công → `READY`; ném liên tục → sau 5 lần `FAILED`, `failure_reason=EMBEDDING_UNAVAILABLE`.
- [ ] Tài liệu bị xóa (`DELETED`) trong lúc đang embed → không ghi chunk, trạng thái vẫn `DELETED`.
- [ ] Văn bản "Hợp đồng" ở dạng NFD trong PDF được lưu ở dạng NFC.
- [ ] PDF mẫu ≤ 100 trang (T-009) với `FakeEmbedding` đạt `READY` < 120 s trên máy CI.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `normalize("Hồ")` | Trả dạng NFC `"Hồ"` |
| Unit | `split_within_page` trang 3.000 ký tự | Mọi chunk `page` giống nhau, chồng lấp ≈ 50 token, `chunk_index` 0..n |
| Unit | `has_meaningful_text` với 30 ký tự / 100 trang có 5 trang có chữ | `False` / `False` |
| Integration | PDF văn bản (fixture T-009) | `READY`, chunk > 0 |
| Integration | PDF scan | `NOT_EXTRACTABLE` |
| Integration | PDF hỏng (cắt đôi tệp) | `FAILED`, `PDF_UNREADABLE`, không thử lại |
| Integration | Con "ngủ" vượt timeout (fixture giả lập) | `FAILED`, `EXTRACTION_TIMEOUT` |
| Integration | Chạy lại sau khi dừng giữa chừng (orphan) | Chunk không trùng |
| Integration | Xóa giữa chừng | Không có chunk, `DELETED` |

## 8. Cấu hình

| Biến | Mặc định | Ghi chú |
|---|---|---|
| `EMBEDDING_MODEL`, `EMBEDDING_DIM` | `fake-384`, `384` `[Default]` | plan §3.3 |
| `AI_PROVIDER` | `fake` | plan §3.3 |
| `MAX_PAGES` | `500` `[Default]` | **`[TBD: OQ-013]`** |
| `PDF_EXTRACT_TIMEOUT_S` | `120` | SAD §2.2; tên biến `[Proposed]` |
| `PDF_MEMORY_LIMIT_MB` | `1024` `[Proposed]` | SAD §2.2 chỉ nêu "giới hạn bộ nhớ" |
| `MIN_TEXT_CHARS`, `MIN_TEXT_PAGE_RATIO` | `50`, `0.10` `[Default]` | Thay bằng kết quả SP-03 |
| `CHUNK_TARGET_TOKENS`, `CHUNK_OVERLAP_TOKENS` | `400`, `50` `[Proposed]` | Hiệu chỉnh bằng OQ-008 |
| `EMBEDDING_BATCH_SIZE` | `64` `[Proposed]` | Theo giới hạn nhà cung cấp (OQ-006) |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| SP-03 chưa xong khi bắt đầu | Ngưỡng `NOT_EXTRACTABLE` chưa đúng | Dùng `[Default]` SAD; cập nhật khi có SP-03 |
| Tiếng Việt trích sai dấu / bảng nhiều cột (RSK-003) | Chất lượng truy xuất | Theo khuyến nghị SP-03 (thử `pdfminer.six`); không dùng PyMuPDF (AGPL) |
| T-104 cần `DocumentService.transition` do T-103 tạo, nhưng T-103 không nằm trong "Phụ thuộc" | Xung đột khi làm song song | Thống nhất `documents/domain.py` theo đặc tả ở T-103 §4; ai làm trước thì tạo |
| Vượt `MAX_PAGES` không có trạng thái "bị từ chối" riêng | Hiển thị là "Lỗi xử lý" | `[Proposed]` `FAILED` + `TOO_MANY_PAGES`, ẩn nút "Thử lại" cho mã này — chờ PO xác nhận |
| `RLIMIT_AS` chỉ có trên Linux | Dev trên Windows/macOS không giới hạn được | Chạy worker trong container (T-002) |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §6.2, §6.3, §6.4, §9.2
- [SAD](../../design/SAD.md) §2.2, §3.1 (DDL `chunk`), §3.2.2, §4.1.4, AD-09
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.6.1, §3.7, DD-04
- [User_Stories](../../design/User_Stories.md) US-A3, US-A4
- Task liên quan: [T-007](./T-007-ports-and-fake-adapters.md), [T-008](./T-008-spike-sp03-pdf-extraction.md), [T-101](./T-101-job-queue.md), [T-102](./T-102-file-store-s3-adapter.md), [T-203](./T-203-hybrid-retrieval.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Test tích hợp quét log khẳng định không có văn bản trang PDF nào xuất hiện trong log.
