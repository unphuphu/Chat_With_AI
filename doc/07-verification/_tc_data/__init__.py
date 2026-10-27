"""Dữ liệu test case cho _build_test_cases.py – mỗi module export CASES: list[dict]."""

# Điều kiện tiên quyết dùng chung
APP = "Ứng dụng chạy tại http://localhost:8080/ (khởi động bằng `node evidence/app.ts start` trong `app/frontend`, hoặc `run.py` trong `app/`); `GET /api/v1/readyz` trả `ready`"
SAMPLES = "Có PDF mẫu trong `app/sample-pdfs/` (`hop-dong-A.pdf`, `chinh-sach-ban-hang-2026.pdf`, `bang-gia-Q4.pdf`, `ho-so-scan-2019.pdf`, `hop-dong-mat-khau.pdf`, `hop-dong-khoa-in.pdf`, `hong.pdf`, `bao-gia.docx`, `gia-mao.pdf`, `qua-nhieu-trang.pdf`)"
VENV = "Backend venv `app/backend/.venv` đã cài `requirements.txt`; có Node.js (test tự khởi động PostgreSQL PGlite trong bộ nhớ)"
EVIDENCE = "Đã chạy `npm install` và `npx playwright install ffmpeg` trong `app/frontend` (ghi video)"
P1 = "Tài khoản mẫu **P1** – Nguyễn Lan (lan.nguyen@congty.vn, nhóm `aichat-users`)"
P2 = "Tài khoản mẫu **P2** – Trần Minh (minh.tran@congty.vn, nhóm `aichat-users`)"
OUTSIDER = "Tài khoản mẫu **Người ngoài nhóm** (khach@congty.vn, không thuộc nhóm nào)"
CLEAN_P2 = "Dùng tài khoản P2 và xóa hết tài liệu của P2 ở bước đầu (để không ảnh hưởng dữ liệu demo của P1)"
RESTART = "Test cần khởi động lại ứng dụng với biến môi trường riêng (bước ghi *Khởi động lại với …*): trong spec gọi `await ev.restartApp({ KEY: 'VALUE' })`, hoặc chạy `node evidence/app.ts restart KEY=VALUE` trong `app/frontend`. Cuối test gọi `ev.restartApp()` (không tham số) để trả cấu hình mặc định. Ứng dụng phải được khởi động bằng `node evidence/app.ts start` (không phải `run.py` chạy tay) để công cụ dừng/khởi động lại được"

PYTEST = ".venv/Scripts/python.exe -m pytest -v -p no:cacheprovider"
