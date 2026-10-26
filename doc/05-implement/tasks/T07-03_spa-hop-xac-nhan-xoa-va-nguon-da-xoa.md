# T07-03 – SPA: hộp xác nhận xóa và nguồn đã xóa

| Trường | Giá trị |
|---|---|
| Lát | VS-7 – Xóa tài liệu (Lát 2) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T07-01](T07-01_api-xoa-tai-lieu-alg-12.md), [T04-05](T04-05_spa-khung-chat-cau-tra-loi-va-nhan-nguon.md) |
| Story | US-010, US-011 |
| Tài liệu tham chiếu | html_design S07, S05 (chip '(đã xóa)'); API_DESIGN 3.7.3; PRD E-13, E-19 |

## Mục tiêu

Xóa có xác nhận, ẩn dòng lạc quan, nhãn nguồn của tài liệu đã xóa hiển thị '(đã xóa)'.

## Phạm vi file

- `frontend/src/features/documents/DeleteDialog.tsx`
- `frontend/e2e/delete.spec.ts`

## Các bước gợi ý

1. `role=alertdialog`, focus mặc định nút Hủy, Esc đóng, trả focus về nút xóa.
2. Lỗi khác 404 → khôi phục dòng + toast lỗi.

## Tiêu chí hoàn thành

- [ ] E2E: xóa → dòng biến mất; hỏi lại câu cũ → không trích tài liệu đã xóa
- [ ] E2E: chip của câu trả lời cũ hiện '(đã xóa)' và không bấm được
- [ ] Kiểm tra bàn phím: Tab vòng trong hộp thoại
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make e2e -- delete.spec.ts
```
