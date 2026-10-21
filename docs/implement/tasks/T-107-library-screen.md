# T-107 — Xây dựng màn hình 02 Thư viện tài liệu (`/library`)

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 1 |
| **Loại** | Frontend |
| **User story** | US-A1, US-A2, US-A3, US-A4, US-A5, US-B1, US-B2 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 4 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-005, T-103, T-104, T-105, T-106 |
| **Mở khóa (task chờ task này)** | T-108, T-111, T-112 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Người dùng tải một hoặc nhiều PDF bằng kéo thả hoặc chọn tệp, thấy tiến trình và lỗi **từng tệp**, xem bảng thư viện có badge trạng thái (biểu tượng + chữ + màu) tự cập nhật, và xóa tài liệu qua hộp thoại xác nhận — giống hệt [02_library.html](../../design/html_design/02_library.html).

## 2. Bối cảnh

- Thiết kế: [02_library.html](../../design/html_design/02_library.html); ảnh nghiệm thu [library.png](../../design/images/library.png), [library_delete_modal.png](../../design/images/library_delete_modal.png).
- Đối chiếu từng story: [User_Stories §2–3](../../design/User_Stories.md#2-epic-a--tiếp-nhận-tài-liệu) (US-A1…A5, B1, B2).
- Thăm dò 3 s/lần **chỉ khi** còn `UPLOADED/PROCESSING` ([SAD §2.1](../../design/SAD.md#21-tầng-frontend--client-cmp-01)); quy ước FE [plan §4.2](../Implement_plan.md#42-frontend).
- PRD §4.2: từ chối tệp sai định dạng ngay khi chọn; cảnh báo "không thể truy vấn" gắn cố định trên dòng; mất mạng khi tải → lỗi rõ ràng + thử lại, không mất tệp đã tải xong.
- API: T-103 (`POST /documents`), T-105 (`GET /documents` có `counts`, `limits`), T-106 (`DELETE`).

## 3. Phạm vi

**Trong phạm vi**
- Trang `LibraryPage` ở route `/library`; thành phần `Dropzone`, `UploadTray`, `DocumentTable`, `StatusBadge`, `ConfirmModal`, `Toast` (dùng lại nếu T-005 đã có).
- Hàm API `listDocuments`, `uploadFile` (có tiến trình), `deleteDocument`.
- Ẩn vùng tải lên và nút xóa với SPONSOR (chỉ xem — SAD §4.1.1) `[Proposed]`.
- Khi `counts.total = 0` và khay rỗng → hiển thị `EmptyLibrary` (T-108).
- Chuỗi trong `i18n/vi.json`; test Vitest + Testing Library.

**Ngoài phạm vi**
- Gọi API thử lại tài liệu `FAILED` (T-112): T-107 chỉ dựng nút "Thử lại" với prop `onRetry`; ẩn sau cờ `features.retryDocument=false` cho tới khi T-112 merge.
- Màn xem trích dẫn (T-210): nút "Xem" chỉ điều hướng tới `/documents/:id/view?page=1`.
- Màn trống (T-108).

## 4. Thiết kế chi tiết

**File**

| File | Nội dung |
|---|---|
| `frontend/src/pages/Library/LibraryPage.tsx` | Bố cục trang, nối query/mutation |
| `frontend/src/components/Dropzone.tsx` | Vùng kéo thả + input ẩn |
| `frontend/src/pages/Library/UploadTray.tsx` | Khay "Đang tải lên" |
| `frontend/src/pages/Library/DocumentTable.tsx` | Bảng + hành động dòng |
| `frontend/src/components/StatusBadge.tsx` | Badge theo trạng thái |
| `frontend/src/components/ConfirmModal.tsx`, `Toast.tsx` | Hộp thoại, thông báo nhanh |
| `frontend/src/api/documents.ts` | `listDocuments`, `uploadFile`, `deleteDocument` |
| `frontend/src/i18n/vi.json` | Khóa `library.*` |

**Bố cục (khớp HTML, khung `.page` max-width 1200px, padding 24/16/56)**
1. AppBar (T-005): mục "Thư viện" `aria-current="page"`.
2. `page-head`: `h1` "Thư viện tài liệu"; `p` "Tài liệu PDF dùng chung của đội. Chỉ tài liệu ở trạng thái “Sẵn sàng” được dùng để trả lời."; bên phải nút `btn-primary` biểu tượng chat "Hỏi đáp với tài liệu" → `/chat` (vô hiệu `aria-disabled` + `title="Cần ít nhất một tài liệu ở trạng thái Sẵn sàng"` khi `counts.ready = 0`).
3. `Dropzone`: viền nét đứt 2px, biểu tượng upload 44px màu primary; `h2` "Kéo thả PDF vào đây"; `p` "hoặc chọn một hoặc nhiều tệp từ máy của bạn"; `label.btn-primary` (biểu tượng +) "Chọn tệp PDF" gắn `input type=file accept="application/pdf,.pdf" multiple` lớp `sr`; dòng `.limits` "Chỉ chấp nhận định dạng PDF · Tối đa {maxUploadMb} MB và {maxPages} trang mỗi tệp" (giá trị từ `limits` của API, `[TBD: OQ-013]`). Khi `dragenter/dragover` thêm lớp `drag` (viền primary, nền `primary-soft`); `dragleave/drop` bỏ lớp.
4. `UploadTray` (chỉ hiện khi có mục): `section.card` `aria-labelledby` `h2` "Đang tải lên", `aria-live="polite"`. Mỗi dòng `.up`:
   - Đang tải: biểu tượng file · tên (cắt `…`) · `div.bar` 160px (90px khi < 640px) `role="progressbar"` `aria-valuemin=0 aria-valuemax=100 aria-valuenow=n aria-label="Tiến trình tải {tên}"` · chữ `n%`.
   - Bị từ chối (`.up.bad`): biểu tượng cảnh báo · tên · chữ màu `--err` "Bị từ chối: chỉ chấp nhận định dạng PDF" hoặc "Bị từ chối: vượt quá giới hạn {maxUploadMb} MB mỗi tệp" · nút ghost 36px biểu tượng X `aria-label="Bỏ qua thông báo về {tên}"`.
   - Lỗi mạng: biểu tượng cảnh báo · tên · "Tải lên không thành công: mất kết nối" · nút `btn-sm` "Thử lại" (gửi lại tệp đó) + nút X `[Proposed — theo PRD §4.2]`.
   - Thành công: dòng biến khỏi khay; toast "Đã tải lên “{tên}”"; tài liệu xuất hiện **đầu bảng** với "Đang xử lý" (invalidate `['documents']`).
5. Khối danh sách: hàng `.cta` gồm `h2` "Tài liệu trong thư viện" và `.count` `aria-live="polite"`: "**{total}** tài liệu" "**{ready}** sẵn sàng".
6. `DocumentTable` trong `.card > .table-wrap` (cuộn ngang khi hẹp), `caption.sr` "Danh sách tài liệu trong thư viện". Cột: Tên tài liệu · Trạng thái · Người tải lên · Ngày tải (`dd/mm/yyyy`, `vi-VN`) · Số trang (căn phải, `—` khi null) · cột hành động (tiêu đề `sr` "Hành động").

**Badge và hành động theo trạng thái**

| `status` | Badge (lớp · biểu tượng · chữ) | Ghi chú dưới tên (`.docnote`) | Hành động |
|---|---|---|---|
| `READY` | `ok` · tick · "Sẵn sàng" | — | Xem (biểu tượng mở ngoài, `aria-label="Xem {tên}"`) · Xóa |
| `UPLOADED`, `PROCESSING` | `proc` · vòng quay `.spin` · "Đang xử lý" | — | Xóa |
| `NOT_EXTRACTABLE` | `warn` · cảnh báo · "Không thể truy vấn" | "PDF chỉ chứa ảnh scan nên chưa thể dùng để trả lời." | Xóa |
| `FAILED` | `err` · cảnh báo · "Lỗi xử lý" | "Xử lý không thành công: {lý do}" | "Thử lại" (`btn-sm`, biểu tượng refresh; T-112) · Xóa |

Ánh xạ `failureReason` → lý do `[Proposed]`: `EMBEDDING_UNAVAILABLE` "dịch vụ tạm thời không phản hồi."; `EXTRACTION_TIMEOUT` "tệp mất quá nhiều thời gian để đọc."; `PDF_UNREADABLE` "tệp PDF bị hỏng hoặc được bảo vệ."; `TOO_MANY_PAGES` "vượt quá giới hạn {maxPages} trang." (ẩn "Thử lại"); khác → "lỗi không xác định.". Nút xóa: ghost 44px biểu tượng thùng rác, `aria-label="Xóa {tên}"`, `title="Xóa"`.

**Hộp thoại xóa** (`.backdrop` nền `rgba(0,0,0,.5)`, `.modal` max-width 460px, bo 14px)
- `role="dialog" aria-modal="true" aria-labelledby` → `h2` "Xóa tài liệu?"; `aria-describedby` → "Tài liệu **“{tên}”** sẽ bị xóa khỏi thư viện và không còn được dùng để trả lời. Các hội thoại cũ vẫn hiển thị tên tài liệu này trong phần trích dẫn."
- Nút: "Hủy" (mặc định) và "Xóa tài liệu" (`btn-danger`), căn phải.
- Mở: focus vào **"Hủy"**; giữ focus trong hộp thoại (Tab vòng); Esc hoặc bấm nền → đóng; đóng xong trả focus về nút xóa đã mở.
- Xác nhận: gọi `DELETE`; nút xác nhận vô hiệu khi đang gửi; `204` → đóng, bỏ dòng, cập nhật bộ đếm, toast "Đã xóa “{tên}”". Lỗi → giữ dòng, toast "Không xóa được tài liệu. Vui lòng thử lại." `[Proposed]`.

**Toast**: cố định giữa đáy (bottom 24px), nền `--ink`, chữ `--surface`, `role="status"`, tự ẩn sau 2,6 s.

**Luồng tải lên**
- Kiểm phía client trước khi gửi: phần mở rộng `.pdf` hoặc `type=application/pdf` → nếu sai, thêm dòng bị từ chối, **không** gửi. Kích thước > `maxUploadMb` → từ chối tại chỗ.
- Mỗi tệp hợp lệ gửi **một yêu cầu riêng** (`files[]` một phần tử, `Idempotency-Key = crypto.randomUUID()`), tối đa 3 yêu cầu song song `[Proposed]` — để có tiến trình từng tệp.
- `uploadFile` dùng `XMLHttpRequest` (`upload.onprogress`) vì `fetch` không báo tiến trình gửi; vẫn phải gửi `X-CSRF-Token` và xử lý 401 → `/login`, 403 → `/error/403` như client chung (T-005/T-006).
- Phản hồi `202` có mục `REJECTED` (server phát hiện sai magic/quá lớn) → chuyển dòng sang trạng thái bị từ chối với thông điệp theo `error.code`.

**Dữ liệu và thăm dò**
- `useQuery(['documents'], listDocuments, { refetchInterval: d => d?.counts.inProgress > 0 ? 3000 : false })`; dừng khi tab ẩn (mặc định TanStack).
- Sau upload/xóa: `invalidateQueries(['documents'])`.
- Đang tải lần đầu: khung xương bảng ≤ 300 ms (Blueprint §2.5). Lỗi tải danh sách: `banner err` "Không tải được thư viện." + "Thử lại" `[Proposed]`.

**Truy cập**: mọi nút có nhãn; focus `outline 3px var(--focus)`; badge có chữ (không chỉ màu); `prefers-reduced-motion` làm chậm `.spin`; dùng được bằng bàn phím (Enter/Space mở hộp chọn tệp).

## 5. Các bước thực hiện

1. Viết `api/documents.ts` (kiểu từ OpenAPI T-103/T-105/T-106) và `uploadFile` bằng XHR.
2. Viết `StatusBadge`, `Toast`, `ConfirmModal` (focus trap, Esc, trả focus) + test.
3. Viết `Dropzone` (kéo thả, chọn nhiều, kiểm client) + test.
4. Viết `UploadTray` (hàng đợi tối đa 3 song song, trạng thái từng tệp) + test.
5. Viết `DocumentTable` + ánh xạ trạng thái/`failureReason`.
6. Ghép `LibraryPage`, thăm dò có điều kiện, vai trò SPONSOR, chuyển sang `EmptyLibrary` khi rỗng.
7. Đưa toàn bộ chuỗi vào `vi.json`; so màn hình với `library.png` ở 1280px (sáng và tối).

## 6. Tiêu chí chấp nhận

- [ ] Chọn 3 PDF hợp lệ cùng lúc → khay hiện 3 thanh tiến trình; xong cả 3 → 3 dòng mới ở đầu bảng với "Đang xử lý" (AC-001).
- [ ] Chọn `.docx`, `.jpg`, `.xlsx` → 3 dòng khay "Bị từ chối: chỉ chấp nhận định dạng PDF", không có yêu cầu mạng nào, bảng không đổi (AC-002).
- [ ] Tệp `.pdf` sai nội dung bị server trả `UNSUPPORTED_FORMAT` → dòng khay chuyển sang "Bị từ chối…".
- [ ] Dòng `PROCESSING` tự chuyển "Sẵn sàng" mà không tải lại trang; khi không còn `UPLOADED/PROCESSING` thì không còn yêu cầu `GET /documents` định kỳ (kiểm bằng mock timer) (AC-003).
- [ ] `NOT_EXTRACTABLE` hiển thị badge vàng "Không thể truy vấn" + câu giải thích dưới tên, vẫn còn sau khi tải lại trang (AC-004).
- [ ] Dòng giới hạn hiển thị giá trị `limits` từ API; tệp vượt giới hạn bị từ chối với thông điệp nêu số MB (AC-005).
- [ ] Mỗi dòng có tên, người tải lên, ngày tải, trạng thái (AC-006).
- [ ] Xóa: hộp thoại nêu tên tài liệu, focus đầu ở "Hủy", Esc đóng và trả focus; xác nhận → dòng biến mất, bộ đếm cập nhật, toast "Đã xóa “…”" (AC-007 phần giao diện).
- [ ] Không có chuỗi hiển thị viết cứng trong component (kiểm bằng lint/rà soát); không dùng `dangerouslySetInnerHTML`.
- [ ] Với vai trò SPONSOR không hiện vùng tải lên và nút xóa.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit (Vitest) | `StatusBadge` 5 trạng thái | Đúng lớp, biểu tượng, chữ |
| Unit | `ConfirmModal`: mở, Tab, Shift+Tab, Esc | Focus "Hủy" → vòng trong hộp → đóng, focus về nút mở |
| Unit | `Dropzone` nhận 1 `.pdf` + 1 `.jpg` | 1 gửi, 1 từ chối tại chỗ |
| Unit | `refetchInterval` với `inProgress` 2 → 0 | 3000 → `false` |
| Unit | `failureReason=TOO_MANY_PAGES` | Không hiện nút "Thử lại" |
| Integration (MSW) | Upload 202 có 1 `REJECTED` | Khay hiện đúng từng tệp |
| Integration (MSW) | XHR lỗi mạng | Dòng "Tải lên không thành công" + "Thử lại" gửi lại đúng tệp |
| Integration (MSW) | `DELETE` 403 | Toast lỗi, dòng còn |
| E2E | Toàn bộ luồng | Trong T-111 |

## 8. Cấu hình

Không có biến môi trường mới phía FE. Giới hạn đọc từ `limits` của API (`MAX_UPLOAD_MB`, `MAX_PAGES` — **`[TBD: OQ-013]`**). Cờ `features.retryDocument` (mặc định `false` tới khi T-112 merge) `[Proposed]`.

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| OQ-013 giới hạn tệp | Dòng giới hạn, thông điệp | Hiển thị từ API, không viết cứng |
| OQ-011 quyền xóa | Có/không hiện nút xóa | Ẩn/hiện theo vai trò từ phiên; khi API trả 403 vẫn báo lỗi thân thiện |
| Nút "Thử lại" chưa có story (User_Stories §10) | Có thể bị bỏ | Ẩn sau cờ; T-112 chờ PO |
| Xóa dòng "Đang xử lý" lệch sơ đồ trạng thái (xem T-106) | Nút có thể phải ẩn | Theo quyết định ghi ở T-106 |
| Thăm dò khi danh sách nhiều trang | Chỉ trang đầu được làm mới | Dựa vào `counts.inProgress`, đủ cho ≤ 500 tài liệu |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §4.2, §5.2 (T-107), §6.2, §6.8
- [SAD](../../design/SAD.md) §2.1, §4.1.1, §4.1.4
- [Blueprint_Design](../../design/Blueprint_Design.md) §2.4, §2.5, §3.7
- [User_Stories](../../design/User_Stories.md) US-A1…A5, US-B1, US-B2
- Màn hình: [02_library.html](../../design/html_design/02_library.html); ảnh [library.png](../../design/images/library.png), [library_delete_modal.png](../../design/images/library_delete_modal.png)
- Task liên quan: [T-103](./T-103-upload-api.md), [T-105](./T-105-document-read-apis.md), [T-106](./T-106-delete-document-purge.md), [T-108](./T-108-empty-library-screen.md), [T-112](./T-112-retry-failed-document.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] QA so khớp với `library.png` và `library_delete_modal.png` (sáng + tối, 1280px và 375px không cuộn ngang trang).
