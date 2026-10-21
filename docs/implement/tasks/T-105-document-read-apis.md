# T-105 — Xây dựng API đọc thư viện: danh sách, chi tiết, tệp PDF có `Range` (API-03/04/06)

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 1 |
| **Loại** | Backend |
| **User story** | US-A3, US-B1, US-C3 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 1,5 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-102, T-103 |
| **Mở khóa (task chờ task này)** | T-107, T-210 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Giao diện lấy được danh sách thư viện (tên, trạng thái, người tải, ngày tải, số trang, lý do lỗi) có phân trang, thăm dò trạng thái một tài liệu, và tải tệp PDF gốc theo khoảng byte để pdf.js mở đúng trang. Tài liệu `DELETED` không bao giờ xuất hiện hay tải được.

## 2. Bối cảnh

- Hợp đồng: [SAD §2.4](../../design/SAD.md#24-tầng-backend--api) (API-03, API-04, API-06; phân trang `limit` mặc định 50, tối đa 200 + `cursor`).
- BR-006 / AC-006: mỗi tài liệu đủ 4 thông tin (tên, người tải lên, ngày tải lên, trạng thái).
- BR-003 / AC-003: giao diện thăm dò 3 s/lần khi còn `UPLOADED/PROCESSING` ([SAD §2.1](../../design/SAD.md#21-tầng-frontend--client-cmp-01)).
- US-C3: viewer pdf.js (T-210) mở `GET /documents/{id}/file` hỗ trợ `Range`.
- Quyền: MEMBER, SPONSOR, ADMIN đều được xem ([SAD §4.1.1](../../design/SAD.md#411-xác-thực-và-phân-quyền)).

## 3. Phạm vi

**Trong phạm vi**
- `GET /api/v1/documents`, `GET /api/v1/documents/{id}`, `GET /api/v1/documents/{id}/file`.
- Lấy `displayName` người tải qua service của `access` (không `JOIN` bảng `app_user` từ module `documents`).
- Trường bổ sung `counts` và `limits` trong phản hồi danh sách `[Proposed]` (cho bộ đếm, quyết định thăm dò và dòng giới hạn của màn 02/03).

**Ngoài phạm vi**
- Tải lên (T-103), xóa (T-106), thử lại (T-112).
- Tìm kiếm/sắp xếp tùy chọn theo cột (không có trong thiết kế).
- Hiển thị/tô đoạn trong pdf.js (T-210).

## 4. Thiết kế chi tiết

**File**: `backend/app/documents/router.py`, `service.py` (`list_documents`, `get_document`, `open_file`), `repository.py`, `schemas.py` (`DocumentOut`, `DocumentListOut`), `backend/app/access/service.py` (`get_display_names(ids) -> dict[UUID, str]`).

**API-03 — danh sách**

```http
GET /api/v1/documents?limit=50&cursor=eyJ1IjoiMjAyNi0xMC0yMVQwODowMDowMFoiLCJpIjoiLi4uIn0&status=READY
```

```json
200 OK
{ "items": [
    { "id": "0b8e…", "name": "Hợp đồng khung đối tác A.pdf", "status": "READY",
      "uploadedBy": { "id": "5f1a…", "displayName": "Nguyễn Văn An" },
      "uploadedAt": "2026-10-14T02:31:00Z", "pageCount": 48, "failureReason": null },
    { "id": "9c2d…", "name": "Biên bản họp 12-10.pdf", "status": "FAILED",
      "uploadedBy": { "id": "77ab…", "displayName": "Lê Thu Hà" },
      "uploadedAt": "2026-10-12T09:00:00Z", "pageCount": null, "failureReason": "EMBEDDING_UNAVAILABLE" } ],
  "nextCursor": null,
  "counts": { "total": 5, "ready": 2, "inProgress": 1 },
  "limits": { "maxUploadMb": 50, "maxPages": 500 } }
```

- SAD ghi `uploadedBy` không nêu kiểu; dạng `{id, displayName}` là `[Proposed]`. `counts`, `limits` là `[Proposed]`.
- `counts.total` = số tài liệu ≠ `DELETED`; `ready` = `READY`; `inProgress` = `UPLOADED` + `PROCESSING` (giao diện thăm dò khi `inProgress > 0`).
- Sắp xếp `uploaded_at DESC, id DESC`; `cursor` = base64url của `{"u": uploaded_at, "i": id}` (keyset) `[Proposed]`.
- `status` lọc tùy chọn, chấp nhận một trong 5 trạng thái ≠ `DELETED`; giá trị khác → `400`.
- `limit` ngoài `1..200` → `400`. Trường query lạ → `400` (Pydantic `extra="forbid"`).

```sql
SELECT id, name, status, uploaded_by, uploaded_at, page_count, failure_reason
FROM document
WHERE status <> 'DELETED' AND (:status IS NULL OR status = :status)
  AND (:cu IS NULL OR (uploaded_at, id) < (:cu, :ci))
ORDER BY uploaded_at DESC, id DESC
LIMIT :limit + 1;
-- counts: một truy vấn
SELECT count(*) FILTER (WHERE status <> 'DELETED') AS total,
       count(*) FILTER (WHERE status = 'READY') AS ready,
       count(*) FILTER (WHERE status IN ('UPLOADED','PROCESSING')) AS in_progress
FROM document;
```

**API-04 — chi tiết**: `GET /api/v1/documents/{id}` → `200` một phần tử như trên. Không tồn tại hoặc `DELETED` → `404` (mã lỗi 404 chung do T-003 định nghĩa; SDD §3.5 chưa có — xem mục 9).

**API-06 — tệp**

| Yêu cầu | Phản hồi |
|---|---|
| Không `Range` | `200`, `Content-Length` = kích thước |
| `Range: bytes=0-65535` | `206`, `Content-Range: bytes 0-65535/<size>` |
| `Range: bytes=-500` / `bytes=1000-` | `206` theo RFC 9110 |
| Range ngoài kích thước | `416`, `Content-Range: bytes */<size>` |
| Nhiều khoảng (`0-1,5-9`) | `200` toàn tệp `[Proposed]` (không hỗ trợ multipart/byteranges) |
| `DELETED` / không tồn tại | `404` |

Header luôn có: `Content-Type: application/pdf`, `Accept-Ranges: bytes`, `Content-Disposition: inline; filename*=UTF-8''<tên đã percent-encode>`, `X-Content-Type-Options: nosniff`, `Cache-Control: private, no-store` `[Proposed]`. Thân phản hồi `StreamingResponse` từ `FileStorePort.open_stream(start, end)` — không nạp cả tệp.

- Trạng thái phục vụ được: mọi trạng thái ≠ `DELETED` (theo plan). Màn 02 chỉ hiện nút "Xem" cho `READY`.
- Kiểm tra trạng thái **trước** khi mở luồng; nếu xóa xảy ra giữa chừng, luồng đang chạy có thể kết thúc (chấp nhận).

## 5. Các bước thực hiện

1. Viết `schemas.py` (Pydantic, `alias_generator` camelCase).
2. Viết repository: `list_page(status, cursor, limit)`, `counts()`, `get_visible(id)`.
3. Viết `access.service.get_display_names()` (một truy vấn `WHERE id = ANY(:ids)`).
4. Viết `DocumentService.list_documents/get_document` + router với `require_role("MEMBER","SPONSOR","ADMIN")`.
5. Viết bộ phân tích `Range` (`parse_range(header, size) -> tuple[int,int] | None`, ném `RangeNotSatisfiable`).
6. Viết `open_file` + router trả `StreamingResponse` 200/206/416.
7. Test (mục 7); cập nhật OpenAPI.

## 6. Tiêu chí chấp nhận

- [ ] Thư viện có 5 tài liệu ≠ `DELETED` và 1 `DELETED` → danh sách trả 5 mục, `counts.total=5`; mỗi mục có `name`, `uploadedBy.displayName`, `uploadedAt`, `status` khác rỗng (AC-006).
- [ ] 250 tài liệu, `limit=200` → trang 1 có 200 mục + `nextCursor`; trang 2 có 50 mục, `nextCursor=null`, không trùng/thiếu.
- [ ] `GET /documents/{id}` của tài liệu `DELETED` → `404`.
- [ ] `GET /file` với `Range: bytes=0-4` → `206`, thân `%PDF-`, `Content-Range: bytes 0-4/<size>`.
- [ ] `GET /file` không `Range` với tệp 50 MB → RSS API tăng < 32 MB.
- [ ] `Range: bytes=999999999-` → `416`.
- [ ] Mọi phản hồi `/file` có `X-Content-Type-Options: nosniff` và `Content-Disposition: inline`.
- [ ] Không cookie → `401` trên cả 3 endpoint.
- [ ] P95 danh sách 50 mục trên 500 tài liệu < 200 ms ở local `[Proposed]`.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `parse_range("bytes=-500", 1000)` | `(500, 999)` |
| Unit | `parse_range("bytes=5-2", 1000)` | `RangeNotSatisfiable` |
| Unit | Mã hóa/giải mã `cursor`; `cursor` rác | Khớp / `400` |
| Integration | Danh sách loại `DELETED`, `counts` đúng | Như mục 6 |
| Integration | Lọc `status=FAILED` | Chỉ `FAILED`, có `failureReason` |
| Integration | Phân trang 250 mục | 200 + 50, không trùng |
| Integration (MinIO) | `Range` đầu/giữa/cuối tệp | Byte khớp tệp gốc |
| Integration | Tên tệp có dấu tiếng Việt | `Content-Disposition` dạng `filename*=UTF-8''…` hợp lệ |
| Contract | Schema `DocumentListOut` | Khớp OpenAPI |

## 8. Cấu hình

| Biến | Mặc định | Ghi chú |
|---|---|---|
| `MAX_UPLOAD_MB`, `MAX_PAGES` | `50`, `500` `[Default]` | Trả trong `limits`; **`[TBD: OQ-013]`** |
| `S3_*` | plan §3.3 | Qua T-102 |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| SDD §3.5 không có mã lỗi cho 404/400 | Thiếu mã chuẩn | Dùng mã chung của T-003 |
| Quyền xem theo tài liệu nếu OQ-011 đòi phân quyền | Phải lọc danh sách/tệp | Điểm mở rộng `document_acl` (SAD §3.1); MVP thư viện chung |
| `counts`/`limits` là trường đề xuất | Lệch hợp đồng SAD | Thêm có tính cộng (không phá vỡ); Tech Lead xác nhận ở review |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §4.1, §5.2 (T-105), §10.1
- [SAD](../../design/SAD.md) §2.1, §2.4, §3.1, §4.1.1, §4.1.4
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.5, §3.7
- [User_Stories](../../design/User_Stories.md) US-A3, US-B1, US-C3
- Màn hình: [02_library.html](../../design/html_design/02_library.html), [06_citation_viewer.html](../../design/html_design/06_citation_viewer.html)
- Task liên quan: [T-102](./T-102-file-store-s3-adapter.md), [T-103](./T-103-upload-api.md), [T-107](./T-107-library-screen.md), [T-210](./T-210-citation-viewer-screen.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] pdf.js (bản thử tối thiểu) mở được tệp qua `/file` với tải theo khoảng (quan sát thấy phản hồi `206`).
