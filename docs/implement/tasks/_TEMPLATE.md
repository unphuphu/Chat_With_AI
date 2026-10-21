# T-XXX — <Tên task ngắn, động từ đứng đầu>

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint N |
| **Loại** | Backend / Frontend / Fullstack / QA / Spike / DevOps / Quy trình |
| **User story** | US-xxx (hoặc "— nền tảng") |
| **Ưu tiên** | P0 / P1 / P2 (theo story; task nền tảng của story P0 là P0) |
| **Ước lượng** | x ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-xxx, OQ-xxx |
| **Mở khóa (task chờ task này)** | T-xxx |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Một đến ba câu: sau khi xong task, hệ thống làm được gì mà trước đó chưa làm được.

## 2. Bối cảnh

Tại sao task tồn tại, nó nằm ở đâu trong luồng (SAD §x), yêu cầu nào (BR/AC) nó phục vụ. Link tới tài liệu nguồn.

## 3. Phạm vi

**Trong phạm vi**
- ...

**Ngoài phạm vi** (để tránh làm thừa)
- ...

## 4. Thiết kế chi tiết

- File/thư mục cần tạo hoặc sửa (đường dẫn theo [Implement_plan §3.1](../Implement_plan.md#31-cấu-trúc-repository-monorepo)).
- Interface/hàm/lớp với chữ ký cụ thể.
- Hợp đồng API (request/response/mã lỗi), SQL, sự kiện, trạng thái giao diện — tùy loại task.
- Quy tắc nghiệp vụ phải giữ.

## 5. Các bước thực hiện

1. ...
2. ...

## 6. Tiêu chí chấp nhận

- [ ] Tiêu chí kiểm được, khách quan (có số, có hành vi cụ thể).
- [ ] AC của story liên quan (Given-When-Then) nếu task hoàn thành story.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | ... | ... |
| Integration | ... | ... |
| E2E | ... | ... |

## 8. Cấu hình

Biến môi trường dùng/thêm (tên theo [Implement_plan §3.3](../Implement_plan.md#33-biến-môi-trường)), giá trị `[Default]` và OQ quyết định giá trị thật.

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §...
- [SAD](../../design/SAD.md) §...
- [User_Stories](../../design/User_Stories.md) US-...
- Màn hình: [html_design/...](../../design/html_design/...)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] (Điều kiện riêng của task, nếu có.)
