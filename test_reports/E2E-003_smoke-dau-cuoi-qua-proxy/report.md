# Test report – E2E-003: Smoke đầu-cuối qua proxy

| Trường | Giá trị |
|---|---|
| Test case | [E2E-003](../../doc/07-verification/test_cases/E2E-003_smoke-dau-cuoi-qua-proxy.md) |
| Kết luận | **ĐẠT** |
| Bắt đầu | 2026-10-27T14:28:46.804Z |
| Kết thúc | 2026-10-27T14:29:19.628Z (32.8 s) |
| Cách thực hiện | Tự động – dòng lệnh (app/frontend/evidence/record-cli.ts) |
| URL ứng dụng | http://localhost:8080/ |
| Bản build | 166929f + thay đổi chưa commit trong app/ |
| Trình duyệt | Microsoft Edge (Playwright, channel msedge) |
| Hệ điều hành | win32 x64 |
| Thư mục chạy | C:\XUANPHU\Hoc AI\Chat_With_AI\app\backend |

## Kết quả từng bước

| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|---|
| 1 | Chạy: .venv/Scripts/python.exe scripts/smoke.py http://localhost:8080 | login ok; 3 tài liệu READY; ANSWERED/ANSWERED/INSUFFICIENT | Mã thoát 0 | Đạt | [ảnh](screenshots/01-ket-qua-lenh.png) [ảnh](screenshots/02-toan-bo-output.png) |

## Video

- [E2E-003-cli.webm](video/E2E-003-cli.webm)

## Ảnh chụp màn hình

![Bước 1 – Chạy: .venv/Scripts/python.exe scripts/smoke.py http://localhost:8080](screenshots/01-ket-qua-lenh.png)
![Bước 1 – Chạy: .venv/Scripts/python.exe scripts/smoke.py http://localhost:8080](screenshots/02-toan-bo-output.png)

## Log

- [output.log](logs/output.log)

## Ghi chú / lỗi phát hiện

- (không có)
