# Test report – UT-002: Chunker – đoạn không vượt ranh giới trang

| Trường | Giá trị |
|---|---|
| Test case | [UT-002](../../doc/07-verification/test_cases/UT-002_chunker-doan-khong-vuot-ranh-gioi-trang.md) |
| Kết luận | **ĐẠT** |
| Bắt đầu | 2026-10-27T13:56:22.700Z |
| Kết thúc | 2026-10-27T13:56:34.223Z (11.5 s) |
| Cách thực hiện | Tự động – dòng lệnh (app/frontend/evidence/record-cli.ts) |
| URL ứng dụng | http://localhost:8080/ |
| Bản build | 166929f + thay đổi chưa commit trong app/ |
| Trình duyệt | Microsoft Edge (Playwright, channel msedge) |
| Hệ điều hành | win32 x64 |
| Thư mục chạy | C:\XUANPHU\Hoc AI\Chat_With_AI\app\backend |

## Kết quả từng bước

| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|---|
| 1 | Chạy: .venv/Scripts/python.exe -m pytest -v -p no:cacheprovider tests/unit/test_algorithms.py::test_chunk_never_spans_pages | Lệnh kết thúc với mã 0 | Mã thoát 0 | Đạt | [ảnh](screenshots/01-ket-qua-lenh.png) [ảnh](screenshots/02-toan-bo-output.png) |

## Video

- [UT-002-cli.webm](video/UT-002-cli.webm)

## Ảnh chụp màn hình

![Bước 1 – Chạy: .venv/Scripts/python.exe -m pytest -v -p no:cacheprovider tests/unit/test_algorithms.py::test_chunk_never_spans_pages](screenshots/01-ket-qua-lenh.png)
![Bước 1 – Chạy: .venv/Scripts/python.exe -m pytest -v -p no:cacheprovider tests/unit/test_algorithms.py::test_chunk_never_spans_pages](screenshots/02-toan-bo-output.png)

## Log

- [output.log](logs/output.log)

## Ghi chú / lỗi phát hiện

- (không có)
