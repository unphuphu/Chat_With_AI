# Test report – SEC-014: Quét lỗ hổng thư viện phụ thuộc

| Trường | Giá trị |
|---|---|
| Test case | [SEC-014](../../doc/07-verification/test_cases/SEC-014_quet-lo-hong-thu-vien-phu-thuoc.md) |
| Kết luận | **ĐẠT** |
| Bắt đầu | 2026-10-27T14:31:04.113Z |
| Kết thúc | 2026-10-27T14:32:10.042Z (65.9 s) |
| Cách thực hiện | Tự động – dòng lệnh (app/frontend/evidence/record-cli.ts) |
| URL ứng dụng | http://localhost:8080/ |
| Bản build | 166929f + thay đổi chưa commit trong app/ |
| Trình duyệt | Microsoft Edge (Playwright, channel msedge) |
| Hệ điều hành | win32 x64 |
| Thư mục chạy | C:\XUANPHU\Hoc AI\Chat_With_AI\app\backend |

## Kết quả từng bước

| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|---|
| 1 | Chạy: .venv/Scripts/python.exe scripts/audit_deps.py | Không có lỗ hổng High/Critical | Mã thoát 0 | Đạt | [ảnh](screenshots/01-ket-qua-lenh.png) [ảnh](screenshots/02-toan-bo-output.png) |

## Video

- [SEC-014-cli.webm](video/SEC-014-cli.webm)

## Ảnh chụp màn hình

![Bước 1 – Chạy: .venv/Scripts/python.exe scripts/audit_deps.py](screenshots/01-ket-qua-lenh.png)
![Bước 1 – Chạy: .venv/Scripts/python.exe scripts/audit_deps.py](screenshots/02-toan-bo-output.png)

## Log

- [output.log](logs/output.log)

## Ghi chú / lỗi phát hiện

- (không có)
