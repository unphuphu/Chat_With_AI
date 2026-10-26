# Intent – AI Chat với tài liệu PDF

## 1. Problem
Người dùng mất nhiều thời gian đọc, tìm kiếm và đối chiếu thông tin trong nhiều tài liệu PDF. Việc tổng hợp thủ công có thể chậm và dễ bỏ sót thông tin.

## 2. Proposed outcome
Xây dựng ứng dụng web cho phép người dùng tải PDF lên, đặt câu hỏi bằng ngôn ngữ tự nhiên và nhận câu trả lời dựa trên nội dung tài liệu, kèm tên tài liệu và số trang tham chiếu khi có thể.

## 3. Affected users
- Người tải và sử dụng tài liệu PDF.
- Người cần tìm kiếm, đối chiếu hoặc tổng hợp thông tin từ nhiều tài liệu.
- Nhóm phát triển và vận hành ứng dụng.

## 4. Constraints
- MVP chỉ hỗ trợ PDF có thể trích xuất văn bản.
- Chưa hỗ trợ OCR cho PDF scan/hình ảnh.
- Chỉ tài liệu đã xử lý thành công mới được dùng để trả lời.
- Cần bảo đảm người dùng không truy cập được tài liệu ngoài phạm vi quyền của mình.
- Giới hạn dung lượng file, số file và thời gian xử lý: **Cần xác nhận**.

## 5. Success measures
MVP được xem là đạt mục tiêu ban đầu khi:
- Người dùng tải được PDF hợp lệ và xem được trạng thái xử lý.
- Người dùng hỏi đáp được trên một hoặc nhiều tài liệu đã xử lý.
- Câu trả lời có nguồn tham chiếu khi xác định được.
- Khi tài liệu không có thông tin phù hợp, hệ thống thông báo chưa đủ thông tin thay vì tự suy diễn.
- Các chỉ tiêu định lượng: **Cần PO/stakeholder xác nhận**.

## 6. Out of scope
- Word, Excel, PowerPoint và các định dạng khác.
- OCR cho tài liệu scan.
- Chia sẻ tài liệu, cộng tác nhóm và phân quyền chi tiết.
- Tích hợp Google Drive, SharePoint hoặc hệ thống bên ngoài.
- Quản lý phiên bản tài liệu.
- Xuất câu trả lời ra file.
- Huấn luyện/tinh chỉnh mô hình AI riêng.
- Dashboard và báo cáo nâng cao.

## 7. Open questions
1. MVP dành cho một người dùng hay nhiều người dùng?
2. Tài liệu chỉ người tải lên được xem hay dùng chung?
3. File PDF tối đa bao nhiêu MB? Mỗi lần được tải bao nhiêu file?
4. Tài liệu được lưu lâu dài hay chỉ trong phiên làm việc?
5. AI/model nào sẽ được sử dụng và dữ liệu có được gửi tới nhà cung cấp bên ngoài không?
6. Thời gian phản hồi mục tiêu là bao lâu?
7. Ai là Product Owner phê duyệt intent và nghiệm thu MVP?

## Trạng thái
- Phiên bản: 0.1 – Bản nháp
- Trạng thái phê duyệt: Chưa phê duyệt
