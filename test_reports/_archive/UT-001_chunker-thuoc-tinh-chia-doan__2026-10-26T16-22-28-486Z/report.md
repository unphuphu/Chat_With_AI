# Test report – UT-001: Chunker – thuộc tính chia đoạn

| Trường | Giá trị |
|---|---|
| Test case | [UT-001](../../doc/07-verification/test_cases/UT-001_chunker-thuoc-tinh-chia-doan.md) |
| Kết luận | **ĐẠT** |
| Bắt đầu | 2026-10-26T16:06:53.019Z |
| Kết thúc | 2026-10-26T16:07:06.372Z (13.4 s) |
| Cách thực hiện | Tự động – dòng lệnh (app/frontend/evidence/record-cli.ts) |
| URL ứng dụng | http://localhost:8080/ |
| Bản build | 166929f + thay đổi chưa commit trong app/ |
| Trình duyệt | Microsoft Edge (Playwright, channel msedge) |
| Hệ điều hành | win32 x64 |
| Thư mục chạy | C:\XUANPHU\Hoc AI\Chat_With_AI\app\backend |

## Kết quả từng bước

| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|---|
| 1 | Chạy: .venv/Scripts/python.exe -m pytest tests/unit/test_algorithms.py::test_chunker_properties -v -p no:cacheprovider | 1 test đạt | Mã thoát 0 | Đạt | [ảnh](screenshots/01-ket-qua-lenh.png) [ảnh](screenshots/02-toan-bo-output.png) |

## Video

- [UT-001-cli.webm](video/UT-001-cli.webm)

## Ảnh chụp màn hình

![Bước 1 – Chạy: .venv/Scripts/python.exe -m pytest tests/unit/test_algorithms.py::test_chunker_properties -v -p no:cacheprovider](screenshots/01-ket-qua-lenh.png)
![Bước 1 – Chạy: .venv/Scripts/python.exe -m pytest tests/unit/test_algorithms.py::test_chunker_properties -v -p no:cacheprovider](screenshots/02-toan-bo-output.png)

## Log

- [output.log](logs/output.log)

## Ghi chú / lỗi phát hiện

- (không có)
