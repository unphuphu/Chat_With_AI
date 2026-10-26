# T04-05 – SPA: khung chat, câu trả lời và nhãn nguồn

| Trường | Giá trị |
|---|---|
| Lát | VS-4 – Hỏi đáp có trích dẫn (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T04-04](T04-04_hoi-thoai-va-api-dat-cau-hoi-alg-08-co-ban.md), [T03-06](T03-06_sse-phat-trang-thai-tai-lieu-toi-giao-dien.md) |
| Story | US-012, US-014, US-020, US-025 |
| Tài liệu tham chiếu | html_design S04; API_DESIGN CA-02 (phần cơ bản), CA-04, 3.7.2; BLUEPRINT DE-02 |

## Mục tiêu

Ô hỏi, danh sách tin nhắn, câu trả lời có [n] bấm được và nhãn 'tên file · tr.X'.

## Phạm vi file

- `frontend/src/features/chat/{Composer,MessageList,MessageItem,CitationChip,AnswerText}.tsx`
- `frontend/src/features/chat/useAsk.ts`
- `frontend/e2e/ask.spec.ts`

## Các bước gợi ý

1. Composer: khóa khi không có tài liệu Sẵn sàng (lý do bằng chữ), bộ đếm 2.000, Enter gửi, Shift+Enter xuống dòng, giữ nháp.
2. AnswerText tách `[n]` bằng regex, không bao giờ dựng HTML từ câu trả lời.
3. Trạng thái 'Đang soạn câu trả lời' ≤ 300 ms; tự cuộn xuống tin mới; vùng `aria-live`.

## Tiêu chí hoàn thành

- [ ] Unit test AnswerText: `[1]` có citation → nút; `[9]` không có → văn bản; chuỗi `<script>` hiển thị nguyên văn
- [ ] E2E (LLM giả): hỏi → câu trả lời + 2 nhãn nguồn; tải lại trang → hội thoại còn
- [ ] axe-core không có lỗi serious
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
pnpm -C frontend test && make e2e -- ask.spec.ts
```

## Kết quả triển khai

**Done** – Khung chat, nút [n], chip nguồn tên + trang.
