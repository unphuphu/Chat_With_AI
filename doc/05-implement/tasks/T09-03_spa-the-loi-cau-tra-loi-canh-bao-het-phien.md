# T09-03 – SPA: thẻ lỗi câu trả lời, cảnh báo hết phiên

| Trường | Giá trị |
|---|---|
| Lát | VS-9 – Lỗi, giới hạn và phiên (Lát 2) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T09-01](T09-01_circuit-breaker-llm-va-anh-xa-503-504-alg-07.md), [T03-06](T03-06_sse-phat-trang-thai-tai-lieu-toi-giao-dien.md), [T01-05](T01-05_spa-phien-header-nguoi-dung-trang-loi-dang-nhap.md) |
| Story | US-025, US-026 |
| Tài liệu tham chiếu | html_design S05, S11; API_DESIGN 3.4.2, 3.4.3, 3.6.3; USER_STORIES US-026 AC |

## Mục tiêu

Lỗi câu hỏi hiện đúng chỗ, sự kiện `session.expiring` hiện cảnh báo.

## Phạm vi file

- `frontend/src/features/chat/FailedAnswer.tsx`
- `backend/app/modules/events/session_expiry.py` (phát `session.expiring` trước 5 phút)
- `frontend/e2e/errors.spec.ts`

## Các bước gợi ý

1. Thẻ lỗi: nhãn 'Chưa trả lời được', thông điệp theo mã, câu hỏi gốc vẫn hiện (nút 'Gửi lại' hoạt động ở T11-02).
2. Timeout phía client 20 s → coi như lỗi mạng.
3. Toast cảnh báo phiên không chặn thao tác.

## Tiêu chí hoàn thành

- [ ] E2E: LLM giả 503 → thẻ lỗi đúng S05
- [ ] E2E: cắt mạng khi hỏi → thẻ lỗi, không treo spinner
- [ ] Test: phiên còn 5 phút → client nhận `session.expiring` đúng 1 lần
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make e2e -- errors.spec.ts
```
