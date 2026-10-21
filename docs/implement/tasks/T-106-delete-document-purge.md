# T-106 — Xây dựng xóa tài liệu `DELETE /api/v1/documents/{id}` và job nền `purge_document`

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 1 |
| **Loại** | Backend |
| **User story** | US-B2 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 1,5 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-101, T-102, T-103 |
| **Mở khóa (task chờ task này)** | T-107, T-110, T-407 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Người dùng có quyền xóa được một tài liệu: ngay khi giao dịch commit, tài liệu biến khỏi danh sách và **không còn được dùng làm nguồn** (xóa mềm `DELETED`); job `purge_document` xóa vật lý chunk/vector và tệp PDF ở nền, giữ lại bản ghi `document` để hội thoại cũ vẫn hiển thị tên trích dẫn.

## 2. Bối cảnh

- DD-10: xóa mềm tức thì rồi xóa vật lý nền; QAS-06: hiệu lực ≤ 1 giây sau xác nhận, xóa vật lý ≤ `[TBD: OQ-019]` (mặc định ≤ 24 giờ).
- Luồng: [SAD §3.2.3](../../design/SAD.md#323-luồng-3--xóa-tài-liệu-api-05); Blueprint §3.6.3.
- BRU-002 / AC-007: sau khi xóa X, X không còn trong danh sách và câu hỏi về nội dung chỉ có trong X trả "không tìm thấy". Truy xuất (T-203) luôn `JOIN document` lọc `READY` ([SAD §3.1](../../design/SAD.md#31-chiến-lược-mô-hình-dữ-liệu-cốt-lõi) "Nhất quán trạng thái").
- Quyền xóa `[TBD: OQ-011]` → mặc định MEMBER được xóa, ADMIN được xóa, SPONSOR không ([SAD §4.1.1](../../design/SAD.md#411-xác-thực-và-phân-quyền)); kiểm qua **một hàm** để đổi nhanh ([plan §9.1](../Implement_plan.md#91-quyết-định-cần-có-và-ảnh-hưởng-tới-lập-trình)).

## 3. Phạm vi

**Trong phạm vi**
- Endpoint API-05, `DocumentService.delete()`, hàm quyền `can_delete_document(user, doc)`.
- Handler `purge_document` (xóa chunk theo lô, xóa đối tượng kho tệp), đăng ký trong `app/worker.py`.
- `audit_log(action="delete")`.

**Ngoài phạm vi**
- Sự kiện `document_deleted` (T-110 thêm `emit` vào điểm đánh dấu).
- Quét lại `DELETED` chưa purge sau khôi phục sao lưu, purge ≤ 24 giờ có giám sát (T-407, T-408).
- Hộp thoại xác nhận trên giao diện (T-107).
- Xóa hội thoại/citation cũ (giữ nguyên theo SAD §3.2.3).

## 4. Thiết kế chi tiết

**File**: `backend/app/documents/router.py`, `service.py` (`delete`), `policies.py` (`can_delete_document`), `backend/app/ingestion/purge_document.py`, `backend/app/ingestion/chunk_repository.py` (`delete_batch`).

**Hợp đồng API**

```http
DELETE /api/v1/documents/0b8e…
Cookie: session=…   X-CSRF-Token: …
```

| Tình huống | Phản hồi |
|---|---|
| Xóa thành công | `204 No Content` |
| Tài liệu đã `DELETED` (gọi lại) | `204`, không tạo job/audit mới (lũy đẳng) |
| Không tồn tại | `404` (mã 404 chung của T-003) |
| Không cookie | `401 UNAUTHENTICATED` |
| SPONSOR, hoặc `can_delete_document` = `False`, hoặc thiếu CSRF | `403 FORBIDDEN` |

**Service**

```python
def can_delete_document(user: CurrentUser, doc: Document) -> bool:
    return user.role in settings.DELETE_ALLOWED_ROLES          # [TBD: OQ-011], mặc định {"MEMBER","ADMIN"}

async def delete(self, user, document_id) -> None:
    async with session.begin():
        doc = await repo.get_for_update(document_id)           # SELECT … FOR UPDATE
        if doc is None: raise AppError("NOT_FOUND", 404, …)
        if doc.status == "DELETED": return                     # lũy đẳng
        if not can_delete_document(user, doc): raise AppError("FORBIDDEN", 403, …)
        await self.transition(doc, "DELETED", deleted_at=now())
        await job_queue.enqueue(session, "purge_document", {"document_id": str(doc.id)})
        await audit.write(session, user_id=user.id, action="delete", target=str(doc.id), result="success")
        # T-110: emit document_deleted tại đây
```

- Trạng thái được phép xóa: `READY`, `NOT_EXTRACTABLE`, `FAILED` (plan §6.2) **và** `UPLOADED`, `PROCESSING` `[Proposed]` — vì màn 02 hiển thị nút xóa trên dòng "Đang xử lý". Handler `ingest_document` (T-104) đã khóa dòng và bỏ ghi chunk khi thấy `DELETED`. Cần Tech Lead xác nhận bổ sung vào sơ đồ trạng thái.
- `retrieval` không cần thay đổi: chỉ đọc chunk của tài liệu `READY`.

**Handler `purge_document`** (lũy đẳng)

```python
async def purge_document(payload):
    doc = await documents.get(payload["document_id"])
    if doc is None or doc.status != "DELETED":
        return                                                  # không bao giờ purge tài liệu chưa xóa
    while await chunk_repo.delete_batch(doc.id, limit=1000):    # mỗi lô một giao dịch ngắn
        pass
    await files.delete(doc.file_ref)                            # lũy đẳng (T-102)
    await documents.mark_purged(doc.id)                         # log purge_completed; giữ bản ghi document
```

```sql
DELETE FROM chunk WHERE id IN (
  SELECT id FROM chunk WHERE document_id = :doc_id LIMIT 1000);
```

- Lỗi kho tệp/CSDL → `TransientJobError` (thử lại theo backoff T-101). Hết lượt → job `failed`; T-407 quét lại.
- `mark_purged`: chỉ ghi log + (nếu cần) cột thời điểm purge — `[Proposed]` không thêm cột ở MVP, dùng job `succeeded` làm bằng chứng.
- `citation.chunk_id` không có khóa ngoại tới `chunk` (plan §6.1) → xóa chunk không ảnh hưởng hội thoại cũ.

## 5. Các bước thực hiện

1. Thêm `DELETE_ALLOWED_ROLES` vào settings và `.env.example`; viết `can_delete_document` + test.
2. Viết `repo.get_for_update`; viết `DocumentService.delete` dùng `transition()` (T-103).
3. Viết router `DELETE /api/v1/documents/{id}` (phụ thuộc phiên + CSRF; kiểm quyền ở service).
4. Viết `chunk_repo.delete_batch` và handler `purge_document`; đăng ký trong `app/worker.py`.
5. Test tích hợp mục 7, gồm test "ngay sau DELETE, truy vấn lọc `READY` không trả chunk của X".

## 6. Tiêu chí chấp nhận

- [ ] Xóa tài liệu `READY` → `204`; trong cùng giao dịch: `status=DELETED`, `deleted_at` khác null, 1 job `purge_document` `queued`, 1 `audit_log(action=delete)`.
- [ ] Ngay sau `204` (trước khi purge chạy), truy vấn vector/full-text theo mẫu [plan §6.5](../Implement_plan.md#65-truy-xuất-lai) không trả chunk nào của X (QAS-06, nền tảng cho AC-007).
- [ ] `GET /api/v1/documents` sau xóa không chứa X; `GET /documents/{id}` và `/file` → `404` (AC-007 phần danh sách).
- [ ] Gọi `DELETE` lần 2 → `204`, số job `purge_document` và audit của X không tăng.
- [ ] Sau khi worker chạy: 0 chunk của X, đối tượng `documents/{X}.pdf` không còn, bản ghi `document` X vẫn còn (`DELETED`).
- [ ] Chạy `purge_document` 2 lần → không lỗi.
- [ ] `purge_document` với tài liệu chưa `DELETED` → không xóa gì.
- [ ] SPONSOR gọi `DELETE` → `403`, tài liệu không đổi; đổi `DELETE_ALLOWED_ROLES=ADMIN` → MEMBER nhận `403` (không sửa code).
- [ ] Xóa tài liệu đang `PROCESSING` rồi để ingest chạy xong → tài liệu vẫn `DELETED`, 0 chunk.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `can_delete_document` theo 3 vai trò và cấu hình | Đúng ma trận SAD §4.1.1 |
| Integration | Xóa `READY` | Như mục 6 |
| Integration | SQL truy xuất mẫu ngay sau xóa | 0 dòng của X |
| Integration | Xóa lặp | `204`, không job trùng |
| Integration | Không tồn tại | `404` |
| Integration (MinIO) | Purge 2.500 chunk | 3 lô, 0 chunk còn lại, đối tượng bị xóa |
| Integration | Kho tệp lỗi lần 1 | Job thử lại, lần 2 thành công |
| Integration | Xóa khi `PROCESSING` + ingest hoàn tất sau | `DELETED`, 0 chunk |

## 8. Cấu hình

| Biến | Mặc định | Ghi chú |
|---|---|---|
| `DELETE_ALLOWED_ROLES` | `MEMBER,ADMIN` `[Default]` `[Proposed tên biến]` | **`[TBD: OQ-011]`** |
| `PURGE_BATCH_SIZE` | `1000` `[Proposed]` | |
| Thời hạn purge | ≤ 24 giờ `[TBD: OQ-019]` | Giám sát ở T-407 |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| OQ-011: ai được xóa | Ma trận quyền | Một hàm + cấu hình; mặc định MEMBER |
| Sơ đồ trạng thái (plan §6.2, SDD §3.7) không có `UPLOADED/PROCESSING → DELETED` nhưng màn 02 có nút xóa ở dòng "Đang xử lý" | Lệch thiết kế | `[Proposed]` cho phép; Tech Lead/PO xác nhận, nếu không thì trả `409` và ẩn nút |
| Purge thất bại hết lượt | Dữ liệu tồn lâu hơn 24 giờ | T-407 quét `DELETED` còn chunk/đối tượng |
| Khôi phục sao lưu làm "sống lại" dữ liệu đã purge | Vi phạm BRU-002 về lưu trữ (không ảnh hưởng truy xuất vì vẫn `DELETED`) | T-408 chạy lại purge |
| Nửa sau AC-007 (hỏi → "không tìm thấy") cần luồng hỏi đáp Sprint 2 | Chưa kiểm E2E được ở Sprint 1 | Kiểm bằng SQL ở đây; E2E đầy đủ ở T-213 |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §6.1, §6.2, §6.5, §9.1
- [SAD](../../design/SAD.md) §2.3 (lưu giữ), §3.1, §3.2.3, §4.1.1, §4.1.6
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.6.3, §3.7, DD-10, QAS-06
- [User_Stories](../../design/User_Stories.md) US-B2
- Task liên quan: [T-101](./T-101-job-queue.md), [T-102](./T-102-file-store-s3-adapter.md), [T-103](./T-103-upload-api.md), [T-107](./T-107-library-screen.md), [T-110](./T-110-telemetry-documents-access.md), [T-407](./T-407-retention-cleanup.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Quyết định về xóa tài liệu đang xử lý được ghi vào PR (đã xác nhận hay chuyển sang `409`).
