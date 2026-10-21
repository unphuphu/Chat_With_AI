# T-103 — Xây dựng API tải lên tài liệu `POST /api/v1/documents` (API-02)

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 1 |
| **Loại** | Backend |
| **User story** | US-A1, US-A2, US-A5 |
| **Ưu tiên** | P0 (US-A5 là P1, phần giới hạn kích thước đi kèm) |
| **Ước lượng** | 2,5 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-006, T-101, T-102 |
| **Mở khóa (task chờ task này)** | T-105, T-106, T-107, T-110 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Người dùng đã đăng nhập gửi 1..n tệp trong một yêu cầu `multipart/form-data`; mỗi tệp được kiểm tra **độc lập** (phần mở rộng, 5 byte `%PDF-`, kích thước khi đang truyền), tệp hợp lệ được truyền luồng xuống kho tệp và tạo `document(UPLOADED)` + `job(ingest_document)` + `audit_log` trong **một giao dịch**; phản hồi `202` liệt kê kết quả từng tệp.

## 2. Bối cảnh

- Luồng: [SAD §3.2.2](../../design/SAD.md#322-luồng-2--tải-lên-và-lập-chỉ-mục-tài-liệu-api-02) bước 1–5; quy ước API & lũy đẳng: [SAD §2.4](../../design/SAD.md#24-tầng-backend--api).
- Bảo vệ khi nhận PDF: [SAD §4.1.4](../../design/SAD.md#414-bảo-vệ-khi-nhận-tệp-pdf).
- Mã lỗi: Blueprint §3.5 — `UNSUPPORTED_FORMAT` (415), `FILE_TOO_LARGE` (413).
- AC phục vụ: AC-001 (3 tệp cùng lúc), AC-002 (.docx/.jpg/.xlsx bị từ chối), AC-005 (giới hạn `[TBD: OQ-013]`).
- Vòng đời tài liệu: [Implement_plan §6.2](../Implement_plan.md#62-trạng-thái-tài-liệu).

## 3. Phạm vi

**Trong phạm vi**
- Router, service, repository, validator của `documents` cho thao tác tải lên.
- `DocumentService.transition(doc, to)` và bảng chuyển trạng thái hợp lệ (dùng chung cho T-104, T-106, T-112).
- Phân tích multipart **dạng luồng** (không dùng `UploadFile` mặc định nạp/spool toàn tệp).
- `Idempotency-Key` tùy chọn và chống trùng theo `content_hash` (cùng người dùng, 24 giờ).
- Migration nhỏ: chỉ mục chống trùng + bảng khóa lũy đẳng `[Proposed]`.

**Ngoài phạm vi**
- Kiểm tra số trang `MAX_PAGES` (cần phân tích PDF → làm trong worker, T-104).
- Sự kiện telemetry `document_upload_*` (T-110 thêm lời gọi `emit` vào đúng điểm đã đánh dấu ở đây).
- Giới hạn tốc độ tải lên `RATE_LIMIT_UPLOADS_PER_MIN` (proxy/T-306).
- Giao diện (T-107).

## 4. Thiết kế chi tiết

**File**

| File | Nội dung |
|---|---|
| `backend/app/documents/router.py` | `POST /api/v1/documents` |
| `backend/app/documents/service.py` | `DocumentService.upload_many()`, `DocumentService.transition()` |
| `backend/app/documents/domain.py` | `DocumentStatus`, `ALLOWED_TRANSITIONS`, `InvalidTransition` |
| `backend/app/documents/validators.py` | `PdfStreamValidator` (magic, đếm byte, SHA-256) |
| `backend/app/documents/multipart.py` | Bộ phân tích multipart luồng (`python-multipart` mức thấp hoặc `streaming-form-data` `[Proposed]`) |
| `backend/app/documents/repository.py` | `insert_document`, `find_recent_by_hash` |
| `backend/migrations/versions/xxxx_documents_upload.py` | Chỉ mục + bảng `upload_idempotency` |

**Hợp đồng API**

```http
POST /api/v1/documents
Cookie: session=…   X-CSRF-Token: …   Idempotency-Key: 7d1c…(tùy chọn, ≤ 64 ký tự)
Content-Type: multipart/form-data; boundary=…
  files[]=@Hop-dong-A.pdf  files[]=@Bao-cao-tuan.docx
```

```json
202 Accepted
{ "items": [
  { "name": "Hop-dong-A.pdf", "id": "0b8e…", "status": "UPLOADED" },
  { "name": "Bao-cao-tuan.docx", "status": "REJECTED",
    "error": { "code": "UNSUPPORTED_FORMAT", "message": "Chỉ chấp nhận định dạng PDF" } },
  { "name": "Ban-ve-lon.pdf", "status": "REJECTED",
    "error": { "code": "FILE_TOO_LARGE", "message": "Tệp vượt quá giới hạn 50 MB" } }
] }
```

- `status` của mục thành công là trạng thái thật của tài liệu (`UPLOADED`, hoặc trạng thái bản ghi cũ khi trùng). `status: "REJECTED"` và cấu trúc `error {code, message}` là `[Proposed]` (SAD chỉ ghi `error?`).
- Thứ tự `items` = thứ tự tệp trong yêu cầu.
- Lỗi toàn yêu cầu (không mở kết quả từng tệp): `401 UNAUTHENTICATED`, `403 FORBIDDEN` (vai trò/CSRF), `400` không có tệp hoặc quá `MAX_FILES_PER_UPLOAD` tệp (mã `VALIDATION_ERROR` `[Proposed]` — xem mục 9), `413` khi proxy chặn tổng dung lượng.
- Quyền: `require_role("MEMBER", "ADMIN")` — SPONSOR chỉ xem (SAD §4.1.1).

**Kiểm tra từng tệp (trên luồng, theo thứ tự)**
1. Tên: lấy phần cuối sau `/` hoặc `\`, chuẩn hóa NFC, bỏ ký tự điều khiển, cắt 255 ký tự `[Proposed]`.
2. Phần mở rộng `.pdf` (không phân biệt hoa thường) — sai → `UNSUPPORTED_FORMAT`, **xả** phần còn lại của part, không ghi kho.
3. 5 byte đầu phải là `b"%PDF-"` — sai → `UNSUPPORTED_FORMAT`, hủy ghi.
4. Đếm byte khi truyền; vượt `MAX_UPLOAD_MB × 1024²` → dừng ghi ngay, `AbortMultipartUpload`, xả phần còn lại, `FILE_TOO_LARGE` (message nêu giới hạn).
5. Đồng thời tính SHA-256 → `content_hash`.

**Ghi dữ liệu (tệp hợp lệ)**

```python
doc_id = uuid4(); key = document_key(doc_id)
info = await files.put_stream(key, validator.wrap(part_stream))       # T-102
existing = await repo.find_recent_by_hash(user.id, sha256, within=timedelta(hours=24))
if existing:                                                          # chống trùng
    await files.delete(key); return Item(name, existing.id, existing.status)
async with session.begin():                                           # MỘT giao dịch
    await repo.insert_document(id=doc_id, name=name, status="UPLOADED", file_ref=key,
                               content_hash=sha256, size_bytes=info.size_bytes, uploaded_by=user.id)
    await job_queue.enqueue(session, "ingest_document", {"document_id": str(doc_id)})
    await audit.write(session, user_id=user.id, action="upload", target=str(doc_id), result="success")
    # T-110: emit document_upload_attempted / rejected tại đây
```

```sql
-- migration [Proposed]
CREATE INDEX document_dedupe_idx ON document (uploaded_by, content_hash, uploaded_at DESC)
  WHERE status <> 'DELETED';
CREATE TABLE upload_idempotency (
  user_id uuid NOT NULL, key text NOT NULL, response jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (user_id, key));
```

- `Idempotency-Key` đã có (cùng user, < 24 giờ) → trả lại nguyên `response` đã lưu, không xử lý lại tệp. Chưa có → xử lý rồi lưu `response`.
- `ALLOWED_TRANSITIONS`: `UPLOADED→PROCESSING`, `PROCESSING→PROCESSING` (chạy lại), `PROCESSING→READY|NOT_EXTRACTABLE|FAILED`, `FAILED→UPLOADED`, `READY|NOT_EXTRACTABLE|FAILED→DELETED`, và `UPLOADED|PROCESSING→DELETED` `[Proposed — xem T-106]`. Chuyển không hợp lệ → `InvalidTransition`; mọi chuyển đều log `document_id`, `from`, `to`.
- Log: không ghi tên tệp đầy đủ ở INFO; chỉ `document_id`, `size_bytes`, `outcome`, mã lỗi.

## 5. Các bước thực hiện

1. Viết `domain.py` (trạng thái, bảng chuyển, `InvalidTransition`) + test đơn vị.
2. Viết `PdfStreamValidator.wrap()` (async generator kiểm magic ở chunk đầu, đếm byte, băm).
3. Viết bộ phân tích multipart luồng đọc `request.stream()`, sinh `(filename, part_stream)` lần lượt.
4. Viết repository + migration (chỉ mục, `upload_idempotency`).
5. Viết `DocumentService.upload_many(user, parts, idempotency_key)`; mỗi tệp một giao dịch riêng để tệp lỗi không làm hỏng tệp khác.
6. Viết router: phụ thuộc `require_role`, CSRF (T-006), trả `202`.
7. Cập nhật `deploy/nginx.conf`: `client_max_body_size` = `MAX_UPLOAD_MB × MAX_FILES_PER_UPLOAD` (+ dư cho header) cho `location /api/v1/documents`.
8. Viết test (mục 7); cập nhật `.env.example`.

## 6. Tiêu chí chấp nhận

- [ ] Gửi 3 PDF hợp lệ trong 1 yêu cầu → `202`, 3 mục `status=UPLOADED`; CSDL có 3 `document`, 3 `job(type=ingest_document, status=queued)`, 3 `audit_log(action=upload)` (AC-001).
- [ ] Gửi `.docx`, `.jpg`, `.xlsx` → 3 mục `REJECTED` mã `UNSUPPORTED_FORMAT`, message chứa "Chỉ chấp nhận định dạng PDF"; không có `document` nào, không có đối tượng nào trong kho (AC-002).
- [ ] Tệp đổi tên `.docx → .pdf` (sai magic) → `UNSUPPORTED_FORMAT`.
- [ ] Tệp đúng bằng `MAX_UPLOAD_MB` → chấp nhận; lớn hơn 1 MB → `FILE_TOO_LARGE`, message nêu giới hạn (AC-005, phần kích thước).
- [ ] Yêu cầu trộn 1 tệp hợp lệ + 1 tệp lỗi → tệp hợp lệ vẫn được lưu.
- [ ] RSS API tăng < 32 MB khi tải tệp 50 MB.
- [ ] Nếu giao dịch lỗi sau khi ghi kho (giả lập) → không có `document`/`job`; đối tượng mồ côi được log `orphan_candidate` để T-407 dọn.
- [ ] Gửi lại cùng `Idempotency-Key` → phản hồi giống hệt, không tạo bản ghi mới.
- [ ] Cùng người dùng tải lại cùng nội dung trong 24 giờ → trả `id` bản ghi cũ, không tạo job mới.
- [ ] Không cookie → `401`; SPONSOR → `403`; thiếu `X-CSRF-Token` → `403`.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `ALLOWED_TRANSITIONS`: `READY→PROCESSING` | `InvalidTransition` |
| Unit | Validator: chunk đầu `PK\x03\x04` | `UNSUPPORTED_FORMAT` |
| Unit | Validator: magic tách qua 2 chunk (`%PD` + `F-…`) | Hợp lệ |
| Unit | Tên `../../etc/x.pdf` | `name = "x.pdf"`; khóa kho là UUID |
| Integration | 3 PDF hợp lệ | 3 document + 3 job + 3 audit, `202` |
| Integration | 1 PDF + 1 `.jpg` | 1 `UPLOADED`, 1 `REJECTED` |
| Integration | `MAX_UPLOAD_MB=1`, tệp 1 MB / 2 MB | Chấp nhận / `FILE_TOO_LARGE` |
| Integration | Lỗi CSDL giả lập khi insert | Không bản ghi; log `orphan_candidate` |
| Integration | `Idempotency-Key` lặp | Cùng phản hồi; số `document` không đổi |
| Integration | Trùng `content_hash` < 24 giờ | Cùng `id`, kho không thêm đối tượng |
| Contract | Schema phản hồi theo OpenAPI | Khớp |

## 8. Cấu hình

| Biến | Mặc định | Ghi chú |
|---|---|---|
| `MAX_UPLOAD_MB` | `50` `[Default]` | **`[TBD: OQ-013]`** |
| `MAX_PAGES` | `500` `[Default]` | Kiểm ở T-104; **`[TBD: OQ-013]`** |
| `MAX_FILES_PER_UPLOAD` | `20` `[Proposed]` | SAD §2.4 "số tệp `[TBD: OQ-013]`"; chưa có trong plan §3.3 |
| `S3_*` | plan §3.3 | Qua T-102 |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| OQ-013 chưa chốt giới hạn kích thước/số trang/số tệp | Thông báo và cấu hình proxy | Đọc từ cấu hình; `[Default]` 50 MB / 500 trang |
| Danh mục mã lỗi SDD §3.5 không có mã cho 400 (đầu vào sai) | Thiếu mã chuẩn | Dùng mã chung do T-003 định nghĩa (đề xuất `VALIDATION_ERROR`) |
| Số trang không kiểm được lúc tải lên (cần phân tích PDF, AD-09) | AC-005 phần "1 trang" chỉ báo được sau khi xử lý | T-104 từ chối ở worker và hiển thị trên dòng tài liệu |
| Tệp mồ côi khi giao dịch lỗi | Tốn dung lượng | T-407 dọn sau 24 giờ |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §4.1, §5.2 (T-103), §6.2
- [SAD](../../design/SAD.md) §2.4, §3.2.2, §4.1.4, §4.1.6
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.5, §3.6.1, §3.7
- [User_Stories](../../design/User_Stories.md) US-A1, US-A2, US-A5
- Task liên quan: [T-101](./T-101-job-queue.md), [T-102](./T-102-file-store-s3-adapter.md), [T-104](./T-104-ingest-worker.md), [T-107](./T-107-library-screen.md), [T-110](./T-110-telemetry-documents-access.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] OpenAPI mô tả đủ 202 (từng tệp), 400, 401, 403, 413.
