# SEC-006 – RLS ở mức cơ sở dữ liệu

| Trường | Giá trị |
|---|---|
| ID | SEC-006 |
| Loại | Security |
| Ưu tiên | Critical |
| Truy vết | NFR-010; DATABASE_DESIGN RLS |
| URL ứng dụng | http://localhost:8080/ |
| Cách thực hiện | Tự động – dòng lệnh, ghi bằng `app/frontend/evidence/record-cli.ts` |
| Test tự động hiện có | `test_schema_invariants_and_rls`, `test_set_local_does_not_leak` |
| Trạng thái chu kỳ C1 | Đạt (tự động) |
| Thư mục artifact | `./test_reports/SEC-006_rls-o-muc-co-so-du-lieu/` |
| Nguồn | [TEST_PLAN.md v0.2](../TEST_PLAN.md) |

## Mục tiêu

Xác nhận kể cả khi truy vấn trực tiếp bằng vai trò ứng dụng, RLS chỉ trả dữ liệu của đúng workspace.

## Điều kiện tiên quyết

- Ứng dụng chạy tại http://localhost:8080/ (khởi động bằng `node evidence/app.ts start` trong `app/frontend`, hoặc `run.py` trong `app/`); `GET /api/v1/readyz` trả `ready`
- Đã chạy `npm install` và `npx playwright install ffmpeg` trong `app/frontend` (ghi video)
- Backend venv `app/backend/.venv` đã cài `requirements.txt`; có Node.js (test tự khởi động PostgreSQL PGlite trong bộ nhớ)

## Dữ liệu test

- Không cần dữ liệu riêng

## Các bước thực hiện

| # | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Chạy 2 test RLS qua bộ ghi dòng lệnh | 2 passed |
| 2 | Đối chiếu output: P1 thấy 3, P2 thấy 0, không scope thấy 0; scope không rò sang transaction sau | Đúng |

## Tiêu chí đạt

Mọi bước đạt kết quả mong đợi; không có lỗi Critical/High mới.

## Nhiệm vụ của agent (bắt buộc)

Agent thực hiện test case này **trên ứng dụng tại http://localhost:8080/** và phải tạo đủ bằng chứng sau trong thư mục **`./test_reports/SEC-006_rls-o-muc-co-so-du-lieu/`** (tính từ thư mục gốc repo):

| Artifact | Vị trí | Yêu cầu |
|---|---|---|
| Test report | `test_reports/SEC-006_rls-o-muc-co-so-du-lieu/report.md` (+ `result.json`) | Kết luận ĐẠT / KHÔNG ĐẠT / CẦN NGƯỜI XÁC NHẬN / BỊ CHẶN; bản build (commit); môi trường; bảng kết quả từng bước có link ảnh; link video; lỗi phát hiện |
| Ảnh chụp màn hình | `test_reports/SEC-006_rls-o-muc-co-so-du-lieu/screenshots/NN-<bước>.png` | Ít nhất **1 ảnh cho mỗi bước** ở bảng trên, và 1 ảnh tại thời điểm lỗi nếu có |
| Video | `test_reports/SEC-006_rls-o-muc-co-so-du-lieu/video/*.webm` | Ghi **toàn bộ quá trình test** từ bước 1 tới bước cuối, không cắt |
| Log | `test_reports/SEC-006_rls-o-muc-co-so-du-lieu/logs/` | Output lệnh / request–response API / log ứng dụng liên quan |

**Quy trình:**

1. **Kiểm tra môi trường:** mở http://localhost:8080/ và gọi `GET http://localhost:8080/api/v1/readyz`, phải nhận `{"status":"ready"}`. Nếu không được, chạy `node evidence/app.ts start` trong `app/frontend` (lần đầu trên máy: chạy `run.py --sample` một lần để sinh PDF mẫu). Nếu vẫn không được, tạo report với kết luận **BỊ CHẶN – môi trường**, kèm ảnh/log lỗi, rồi dừng.
2. **Chạy lệnh qua bộ ghi bằng chứng:** trong `app/frontend`, chạy:

   ```bash
   node evidence/record-cli.ts --tc SEC-006_rls-o-muc-co-so-du-lieu --title "RLS ở mức cơ sở dữ liệu" --cwd ../backend \
     --expect "Lệnh kết thúc với mã 0" -- .venv/Scripts/python.exe -m pytest -v -p no:cacheprovider tests/integration/test_slice1.py::test_schema_invariants_and_rls tests/integration/test_slice1.py::test_set_local_does_not_leak
   ```

   Bộ ghi hiển thị output trên một trang Edge và quay video, chụp ảnh khi kết thúc, lưu log và ghi `report.md`.
3. **Bổ sung report:** mở `test_reports/SEC-006_rls-o-muc-co-so-du-lieu/report.md`, đối chiếu output với từng dòng ở bảng *Các bước thực hiện*, ghi kết quả từng dòng vào mục *Ghi chú / lỗi phát hiện*.

**Không được:** lưu artifact ngoài thư mục trên; sửa dữ liệu của người dùng khác ngoài tài khoản test đã nêu; đánh dấu ĐẠT khi còn bước chưa thực hiện. Mỗi lần chạy lại, kết quả cũ tự chuyển sang `test_reports/_archive/`.

**Lỗi phát hiện:** ghi vào report theo mẫu `DEF-T-xxx` (bước tái hiện, mong đợi, thực tế, ảnh/video, mức độ, yêu cầu bị ảnh hưởng: NFR-010; DATABASE_DESIGN RLS).
