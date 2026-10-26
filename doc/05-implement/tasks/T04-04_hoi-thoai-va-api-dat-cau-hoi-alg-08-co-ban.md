# T04-04 – Hội thoại và API đặt câu hỏi (ALG-08 cơ bản)

| Trường | Giá trị |
|---|---|
| Lát | VS-4 – Hỏi đáp có trích dẫn (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T04-03](T04-03_sinh-cau-tra-loi-va-kiem-tra-trich-dan-alg-06.md), [T01-04](T01-04_middleware-csrf-va-thu-tu-middleware.md) |
| Story | US-012, US-014 |
| Tài liệu tham chiếu | BLUEPRINT ALG-08; openapi.yaml `/conversations/current`, `POST /conversations/{id}/messages`, `Answer`; schema.sql `conversation`, `message`, `citation` |

## Mục tiêu

Người dùng đặt câu hỏi, nhận `Answer`; hội thoại giữ khi tải lại trang.

## Phạm vi file

- `backend/app/modules/qa/{service.py,repository.py}`
- `backend/app/api/v1/conversations.py`
- `backend/tests/integration/test_ask.py`

## Các bước gợi ý

1. `GET /conversations/current` tạo nếu chưa có cho phiên.
2. `POST …/messages`: kiểm tra hội thoại thuộc phiên; 409 `no_ready_documents`; INSERT … ON CONFLICT; commit trước khi gọi LLM (DD-06); lưu answer + citations (bản chụp tên tài liệu).
3. Gửi lại cùng `client_request_id` sau ANSWERED/INSUFFICIENT → trả kết quả cũ, không gọi LLM.
4. Audit `question_asked`.

## Tiêu chí hoàn thành

- [ ] Test (LLM giả): câu trả lời có citations khớp tài liệu/trang
- [ ] Test: không có tài liệu Sẵn sàng → 409
- [ ] Test: gửi lại cùng id → LLM giả chỉ được gọi 1 lần
- [ ] Test: hội thoại của phiên khác → 404
- [ ] Test: tải lại `/conversations/current` trả đủ tin nhắn
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k ask
```

## Kết quả triển khai

**Done** – Hội thoại theo phiên, idempotency, commit trước khi gọi LLM.
