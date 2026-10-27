# Test report – UI-001: So sánh giao diện với thiết kế

| Trường | Giá trị |
|---|---|
| Test case | [UI-001](../../doc/07-verification/test_cases/UI-001_so-sanh-giao-dien-voi-thiet-ke.md) |
| Kết luận | **KHÔNG ĐẠT** |
| Bắt đầu | 2026-10-27T16:38:59.129Z |
| Kết thúc | 2026-10-27T16:41:36.701Z (157.6 s) |
| Cách thực hiện | Tự động – Playwright (app/frontend/evidence/fixture.ts) |
| URL ứng dụng | http://localhost:8080/ |
| Bản build | 166929f + thay đổi chưa commit trong app/ |
| Trình duyệt | Microsoft Edge (Playwright, channel msedge) |
| Hệ điều hành | win32 x64 |
| Spec | app/frontend/testcases/UI-001_so-sanh-giao-dien-voi-thiet-ke.spec.ts |

## Kết quả từng bước

| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|---|
| 1 | S01 Màn hình chính – chưa có tài liệu | Bố cục, chữ, trạng thái khớp thiết kế | Ảnh so sánh S01: thiết kế (S01_main_empty.html) và thực tế đặt cạnh nhau – Designer đánh giá bố cục, chữ, trạng thái. | Cần người xác nhận | [ảnh](screenshots/01-s01-so-sanh.png) [ảnh](screenshots/02-s01-man-hinh-chinh-chua-co-tai-lieu.png) |
| 2 | S08 Vượt giới hạn tải lên (chọn 12 file) | Khớp thiết kế | Ảnh so sánh S08: thiết kế (S08_upload_limits.html) và thực tế đặt cạnh nhau – Designer đánh giá bố cục, chữ, trạng thái. | Cần người xác nhận | [ảnh](screenshots/03-s08-so-sanh.png) [ảnh](screenshots/04-s08-vuot-gioi-han-tai-len-chon-12-file.png) |
| 3 | S03 Trạng thái tài liệu (Sẵn sàng, Thất bại) | Khớp thiết kế | [31mTimed out 90000ms waiting for [39m[2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m()[22m  Locator: locator('li.row').filter({ hasText: 'hop-dong-A.pdf' }).getByText('Sẵn sàng') Expected: visible Received: <element(s) not found> Call log: | Không đạt | [ảnh](screenshots/05-s03-trang-thai-tai-lieu-san-sang-that-bai.png) |

## Video

- [UI-001-app.webm](video/UI-001-app.webm)

## Ảnh chụp màn hình

![Bước 1 – S01 Màn hình chính – chưa có tài liệu](screenshots/01-s01-so-sanh.png)
![Bước 1 – S01 Màn hình chính – chưa có tài liệu](screenshots/02-s01-man-hinh-chinh-chua-co-tai-lieu.png)
![Bước 2 – S08 Vượt giới hạn tải lên (chọn 12 file)](screenshots/03-s08-so-sanh.png)
![Bước 2 – S08 Vượt giới hạn tải lên (chọn 12 file)](screenshots/04-s08-vuot-gioi-han-tai-len-chon-12-file.png)
![Bước 3 – S03 Trạng thái tài liệu (Sẵn sàng, Thất bại)](screenshots/05-s03-trang-thai-tai-lieu-san-sang-that-bai.png)

## Log

- (không có)

## Ghi chú / lỗi phát hiện

- (không có)
