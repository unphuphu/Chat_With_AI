# Test report – UAT-007: Xóa tài liệu không còn được dùng

| Trường | Giá trị |
|---|---|
| Test case | [UAT-007](../../doc/07-verification/test_cases/UAT-007_xoa-tai-lieu-khong-con-duoc-dung.md) |
| Kết luận | **BỊ CHẶN** |
| Bắt đầu | 2026-10-27T15:16:30.453Z |
| Kết thúc | 2026-10-27T15:16:37.670Z (7.2 s) |
| Cách thực hiện | Không thực thi – bị chặn (evidence/blocked.ts) |
| URL ứng dụng | http://localhost:8080/ |
| Bản build | 166929f + thay đổi chưa commit trong app/ |
| Trình duyệt | Microsoft Edge (Playwright, channel msedge) |
| Hệ điều hành | win32 x64 |

## Kết quả từng bước

| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|---|
| 1 | Kiểm tra điều kiện thực thi | Người dùng nghiệp vụ trên staging. | Cần người dùng nghiệp vụ/PO thực hiện và ký xác nhận trên môi trường nghiệm thu – agent không thể thay thế. | Bị chặn | [ảnh](screenshots/01-ly-do-bi-chan.png) |

## Video

- [UAT-007-blocked.webm](video/UAT-007-blocked.webm)

## Ảnh chụp màn hình

![Bước 1 – Kiểm tra điều kiện thực thi](screenshots/01-ly-do-bi-chan.png)

## Log

- (không có)

## Ghi chú / lỗi phát hiện

- Bị chặn: Cần người dùng nghiệp vụ/PO thực hiện và ký xác nhận trên môi trường nghiệm thu – agent không thể thay thế.
- Cần: Người dùng nghiệp vụ trên staging.
