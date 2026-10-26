# BRD – MVP: Ứng dụng AI Chat với tài liệu PDF

## 1. Bối cảnh nghiệp vụ (Business Context)

Trong quá trình triển khai các dự án kinh doanh, đội ngũ phát triển kinh doanh thường phải làm việc với số lượng lớn tài liệu PDF chứa thông tin về sản phẩm, dịch vụ, thị trường, chính sách và các nội dung liên quan.

Việc tìm kiếm, đối chiếu và tổng hợp thông tin từ nhiều tài liệu đang tiêu tốn thời gian, làm giảm hiệu suất làm việc và gây khó khăn trong việc khai thác thông tin phục vụ công việc.

Do đó, doanh nghiệp có nhu cầu xây dựng một công cụ ứng dụng AI, cho phép người dùng tương tác trực tiếp với nội dung tài liệu thông qua hội thoại bằng ngôn ngữ tự nhiên.

## 2. Mục tiêu sản phẩm (Business Objectives)

Xây dựng một ứng dụng web MVP cho phép người dùng tải lên tài liệu PDF và sử dụng AI để hỏi đáp về nội dung của các tài liệu đã tải lên.

Sản phẩm hướng đến các mục tiêu:

- Tiết kiệm thời gian: Giảm thời gian tìm kiếm và tổng hợp thông tin từ nhiều tài liệu.
- Truy xuất thông tin thuận tiện: Cho phép người dùng đặt câu hỏi bằng ngôn ngữ tự nhiên thay vì đọc thủ công từng file.
- Tổng hợp thông tin: Hỗ trợ AI tổng hợp câu trả lời dựa trên nội dung của một hoặc nhiều tài liệu.
- Ra mắt nhanh: Ưu tiên các tính năng thiết yếu để sớm có sản phẩm hoạt động thực tế.

## 3. Phạm vi sản phẩm (Product Scope)

### 3.1. Các tính năng trong phạm vi MVP

| Mã | Tính năng | Mô tả nghiệp vụ |
| --- | --- | --- |
| FR-01 | Tải lên tài liệu PDF | Người dùng có thể tải một hoặc nhiều file PDF lên hệ thống. |
| FR-02 | Quản lý danh sách tài liệu | Hiển thị danh sách các tài liệu đã tải lên, bao gồm tên file và trạng thái xử lý. |
| FR-03 | Xử lý nội dung tài liệu | Hệ thống trích xuất và xử lý nội dung PDF để phục vụ việc tìm kiếm và hỏi đáp bằng AI. |
| FR-04 | Chat với tài liệu | Người dùng nhập câu hỏi bằng ngôn ngữ tự nhiên và nhận câu trả lời từ AI dựa trên nội dung tài liệu đã tải lên. |
| FR-05 | Hỏi đáp trên nhiều tài liệu | AI có thể tổng hợp thông tin từ nhiều tài liệu trong phạm vi dữ liệu người dùng đang truy vấn. |
| FR-06 | Hiển thị nguồn tham chiếu | Câu trả lời hiển thị tài liệu nguồn và số trang tham chiếu khi xác định được, giúp người dùng kiểm tra tính chính xác của thông tin. |

### 3.2. Luồng nghiệp vụ chính (Main User Flow)

**Bước 1. Tải tài liệu**

Người dùng tải một hoặc nhiều file PDF lên ứng dụng.

**Bước 2. Xử lý tài liệu**

Hệ thống trích xuất nội dung và thông báo khi tài liệu sẵn sàng để truy vấn.

**Bước 3. Đặt câu hỏi**

Người dùng nhập câu hỏi về một hoặc nhiều tài liệu đã tải lên.

**Bước 4. Nhận câu trả lời**

AI trả lời dựa trên nội dung tài liệu, kèm nguồn tham chiếu nếu có.

## 4. Yêu cầu chức năng chi tiết (Functional Requirements)

### FR-01. Tải lên tài liệu PDF

- Người dùng có thể chọn và tải file PDF từ thiết bị lên hệ thống.
- Hệ thống kiểm tra định dạng file và thông báo khi file không hợp lệ.
- Hệ thống ghi nhận tài liệu và bắt đầu xử lý nội dung sau khi tải lên thành công.

### FR-02. Quản lý danh sách tài liệu

- Người dùng xem được danh sách tài liệu đã tải lên.
- Mỗi tài liệu có trạng thái xử lý: **Đang xử lý**, **Sẵn sàng** hoặc **Thất bại**.
- Người dùng có thể xóa tài liệu không còn nhu cầu sử dụng.

### FR-03. Xử lý nội dung tài liệu

- Hệ thống trích xuất văn bản từ PDF để phục vụ truy vấn.
- Hệ thống thông báo trạng thái xử lý cho người dùng.
- Chỉ những tài liệu đã xử lý thành công mới được sử dụng để trả lời câu hỏi.

**Giới hạn MVP đề xuất:** Chỉ hỗ trợ PDF có thể trích xuất văn bản. Chưa yêu cầu nhận dạng nội dung từ PDF scan hoặc hình ảnh bằng OCR.

### FR-04. Chat với tài liệu

- Người dùng nhập câu hỏi bằng ngôn ngữ tự nhiên.
- AI sử dụng nội dung tài liệu đã xử lý để tạo câu trả lời phù hợp.
- Người dùng có thể đặt nhiều câu hỏi liên tiếp trong cùng một phiên chat.
- Nếu không tìm thấy thông tin phù hợp trong tài liệu, AI cần thông báo rõ rằng chưa đủ thông tin để trả lời, thay vì tự suy diễn.

### FR-05. Hỏi đáp trên nhiều tài liệu

- Người dùng có thể đặt câu hỏi liên quan đến nhiều tài liệu đã tải lên.
- AI tổng hợp thông tin từ các tài liệu liên quan để đưa ra câu trả lời thống nhất.
- Khi thông tin giữa các tài liệu khác nhau hoặc mâu thuẫn, AI cần nêu rõ sự khác biệt nếu phát hiện được.

### FR-06. Hiển thị nguồn tham chiếu

- Câu trả lời hiển thị tên tài liệu nguồn.
- Hiển thị số trang liên quan khi xác định được.
- Người dùng có thể dựa vào nguồn tham chiếu để mở tài liệu gốc và kiểm chứng thông tin.

## 5. Ngoài phạm vi MVP (Out of Scope)

Để rút ngắn thời gian phát triển, các tính năng sau chưa nằm trong phạm vi phiên bản đầu tiên:

- Hỗ trợ các định dạng ngoài PDF như Word, Excel, PowerPoint.
- OCR cho tài liệu scan hoặc tài liệu dạng hình ảnh.
- Chia sẻ tài liệu, cộng tác nhóm và phân quyền chi tiết.
- Tích hợp Google Drive, SharePoint hoặc các hệ thống quản lý tài liệu khác.
- Quản lý phiên bản tài liệu và lịch sử thay đổi.
- Xuất câu trả lời ra Word, Excel hoặc PDF.
- Đánh giá, huấn luyện hoặc tinh chỉnh mô hình AI riêng.
- Dashboard thống kê và báo cáo sử dụng nâng cao.

## 6. Yêu cầu phi chức năng cơ bản (Non-functional Requirements)

Trong MVP, chỉ ưu tiên các yêu cầu tối thiểu cần thiết để sản phẩm có thể sử dụng:

- **Hiệu năng:** Giao diện phản hồi nhanh; thời gian xử lý tài liệu và trả lời được hiển thị rõ ràng cho người dùng.
- **Tính ổn định:** Hệ thống thông báo khi tải lên, xử lý hoặc truy vấn thất bại và cho phép người dùng thử lại khi phù hợp.
- **Tính chính xác:** Câu trả lời phải dựa trên nội dung tài liệu được truy xuất; hạn chế tối đa việc tạo thông tin không có căn cứ.
- **Bảo mật cơ bản:** Chỉ người dùng được phép mới có thể truy cập tài liệu; dữ liệu không được cung cấp cho người dùng không có quyền.
- **Tính dễ sử dụng:** Giao diện đơn giản, tập trung vào hai thao tác chính: tải tài liệu và chat với AI.

Các chỉ tiêu định lượng như thời gian phản hồi tối đa, dung lượng file tối đa, số lượng file mỗi lần tải và số người dùng đồng thời sẽ được xác định sau khi thống nhất quy mô MVP.

## 7. Tiêu chí nghiệm thu MVP (Acceptance Criteria)

MVP được xem là đáp ứng yêu cầu khi hoàn thành các kịch bản chính sau:

| Mã | Kịch bản nghiệm thu | Kết quả mong đợi |
| --- | --- | --- |
| AC-01 | Tải lên một PDF hợp lệ | File được ghi nhận và chuyển sang trạng thái xử lý. |
| AC-02 | Tải lên file không phải PDF | Hệ thống thông báo file không hợp lệ. |
| AC-03 | Chat với tài liệu đã xử lý thành công | AI trả lời dựa trên nội dung tài liệu. |
| AC-04 | Hỏi câu hỏi cần tổng hợp nhiều file | AI tổng hợp thông tin từ các tài liệu liên quan. |
| AC-05 | Hỏi nội dung không có trong tài liệu | AI thông báo không tìm thấy đủ thông tin để trả lời. |
| AC-06 | Kiểm tra nguồn câu trả lời | Người dùng xem được tài liệu nguồn và số trang khi có dữ liệu tham chiếu. |
| AC-07 | Xóa một tài liệu | Tài liệu bị xóa không còn được sử dụng trong các truy vấn tiếp theo. |

## 8. Đề xuất của BA để tối ưu MVP

Từ góc độ BA, tôi đề xuất chỉ bổ sung những yêu cầu giúp sản phẩm thực sự hữu ích ngay từ phiên bản đầu tiên:

1. **Xử lý trạng thái tài liệu rõ ràng:** Người dùng biết khi nào có thể bắt đầu chat, tránh nhầm lẫn khi file chưa sẵn sàng.
2. **Trả lời kèm nguồn:** Đây là yêu cầu có giá trị cao trong môi trường kinh doanh, giúp người dùng kiểm chứng thông tin nhanh chóng.
3. **Thông báo khi thiếu thông tin:** Giảm rủi ro người dùng đưa ra quyết định dựa trên câu trả lời AI không có căn cứ.
4. **Hỗ trợ nhiều tài liệu trong cùng phạm vi truy vấn:** Đây là giá trị cốt lõi khác biệt so với việc chỉ chat với từng file riêng lẻ.

Chưa nên phát triển các tính năng như quản lý hội thoại nâng cao, phân tích dữ liệu, báo cáo hoặc tích hợp hệ thống bên ngoài ở giai đoạn này.

## 9. Các giả định và vấn đề cần xác nhận

Để đội phát triển có thể ước lượng và triển khai ngay, cần thống nhất một số điểm:

- **Phạm vi người dùng:** MVP dành cho một người dùng cá nhân hay nhiều người dùng trong cùng doanh nghiệp?
- **Phạm vi tài liệu:** Các tài liệu tải lên được dùng chung cho tất cả người dùng hay chỉ người tải lên?
- **Loại PDF:** Có chấp nhận chỉ hỗ trợ PDF có thể trích xuất văn bản trong phiên bản đầu tiên không?
- **Quy mô dữ liệu:** Dự kiến mỗi người dùng tải lên bao nhiêu file và dung lượng tối đa của mỗi file?
- **Lưu trữ dữ liệu:** Tài liệu được lưu cho các lần sử dụng tiếp theo hay chỉ trong phiên làm việc hiện tại?

Đây là các quyết định ảnh hưởng trực tiếp đến kiến trúc, bảo mật, chi phí vận hành và thời gian phát triển.

## Kết luận và phạm vi MVP khuyến nghị

Để ra mắt nhanh, tôi khuyến nghị tập trung vào 6 tính năng: tải PDF, xem danh sách tài liệu, xử lý nội dung, chat với AI, hỏi đáp trên nhiều tài liệu và hiển thị nguồn tham chiếu.

Trong đó, luồng nghiệp vụ tối thiểu cần chạy tốt là:

**Upload PDF → Xử lý tài liệu → Đặt câu hỏi → Nhận câu trả lời có nguồn dẫn chứng.**

Các tính năng còn lại chỉ nên được đưa vào khi chúng cần thiết để hoàn thiện luồng này hoặc bảo đảm an toàn khi sử dụng. Đây là cơ sở phù hợp để chuyển tiếp sang tài liệu SRS, thiết kế giao diện và lập kế hoạch phát triển MVP.
