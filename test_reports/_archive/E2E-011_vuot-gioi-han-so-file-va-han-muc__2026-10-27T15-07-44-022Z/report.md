# Test report – E2E-011: Vượt giới hạn số file và hạn mức

| Trường | Giá trị |
|---|---|
| Test case | [E2E-011](../../doc/07-verification/test_cases/E2E-011_vuot-gioi-han-so-file-va-han-muc.md) |
| Kết luận | **KHÔNG ĐẠT** |
| Bắt đầu | 2026-10-27T14:57:33.945Z |
| Kết thúc | 2026-10-27T15:07:11.476Z (577.5 s) |
| Cách thực hiện | Tự động – Playwright (app/frontend/evidence/fixture.ts) |
| URL ứng dụng | http://localhost:8080/ |
| Bản build | 166929f + thay đổi chưa commit trong app/ |
| Trình duyệt | Microsoft Edge (Playwright, channel msedge) |
| Hệ điều hành | win32 x64 |
| Spec | app/frontend/testcases/E2E-011_vuot-gioi-han-so-file-va-han-muc.spec.ts |

## Kết quả từng bước

| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|---|
| 1 | Đăng nhập P2, xóa tài liệu cũ; chọn 12 file PDF cùng lúc | Thông báo "Mỗi lần chỉ tải tối đa 10 file – bạn đã chọn 12 file"; danh sách không đổi | Như mong đợi | Đạt | [ảnh](screenshots/01-dang-nhap-p2-xoa-tai-lieu-cu-chon-12-file-pdf-cung.png) |
| 2 | Khởi động lại với MAX_DOCS_PER_WORKSPACE=6; tải 2 file | Cảnh báo "Sắp đạt giới hạn… còn 4 tài liệu"; huy hiệu hạn mức màu cảnh báo | locator.waitFor: Target page, context or browser has been closed | Không đạt |  |

## Video

- [E2E-011-app.webm](video/E2E-011-app.webm)

## Ảnh chụp màn hình

![Bước 1 – Đăng nhập P2, xóa tài liệu cũ; chọn 12 file PDF cùng lúc](screenshots/01-dang-nhap-p2-xoa-tai-lieu-cu-chon-12-file-pdf-cung.png)

## Log

- (không có)

## Ghi chú / lỗi phát hiện

- Khởi động lại ứng dụng với {"MAX_DOCS_PER_WORKSPACE":"6"}: [app] restart xong – http://localhost:8080/ sẵn sàng
- Khởi động lại ứng dụng với {}: [app] restart xong – http://localhost:8080/ sẵn sàng
