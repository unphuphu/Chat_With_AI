# T-110 — Ghi sự kiện telemetry cho tải lên, xóa tài liệu và truy cập bị từ chối

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 1 |
| **Loại** | Backend |
| **User story** | US-A1, US-A2, US-B2, US-E1 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 0,5 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-103, T-106 |
| **Mở khóa (task chờ task này)** | T-401 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Bảng `usage_event` nhận đúng 5 sự kiện của PRD §5.2 cho nhóm tài liệu và truy cập — `document_upload_attempted`, `document_upload_succeeded`, `document_upload_rejected`, `document_deleted`, `access_denied` — với thuộc tính đúng danh sách, **không** chứa tên tệp hay nội dung tài liệu, ghi trong cùng giao dịch với thao tác nghiệp vụ.

## 2. Bối cảnh

- Danh mục sự kiện: PRD §5.2; phân công: [Implement_plan §10.2](../Implement_plan.md#102-sự-kiện-telemetry-prd-52).
- `usage_event` tách khỏi log kỹ thuật, chỉ chứa thuộc tính vận hành (DD-11, [SAD §3.1](../../design/SAD.md#31-chiến-lược-mô-hình-dữ-liệu-cốt-lõi), [SAD §4.3](../../design/SAD.md#43-khả-năng-quan-sát-observability)). Bảng phân vùng theo tháng (plan §6.1).
- Mục đích: phễu tải lên (AC-002, AC-004, AC-005), vòng đời thư viện (US-B2), kiểm chứng AC-018; nguồn cho báo cáo tuần (T-401) và đối soát AC-021 (T-403).

## 3. Phạm vi

**Trong phạm vi**
- `app/analytics/events.py`: `emit()` + mô hình thuộc tính **theo danh sách trắng** cho từng sự kiện (khung dùng chung cho T-212, T-303, T-304, T-401).
- Gọi `emit` tại các điểm đã đánh dấu ở T-103 (tải lên), T-104 (kết quả xử lý), T-106 (xóa), và trong xử lý lỗi xác thực/phân quyền của T-006 (`access_denied`).
- Ghi `audit_log(action="access_denied")` cùng lúc với sự kiện (SAD §4.1.6).

**Ngoài phạm vi**
- Sự kiện hỏi đáp (T-212), phản hồi/lịch sử (T-303, T-304), báo cáo tuần (T-401).
- Metric Prometheus `access_denied_total` (T-404).
- Tạo phân vùng hằng tháng tự động (T-407) — xem mục 9.

## 4. Thiết kế chi tiết

**File**: `backend/app/analytics/events.py`, `backend/app/analytics/repository.py`, sửa `backend/app/documents/service.py`, `backend/app/ingestion/ingest_document.py`, `backend/app/access/dependencies.py` (hoặc handler lỗi của T-006).

**API nội bộ**

```python
class EventName(StrEnum):
    DOCUMENT_UPLOAD_ATTEMPTED = "document_upload_attempted"
    DOCUMENT_UPLOAD_SUCCEEDED = "document_upload_succeeded"
    DOCUMENT_UPLOAD_REJECTED  = "document_upload_rejected"
    DOCUMENT_DELETED          = "document_deleted"
    ACCESS_DENIED             = "access_denied"

async def emit(session: AsyncSession, name: EventName, *, user_id: UUID | None, **props) -> None:
    model = PROPERTY_MODELS[name](**props)        # Pydantic, extra="forbid" → trường lạ là lỗi
    await repo.insert(session, id=uuid4(), event_name=name, user_id=user_id,
                      properties=model.model_dump(mode="json"))   # occurred_at = now() (DB)
```

**Danh mục sự kiện và điểm ghi**

| Sự kiện | `properties` (PRD §5.2) | Ghi ở đâu | Khi nào |
|---|---|---|---|
| `document_upload_attempted` | `file_type`, `file_size` | `DocumentService.upload_many` (T-103) | Mỗi tệp trong yêu cầu, kể cả bị từ chối |
| `document_upload_rejected` | `reason` ∈ `wrong_format` \| `too_large`, `file_type` | T-103 | Tệp bị `UNSUPPORTED_FORMAT` / `FILE_TOO_LARGE` |
| `document_upload_rejected` | `reason = not_extractable`, `file_type="pdf"` | `ingest_document` (T-104) | Tài liệu chuyển `NOT_EXTRACTABLE` |
| `document_upload_rejected` | `reason = too_large`, `file_type="pdf"` | T-104 | `FAILED` với `TOO_MANY_PAGES` `[Proposed]` |
| `document_upload_succeeded` | `document_id`, `page_count`, `processing_time_ms` | T-104 | Cùng giao dịch đặt `READY` |
| `document_deleted` | `document_id` | `DocumentService.delete` (T-106) | Cùng giao dịch đặt `DELETED` (không ghi khi gọi lặp) |
| `access_denied` | `attempted_path`, `reason` ∈ `unauthenticated` \| `unauthorized` | Phụ thuộc xác thực / `require_role` (T-006) | Mỗi phản hồi `401`/`403` của `/api/v1/*` |

- `user_id` là cột riêng của `usage_event` (PRD liệt kê `user_id` trong thuộc tính — lưu ở cột, không lặp trong `properties`). `timestamp` = cột `occurred_at`.
- `file_type`: phần mở rộng chữ thường không dấu chấm, cắt 10 ký tự (`pdf`, `docx`, `jpg`…); không có → `unknown`. `file_size`: byte đã nhận (với tệp bị dừng do quá lớn là số byte tại thời điểm dừng).
- `processing_time_ms` = thời điểm đặt `READY` − `document.uploaded_at`.
- `attempted_path`: **mẫu route** (`/api/v1/documents/{id}`), không phải đường dẫn thật, để không lưu ID/tham số; route không khớp → `"unmatched"`. `user_id = null` khi `unauthenticated`.
- **Cấm** trong `properties`: tên tệp, nội dung, query string, header. Danh sách trắng bằng `extra="forbid"`.
- `document_upload_succeeded` được ghi bởi Worker — Worker cần quyền INSERT `usage_event`.
- Lỗi khi ghi sự kiện **làm hỏng** giao dịch nghiệp vụ (cùng giao dịch) — chấp nhận để số liệu khớp AC-021; riêng `access_denied` ghi bằng giao dịch riêng, lỗi chỉ log cảnh báo (không đổi mã 401/403).

## 5. Các bước thực hiện

1. Viết `events.py` (enum, mô hình thuộc tính, `emit`) + repository.
2. Gắn `emit` vào T-103 (attempted/rejected), T-106 (deleted) trong cùng `session`.
3. Gắn `emit` vào T-104 (succeeded, rejected `not_extractable`/`too_large`) — nếu T-104 chưa merge, để PR nhỏ bổ sung sau khi merge.
4. Gắn `access_denied` + `audit_log` vào phụ thuộc xác thực/phân quyền.
5. Test (mục 7), gồm test quét `usage_event.properties` không chứa tên tệp của fixture.

## 6. Tiêu chí chấp nhận

- [ ] Tải 3 PDF + 1 `.docx` trong một yêu cầu → 4 `document_upload_attempted`, 1 `document_upload_rejected{reason: wrong_format, file_type: docx}`.
- [ ] Tệp vượt `MAX_UPLOAD_MB` → `document_upload_rejected{reason: too_large}`.
- [ ] PDF xử lý xong `READY` → đúng 1 `document_upload_succeeded` có `document_id`, `page_count`, `processing_time_ms > 0`.
- [ ] PDF scan → `document_upload_rejected{reason: not_extractable}`.
- [ ] Xóa 1 tài liệu 2 lần → đúng 1 `document_deleted`.
- [ ] Gọi `GET /api/v1/documents/{uuid}` không cookie → 1 `access_denied{attempted_path: "/api/v1/documents/{id}", reason: unauthenticated}`, `user_id` null; SPONSOR gọi `DELETE` → `reason: unauthorized`, có `user_id`.
- [ ] Không bản ghi `usage_event` nào chứa tên tệp gốc hoặc chuỗi con của nội dung PDF fixture (test quét).
- [ ] Gọi `emit` với thuộc tính ngoài danh sách → lỗi kiểm tra (test đơn vị).

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `emit(DOCUMENT_DELETED, file_name="x")` | `ValidationError` |
| Unit | `file_type` từ `"Bao-Cao.DOCX"`, `"noext"` | `docx`, `unknown` |
| Integration | Luồng tải lên trộn hợp lệ/lỗi | Số sự kiện như mục 6 |
| Integration | Giao dịch tải lên rollback | Không còn sự kiện `attempted` của tệp đó |
| Integration | Worker `READY` / `NOT_EXTRACTABLE` | `succeeded` / `rejected` |
| Integration | 401 / 403 | `access_denied` + `audit_log` tương ứng |
| Integration | Quét toàn bảng tìm tên tệp fixture | 0 kết quả |

## 8. Cấu hình

Không có biến mới. Phụ thuộc `DATABASE_URL`. Thời gian lưu `usage_event` 13 tháng (SAD §2.3) — `[TBD: OQ-019]`, thực thi ở T-407.

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| `usage_event` phân vùng theo tháng; chưa có phân vùng của tháng hiện tại → INSERT lỗi | Hỏng giao dịch tải lên/xóa | Kiểm T-004 đã tạo phân vùng đủ cho thời gian dự án hoặc phân vùng `DEFAULT`; tự động hóa ở T-407 |
| Ghi sự kiện ở Worker cần code T-104, nhưng T-104 không nằm trong "Phụ thuộc" | Thiếu `succeeded`/`not_extractable` nếu làm trước T-104 | Làm bước 3 sau khi T-104 merge (cùng sprint) |
| Bot gọi API không phiên tạo nhiều `access_denied` | Bảng phình | Giới hạn tốc độ ở proxy; theo dõi ở T-404 |
| OQ-006 có thể giới hạn cả thuộc tính vận hành | Phải bỏ bớt trường | Danh sách trắng tập trung một chỗ |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §4.1 (log), §6.1 (`usage_event`), §10.2
- [SAD](../../design/SAD.md) §2.3 (lưu giữ), §3.1, §3.2.2 bước 7, §4.1.6, §4.3
- [Blueprint_Design](../../design/Blueprint_Design.md) DD-11, QAS-04, QAS-09
- [User_Stories](../../design/User_Stories.md) US-A1, US-A2, US-B2, US-E1
- Task liên quan: [T-103](./T-103-upload-api.md), [T-104](./T-104-ingest-worker.md), [T-106](./T-106-delete-document-purge.md), [T-006](./T-006-auth-session-dev-identity.md), [T-401](./T-401-weekly-report-api.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Bảng "danh mục sự kiện" ở mục 4 được giữ đồng bộ với `PROPERTY_MODELS` (review kiểm).
