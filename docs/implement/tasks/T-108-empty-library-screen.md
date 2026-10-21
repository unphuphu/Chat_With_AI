# T-108 — Xây dựng màn hình 03 Thư viện trống và khóa mục "Hỏi đáp" khi chưa có tài liệu `READY`

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 1 |
| **Loại** | Frontend |
| **User story** | US-A5 |
| **Ưu tiên** | P1 |
| **Ước lượng** | 1 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-107 |
| **Mở khóa (task chờ task này)** | T-111 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Khi thư viện chưa có tài liệu nào, `/library` hiển thị trạng thái rỗng hướng dẫn bước tiếp theo (tải PDF lên, giới hạn tệp, 3 bước sử dụng) giống [03_library_empty.html](../../design/html_design/03_library_empty.html). Mục "Hỏi đáp" trên AppBar và nút "Hỏi đáp với tài liệu" bị vô hiệu hóa (có lý do) khi không có tài liệu nào ở trạng thái `READY`.

## 2. Bối cảnh

- PRD §4.2 "Thư viện rỗng": hướng dẫn tải tài liệu trước, chặn đặt câu hỏi khi chưa có tài liệu sẵn sàng. Blueprint §2.5: mọi màn rỗng chỉ rõ bước tiếp theo.
- US-A5: dòng "Chỉ chấp nhận định dạng PDF · Tối đa `{{MAX_MB}}` MB và `{{MAX_PAGES}}` trang mỗi tệp" ở cả màn 02 và 03 (`[TBD: OQ-013]`). Ảnh: [library_empty.png](../../design/images/library_empty.png).
- Màn 03 là trạng thái rỗng của route `/library` ([plan §6.8](../Implement_plan.md#68-ánh-xạ-màn-hình--route-frontend)); API phía hỏi đáp vẫn trả `409 NO_READY_DOCUMENTS` (xử lý ở T-307).

## 3. Phạm vi

**Trong phạm vi**
- Component `EmptyLibrary` render trong `LibraryPage` khi `counts.total = 0` **và** khay tải lên rỗng.
- Nút "Tải tệp PDF lên" mở hộp chọn tệp (cùng `Dropzone`/luồng upload của T-107); vùng hero nhận kéo thả.
- Hook `useHasReadyDocuments()` dựa trên `counts.ready` của `['documents']`; AppBar (T-005) và CTA dùng hook này để vô hiệu "Hỏi đáp".

**Ngoài phạm vi**
- Trạng thái "chưa có tài liệu sẵn sàng" bên trong màn Hỏi đáp (màn 05, T-307).
- Chặn route `/chat` bằng điều hướng cưỡng bức — vẫn vào được bằng URL, màn 04/05 tự xử lý `409`.

## 4. Thiết kế chi tiết

**File**

| File | Nội dung |
|---|---|
| `frontend/src/pages/Library/EmptyLibrary.tsx` | Trạng thái rỗng |
| `frontend/src/pages/Library/LibraryPage.tsx` | Chọn `EmptyLibrary` / bảng |
| `frontend/src/api/useHasReadyDocuments.ts` | Hook |
| `frontend/src/app/AppBar.tsx` | Vô hiệu mục "Hỏi đáp" |
| `frontend/src/i18n/vi.json` | Khóa `library.empty.*`, `nav.chatDisabledReason` |

**Bố cục (khớp HTML)**
1. `page-head`: `h1` "Thư viện tài liệu"; `p` "Thư viện hiện chưa có tài liệu nào."; bên phải `btn-primary` biểu tượng chat "Hỏi đáp với tài liệu" ở trạng thái `aria-disabled="true"`, độ mờ 0,5, `title="Cần ít nhất một tài liệu ở trạng thái Sẵn sàng"` (render là `span`/`button` không điều hướng).
2. `.hero` (max-width 720px, căn giữa, margin-top 24px) chứa `.dropzone` padding 44px/24px:
   - Biểu tượng thư mục 44px màu primary.
   - `h2` "Bắt đầu bằng việc tải tài liệu lên".
   - `p` "Tải các tệp PDF của dự án. Sau khi tài liệu ở trạng thái “Sẵn sàng”, bạn có thể đặt câu hỏi bằng ngôn ngữ tự nhiên."
   - `btn-primary` biểu tượng upload "Tải tệp PDF lên" → mở `input type=file accept="application/pdf,.pdf" multiple` (trong HTML mẫu là liên kết tới 02; ở app thật mở hộp chọn tệp).
   - `.limits` "Chỉ chấp nhận định dạng PDF · Tối đa {maxUploadMb} MB và {maxPages} trang mỗi tệp" (từ `limits` API, T-105).
3. `ol.how` `aria-label="Các bước sử dụng"`: lưới 3 cột (1 cột khi < 700px), mỗi `li` là thẻ viền `--line`, bo `--r`, vòng tròn số 28px nền `primary-soft` (`aria-hidden`):
   1. **Tải PDF lên** — "Chọn một hoặc nhiều tệp cùng lúc."
   2. **Chờ “Sẵn sàng”** — "Hệ thống đọc và lập chỉ mục tài liệu."
   3. **Đặt câu hỏi** — "Nhận câu trả lời kèm tên tài liệu và số trang."

**AppBar khi `hasReady = false`** (chỉ với vai trò MEMBER — vai trò SPONSOR không có mục Hỏi đáp, plan §6.8)
- Thẻ "Hỏi đáp" có lớp `disabled` (độ mờ 0,5, `pointer-events:none`), `aria-disabled="true"`, `tabindex="-1"`, `title` nêu lý do.
- Mục "Thư viện" `aria-current="page"`; "Lịch sử" vẫn hoạt động.

**Quy tắc chuyển trạng thái**
- `counts.total = 0` và khay rỗng → `EmptyLibrary`.
- Người dùng thả/chọn tệp trong `EmptyLibrary` → chuyển ngay sang bố cục màn 02 để thấy khay "Đang tải lên" (khay không rỗng).
- Có tài liệu nhưng `counts.ready = 0` (ví dụ đều đang xử lý) → hiển thị màn 02 nhưng CTA + mục "Hỏi đáp" vẫn vô hiệu; khi có tài liệu đầu tiên `READY` (nhờ thăm dò 3 s của T-107) → tự bật, không tải lại trang.
- Đang tải `['documents']` lần đầu → không hiện `EmptyLibrary` (tránh nháy), hiện khung xương.

## 5. Các bước thực hiện

1. Viết `useHasReadyDocuments()` (đọc cache `['documents']`; khi trang khác chưa có cache thì gọi `listDocuments({limit:1})`).
2. Cập nhật `AppBar` dùng hook; thêm test vai trò MEMBER/SPONSOR.
3. Viết `EmptyLibrary`, dùng lại logic chọn tệp/kéo thả của `Dropzone` (T-107) qua prop `variant="hero"`.
4. Cập nhật `LibraryPage` theo quy tắc chuyển trạng thái.
5. Đưa chuỗi vào `vi.json`; so khớp `library_empty.png` (sáng/tối, 1280px và 375px).

## 6. Tiêu chí chấp nhận

- [ ] API trả `counts.total=0` → hiển thị đúng tiêu đề, mô tả, hero, dòng giới hạn và 3 bước như `library_empty.png`; không hiện bảng.
- [ ] Nút "Tải tệp PDF lên" mở hộp chọn tệp; chọn 1 PDF → hiện khay "Đang tải lên"; xong → bảng có 1 dòng "Đang xử lý".
- [ ] Khi không có tài liệu `READY`: mục "Hỏi đáp" trên AppBar có `aria-disabled="true"`, `tabindex="-1"`, không bấm được; CTA "Hỏi đáp với tài liệu" vô hiệu và có `title` nêu lý do.
- [ ] Khi tài liệu đầu tiên chuyển `READY`, cả hai được bật trong ≤ 3 s (một chu kỳ thăm dò) mà không tải lại trang.
- [ ] Dòng giới hạn hiển thị số từ `limits` (đổi `MAX_UPLOAD_MB=10` ở backend → hiển thị "10 MB") (AC-005 phần "biết trước giới hạn").
- [ ] Danh sách bước là `ol` có `aria-label`; số thứ tự `aria-hidden`; lưới về 1 cột khi < 700px.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit (Vitest) | `counts.total=0`, khay rỗng | Render `EmptyLibrary` |
| Unit | `counts.total=0`, khay có 1 tệp đang tải | Render bố cục 02 |
| Unit | Đang tải lần đầu | Khung xương, không `EmptyLibrary` |
| Unit | AppBar MEMBER, `ready=0` / `ready=1` | "Hỏi đáp" vô hiệu / hoạt động |
| Unit | AppBar SPONSOR | Không có mục "Hỏi đáp" |
| Integration (MSW) | `ready` 0 → 1 qua thăm dò | CTA bật không tải lại |
| E2E | Thư viện trống sau khi xóa tài liệu cuối cùng | Trong T-111 |

## 8. Cấu hình

Không có biến mới. Hiển thị `MAX_UPLOAD_MB`, `MAX_PAGES` qua `limits` của API — **`[TBD: OQ-013]`**, `[Default]` 50 MB / 500 trang.

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| OQ-013 chưa chốt | Giá trị hiển thị | Đọc từ API; HTML mẫu tô nét đứt là giữ chỗ |
| Ghi chú màn 03 nói khóa "khi chưa có tài liệu", plan T-108 nói "khi không có tài liệu `READY`" | Hai điều kiện khác nhau khi có tài liệu đang xử lý | Dùng điều kiện `READY` (khớp PRD §4.2 và `NO_READY_DOCUMENTS`) |
| AppBar ở trang khác (Lịch sử) cần biết `hasReady` | Thêm một lời gọi API | `listDocuments({limit:1})` có `counts`; cache 30 s `[Proposed]` |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §4.2, §5.2 (T-108), §6.8
- [SAD](../../design/SAD.md) §2.1
- [Blueprint_Design](../../design/Blueprint_Design.md) §2.4, §2.5, §3.5 (`NO_READY_DOCUMENTS`)
- [User_Stories](../../design/User_Stories.md) US-A5
- Màn hình: [03_library_empty.html](../../design/html_design/03_library_empty.html); ảnh [library_empty.png](../../design/images/library_empty.png)
- Task liên quan: [T-005](./T-005-frontend-skeleton.md), [T-107](./T-107-library-screen.md), [T-307](./T-307-chat-states.md), [T-111](./T-111-e2e-sprint1.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] QA so khớp `library_empty.png` (sáng + tối).
