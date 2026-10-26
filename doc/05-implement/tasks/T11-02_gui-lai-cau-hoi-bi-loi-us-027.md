# T11-02 – Gửi lại câu hỏi bị lỗi (US-027)

| Trường | Giá trị |
|---|---|
| Lát | VS-11 – Tính năng P1 (Lát 3) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T09-03](T09-03_spa-the-loi-cau-tra-loi-canh-bao-het-phien.md), [T04-04](T04-04_hoi-thoai-va-api-dat-cau-hoi-alg-08-co-ban.md) |
| Story | US-027 |
| Tài liệu tham chiếu | USER_STORIES US-027 AC; BLUEPRINT ALG-08 (FAILED → PENDING), 3.7.2; API_DESIGN 3.4.2 (409 → thăm dò) |

## Mục tiêu

Bấm 'Gửi lại' chạy lại đúng câu hỏi với cùng `client_request_id`.

## Phạm vi file

- `backend/app/modules/qa/service.py` (nhánh FAILED/PENDING quá hạn, `idempotency_mismatch`)
- `frontend/src/features/chat/useAsk.ts` (retry, polling khi 409)
- `backend/tests/integration/test_resend.py`

## Các bước gợi ý

1. Đúng ALG-08; analytics `question_retried`.
2. SPA: 409 `request_in_progress` → thăm dò `/conversations/current` mỗi 2 s tối đa 20 s.

## Tiêu chí hoàn thành

- [ ] Test: FAILED → gửi lại → ANSWERED, `attempt=2`
- [ ] Test: cùng id khác nội dung → 422 `idempotency_mismatch`
- [ ] E2E: LLM giả lỗi lần 1, thành công lần 2 → thẻ lỗi thành câu trả lời
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k resend
```

## Kết quả triển khai

**Done** – Gửi lại cùng `client_request_id`, attempt + `question_retried`.
