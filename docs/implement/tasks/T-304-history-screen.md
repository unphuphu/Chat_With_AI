# T-304 — Xây màn hình 07 Lịch sử hội thoại

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 3 |
| **Loại** | Frontend |
| **User story** | US-D2 |
| **Ưu tiên** | P2 |
| **Ước lượng** | 2 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-005, T-202 |
| **Mở khóa (task chờ task này)** | T-311 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Người dùng mở `/history`, thấy toàn bộ hội thoại **của chính mình** nhóm theo ngày, tìm nhanh theo tiêu đề hoặc câu hỏi đầu (không phân biệt dấu), và mở lại một hội thoại để xem đầy đủ câu hỏi/câu trả lời (AC-017). Việc mở lại ghi sự kiện `conversation_resumed`.

## 2. Bối cảnh

- BR-017 / **AC-017**: "Người dùng mở lại được hội thoại cũ và thấy đầy đủ câu hỏi, câu trả lời đã có; người dùng khác không xem được hội thoại này." ([User_Stories US-D2](../../design/User_Stories.md#us-d2)).
- API-08 `GET /api/v1/conversations` (`limit` mặc định 50, tối đa 200, `cursor`), lọc cứng `owner_id` — T-202. Route `/history` ([Implement_plan §6.8](../Implement_plan.md#68-ánh-xạ-màn-hình--route-frontend)).
- Thiết kế [07_history.html](../../design/html_design/07_history.html), ảnh [history.png](../../design/images/history.png), [history_noresult.png](../../design/images/history_noresult.png).
- **Ô tìm kiếm là thiết kế bổ sung, chưa có trong story** ([User_Stories §10](../../design/User_Stories.md)): cần **PO xác nhận** giữ lại; nếu cắt phạm vi, ẩn ô tìm kiếm bằng cờ cấu hình, phần còn lại không đổi.
- Sự kiện PRD §5.2: `conversation_resumed` — `conversation_id, user_id`.

## 3. Phạm vi

**Trong phạm vi**
- Trang `HistoryPage` theo §4.2; nhóm theo ngày; tìm kiếm phía client; trạng thái không có kết quả; trạng thái chưa có hội thoại; tải thêm trang.
- Các trường danh sách cần từ API-08 (§4.1) — nếu T-202 chưa trả, bổ sung ở backend trong task này.
- Ghi `conversation_resumed` khi mở hội thoại từ lịch sử.

**Ngoài phạm vi** (để tránh làm thừa)
- Xóa hội thoại (ghi chú thiết kế: "nút xóa hội thoại chưa đưa vào MVP"); thời gian lưu giữ `[TBD: OQ-019]` (T-407).
- Tìm kiếm toàn văn phía server trong nội dung tin nhắn.
- Thanh hội thoại bên trái màn 04 (T-209).

## 4. Thiết kế chi tiết

### 4.1 Dữ liệu từ API-08 (danh sách)

```json
GET /api/v1/conversations?limit=200
{ "items": [
    { "id": "…", "title": "Điều kiện thanh toán hợp đồng A",
      "firstQuestion": "Điều kiện thanh toán trong hợp đồng khung với đối tác A là gì?",
      "messageCount": 4, "startedAt": "2026-11-24T03:15:00Z", "lastMessageAt": "2026-11-24T03:42:00Z" } ],
  "nextCursor": null }
```

`firstQuestion`, `messageCount`, `lastMessageAt` là `[Proposed]` nếu T-202 chưa định nghĩa. Sắp xếp `lastMessageAt DESC` (fallback `startedAt`). `title` null → hiển thị `firstQuestion` cắt 60 ký tự; cả hai null → "Hội thoại chưa có câu hỏi" `[Proposed]`.

### 4.2 Bố cục (bám `07_history.html`)

| Vùng | Chi tiết |
|---|---|
| AppBar | Mục "Lịch sử" `aria-current="page"` (T-005) |
| Đầu trang (`.page-head`) | `<h1>` "**Lịch sử hội thoại**"; dưới là dòng riêng tư icon `lock` + "**Chỉ bạn nhìn thấy các hội thoại này.**" (chữ `--ink2`, 0,9 rem); bên phải nút `btn-primary` icon `plus` "**Hội thoại mới**" → `/chat` (tạo hội thoại mới như nút ở màn 04) |
| Thanh công cụ | Ô tìm kiếm (rộng tối thiểu 240 px, tối đa 460 px, icon `search` bên trái trong ô), `type="search"`, nhãn ẩn "Tìm trong lịch sử hội thoại", placeholder "**Tìm theo tiêu đề hoặc câu hỏi…**", `autocomplete="off"`; bên cạnh chữ muted đếm "**{n} hội thoại**" với `aria-live="polite"` |
| Nhóm | `<section aria-labelledby>`; tiêu đề `<h2>` chữ hoa nhỏ muted (0,8 rem, giãn chữ); danh sách là `ul.card.list` |
| Mục | Toàn dòng là liên kết tới `/chat/:id?from=history`; icon `chat`; **tiêu đề** đậm; dưới là **câu hỏi đầu** (`--ink2`, 0,9 rem, một dòng, cắt `…`, tối đa 62ch); bên phải `meta` muted 2 dòng: "**{messageCount} tin nhắn**" và thời gian; hover nền `--surface2`; viền trên giữa các mục |
| Không có kết quả | Thẻ căn giữa: icon `search` cỡ 44 px muted, `<h2>` "**Không có hội thoại phù hợp**", dòng "**Thử từ khóa khác hoặc xóa ô tìm kiếm.**"; ẩn mọi nhóm |
| Chưa có hội thoại | `[Proposed]` (thiết kế chưa có): thẻ căn giữa "Bạn chưa có hội thoại nào" + nút "Hội thoại mới" |
| Đang tải | Khung xương `.skel` 3 dòng trong ≤ 300 ms |
| Lỗi tải | Banner `err` "Không tải được lịch sử." + nút "Thử lại" `[Proposed]` |
| ≤ 640 px | Mục xuống dòng, `meta` dịch sang trái thẳng hàng nội dung (`margin-left: 32px`) |

### 4.3 Quy tắc nhóm và hiển thị thời gian `[Proposed]`

Theo múi giờ trình duyệt, dựa trên `lastMessageAt`:

| Nhóm | Điều kiện | Định dạng giờ trong `meta` |
|---|---|---|
| Hôm nay | cùng ngày lịch | `HH:mm` (vd. 10:42) |
| Hôm qua | ngày trước | `HH:mm` |
| Tuần này | từ thứ Hai tuần hiện tại, trừ 2 nhóm trên | `dd/MM` |
| Tuần trước | tuần lịch liền trước | `dd/MM` (vd. 14/10) |
| Tháng {M}/{YYYY} | cũ hơn | `dd/MM` |

Nhóm rỗng không hiển thị. Thiết kế chỉ minh họa 3 nhóm đầu + "Tuần trước"; nhóm "Tuần này" và "Tháng …" là phần mở rộng hợp lý, cần PO duyệt chữ.

### 4.4 Tìm kiếm (phía client)

```ts
// frontend/src/pages/History/search.ts
export function normalize(s: string): string {
  return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd');
}
export function matches(item: ConversationSummary, q: string): boolean; // tiêu đề + câu hỏi đầu
```

- Khớp chuỗi con sau chuẩn hóa: "thanh toan" khớp "Điều kiện thanh toán…"; "DIEU KIEN" khớp; "đ"/"d" như nhau.
- Lọc ngay khi gõ (debounce 150 ms `[Proposed]`); ẩn nhóm không còn mục; cập nhật số đếm.
- Phạm vi tìm: các hội thoại **đã tải**. Trang tải tối đa 200/lần; nếu còn `nextCursor`, tự tải tiếp tới hết trước khi lọc (người dùng ≤ vài trăm hội thoại trong MVP) `[Proposed]`.
- Không gửi từ khóa lên server, không log.

### 4.5 Sự kiện `conversation_resumed` `[Proposed]`

FE điều hướng tới `/chat/:id?from=history`; trang Chat gọi `GET /api/v1/conversations/{id}?resumed=true` **một lần** khi vào từ lịch sử. Backend (T-202 router) khi `resumed=true` và hội thoại thuộc người dùng → `analytics.emit("conversation_resumed", user_id, {"conversation_id": id})`. Hội thoại của người khác → 404 như T-202, không ghi sự kiện. Mở hội thoại từ thanh bên của màn 04 cũng truyền `resumed=true` nếu không phải hội thoại vừa tạo.

### 4.6 File

`frontend/src/pages/History/HistoryPage.tsx`, `HistoryGroup.tsx`, `HistoryItem.tsx`, `grouping.ts`, `search.ts`, test tương ứng; `frontend/src/api/conversations.ts` (dùng chung với T-209); backend: `app/conversations/router.py` (tham số `resumed`), `schemas.py` (trường danh sách nếu thiếu).

## 5. Các bước thực hiện

1. Thống nhất với người làm T-202 các trường §4.1; bổ sung nếu thiếu (truy vấn đếm `message` + câu hỏi đầu bằng một truy vấn, có test).
2. Viết `grouping.ts` và `search.ts` (thuần) + unit test.
3. Dựng `HistoryPage` với TanStack Query `['conversations']`, đọc hết trang.
4. Dựng các trạng thái: đang tải, lỗi, rỗng, không có kết quả.
5. Thêm `resumed=true` và sự kiện `conversation_resumed` ở backend + test.
6. Chuỗi vào `vi.json` (khóa `history.*`).
7. Đối chiếu với `history.png`, `history_noresult.png`; kiểm bàn phím (Tab qua ô tìm → từng mục).

## 6. Tiêu chí chấp nhận

- [ ] `/history` chỉ hiển thị hội thoại có `owner_id` = người dùng hiện tại (kiểm với 2 người dùng dev).
- [ ] Mỗi mục có tiêu đề, câu hỏi đầu, số tin nhắn, giờ; nhóm đúng theo bảng §4.3 với dữ liệu mẫu cố định đồng hồ.
- [ ] Gõ "thanh toan" (không dấu) tìm thấy hội thoại "Điều kiện thanh toán hợp đồng A"; số đếm cập nhật.
- [ ] Từ khóa không khớp → hiện "Không có hội thoại phù hợp", ẩn mọi nhóm; xóa ô → danh sách trở lại.
- [ ] Bấm một mục → mở `/chat/:id` hiển thị **đầy đủ** câu hỏi, câu trả lời và trích dẫn đã lưu (AC-017, kể cả trích dẫn tới tài liệu đã xóa dùng `document_name_snapshot`).
- [ ] Mở từ lịch sử ghi đúng 1 sự kiện `conversation_resumed`; người dùng B mở URL hội thoại của A → trang lỗi, không có sự kiện.
- [ ] Dòng "Chỉ bạn nhìn thấy các hội thoại này." luôn hiển thị.
- [ ] Không có chuỗi viết cứng (lint T-308 xanh).

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `normalize("Điều Kiện")` | `"dieu kien"` |
| Unit | `matches` với "ĐIỀU", "dieu", "thanh toán", "xyz" | true, true, true, false |
| Unit | `grouping` với đồng hồ cố định 2026-11-24 (thứ Hai) | Hôm nay / Hôm qua / Tuần trước / Tháng 10/2026 đúng |
| Unit | Mục có `title=null` | Hiển thị câu hỏi đầu cắt 60 ký tự |
| Component | Không có kết quả | Hiện thẻ "Không có hội thoại phù hợp", `aria-live` đọc "0 hội thoại" |
| Integration | `GET /conversations` 2 người dùng | Mỗi người chỉ thấy của mình; có `firstQuestion`, `messageCount` |
| Integration | `GET /conversations/{id}?resumed=true` | 1 bản ghi `conversation_resumed` |
| E2E | AC-017 | Xem T-311 |

## 8. Cấu hình

| Biến | Giá trị | Ghi chú |
|---|---|---|
| `VITE_FEATURE_HISTORY_SEARCH` | `true` `[Proposed]` | Tắt nếu PO quyết định bỏ tìm kiếm |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Tìm kiếm là thiết kế bổ sung, chưa có story | Có thể bị cắt | Làm sau cùng trong task, sau cờ cấu hình; PO xác nhận |
| Tìm phía client chỉ trên dữ liệu đã tải | Chậm nếu rất nhiều hội thoại | Chấp nhận ở MVP (~50 người dùng); chuyển sang tham số `q` phía server nếu cần |
| Tên nhóm ngoài thiết kế ("Tuần này", "Tháng …") | Chữ giao diện | PO duyệt chữ |
| Thời gian lưu giữ hội thoại `[TBD: OQ-019]` | Hội thoại cũ có thể biến mất | T-407 |
| Cách ghi `conversation_resumed` (tham số `resumed`) là đề xuất | Số liệu "dùng lại lịch sử" | Tech Lead xác nhận |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §5.4, §6.8, §10.2
- [SAD](../../design/SAD.md) §2.4 (API-08), §3.1 (cách ly theo `owner_id`, RLS)
- [User_Stories](../../design/User_Stories.md) US-D2, §10
- Màn hình: [html_design/07_history.html](../../design/html_design/07_history.html), ảnh [history.png](../../design/images/history.png), [history_noresult.png](../../design/images/history_noresult.png)
- Task liên quan: [T-202](./T-202-conversation-apis.md), [T-209](./T-209-chat-screen-core.md), [T-308](./T-308-i18n.md), [T-311](./T-311-e2e-sprint3.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] PO đã ghi quyết định giữ/bỏ ô tìm kiếm vào PR.
