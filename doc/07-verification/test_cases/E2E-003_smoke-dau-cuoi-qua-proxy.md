# E2E-003 – Smoke đầu-cuối qua proxy

| Trường | Giá trị |
|---|---|
| ID | E2E-003 |
| Loại | System (E2E) |
| Ưu tiên | P0 |
| Truy vết | AC-01; AC-03; AC-04; AC-05; REG-005 |
| URL ứng dụng | http://localhost:8080/ |
| Cách thực hiện | Tự động – dòng lệnh, ghi bằng `app/frontend/evidence/record-cli.ts` |
| Test tự động hiện có | `app/backend/scripts/smoke.py` |
| Trạng thái chu kỳ C1 | Đạt (thủ công, 26/10) |
| Thư mục artifact | `./test_reports/E2E-003_smoke-dau-cuoi-qua-proxy/` |
| Nguồn | [TEST_PLAN.md v0.2](../TEST_PLAN.md) |

## Mục tiêu

Xác nhận nhanh sau mỗi lần triển khai: đăng nhập OIDC, tải 3 PDF, READY, và 3 loại câu trả lời (có nguồn, đa tài liệu, chưa đủ thông tin).

## Điều kiện tiên quyết

- Ứng dụng chạy tại http://localhost:8080/ (khởi động bằng `node evidence/app.ts start` trong `app/frontend`, hoặc `run.py` trong `app/`); `GET /api/v1/readyz` trả `ready`
- Có PDF mẫu trong `app/sample-pdfs/` (`hop-dong-A.pdf`, `chinh-sach-ban-hang-2026.pdf`, `bang-gia-Q4.pdf`, `ho-so-scan-2019.pdf`, `hop-dong-mat-khau.pdf`, `hop-dong-khoa-in.pdf`, `hong.pdf`, `bao-gia.docx`, `gia-mao.pdf`, `qua-nhieu-trang.pdf`)
- Đã chạy `npm install` và `npx playwright install ffmpeg` trong `app/frontend` (ghi video)
- Tài khoản mẫu **P1** – Nguyễn Lan (lan.nguyen@congty.vn, nhóm `aichat-users`)

## Dữ liệu test

- Không cần dữ liệu riêng

## Các bước thực hiện

| # | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Chạy smoke với URL http://localhost:8080 | `login ok: lan.nguyen@congty.vn` |
| 2 | Đối chiếu output tải lên | 3 file 201 (hoặc bỏ qua nếu đã có); 3 tài liệu READY |
| 3 | Đối chiếu câu "Bên B thanh toán…" | ANSWERED, nguồn (hop-dong-A.pdf, 2) |
| 4 | Đối chiếu câu "Giá gói Premium là bao nhiêu?" | ANSWERED, 2 nguồn: bảng giá Q4 và chính sách 2026 |
| 5 | Đối chiếu câu "Đối thủ … Nhật Bản…" | INSUFFICIENT |
| 6 | Mở http://localhost:8080/ bằng tài khoản P1 để chụp màn hình kết quả | 3 tài liệu Sẵn sàng; hội thoại có 3 lượt |

## Tiêu chí đạt

Mọi bước đạt kết quả mong đợi; không có lỗi Critical/High mới.

## Ghi chú

- Bước 6 (ảnh giao diện) chạy thêm spec ngắn bằng fixture hoặc chụp thủ công vào `screenshots/` của cùng thư mục

## Nhiệm vụ của agent (bắt buộc)

Agent thực hiện test case này **trên ứng dụng tại http://localhost:8080/** và phải tạo đủ bằng chứng sau trong thư mục **`./test_reports/E2E-003_smoke-dau-cuoi-qua-proxy/`** (tính từ thư mục gốc repo):

| Artifact | Vị trí | Yêu cầu |
|---|---|---|
| Test report | `test_reports/E2E-003_smoke-dau-cuoi-qua-proxy/report.md` (+ `result.json`) | Kết luận ĐẠT / KHÔNG ĐẠT / CẦN NGƯỜI XÁC NHẬN / BỊ CHẶN; bản build (commit); môi trường; bảng kết quả từng bước có link ảnh; link video; lỗi phát hiện |
| Ảnh chụp màn hình | `test_reports/E2E-003_smoke-dau-cuoi-qua-proxy/screenshots/NN-<bước>.png` | Ít nhất **1 ảnh cho mỗi bước** ở bảng trên, và 1 ảnh tại thời điểm lỗi nếu có |
| Video | `test_reports/E2E-003_smoke-dau-cuoi-qua-proxy/video/*.webm` | Ghi **toàn bộ quá trình test** từ bước 1 tới bước cuối, không cắt |
| Log | `test_reports/E2E-003_smoke-dau-cuoi-qua-proxy/logs/` | Output lệnh / request–response API / log ứng dụng liên quan |

**Quy trình:**

1. **Kiểm tra môi trường:** mở http://localhost:8080/ và gọi `GET http://localhost:8080/api/v1/readyz`, phải nhận `{"status":"ready"}`. Nếu không được, chạy `node evidence/app.ts start` trong `app/frontend` (lần đầu trên máy: chạy `run.py --sample` một lần để sinh PDF mẫu). Nếu vẫn không được, tạo report với kết luận **BỊ CHẶN – môi trường**, kèm ảnh/log lỗi, rồi dừng.
2. **Chạy lệnh qua bộ ghi bằng chứng:** trong `app/frontend`, chạy:

   ```bash
   node evidence/record-cli.ts --tc E2E-003_smoke-dau-cuoi-qua-proxy --title "Smoke đầu-cuối qua proxy" --cwd ../backend \
     --expect "login ok; 3 tài liệu READY; ANSWERED/ANSWERED/INSUFFICIENT" -- .venv/Scripts/python.exe scripts/smoke.py http://localhost:8080
   ```

   Bộ ghi hiển thị output trên một trang Edge và quay video, chụp ảnh khi kết thúc, lưu log và ghi `report.md`.
3. **Bổ sung report:** mở `test_reports/E2E-003_smoke-dau-cuoi-qua-proxy/report.md`, đối chiếu output với từng dòng ở bảng *Các bước thực hiện*, ghi kết quả từng dòng vào mục *Ghi chú / lỗi phát hiện*.

**Không được:** lưu artifact ngoài thư mục trên; sửa dữ liệu của người dùng khác ngoài tài khoản test đã nêu; đánh dấu ĐẠT khi còn bước chưa thực hiện. Mỗi lần chạy lại, kết quả cũ tự chuyển sang `test_reports/_archive/`.

**Lỗi phát hiện:** ghi vào report theo mẫu `DEF-T-xxx` (bước tái hiện, mong đợi, thực tế, ảnh/video, mức độ, yêu cầu bị ảnh hưởng: AC-01; AC-03; AC-04; AC-05; REG-005).
