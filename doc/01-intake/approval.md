# Intent Approval – Phê duyệt phạm vi MVP

## 1. Thông tin phê duyệt

| Trường | Giá trị |
|---|---|
| Sản phẩm | AI Chat với tài liệu PDF |
| Tài liệu cần duyệt | `intent.md` |
| Phiên bản | 0.1 |
| Product Owner | Cần điền |
| Business Analyst | Cần điền |
| Ngày phê duyệt | Chưa xác nhận |
| Trạng thái | Draft – Chưa phê duyệt |

## 2. Acceptance criteria cấp MVP

- [ ] AC-01: Tải PDF hợp lệ; hệ thống ghi nhận và bắt đầu xử lý.
- [ ] AC-02: Tải file không phải PDF; hệ thống thông báo file không hợp lệ.
- [ ] AC-03: PDF xử lý thành công có thể được dùng để hỏi đáp.
- [ ] AC-04: AI trả lời câu hỏi dựa trên một hoặc nhiều tài liệu liên quan.
- [ ] AC-05: Khi không có đủ thông tin trong tài liệu, AI nói rõ chưa đủ thông tin.
- [ ] AC-06: Hiển thị tên tài liệu nguồn và số trang khi xác định được.
- [ ] AC-07: Sau khi xóa tài liệu, tài liệu đó không còn được dùng cho các truy vấn tiếp theo.

## 3. Risk tier

**Đề xuất ban đầu: Medium – cần PO và IT/Security xác nhận.**

Lý do:
- AI có thể trả lời sai hoặc không có đủ căn cứ.
- PDF có thể chứa thông tin nội bộ hoặc nhạy cảm.
- Cần xác định tài liệu được lưu ở đâu và nội dung có gửi tới nhà cung cấp AI bên ngoài hay không.

Nếu ứng dụng xử lý dữ liệu nhạy cảm, dữ liệu khách hàng hoặc dữ liệu có yêu cầu tuân thủ cao, cần đánh giá lại và có thể nâng lên High.

## 4. Owner và trách nhiệm

| Hạng mục | Owner đề xuất | Trạng thái |
|---|---|---|
| Phê duyệt mục tiêu/phạm vi | Product Owner | Cần chỉ định |
| Làm rõ yêu cầu và cập nhật tài liệu | BA | Cần chỉ định |
| Thiết kế và triển khai | Tech Lead/Developer | Cần chỉ định |
| Kiểm thử acceptance criteria | QA/Tester | Cần chỉ định |
| Duyệt bảo mật và dữ liệu | IT/Security | Cần xác nhận có tham gia hay không |

## 5. Quyết định cần có trước khi phát triển

- [ ] Chốt đối tượng người dùng và phạm vi truy cập tài liệu.
- [ ] Chốt giới hạn dung lượng/số lượng PDF.
- [ ] Chốt chính sách lưu trữ và xóa dữ liệu.
- [ ] Chốt nhà cung cấp AI và cách dữ liệu được xử lý.
- [ ] Chốt chỉ tiêu hiệu năng tối thiểu.
- [ ] PO phê duyệt `intent.md`.

## 6. Kết quả phê duyệt

- Quyết định: Chưa phê duyệt
- Người phê duyệt: ____________________
- Ngày: ____________________
- Ghi chú/điều kiện: ____________________
