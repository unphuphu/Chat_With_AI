# UT-003 – Chuẩn hóa văn bản trích xuất

| Trường | Giá trị |
|---|---|
| ID | UT-003 |
| Loại | Unit |
| Ưu tiên | High |
| Truy vết | ALG-03; NFR-016 |
| URL ứng dụng | http://localhost:8080/ |
| Cách thực hiện | Tự động – dòng lệnh, ghi bằng `app/frontend/evidence/record-cli.ts` |
| Test tự động hiện có | `tests/unit/test_algorithms.py::test_normalize` |
| Trạng thái chu kỳ C1 | Đạt (tự động) |
| Thư mục artifact | `./test_reports/UT-003_chuan-hoa-van-ban-trich-xuat/` |
| Nguồn | [TEST_PLAN.md v0.2](../TEST_PLAN.md) |

## Mục tiêu

Xác nhận văn bản tiếng Việt được chuẩn hóa NFC, nối từ bị ngắt bằng gạch nối cuối dòng, gộp dòng trống.

## Điều kiện tiên quyết

- Backend venv `app/backend/.venv` đã cài `requirements.txt`; có Node.js (test tự khởi động PostgreSQL PGlite trong bộ nhớ)
- Đã chạy `npm install` và `npx playwright install ffmpeg` trong `app/frontend` (ghi video)
- Ứng dụng chạy tại http://localhost:8080/ (khởi động bằng `node evidence/app.ts start` trong `app/frontend`, hoặc `run.py` trong `app/`); `GET /api/v1/readyz` trả `ready` (để ghi bản build đang kiểm thử)

## Dữ liệu test

- Dữ liệu sinh trong test (không cần file ngoài)

## Các bước thực hiện

| # | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Kiểm tra môi trường tại http://localhost:8080/ và ghi commit đang kiểm thử | readyz = ready; report có mã commit |
| 2 | Chạy `tests/unit/test_algorithms.py::test_normalize` qua bộ ghi bằng chứng | pytest báo `passed`, mã thoát 0 |
| 3 | Đối chiếu: `thanh to-\nán` → `thanh toán`; tổ hợp dấu rời → ký tự dựng sẵn | Test đạt |

## Tiêu chí đạt

Mọi bước đạt kết quả mong đợi; không có lỗi Critical/High mới.

## Nhiệm vụ của agent (bắt buộc)

Agent thực hiện test case này **trên ứng dụng tại http://localhost:8080/** và phải tạo đủ bằng chứng sau trong thư mục **`./test_reports/UT-003_chuan-hoa-van-ban-trich-xuat/`** (tính từ thư mục gốc repo):

| Artifact | Vị trí | Yêu cầu |
|---|---|---|
| Test report | `test_reports/UT-003_chuan-hoa-van-ban-trich-xuat/report.md` (+ `result.json`) | Kết luận ĐẠT / KHÔNG ĐẠT / CẦN NGƯỜI XÁC NHẬN / BỊ CHẶN; bản build (commit); môi trường; bảng kết quả từng bước có link ảnh; link video; lỗi phát hiện |
| Ảnh chụp màn hình | `test_reports/UT-003_chuan-hoa-van-ban-trich-xuat/screenshots/NN-<bước>.png` | Ít nhất **1 ảnh cho mỗi bước** ở bảng trên, và 1 ảnh tại thời điểm lỗi nếu có |
| Video | `test_reports/UT-003_chuan-hoa-van-ban-trich-xuat/video/*.webm` | Ghi **toàn bộ quá trình test** từ bước 1 tới bước cuối, không cắt |
| Log | `test_reports/UT-003_chuan-hoa-van-ban-trich-xuat/logs/` | Output lệnh / request–response API / log ứng dụng liên quan |

**Quy trình:**

1. **Kiểm tra môi trường:** mở http://localhost:8080/ và gọi `GET http://localhost:8080/api/v1/readyz`, phải nhận `{"status":"ready"}`. Nếu không được, chạy `node evidence/app.ts start` trong `app/frontend` (lần đầu trên máy: chạy `run.py --sample` một lần để sinh PDF mẫu). Nếu vẫn không được, tạo report với kết luận **BỊ CHẶN – môi trường**, kèm ảnh/log lỗi, rồi dừng.
2. **Chạy lệnh qua bộ ghi bằng chứng:** trong `app/frontend`, chạy:

   ```bash
   node evidence/record-cli.ts --tc UT-003_chuan-hoa-van-ban-trich-xuat --title "Chuẩn hóa văn bản trích xuất" --cwd ../backend \
     --expect "Lệnh kết thúc với mã 0" -- .venv/Scripts/python.exe -m pytest -v -p no:cacheprovider tests/unit/test_algorithms.py::test_normalize
   ```

   Bộ ghi hiển thị output trên một trang Edge và quay video, chụp ảnh khi kết thúc, lưu log và ghi `report.md`.
3. **Bổ sung report:** mở `test_reports/UT-003_chuan-hoa-van-ban-trich-xuat/report.md`, đối chiếu output với từng dòng ở bảng *Các bước thực hiện*, ghi kết quả từng dòng vào mục *Ghi chú / lỗi phát hiện*.

**Không được:** lưu artifact ngoài thư mục trên; sửa dữ liệu của người dùng khác ngoài tài khoản test đã nêu; đánh dấu ĐẠT khi còn bước chưa thực hiện. Mỗi lần chạy lại, kết quả cũ tự chuyển sang `test_reports/_archive/`.

**Lỗi phát hiện:** ghi vào report theo mẫu `DEF-T-xxx` (bước tái hiện, mong đợi, thực tế, ảnh/video, mức độ, yêu cầu bị ảnh hưởng: ALG-03; NFR-016).
