# Test report – UAT-001: Tải lên một PDF hợp lệ

| Trường | Giá trị |
|---|---|
| Test case | [UAT-001](../../doc/07-verification/test_cases/UAT-001_tai-len-mot-pdf-hop-le.md) |
| Kết luận | **BỊ CHẶN** |
| Bắt đầu | 2026-10-27T15:15:28.253Z |
| Kết thúc | 2026-10-27T15:15:37.121Z (8.9 s) |
| Cách thực hiện | Không thực thi – bị chặn (evidence/blocked.ts) |
| URL ứng dụng | http://localhost:8080/ |
| Bản build | 166929f + thay đổi chưa commit trong app/ |
| Trình duyệt | Microsoft Edge (Playwright, channel msedge) |
| Hệ điều hành | win32 x64 |

## Kết quả từng bước

| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|---|
| 1 | Kiểm tra điều kiện thực thi | Người dùng nghiệp vụ, tài liệu dự án thật, staging. (Luồng tương ứng đã đạt ở E2E-001/E2E-003 trên bản demo.) | Cần người dùng nghiệp vụ/PO thực hiện và ký xác nhận trên môi trường nghiệm thu – agent không thể thay thế. | Bị chặn | [ảnh](screenshots/01-ly-do-bi-chan.png) |

## Video

- [UAT-001-blocked.webm](video/UAT-001-blocked.webm)

## Ảnh chụp màn hình

![Bước 1 – Kiểm tra điều kiện thực thi](screenshots/01-ly-do-bi-chan.png)

## Log

- (không có)

## Ghi chú / lỗi phát hiện

- Bị chặn: Cần người dùng nghiệp vụ/PO thực hiện và ký xác nhận trên môi trường nghiệm thu – agent không thể thay thế.
- Cần: Người dùng nghiệp vụ, tài liệu dự án thật, staging. (Luồng tương ứng đã đạt ở E2E-001/E2E-003 trên bản demo.)
