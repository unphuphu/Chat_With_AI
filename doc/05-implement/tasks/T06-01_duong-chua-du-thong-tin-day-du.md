# T06-01 – Đường 'Chưa đủ thông tin' đầy đủ

| Trường | Giá trị |
|---|---|
| Lát | VS-6 – Chất lượng câu trả lời (Lát 2) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T04-04](T04-04_hoi-thoai-va-api-dat-cau-hoi-alg-08-co-ban.md), [T04-05](T04-05_spa-khung-chat-cau-tra-loi-va-nhan-nguon.md) |
| Story | US-016 |
| Tài liệu tham chiếu | USER_STORIES US-016 AC; BLUEPRINT ALG-05 (cổng), ALG-06; html_design S04 (thẻ Chưa đủ thông tin); PRD E-11, E-16 |

## Mục tiêu

Ba lớp phát hiện thiếu căn cứ hoạt động và hiển thị đúng thiết kế.

## Phạm vi file

- `backend/tests/integration/test_insufficient.py`
- `frontend/src/features/chat/InsufficientAnswer.tsx`

## Các bước gợi ý

1. Test 3 đường: dưới ngưỡng (LLM không được gọi), LLM trả `insufficient`, LLM trả answered nhưng không có trích dẫn hợp lệ.
2. Giao diện: nhãn 'Chưa đủ thông tin', viền nét đứt, không có phần nguồn, gợi ý hành động.

## Tiêu chí hoàn thành

- [ ] 3 test backend xanh; đường dưới ngưỡng xác nhận 0 lần gọi LLM
- [ ] Unit test component + axe
- [ ] Câu chào hỏi ('xin chào') → INSUFFICIENT (E-16) với LLM giả kịch bản tương ứng
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k insufficient && pnpm -C frontend test
```

## Kết quả triển khai

**Done** – INSUFFICIENT từ cổng ngưỡng và từ LLM; thẻ 'Chưa đủ thông tin' ở SPA.
