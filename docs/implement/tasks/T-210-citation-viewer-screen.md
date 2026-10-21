# T-210 — Dựng màn hình 06 Xem trích dẫn bằng pdf.js

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 2 |
| **Loại** | Frontend |
| **User story** | US-C3 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 3 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-105, T-209 |
| **Mở khóa (task chờ task này)** | T-213 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Từ số hiệu hoặc chip trích dẫn ở màn 04, người dùng mở đúng tài liệu PDF tại đúng trang, thấy đoạn được trích dẫn được tô nền vàng kèm nhãn chữ "Đoạn được trích dẫn [n]", chuyển nhanh giữa các trích dẫn của cùng câu trả lời, chuyển trang và thu phóng. Nếu không định vị được đoạn văn, vẫn mở đúng trang. Giao diện khớp [06_citation_viewer.html](../../design/html_design/06_citation_viewer.html).

## 2. Bối cảnh

- US-C3 / BR-010 / AC-010: mở được trong 1 thao tác, ≥ 95% trích dẫn trỏ đúng trang (đối chiếu thủ công).
- Route: `/documents/:id/view?page=12&cite=1&message=:messageId` (Implement_plan §6.8); API-06 `GET /api/v1/documents/{id}/file` hỗ trợ `Range` (T-105, SAD §2.1); danh sách trích dẫn lấy từ API-08 (T-202, gồm `quote`).
- Tô đoạn: tìm vị trí văn bản chunk trên lớp text của pdf.js; không tìm được → chỉ nhảy trang + hiện đoạn trích ở danh sách bên trái (Implement_plan §5.3 T-210, §9.2).
- Ảnh đối chiếu: [viewer_p12.png](../../design/images/viewer_p12.png), [viewer_p14.png](../../design/images/viewer_p14.png), [viewer_beta_p5.png](../../design/images/viewer_beta_p5.png).

## 3. Phạm vi

**Trong phạm vi**
- Trang `CitationViewer` với pdf.js (`pdfjs-dist`), một trang mỗi lần (canvas + text layer).
- Danh sách trích dẫn bên trái, nút "Quay lại hội thoại", thanh công cụ (tên tài liệu, chuyển trang, thu phóng).
- Thuật toán tô đoạn + phương án dự phòng; trạng thái tài liệu đã xóa/lỗi tải.

**Ngoài phạm vi** (để tránh làm thừa)
- Thanh tìm kiếm trong PDF, in, tải xuống (không có trong thiết kế; xuất file ngoài MVP — BRD §5.2).
- Chế độ cuộn liên tục nhiều trang, ảnh thu nhỏ.
- Thay đổi API (dùng API-06, API-08 như đã có).

## 4. Thiết kế chi tiết

**File:**

```text
frontend/src/pages/CitationViewer/CitationViewerPage.tsx
frontend/src/pages/CitationViewer/CitationList.tsx
frontend/src/pages/CitationViewer/PdfPageView.tsx      # canvas + text layer + highlight
frontend/src/pages/CitationViewer/highlight.ts         # findQuoteRange(), thuần hàm
frontend/src/pages/CitationViewer/usePdfDocument.ts
frontend/src/i18n/vi.json                              # khóa viewer.*
```

**Bố cục** (theo CSS 06_citation_viewer.html):

| Vùng | Đặc tả |
|---|---|
| Lưới `.viewer` | `grid-template-columns: 300px 1fr`, cao `calc(100vh - 60px)`, tối thiểu 560 px. ≤ 860 px: 1 cột, danh sách thành hàng cuộn ngang (mỗi mục ≥ 220 px), ẩn tiêu đề danh sách |
| Cột trái `.vside` | Nút nhỏ "Quay lại hội thoại" (icon back) → `/chat/:conversationId`; tiêu đề chữ hoa nhỏ "Trích dẫn trong câu trả lời"; mỗi mục là `<button>` viền bo 10 px: "**n** Tên tài liệu" + dòng phụ "Trang p"; mục hiện tại `aria-current="true"`, viền `--primary`, nền `--primary-soft`. Khi tô đoạn thất bại, mục hiện tại hiện thêm đoạn trích (`quote`, tối đa ~300 ký tự) |
| Thanh `.vbar` | Tên tài liệu (đậm, cắt "…"); nhóm "Chuyển trang" (`role="group"`): nút "Trang trước"/"Trang sau" (icon, `aria-label`) + `<output aria-live="polite">` "Trang 12 / 48"; nhóm "Thu phóng": "Thu nhỏ"/"Phóng to" + `<output>` "100%" |
| Vùng trang `.canvas` | Nền `--surface2`, căn giữa, cuộn; trang PDF có bóng `--shadow` |
| Tô đoạn | Lớp phủ nền `#ffe58a` trên các span của text layer thuộc đoạn trích + nhãn đen chữ trắng "Đoạn được trích dẫn [n]" đặt ngay trên dòng đầu đoạn (không chỉ dựa vào màu) |

Phần `.vnote` "Bản minh họa…" trong HTML là ghi chú thiết kế, **không** đưa vào sản phẩm.

**Nguồn dữ liệu:**

1. `id` (path), `page`, `cite`, `message` (query); `conversationId` từ `location.state` do T-209 truyền.
2. Danh sách trích dẫn: tìm tin nhắn `message` trong cache `['conversation', conversationId]`; nếu thiếu thì `getConversation(conversationId)`. Không có `conversationId` (mở từ tab mới) → tìm trong mọi cache `['conversation', *]`; vẫn không có → **chế độ đơn**: danh sách chỉ có 1 mục dựng từ query (`cite`, `page`), nút "Quay lại hội thoại" → `/chat`, không có `quote` → chỉ nhảy trang `[Proposed]`.
3. PDF: `pdfjsLib.getDocument({ url: '/api/v1/documents/{id}/file', withCredentials: true, disableAutoFetch: true, rangeChunkSize: 65536 })` — dùng `Range`, không tải cả tệp trước. Worker pdf.js nạp từ bundle cùng nguồn gốc (CSP `default-src 'self'`).

**Điều hướng:**

- `page` ngoài `[1, numPages]` hoặc không phải số → trang 1, hiện ghi chú nhỏ "Không tìm thấy trang p, đang hiện trang 1" `[Proposed]`.
- Trước/sau: vô hiệu ở trang đầu/cuối; đổi trang cập nhật `?page=` bằng `navigate(..., { replace: true })`. Tô đoạn chỉ hiện khi đang ở đúng trang của trích dẫn hiện tại.
- Bấm mục trong danh sách: cùng tài liệu → nhảy trang; khác tài liệu → đổi `:id` (tải PDF mới), cập nhật `cite`, `page`.
- Thu phóng: 60%–160%, bước 15%, mặc định 100% (theo thiết kế); render lại canvas + text layer theo `scale`.
- Phím: `←`/`→` hoặc `PageUp`/`PageDown` đổi trang khi focus trong vùng trang `[Proposed]`.

**Thuật toán tô đoạn** (`highlight.ts`, thuần hàm, test được):

```ts
export function findQuoteRange(items: { str: string }[], quote: string):
  { startItem: number; startOffset: number; endItem: number; endOffset: number } | null;
```

1. Ghép `items[].str` thành một chuỗi, lưu bảng ánh xạ vị trí ký tự → (item, offset).
2. Chuẩn hóa cả hai chuỗi giống nhau: Unicode NFC, gộp mọi khoảng trắng thành một dấu cách, bỏ khoảng trắng ở dấu gạch nối cuối dòng, so sánh không phân biệt hoa thường (vẫn giữ dấu tiếng Việt).
3. Tìm `quote` nguyên vẹn; không thấy → tìm 120 ký tự đầu, rồi 60 ký tự đầu; đoạn khớp phải ≥ 40 ký tự `[Proposed]`.
4. Có kết quả → bao các span tương ứng của text layer bằng lớp tô; cuộn để đoạn nằm trong khung nhìn.
5. Không có kết quả hoặc không có `quote` (chunk đã purge) → chỉ nhảy trang, hiện banner thông tin "Không xác định được vị trí đoạn trích trên trang này. Xem đoạn trích ở danh sách bên trái." và hiện `quote` trong mục danh sách (nếu có).

**Trạng thái lỗi:**

| Tình huống | Hiển thị |
|---|---|
| API-06 trả 404 (tài liệu đã xóa) | Khối thông báo "Tài liệu này đã bị xóa khỏi thư viện" kèm tên snapshot + "Trang p"; danh sách vẫn dùng được; nút quay lại |
| 401 / 403 | Client chung chuyển `/login` hoặc `/error/403` (T-005/T-006) |
| Lỗi mạng / PDF hỏng | Banner lỗi + nút "Thử lại" (tải lại tài liệu) |
| Đang tải | Skeleton kích thước trang A4 tỉ lệ 595×842 |

## 5. Các bước thực hiện

1. Thêm `pdfjs-dist` (giấy phép Apache-2.0, phiên bản `[Verify]`); cấu hình worker qua Vite.
2. Viết `highlight.ts` + test đơn vị (mục 7) trước.
3. Viết `usePdfDocument(id)` (tải, hủy khi đổi tài liệu, xử lý lỗi theo mã HTTP).
4. Viết `PdfPageView` (canvas + `TextLayer`, render lại khi đổi `page`/`scale`, lớp tô + nhãn).
5. Viết `CitationList`, `CitationViewerPage`; gắn route `/documents/:id/view`.
6. Chép CSS `.viewer/.vside/.citem/.vbar/.pgn/.canvas` từ thiết kế; nhãn tô dùng kiểu `.paper .tag`.
7. Kiểm với 3 PDF mẫu (T-009) gồm 1 PDF tiếng Việt có bảng; so ảnh `viewer_p12.png`, `viewer_p14.png`, `viewer_beta_p5.png`.

## 6. Tiêu chí chấp nhận

- [ ] Từ chip trích dẫn ở màn 04, màn 06 mở đúng tài liệu và hiển thị "Trang p / N" đúng `page` của trích dẫn.
- [ ] Đoạn trích tìm được trên text layer được tô nền vàng **và** có nhãn chữ "Đoạn được trích dẫn [n]".
- [ ] Không tìm được đoạn trích (hoặc `quote = null`) → vẫn ở đúng trang, có banner giải thích, không lỗi JS.
- [ ] Danh sách bên trái liệt kê đủ trích dẫn của tin nhắn `message`, đúng thứ tự `ordinal`, mục hiện tại có `aria-current="true"`; bấm mục khác tài liệu tải đúng tài liệu và trang.
- [ ] Nút trang trước/sau bị vô hiệu ở trang 1 và trang cuối; thu phóng giới hạn 60%–160%.
- [ ] Mở PDF 48 trang tới trang 12 không tải toàn bộ tệp trước khi hiện trang (thấy yêu cầu `Range`/`206` trong tab Network).
- [ ] Tài liệu đã xóa → thông báo "đã bị xóa", không lộ nội dung.
- [ ] Mọi nút có nhãn truy cập; chuỗi lấy từ `vi.json`.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `findQuoteRange`: quote nằm gọn 1 item | Đúng item/offset |
| Unit | Quote trải nhiều item, khoảng trắng/xuống dòng khác nhau | Tìm thấy |
| Unit | Quote dạng NFD, trang dạng NFC ("thanh toán") | Tìm thấy |
| Unit | Chỉ khớp 60 ký tự đầu | Trả phạm vi của phần khớp |
| Unit | Không khớp / quote rỗng | `null` |
| Component | `page=999` trên PDF 12 trang | Hiện trang 1 + ghi chú |
| Component | API-06 trả 404 | Khối "đã bị xóa" |
| Component | Không có `location.state`, cache trống | Chế độ đơn, 1 mục |
| E2E (T-213) | Bấm chip [1] → viewer đúng trang, có nhãn tô | Pass |
| Visual (QA) | So với `viewer_p12.png`, `viewer_p14.png`, `viewer_beta_p5.png` | Khớp bố cục |

## 8. Cấu hình

Không có biến môi trường mới. CSP phải cho phép worker pdf.js cùng nguồn gốc (`worker-src 'self'`) — xác nhận với T-405.

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Văn bản chunk (pypdfium2) khác text layer của pdf.js (khoảng trắng, thứ tự cột, ký tự ghép) | Tô đoạn thất bại | So khớp chuẩn hóa + tiền tố; dự phòng chỉ nhảy trang (Implement_plan §9.2); đo tỷ lệ tô thành công trên PDF mẫu |
| Route chuẩn không có `conversationId` | Mở ở tab mới không lấy được danh sách trích dẫn | Dùng `location.state` + cache; chế độ đơn `[Proposed]`. Đề xuất bổ sung tham số hoặc API tra theo `messageId` nếu PO cần |
| Thiết kế liệt kê trích dẫn [1][2][3] từ cả hội thoại, ghi chú nói "của cùng câu trả lời" | Mâu thuẫn trong thiết kế | Theo ghi chú: chỉ trích dẫn của tin nhắn `message` |
| `quote` là trường `[Proposed]` của API-08 (T-202) | Thiếu nếu T-202 không làm | Dự phòng chỉ nhảy trang |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §4.2, §5.3 (T-210), §6.8, §9.2
- [SAD](../../design/SAD.md) §2.1 (pdf.js, CSP), §2.4 (API-06, API-08)
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.5
- [User_Stories](../../design/User_Stories.md) US-C3
- Màn hình: [html_design/06_citation_viewer.html](../../design/html_design/06_citation_viewer.html); ảnh [viewer_p12.png](../../design/images/viewer_p12.png), [viewer_p14.png](../../design/images/viewer_p14.png), [viewer_beta_p5.png](../../design/images/viewer_beta_p5.png)
- Task liên quan: [T-105](./T-105-document-read-apis.md), [T-202](./T-202-conversation-apis.md), [T-209](./T-209-chat-screen-core.md), [T-213](./T-213-e2e-sprint2.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Ghi vào PR tỷ lệ tô đoạn thành công trên các PDF mẫu (T-009) để theo dõi rủi ro §9.2.
