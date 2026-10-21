# T-112 — Thêm "Thử lại" cho tài liệu lỗi xử lý: `POST /api/v1/documents/{id}/retry` và nút trên màn 02

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 1 |
| **Loại** | Fullstack |
| **User story** | — chưa có story (xem [User_Stories §10](../../design/User_Stories.md#10-phần-thiết-kế-vượt-ra-ngoài-user-story-hiện-có)); đề xuất gắn vào US-A3 |
| **Ưu tiên** | **Chờ PO xác nhận** |
| **Ước lượng** | 0,5 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-101, T-104, T-107 |
| **Mở khóa (task chờ task này)** | — |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do — **không bắt đầu trước khi PO xác nhận giữ tính năng** |

## 1. Mục tiêu

Tài liệu ở trạng thái `FAILED` (ví dụ dịch vụ embedding tạm thời không phản hồi) có thể được người dùng gửi xử lý lại bằng một nút "Thử lại" trên dòng tài liệu, thay vì phải xóa rồi tải lên lại. Backend chuyển `FAILED → UPLOADED` và đưa lại job `ingest_document` vào hàng đợi.

## 2. Bối cảnh

- Nút "Thử lại" có trong thiết kế [02_library.html](../../design/html_design/02_library.html) (dòng "Biên bản họp 12-10.pdf" — badge "Lỗi xử lý"), và chuyển trạng thái `FAILED → UPLOADED : người dùng thử lại` có trong Blueprint §3.7 / [plan §6.2](../Implement_plan.md#62-trạng-thái-tài-liệu); Blueprint §3.6.1: "đặt `FAILED` kèm `failure_reason` và cho người dùng thử lại (không lỗi âm thầm, CN-08)".
- **Nhưng** không có BR/story/AC tương ứng: [User_Stories §10](../../design/User_Stories.md#10-phần-thiết-kế-vượt-ra-ngoài-user-story-hiện-có) đề xuất "thêm vào US-A3 hoặc tạo story riêng". [Plan §5.2](../Implement_plan.md#52-sprint-1--đăng-nhập--thư-viện-us-e1-a1a5-b1-b2): "Triển khai đơn giản… Ước lượng 0,5 ngày; cần PO xác nhận giữ lại". Endpoint ghi ở [plan §10.1](../Implement_plan.md#101-danh-mục-api-tóm-tắt) là *(bổ sung) — chờ PO xác nhận*.
- Nếu PO **bỏ** tính năng: giữ cờ `features.retryDocument=false` (T-107), không merge endpoint; người dùng xóa rồi tải lên lại.

## 3. Phạm vi

**Trong phạm vi**
- Endpoint `POST /api/v1/documents/{id}/retry`, `DocumentService.retry()`.
- Nối nút "Thử lại" đã dựng ở T-107 với API, bật cờ `features.retryDocument`.
- Khai báo route trong `ROUTE_ROLES` của T-109.

**Ngoài phạm vi**
- Thử lại tự động (đã có backoff của T-101).
- Thử lại tài liệu `NOT_EXTRACTABLE` (cần OCR — ngoài MVP).
- Thử lại khi tải lên bị lỗi mạng (khay tải lên, T-107).

## 4. Thiết kế chi tiết

**File**: `backend/app/documents/router.py`, `service.py` (`retry`), `frontend/src/api/documents.ts` (`retryDocument`), `frontend/src/pages/Library/DocumentTable.tsx`, `backend/tests/security/route_policy.py`.

**Hợp đồng API**

```http
POST /api/v1/documents/9c2d…/retry
Cookie: session=…   X-CSRF-Token: …
```

```json
202 Accepted
{ "id": "9c2d…", "name": "Biên bản họp 12-10.pdf", "status": "UPLOADED",
  "uploadedBy": { "id": "77ab…", "displayName": "Lê Thu Hà" },
  "uploadedAt": "2026-10-12T09:00:00Z", "pageCount": null, "failureReason": null }
```

| Tình huống | Phản hồi |
|---|---|
| `FAILED` (lý do thử lại được) | `202`, như trên |
| Đã `UPLOADED`/`PROCESSING` (bấm hai lần) | `202` trả trạng thái hiện tại, **không** tạo job mới (lũy đẳng) |
| `READY`, `NOT_EXTRACTABLE`, hoặc `FAILED` với `failure_reason = TOO_MANY_PAGES` | `409`, mã `INVALID_STATE` `[Proposed — SDD §3.5 chưa có mã 409 cho trường hợp này]` |
| Không tồn tại / `DELETED` | `404` |
| Không phiên / sai vai trò (SPONSOR) / thiếu CSRF | `401` / `403` / `403` |

Quyền: `require_role("MEMBER", "ADMIN")` — cùng nhóm với tải lên `[Proposed]` (SAD §4.1.1 không có dòng riêng cho thử lại).

**Service** (một giao dịch, plan §4.1)

```python
async def retry(self, user, document_id) -> Document:
    async with session.begin():
        doc = await repo.get_for_update(document_id)
        if doc is None or doc.status == "DELETED": raise AppError("NOT_FOUND", 404, …)
        if doc.status in ("UPLOADED", "PROCESSING"): return doc                  # lũy đẳng
        if doc.status != "FAILED" or doc.failure_reason in NON_RETRYABLE:       # {"TOO_MANY_PAGES"}
            raise AppError("INVALID_STATE", 409, "Tài liệu này không thể thử lại")
        await self.transition(doc, "UPLOADED", failure_reason=None)             # FAILED → UPLOADED (§6.2)
        await job_queue.enqueue(session, "ingest_document", {"document_id": str(doc.id)})
        await audit.write(session, user_id=user.id, action="retry", target=str(doc.id), result="success")
    return doc
```

- Handler `ingest_document` (T-104) đã lũy đẳng: xóa chunk dở dang trước khi ghi lại.
- Không phát sự kiện telemetry mới (PRD §5.2 không có); kết quả xử lý lại vẫn phát `document_upload_succeeded/rejected` như bình thường (T-110).

**Giao diện** (khớp 02_library.html)
- Nút chỉ hiện trên dòng `FAILED` có lý do thử lại được: `btn btn-sm`, biểu tượng refresh 16px, chữ "Thử lại", đứng trước nút xóa trong `.row-actions`; ẩn với SPONSOR.
- Bấm: vô hiệu nút ngay (tránh bấm đúp) → gọi API → thành công: dòng chuyển badge `proc` "Đang xử lý" (vòng quay), bỏ `.docnote` lỗi, bỏ nút "Thử lại", toast "Đã gửi lại để xử lý", `invalidateQueries(['documents'])` để thăm dò 3 s chạy lại.
- Lỗi `409`: toast "Tài liệu này không thể thử lại." và làm mới danh sách; lỗi mạng/5xx: toast "Không gửi lại được. Vui lòng thử lại." và bật lại nút `[Proposed]`.
- Nút có tên truy cập rõ ràng: `aria-label="Thử lại xử lý {tên}"` `[Proposed]` (HTML mẫu chỉ có chữ "Thử lại").

## 5. Các bước thực hiện

1. **Xác nhận với PO** (ghi kết quả vào mục "Trạng thái" và User_Stories §10 qua BA): giữ / gắn US-A3 / bỏ.
2. Viết `DocumentService.retry` + router; thêm `("POST", "/api/v1/documents/{id}/retry"): {"MEMBER","ADMIN"}` vào `ROUTE_ROLES` (T-109).
3. Test tích hợp backend (mục 7).
4. Viết `retryDocument()` ở frontend, nối `onRetry` của `DocumentTable`, bật `features.retryDocument=true`.
5. Test Vitest/MSW cho nút; thêm 1 kịch bản Playwright vào bộ Sprint 1 (`retry.spec.ts`) dùng `FakeEmbedding` ở chế độ lỗi.

## 6. Tiêu chí chấp nhận

- [ ] PO đã xác nhận giữ tính năng (có ghi nhận) trước khi merge.
- [ ] Tài liệu `FAILED` + `POST /retry` → `202`; CSDL: `status=UPLOADED`, `failure_reason` null, 1 job `ingest_document` mới `queued`, 1 `audit_log(action=retry)` — trong cùng giao dịch.
- [ ] Gọi `/retry` hai lần liên tiếp → chỉ 1 job mới.
- [ ] `/retry` trên `READY` hoặc `NOT_EXTRACTABLE` → `409 INVALID_STATE`, trạng thái không đổi.
- [ ] Sau thử lại, với embedding đã hoạt động lại, tài liệu tự đạt `READY` và màn 02 hiển thị "Sẵn sàng" không cần tải lại trang.
- [ ] Trên màn 02, nút "Thử lại" chỉ xuất hiện ở dòng `FAILED`; bấm → badge "Đang xử lý", toast "Đã gửi lại để xử lý".
- [ ] Route mới được T-109 kiểm: không phiên → `401`, SPONSOR → `403`.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `retry` với từng trạng thái (6) | Đúng bảng mục 4 |
| Integration | `FAILED → retry →` worker chạy với `FakeEmbedding` bình thường | `READY` |
| Integration | Retry lặp | 1 job mới |
| Integration | `failure_reason=TOO_MANY_PAGES` | `409` |
| Unit (Vitest) | Bấm "Thử lại", API 202 | Badge "Đang xử lý", toast, nút biến mất |
| Unit (Vitest) | API 409 | Toast lỗi, danh sách làm mới |
| E2E | `retry.spec.ts`: embedding lỗi → `FAILED` → bật lại → "Thử lại" | "Sẵn sàng" |

## 8. Cấu hình

Không có biến mới. Cờ frontend `features.retryDocument` (`true` khi PO xác nhận) `[Proposed]`. Embedding giả lập lỗi cho E2E dùng cơ chế kịch bản của `FakeEmbedding` (T-007).

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| **Chưa có story/AC** (User_Stories §10) | Có thể bị cắt phạm vi | Không làm trước khi PO xác nhận; T-107 ẩn nút sau cờ |
| Mã `INVALID_STATE` không có trong SDD §3.5 | Thiếu chuẩn hóa mã lỗi | Đề xuất bổ sung danh mục khi review |
| Người dùng bấm thử lại liên tục khi dịch vụ AI vẫn sập | Tạo tải lặp | Lũy đẳng + backoff T-101; giới hạn tốc độ chung (T-306) |
| Ai được thử lại (OQ-011) | Ma trận quyền | Cùng nhóm với tải lên; đổi tại `ROUTE_ROLES` + `require_role` |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §5.2 (đoạn "Retry tài liệu lỗi"), §6.2, §10.1
- [SAD](../../design/SAD.md) §2.2 (thử lại), §4.1.1
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.6.1, §3.7
- [User_Stories](../../design/User_Stories.md) US-A3, §10
- Màn hình: [02_library.html](../../design/html_design/02_library.html); ảnh [library.png](../../design/images/library.png)
- Task liên quan: [T-101](./T-101-job-queue.md), [T-104](./T-104-ingest-worker.md), [T-107](./T-107-library-screen.md), [T-109](./T-109-route-auth-guard-test.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Quyết định của PO được ghi lại (và BA cập nhật User_Stories §10 nếu thêm vào US-A3).
