# T-209 — Dựng màn hình 04 Hỏi đáp (phần lõi)

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 2 |
| **Loại** | Frontend |
| **User story** | US-D1, US-C1, US-C2, US-C3, US-C4 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 4 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-005, T-202, T-207 |
| **Mở khóa (task chờ task này)** | T-210, T-213, T-302, T-303, T-307 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Người dùng mở `/chat`, bắt đầu hội thoại mới, gửi câu hỏi, thấy tiến trình ("Tìm đoạn liên quan" → "Soạn câu trả lời"), rồi nhận câu trả lời có số hiệu trích dẫn trong văn bản + chip nguồn mở được màn 06 bằng 1 thao tác; hoặc thấy khối "Không tìm thấy thông tin" khác hẳn câu trả lời thường. Giao diện khớp [04_chat.html](../../design/html_design/04_chat.html) và panel A của [05_chat_states.html](../../design/html_design/05_chat_states.html).

## 2. Bối cảnh

- Route `/chat`, `/chat/:conversationId` (Implement_plan §6.8); API-07/08 (T-202), API-09 SSE (T-207).
- SSE qua `fetch` + `ReadableStream`, **không** `EventSource` (SAD §2.1, Implement_plan §6.7). Chỉ `final` tạo tin nhắn trợ lý; mất kết nối → bỏ mọi trạng thái tạm (Blueprint §3.7).
- Nội dung AI là đầu vào không tin cậy: render Markdown đã làm sạch, cấm `dangerouslySetInnerHTML` (Implement_plan §4.2).
- Ảnh đối chiếu: [chat.png](../../design/images/chat.png), [chat_notfound.png](../../design/images/chat_notfound.png), [chat_loading.png](../../design/images/chat_loading.png).

## 3. Phạm vi

**Trong phạm vi**
- Bố cục 2 cột: thanh hội thoại bên trái + khung hội thoại; nút "Hội thoại mới"; luồng tin nhắn; ô nhập; số hiệu + chip trích dẫn; khối NOT_FOUND; khối đang xử lý với 2 bước.
- Bộ phân tích SSE + client `askQuestion()`; máy trạng thái lượt hỏi (Idle/Sending/Streaming/Answered/NotFound/Error).
- Xử lý lỗi tối thiểu: hiện thông báo lỗi chung, trả câu hỏi về ô nhập.

**Ngoài phạm vi** (để tránh làm thừa)
- Nút/bộ chọn "Phạm vi" (T-302) — ở Sprint 2 không hiện nút phạm vi.
- Nút "Hữu ích/Không hữu ích" (T-303).
- Các trạng thái màn 05 B–F đầy đủ: "Gửi lại", mất mạng, `409` khóa ô nhập, `429`, dòng "Có thể mất tới N giây" (T-307).
- Màn 07 Lịch sử, tìm kiếm (T-304). Đổi ngôn ngữ (T-308).

## 4. Thiết kế chi tiết

**File:**

```text
frontend/src/pages/Chat/ChatPage.tsx              # route /chat và /chat/:conversationId
frontend/src/pages/Chat/ConversationSidebar.tsx
frontend/src/pages/Chat/MessageList.tsx
frontend/src/pages/Chat/AssistantAnswer.tsx       # body + CitationChips
frontend/src/pages/Chat/NotFoundBlock.tsx
frontend/src/pages/Chat/PendingAnswer.tsx         # các bước + skeleton
frontend/src/pages/Chat/Composer.tsx
frontend/src/pages/Chat/useAsk.ts                 # máy trạng thái lượt hỏi
frontend/src/components/CitationChip.tsx, CitationRef.tsx, SafeMarkdown.tsx
frontend/src/api/sse.ts                           # readSse()
frontend/src/api/conversations.ts                 # createConversation, listConversations, getConversation, askQuestion
frontend/src/i18n/vi.json                         # khóa chat.*
```

**Bố cục** (giá trị từ CSS của 04_chat.html, biến màu lấy từ `styles/tokens.css`):

| Vùng | Đặc tả |
|---|---|
| Lưới `.chat` | `grid-template-columns: 280px 1fr`; cao `calc(100vh - 60px)`, tối thiểu 560 px. ≤ 860 px: 1 cột, ẩn thanh bên |
| Thanh bên `.side` | Nền `--surface`, viền phải `--line`. Trên: nút chính "Hội thoại mới" (icon plus, rộng 100%). Danh sách nhóm theo ngày với tiêu đề nhóm chữ hoa nhỏ ("Hôm nay", "Hôm qua", "Trước đó" `[Proposed]`). Mỗi mục: tiêu đề + dòng phụ "`{messageCount}` tin nhắn · `HH:mm`" (từ `lastMessageAt`); mục đang mở `aria-current="true"`, nền `--primary-soft`. Chân: liên kết "Xem tất cả lịch sử →" tới `/history` |
| Đầu khung `.chat-head` | `h1` = tiêu đề hội thoại (hoặc "Hội thoại mới" khi chưa có), viền dưới |
| Luồng `.stream` | Cuộn dọc, nội dung giữa tối đa 820 px, khoảng cách 22 px; `aria-live="polite"`; tự cuộn xuống cuối khi có tin mới |
| Tin người dùng | Bong bóng phải, nền `--primary`, chữ `--on-primary`, bo `16px 16px 4px 16px`, rộng tối đa 78% |
| Câu trả lời | Avatar AI 32 px trái; thân viền `--line`, bo `4px 16px 16px 16px`; số hiệu `.cref` nền `--primary-soft`, chữ đậm 0,75 rem, `aria-label="Trích dẫn n"`; dưới thân là hàng chip `.cite`: "**n** Tên tài liệu.pdf · trang p" + icon mở ngoài |
| Khối NOT_FOUND | Viền **nét đứt 2 px** `--warn`, nền `--warn-bg`, `role="status"`; tiêu đề có icon tìm kiếm "Không tìm thấy thông tin trong tài liệu"; 2 đoạn văn (theo panel A); 2 nút nhỏ "Chọn tài liệu", "Tải tài liệu lên" (→ `/library`). Không có chip |
| Đang xử lý | Thân câu trả lời với "Đang tìm trong tài liệu…" đậm; danh sách 2 bước: "Tìm đoạn liên quan", "Soạn câu trả lời" — bước xong màu `--ok` + icon check, bước hiện tại đậm + spinner; 2 thanh skeleton (85%, 65%); `role="status"`; tôn trọng `prefers-reduced-motion` |
| Ô nhập `.composer` | Dòng chip "Đang hỏi trên: toàn bộ thư viện (N tài liệu)" (N = số tài liệu `READY` từ `['documents']`); hộp bo 14 px với `textarea` (nhãn ẩn "Câu hỏi của bạn", placeholder "Đặt câu hỏi về các tài liệu của bạn…", `maxLength=2000`, tự giãn tới 160 px) + nút chính "Gửi"; dưới: "Enter để gửi · Shift+Enter xuống dòng" và bộ đếm "0 / 2000"; dòng cảnh báo "AI có thể sai. Hãy mở trích dẫn để kiểm tra trước khi sử dụng thông tin." |

**Hành vi:**

- `/chat` (không id): luồng trống + ô nhập. Gửi câu đầu → `POST /conversations` → `navigate('/chat/:id', {replace: true})` → gửi câu hỏi `[Proposed]` (không tạo hội thoại rỗng khi chỉ bấm nút). "Hội thoại mới" → về `/chat`, xóa trạng thái lượt hỏi (AC-016).
- `/chat/:id`: `useQuery(['conversation', id], getConversation)`; 404 → trang lỗi `/error/404`.
- Gửi: chặn khi câu hỏi rỗng sau `trim` hoặc đang có lượt chưa xong; Enter gửi, Shift+Enter xuống dòng; thêm bong bóng người dùng ngay, xóa ô nhập, hiện khối đang xử lý trong ≤ 300 ms (ở trạng thái Sending bước 1 là "hiện tại").
- Sự kiện `status`: `retrieving` → bước 1 hiện tại; `generating` → bước 1 xong, bước 2 hiện tại. Sự kiện khác `status/final/error` (ví dụ `token`) bị bỏ qua.
- `final`: thay khối đang xử lý bằng câu trả lời hoặc khối NOT_FOUND; cập nhật cache `['conversation', id]`; `invalidateQueries(['conversations'])`; trả focus về ô nhập.
- `error`/lỗi HTTP/luồng đóng không có `final`: bỏ khối đang xử lý (không hiện nội dung dở dang), hiện banner lỗi chung `role="alert"` "Chưa nhận được câu trả lời", đưa câu hỏi trở lại ô nhập. Chi tiết theo mã lỗi là T-307.
- Rời trang trong app khi đang chờ: **không** hủy yêu cầu (câu trả lời vẫn được lưu phía server và hiện khi quay lại — màn 05 panel B); chỉ hủy khi tải lại/đóng tab.

**Trích dẫn trong văn bản:** `SafeMarkdown` dùng `react-markdown` (không bật HTML thô, không render liên kết/ảnh) `[Proposed]` + plugin thay mẫu `[n]` bằng `<CitationRef>` **chỉ khi** `n` có trong `citations`. Đích liên kết (số hiệu và chip như nhau):
`/documents/{documentId}/view?page={page}&cite={ordinal}&message={messageId}`, truyền `state: { conversationId }` cho T-210.

**SSE client:**

```ts
export type SseEvent = { event: string; data: string };
export async function* readSse(body: ReadableStream<Uint8Array>): AsyncGenerator<SseEvent>;
// TextDecoder({stream:true}); tách khung theo dòng trống (\n\n hoặc \r\n\r\n);
// dòng "event:" / "data:" (nhiều dòng data nối bằng \n); bỏ dòng bắt đầu bằng ":".

export async function askQuestion(conversationId: string, body: { question: string; documentIds?: string[] },
  opts: { onStatus: (stage: 'retrieving' | 'generating') => void; signal?: AbortSignal }): Promise<FinalPayload>;
// !res.ok → ném ApiError(code, status, requestId) từ JSON; event:error → ném StreamError(code);
// kết thúc luồng không có final → ném StreamInterrupted. Gửi X-CSRF-Token qua client chung.
```

**Khóa i18n** (trong `vi.json`, không viết cứng): `chat.newConversation`, `chat.history.today`, `chat.history.yesterday`, `chat.history.older`, `chat.history.viewAll`, `chat.messageCount`, `chat.composer.placeholder`, `chat.composer.hint`, `chat.composer.send`, `chat.composer.scopeAll`, `chat.disclaimer`, `chat.pending.title`, `chat.pending.retrieving`, `chat.pending.generating`, `chat.notFound.title`, `chat.notFound.body`, `chat.notFound.hint`, `chat.notFound.chooseDocs`, `chat.notFound.upload`, `chat.citation.page`, `chat.citation.aria`, `chat.error.generic`.

## 5. Các bước thực hiện

1. Viết `readSse()` + test đơn vị trước (mục 7).
2. Viết `api/conversations.ts` dùng client fetch chung (T-005/T-006).
3. Viết `useAsk` (reducer theo Blueprint §3.7: Idle → Sending → Streaming → Answered/NotFound/Error).
4. Dựng component theo bảng bố cục; chép CSS lớp `.chat/.side/.conv/.stream/.msg/.bubble/.ans/.cref/.cites/.cite/.nf/.composer/.cbox/.chint/.skel/.steps` từ 04_chat.html vào CSS module của trang.
5. Viết `SafeMarkdown` + plugin số hiệu trích dẫn.
6. Gắn route `/chat`, `/chat/:conversationId` trong `app/router`; mục "Hỏi đáp" của AppBar có `aria-current="page"`.
7. Test component (Vitest + Testing Library, mock API bằng MSW `[Proposed]`); so ảnh với `chat.png`, `chat_notfound.png`, `chat_loading.png`.

## 6. Tiêu chí chấp nhận

- [ ] Gửi câu hỏi → khối đang xử lý xuất hiện ≤ 300 ms; bước chuyển đúng theo `status`; câu trả lời chỉ xuất hiện khi nhận `final`.
- [ ] Câu trả lời `ANSWERED` hiển thị số hiệu trong văn bản khớp chip bên dưới; bấm số hiệu hoặc chip mở `/documents/{id}/view?page=…&cite=…&message=…` (1 thao tác).
- [ ] `NOT_FOUND` hiển thị khối viền nét đứt, nền cảnh báo, tiêu đề "Không tìm thấy thông tin trong tài liệu", không có chip; khác biệt nhìn thấy được và đọc được bằng trình đọc màn hình (`role="status"`).
- [ ] Nội dung chứa `<script>`/`<img onerror>` hiển thị như văn bản, không thực thi; không có `dangerouslySetInnerHTML` trong mã (kiểm bằng lint rule).
- [ ] "Hội thoại mới" → URL `/chat`, luồng trống; câu hỏi tiếp theo tạo hội thoại mới (id khác) — AC-016 phía giao diện.
- [ ] Enter gửi, Shift+Enter xuống dòng; bộ đếm cập nhật; nút "Gửi" vô hiệu khi ô trống hoặc đang chờ; tối đa 2000 ký tự.
- [ ] Luồng đóng không có `final` hoặc có `error` → không còn khối đang xử lý, không hiện nội dung dở dang, câu hỏi được trả về ô nhập.
- [ ] Mọi chuỗi hiển thị lấy từ `vi.json`; mọi nút có nhãn; focus nhìn thấy được.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `readSse`: một khung bị cắt giữa 2 chunk byte, ký tự tiếng Việt bị cắt giữa byte UTF-8 | Phân tích đúng 1 sự kiện, chữ không lỗi |
| Unit | `readSse`: `\r\n`, nhiều dòng `data`, dòng chú thích `:` | Đúng sự kiện; bỏ chú thích |
| Unit | `askQuestion`: sự kiện `token` lạ | Bỏ qua, vẫn trả `final` |
| Unit | `askQuestion`: HTTP 409 JSON | `ApiError` code `NO_READY_DOCUMENTS` |
| Unit | `askQuestion`: luồng kết thúc không `final` | `StreamInterrupted` |
| Component | `AssistantAnswer` với `[1]`, `[2]`, `[9]` (không có ordinal 9) | 2 liên kết trích dẫn, `[9]` là chữ thường |
| Component | `NotFoundBlock` | Có `role="status"`, không có `.cite` |
| Component | Composer: Enter/Shift+Enter/đếm ký tự/nút vô hiệu | Đúng hành vi |
| Component | `useAsk` khi `error` | Trạng thái Error, câu hỏi khôi phục |
| Visual (QA) | So với `chat.png`, `chat_notfound.png`, `chat_loading.png` | Khớp bố cục, màu, chữ |

## 8. Cấu hình

Không có biến môi trường frontend mới. Giới hạn 2000 ký tự theo API-09 (SAD §2.4). Thời gian chờ tối đa hiển thị `[TBD: OQ-014]` — thuộc T-307.

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Thiết kế đánh số trích dẫn liên tục trong hội thoại; backend đánh số theo tin nhắn `[Proposed]` (T-205) | Số hiệu khác ảnh `chat.png` ở lượt 2 | Hiển thị đúng `ordinal` từ API; PO xác nhận |
| Thanh bên bị ẩn ở ≤ 860 px, không có nút "Hội thoại mới" thay thế trong thiết kế | Người dùng di động khó tạo hội thoại mới | Giữ theo thiết kế; ghi nhận cho UX |
| Tin nhắn người dùng đã được server lưu khi lượt hỏi lỗi | Tải lại thấy câu hỏi không có trả lời | Chấp nhận; T-307 xử lý "Gửi lại" |
| Nút "Chọn tài liệu" ở khối NOT_FOUND cần bộ chọn phạm vi (T-302) | Chưa có đích | Sprint 2: đưa focus về ô nhập; T-302 nối vào bộ chọn |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §4.2, §6.7, §6.8
- [SAD](../../design/SAD.md) §2.1, §2.4 (API-07…09), §5 AD-07
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.5, §3.7 (vòng đời lượt hỏi)
- [User_Stories](../../design/User_Stories.md) US-C1…C4, US-D1, §9
- Màn hình: [html_design/04_chat.html](../../design/html_design/04_chat.html), [html_design/05_chat_states.html](../../design/html_design/05_chat_states.html) (panel A, B); ảnh [chat.png](../../design/images/chat.png), [chat_notfound.png](../../design/images/chat_notfound.png), [chat_loading.png](../../design/images/chat_loading.png)
- Task liên quan: [T-202](./T-202-conversation-apis.md), [T-207](./T-207-messages-sse-api.md), [T-210](./T-210-citation-viewer-screen.md), [T-302](./T-302-document-scope.md), [T-303](./T-303-answer-feedback.md), [T-307](./T-307-chat-states.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] QA ký so sánh ảnh với `chat.png` và `chat_notfound.png`.
