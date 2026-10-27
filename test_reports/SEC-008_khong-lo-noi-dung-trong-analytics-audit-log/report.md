# Test report – SEC-008: Không lộ nội dung trong analytics, audit, log

| Trường | Giá trị |
|---|---|
| Test case | [SEC-008](../../doc/07-verification/test_cases/SEC-008_khong-lo-noi-dung-trong-analytics-audit-log.md) |
| Kết luận | **ĐẠT** |
| Bắt đầu | 2026-10-27T14:26:32.649Z |
| Kết thúc | 2026-10-27T14:26:52.725Z (20.1 s) |
| Cách thực hiện | Tự động – dòng lệnh (app/frontend/evidence/record-cli.ts) |
| URL ứng dụng | http://localhost:8080/ |
| Bản build | 166929f + thay đổi chưa commit trong app/ |
| Trình duyệt | Microsoft Edge (Playwright, channel msedge) |
| Hệ điều hành | win32 x64 |
| Thư mục chạy | C:\XUANPHU\Hoc AI\Chat_With_AI\app\backend |

## Kết quả từng bước

| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|---|
| 1 | Chạy: .venv/Scripts/python.exe -m pytest -v -p no:cacheprovider tests/integration/test_qa.py::test_no_content_in_analytics tests/unit/test_algorithms.py::test_redact_forbidden | Lệnh kết thúc với mã 0 | Mã thoát 0 | Đạt | [ảnh](screenshots/01-ket-qua-lenh.png) [ảnh](screenshots/02-toan-bo-output.png) |

## Video

- [SEC-008-cli.webm](video/SEC-008-cli.webm)

## Ảnh chụp màn hình

![Bước 1 – Chạy: .venv/Scripts/python.exe -m pytest -v -p no:cacheprovider tests/integration/test_qa.py::test_no_content_in_analytics tests/unit/test_algorithms.py::test_redact_forbidden](screenshots/01-ket-qua-lenh.png)
![Bước 1 – Chạy: .venv/Scripts/python.exe -m pytest -v -p no:cacheprovider tests/integration/test_qa.py::test_no_content_in_analytics tests/unit/test_algorithms.py::test_redact_forbidden](screenshots/02-toan-bo-output.png)

## Log

- [output.log](logs/output.log)

## Ghi chú / lỗi phát hiện

- (không có)
