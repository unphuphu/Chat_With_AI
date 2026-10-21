# T-307 — Hiện thực các trạng thái đặc biệt của màn Hỏi đáp (màn 05)

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 3 |
| **Loại** | Frontend |
| **User story** | US-C4, US-C5 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 3 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-209, T-305, T-306 |
| **Mở khóa (task chờ task này)** | T-311 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Màn 04 (`/chat/:conversationId`) xử lý đủ các trạng thái của màn 05: đang xử lý theo sự kiện `status`, lỗi dịch vụ AI có "Gửi lại" giữ câu hỏi, mất mạng (giữ nội dung đang nhập), chưa có tài liệu sẵn sàng (`409`, khóa ô nhập) và hỏi quá nhanh (`429`). **Không bao giờ** hiển thị câu trả lời dở dang.

## 2. Bối cảnh

- Máy trạng thái lượt hỏi [Blueprint §3.7](../../design/Blueprint_Design.md): `Idle → Blocked | Sending → Streaming → Answered | NotFound | Error`; `Error → Sending` khi gửi lại (câu hỏi được giữ). Câu trả lời chưa qua kiểm tra trích dẫn không hiển thị như kết quả cuối.
- SSE API-09: `status` (`retrieving`, `generating`), `final`, `error`; lỗi trước khi mở luồng (401/403/404/409/422/429) trả HTTP thường ([Implement_plan §6.7](../Implement_plan.md#67-giao-thức-sse-của-api-09)). Chỉ `final` tạo tin nhắn trợ lý; mất kết nối → bỏ mọi trạng thái tạm.
- PRD §4.2, [User_Stories §9](../../design/User_Stories.md); chỉ báo tiến trình ≤ 300 ms (Blueprint §2.4).
- Thiết kế [05_chat_states.html](../../design/html_design/05_chat_states.html) — khung A…F; ảnh `chat_loading.png`, `chat_error.png`, `chat_offline.png`, `chat_blocked.png`, `chat_ratelimit.png`, `chat_notfound.png`.

## 3. Phạm vi

**Trong phạm vi**
- Khung B (đang xử lý), C (lỗi AI), D (mất mạng), E (chưa có tài liệu sẵn sàng), F (giới hạn tốc độ) trên màn 04.
- Kiểm lại khung A (không tìm thấy, đã làm ở T-209): nút "Chọn tài liệu" mở bộ chọn phạm vi (nếu T-302 đã merge), "Tải tài liệu lên" → `/library`.
- Store lượt hỏi (`askMachine`) theo máy trạng thái §4.1.

**Ngoài phạm vi** (để tránh làm thừa)
- Phát luồng `token` (không bật ở MVP, AD-07).
- Logic backend 409/429/503/504 (T-207, T-305, T-306).
- Lỗi 401/403 toàn cục (client API chung của T-005/T-006 đã xử lý).

## 4. Thiết kế chi tiết

### 4.1 Máy trạng thái phía client

```ts
// frontend/src/pages/Chat/askMachine.ts
type AskState =
  | { kind: 'idle' }
  | { kind: 'blocked'; processingCount: number }                       // E
  | { kind: 'sending'; question: string; scope: Scope; stage: 'pending' | 'retrieving' | 'generating' } // B
  | { kind: 'error'; question: string; scope: Scope; code: string }     // C
  | { kind: 'rateLimited'; question: string; retryAt: number };         // F
// Trạng thái mạng tách riêng: online: boolean (D) — chồng lên mọi trạng thái trên.
```

| Sự kiện | Từ → Đến | Ghi chú |
|---|---|---|
| Bấm Gửi / Enter | `idle` → `sending(stage='pending')` | Hiện ngay bong bóng câu hỏi + khung B (≤ 300 ms, không chờ mạng) |
| `status: retrieving` | `sending` → `stage='retrieving'` | |
| `status: generating` | → `stage='generating'` | |
| `final` | `sending` → `idle` | Thêm tin nhắn trợ lý (ANSWERED hoặc khung A); làm mới `['conversation', id]` |
| `event: error` / HTTP 503, 504, 5xx / luồng đóng khi chưa có `final` / `fetch` ném lỗi mạng | `sending` → `error` | Xóa khung B; **không** giữ nội dung tạm |
| HTTP 409 `NO_READY_DOCUMENTS` | → `blocked` | Đặt lại câu hỏi vào ô nhập |
| HTTP 429 `RATE_LIMITED` | → `rateLimited` | `retryAt = now + Retry-After` (mặc định 5 s nếu thiếu `[Proposed]`) |
| HTTP 422 `INVALID_SCOPE` | → `idle` | Xử lý ở T-302 |
| Bấm "Gửi lại" | `error` → `sending` | Gửi lại **cùng câu hỏi + cùng phạm vi** |
| Hết `retryAt` | `rateLimited` → `idle` | |
| Danh sách tài liệu có ≥ 1 `READY` | `blocked` → `idle` | |

Request đang chạy được giữ trong store cấp ứng dụng (không gắn với vòng đời component) để người dùng chuyển sang Thư viện rồi quay lại vẫn thấy kết quả, như câu chữ của khung B `[Proposed]`. Tải lại trang/đóng tab → mất (server không lưu tin nhắn trợ lý khi client ngắt).

### 4.2 Giao diện từng khung (bám `05_chat_states.html`)

**B · Đang xử lý** — tin nhắn trợ lý tạm: avatar AI + khối `.body` có `role="status"`:
- Dòng đậm "**Đang tìm trong tài liệu…**".
- Danh sách bước `.steps`: "**Tìm đoạn liên quan**", "**Soạn câu trả lời**". Bước xong: icon `check`, màu `--ok`; bước đang chạy: spinner `.spin` (14 px), chữ `--ink` đậm; bước chưa tới: chữ `--ink2`.

| `stage` | Tìm đoạn liên quan | Soạn câu trả lời |
|---|---|---|
| `pending`, `retrieving` | đang chạy | chưa tới |
| `generating` | xong | đang chạy |

- Hai thanh xương `.skel` (rộng 85% và 65%, cao 12 px, hiệu ứng ánh sáng; tắt khi `prefers-reduced-motion`).
- Dòng muted 0,82 rem: "**Có thể mất tới {{N}} giây. Bạn có thể tiếp tục xem thư viện, câu trả lời sẽ ở lại đây.**" — `N` từ cấu hình `VITE_ANSWER_WAIT_HINT_S` `[Proposed]`, giá trị thật `[TBD: OQ-014]`.
- Nút Gửi bị vô hiệu trong khi `sending`; ô nhập vẫn gõ được.

**C · Lỗi dịch vụ AI / quá thời gian** — giữ bong bóng câu hỏi; ngay dưới là banner `.banner.err` `role="alert"`: icon `alert`, tiêu đề đậm "**Chưa nhận được câu trả lời**", thân "**Dịch vụ AI không phản hồi kịp. Câu hỏi của bạn vẫn được giữ, bạn có thể gửi lại.**", nút `btn-sm` icon `refresh` "**Gửi lại**". Dùng chung cho `UPSTREAM_TIMEOUT`, `UPSTREAM_UNAVAILABLE`, mất kết nối giữa chừng. Focus chuyển tới nút "Gửi lại".

**D · Mất kết nối mạng** — banner `.banner.warn` `role="alert"` phía trên ô nhập: icon `wifi-off`, "**Mất kết nối mạng**", "**Đang thử kết nối lại. Không có câu trả lời dở dang nào được hiển thị; nội dung bạn đang nhập được giữ nguyên.**". Ô nhập `.cbox.disabled` (`aria-disabled="true"`, độ mờ 0,6), textarea `disabled` nhưng **giữ nguyên văn bản**; nút Gửi `disabled`.
- Phát hiện: sự kiện `offline` của `window` hoặc `fetch` ném `TypeError`. Thử lại: sự kiện `online` + gọi `GET /api/v1/auth/session` mỗi 5 s `[Proposed]`; thành công → ẩn banner, mở lại ô nhập.
- Nếu đang `sending` khi mất mạng → chuyển `error` (khung C) để người dùng "Gửi lại" khi có mạng.

**E · Chưa có tài liệu sẵn sàng** — banner `.banner.info` (không `alert`): icon `info`, "**Chưa có tài liệu nào sẵn sàng để hỏi**", "**Hãy tải tài liệu PDF lên và chờ trạng thái “Sẵn sàng”.**" + câu "**{n} tài liệu đang được xử lý.**" chỉ khi n > 0; nút `btn-primary btn-sm` "**Mở thư viện**" → `/library`. Ô nhập khóa, placeholder "**Cần ít nhất một tài liệu sẵn sàng để đặt câu hỏi**".
- Vào trạng thái này khi: khi mở màn hình `GET /api/v1/documents` không có tài liệu `READY` (dùng chung truy vấn với T-108/T-302), **hoặc** API-09 trả 409.
- Thăm dò `GET /documents` mỗi 3 s **chỉ khi** còn `UPLOADED/PROCESSING` (cùng quy tắc T-107); có `READY` → tự mở khóa.

**F · Hỏi quá nhanh** — banner `.banner.warn` `role="status"`: icon `clock`, "**Bạn đang hỏi hơi nhanh**", "**Vui lòng đợi vài giây rồi gửi lại câu hỏi.**". Câu hỏi được đặt lại vào ô nhập; nút Gửi vô hiệu tới `retryAt`, sau đó banner tự ẩn.

**A · Không tìm thấy** (kiểm lại T-209) — khung `.nf` nét đứt 2 px màu `--warn`, nền `--warn-bg`, `role="status"`; tiêu đề icon `search` "**Không tìm thấy thông tin trong tài liệu**"; 2 đoạn giải thích; nút "**Chọn tài liệu**" (icon `layers`) và "**Tải tài liệu lên**" (icon `upload`); không có trích dẫn, không có nút đánh giá.

### 4.3 Quy tắc bắt buộc

- Chỉ `final` tạo tin nhắn trợ lý. Bỏ qua mọi sự kiện `token` nếu có.
- Không lưu câu trả lời tạm vào `localStorage`/`sessionStorage`.
- Không hiện mã lỗi kỹ thuật trên banner; `requestId` chỉ ghi vào `console.debug` `[Proposed]`.
- Mọi chuỗi qua `t()` (khóa `chat.states.*`, T-308).

### 4.4 File

`frontend/src/pages/Chat/askMachine.ts` (+ test), `AskProgress.tsx` (B), `AskErrorBanner.tsx` (C), `OfflineBanner.tsx` (D), `NoReadyDocumentsBanner.tsx` (E), `RateLimitBanner.tsx` (F), `useOnlineStatus.ts`, sửa `Composer.tsx`, `ChatPage.tsx`, `api/sse.ts` (phân biệt "luồng đóng khi chưa có final").

## 5. Các bước thực hiện

1. Viết `askMachine` thuần (reducer) + unit test toàn bộ bảng §4.1.
2. Sửa `api/sse.ts` để báo `stream_incomplete` khi luồng kết thúc không có `final`, và trả mã HTTP/`Retry-After` cho lỗi trước luồng.
3. Dựng 5 component banner/tiến trình theo §4.2 dùng `tokens.css`.
4. `useOnlineStatus` + ping phiên khi mất mạng.
5. Nối truy vấn tài liệu `READY` để vào/ra `blocked`.
6. Giữ request trong store cấp ứng dụng; kiểm chuyển trang rồi quay lại.
7. Đối chiếu từng khung với ảnh trong `docs/design/images/`; kiểm `aria-live`/`role` bằng trình đọc màn hình.

## 6. Tiêu chí chấp nhận

- [ ] Sau khi bấm Gửi, khung B xuất hiện trong ≤ 300 ms (đo bằng Playwright với API trễ giả).
- [ ] `status: generating` → bước 1 có dấu tích, bước 2 có spinner.
- [ ] `event: error` `UPSTREAM_TIMEOUT` → khung C, câu hỏi vẫn hiển thị; "Gửi lại" gửi đúng câu hỏi và phạm vi cũ; thành công → câu trả lời hiển thị, banner biến mất.
- [ ] Ngắt mạng giữa lúc chờ → không có bất kỳ đoạn câu trả lời nào hiển thị; chuyển sang C; banner D hiện; văn bản đang gõ trong ô nhập còn nguyên; có mạng lại → banner D ẩn trong ≤ 5 s.
- [ ] Thư viện không có tài liệu `READY` → banner E, ô nhập khóa với placeholder đúng chữ; tài liệu chuyển `READY` → tự mở khóa không cần tải lại trang.
- [ ] API-09 trả 409 → vào E, câu hỏi được trả lại ô nhập.
- [ ] API-09 trả 429 `Retry-After: 3` → banner F, nút Gửi vô hiệu ~3 s rồi mở lại; câu hỏi còn trong ô nhập.
- [ ] Không có chuỗi viết cứng; banner có `role` đúng như §4.2.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | Reducer: mọi hàng bảng §4.1 | Trạng thái đích đúng |
| Unit | Luồng đóng sau `status: generating`, không có `final` | `error`, không có tin nhắn trợ lý |
| Unit | Sự kiện `token` nhận được | Bị bỏ qua |
| Component | `AskProgress` với 3 giá trị `stage` | Đúng biểu tượng mỗi bước |
| Component | `RateLimitBanner` với đồng hồ giả | Tự ẩn tại `retryAt` |
| E2E (mock API) | 409, 429, 504, mất mạng (`context.setOffline(true)`) | Đúng khung C/D/E/F; ảnh chụp khớp thiết kế |
| E2E (FakeLlm kịch bản `timeout`) | Luồng thật qua backend | Khung C, "Gửi lại" thành công khi tắt kịch bản |

## 8. Cấu hình

| Biến | Mặc định | Ghi chú |
|---|---|---|
| `VITE_ANSWER_WAIT_HINT_S` | `60` `[Proposed]` | Số `N` trong khung B; giá trị thật `[TBD: OQ-014]` |
| Chu kỳ ping khi mất mạng | 5 s `[Proposed]` | Hằng số trong `useOnlineStatus` |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Server lưu tin nhắn người dùng trước khi gọi AI (SAD §3.2.1 bước 4) → "Gửi lại" tạo thêm một tin nhắn câu hỏi trùng không có trả lời | Lịch sử hội thoại có câu hỏi lặp; lịch sử đưa vào `rewrite` | Chấp nhận ở MVP; báo Tech Lead quyết định (bỏ qua câu hỏi chưa có trả lời khi hiển thị/viết lại) |
| Ngưỡng thời gian chờ `[TBD: OQ-014]` | Chữ khung B | Lấy từ cấu hình |
| Giữ request khi chuyển trang là cam kết của câu chữ thiết kế | Độ phức tạp store | Làm theo §4.1; nếu PO bỏ, sửa chữ khung B |
| Phát hiện mất mạng bằng `navigator.onLine` không chính xác trên mọi trình duyệt (OQ-020) | Banner D trễ | Kết hợp lỗi `fetch` + ping |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §5.4, §6.7, §6.8
- [SAD](../../design/SAD.md) §2.1, §3.2.1 (hành vi lỗi), §4.2 (suy giảm có kiểm soát)
- [Blueprint_Design](../../design/Blueprint_Design.md) §2.4, §2.5, §3.5, §3.7
- [User_Stories](../../design/User_Stories.md) US-C4, US-C5, §9
- Màn hình: [html_design/05_chat_states.html](../../design/html_design/05_chat_states.html); ảnh [chat_loading.png](../../design/images/chat_loading.png), [chat_error.png](../../design/images/chat_error.png), [chat_offline.png](../../design/images/chat_offline.png), [chat_blocked.png](../../design/images/chat_blocked.png), [chat_ratelimit.png](../../design/images/chat_ratelimit.png), [chat_notfound.png](../../design/images/chat_notfound.png)
- Task liên quan: [T-209](./T-209-chat-screen-core.md), [T-302](./T-302-document-scope.md), [T-305](./T-305-upstream-resilience.md), [T-306](./T-306-rate-limiting.md), [T-311](./T-311-e2e-sprint3.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] QA đã so 6 khung với 6 ảnh `chat_*.png` và đính ảnh chụp vào PR.
