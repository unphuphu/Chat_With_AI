# Test report – INT-015: Adapter tích hợp thật (OIDC, blob, embedding, LLM)

| Trường | Giá trị |
|---|---|
| Test case | [INT-015](../../doc/07-verification/test_cases/INT-015_adapter-tich-hop-that-oidc-blob-embedding-llm.md) |
| Kết luận | **ĐẠT** |
| Bắt đầu | 2026-10-27T14:28:06.461Z |
| Kết thúc | 2026-10-27T14:28:45.150Z (38.7 s) |
| Cách thực hiện | Tự động – dòng lệnh (app/frontend/evidence/record-cli.ts) |
| URL ứng dụng | http://localhost:8080/ |
| Bản build | 166929f + thay đổi chưa commit trong app/ |
| Trình duyệt | Microsoft Edge (Playwright, channel msedge) |
| Hệ điều hành | win32 x64 |
| Thư mục chạy | C:\XUANPHU\Hoc AI\Chat_With_AI\app\backend |

## Kết quả từng bước

| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|---|
| 1 | Chạy: .venv/Scripts/python.exe scripts/smoke.py http://localhost:8080 | Lệnh kết thúc với mã 0 | Mã thoát 0 | Đạt | [ảnh](screenshots/01-ket-qua-lenh.png) [ảnh](screenshots/02-toan-bo-output.png) |

## Video

- [INT-015-cli.webm](video/INT-015-cli.webm)

## Ảnh chụp màn hình

![Bước 1 – Chạy: .venv/Scripts/python.exe scripts/smoke.py http://localhost:8080](screenshots/01-ket-qua-lenh.png)
![Bước 1 – Chạy: .venv/Scripts/python.exe scripts/smoke.py http://localhost:8080](screenshots/02-toan-bo-output.png)

## Log

- [output.log](logs/output.log)

## Ghi chú / lỗi phát hiện

- (không có)
