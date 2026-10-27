# Test report – INT-011: Truy xuất đa tài liệu với ngưỡng dev

| Trường | Giá trị |
|---|---|
| Test case | [INT-011](../../doc/07-verification/test_cases/INT-011_truy-xuat-da-tai-lieu-voi-nguong-dev.md) |
| Kết luận | **ĐẠT** |
| Bắt đầu | 2026-10-27T14:09:59.011Z |
| Kết thúc | 2026-10-27T14:10:46.005Z (47.0 s) |
| Cách thực hiện | Tự động – dòng lệnh (app/frontend/evidence/record-cli.ts) |
| URL ứng dụng | http://localhost:8080/ |
| Bản build | 166929f + thay đổi chưa commit trong app/ |
| Trình duyệt | Microsoft Edge (Playwright, channel msedge) |
| Hệ điều hành | win32 x64 |
| Thư mục chạy | C:\XUANPHU\Hoc AI\Chat_With_AI\app\backend |

## Kết quả từng bước

| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|---|
| 1 | Chạy: .venv/Scripts/python.exe -m pytest -v -p no:cacheprovider tests/integration/test_slice1.py::test_extractive_multi_document_price | Lệnh kết thúc với mã 0 | Mã thoát 0 | Đạt | [ảnh](screenshots/01-ket-qua-lenh.png) [ảnh](screenshots/02-toan-bo-output.png) |

## Video

- [INT-011-cli.webm](video/INT-011-cli.webm)

## Ảnh chụp màn hình

![Bước 1 – Chạy: .venv/Scripts/python.exe -m pytest -v -p no:cacheprovider tests/integration/test_slice1.py::test_extractive_multi_document_price](screenshots/01-ket-qua-lenh.png)
![Bước 1 – Chạy: .venv/Scripts/python.exe -m pytest -v -p no:cacheprovider tests/integration/test_slice1.py::test_extractive_multi_document_price](screenshots/02-toan-bo-output.png)

## Log

- [output.log](logs/output.log)

## Ghi chú / lỗi phát hiện

- (không có)
