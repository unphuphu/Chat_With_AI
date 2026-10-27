# Test report – INT-005: Lỗi tạm thời khi ingest → R-04 → xử lý lại

| Trường | Giá trị |
|---|---|
| Test case | [INT-005](../../doc/07-verification/test_cases/INT-005_loi-tam-thoi-khi-ingest-r-04-xu-ly-lai.md) |
| Kết luận | **KHÔNG ĐẠT** |
| Bắt đầu | 2026-10-27T14:04:29.161Z |
| Kết thúc | 2026-10-27T14:06:13.530Z (104.4 s) |
| Cách thực hiện | Tự động – dòng lệnh (app/frontend/evidence/record-cli.ts) |
| URL ứng dụng | http://localhost:8080/ |
| Bản build | 166929f + thay đổi chưa commit trong app/ |
| Trình duyệt | Microsoft Edge (Playwright, channel msedge) |
| Hệ điều hành | win32 x64 |
| Thư mục chạy | C:\XUANPHU\Hoc AI\Chat_With_AI\app\backend |

## Kết quả từng bước

| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|---|
| 1 | Chạy: .venv/Scripts/python.exe -m pytest -v -p no:cacheprovider tests/integration/test_documents.py::test_reprocess_only_r04 | Lệnh kết thúc với mã 0 | Mã thoát 1 | Không đạt | [ảnh](screenshots/01-ket-qua-lenh.png) [ảnh](screenshots/02-toan-bo-output.png) |

## Video

- [INT-005-cli.webm](video/INT-005-cli.webm)

## Ảnh chụp màn hình

![Bước 1 – Chạy: .venv/Scripts/python.exe -m pytest -v -p no:cacheprovider tests/integration/test_documents.py::test_reprocess_only_r04](screenshots/01-ket-qua-lenh.png)
![Bước 1 – Chạy: .venv/Scripts/python.exe -m pytest -v -p no:cacheprovider tests/integration/test_documents.py::test_reprocess_only_r04](screenshots/02-toan-bo-output.png)

## Log

- [output.log](logs/output.log)

## Ghi chú / lỗi phát hiện

- (không có)
