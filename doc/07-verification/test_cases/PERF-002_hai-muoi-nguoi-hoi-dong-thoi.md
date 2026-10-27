# PERF-002 – Hai mươi người hỏi đồng thời

| Trường | Giá trị |
|---|---|
| ID | PERF-002 |
| Loại | Performance |
| Ưu tiên | High |
| Truy vết | NFR-007; NFR-001; G-03 |
| URL ứng dụng | http://localhost:8080/ |
| Cách thực hiện | Tự động/bán tự động – kết quả chính thức cần ENV-STAGING; trên localhost chỉ để tham khảo |
| Test tự động hiện có | – |
| Trạng thái chu kỳ C1 | Bị chặn (staging) |
| Thư mục artifact | `./test_reports/PERF-002_hai-muoi-nguoi-hoi-dong-thoi/` |
| Nguồn | [TEST_PLAN.md v0.2](../TEST_PLAN.md) |

## Mục tiêu

Xác nhận NFR-001 vẫn đạt khi 20 người dùng hỏi đồng thời trong 15 phút.

## Điều kiện tiên quyết

- Ứng dụng chạy tại http://localhost:8080/ (khởi động bằng `node evidence/app.ts start` trong `app/frontend`, hoặc `run.py` trong `app/`); `GET /api/v1/readyz` trả `ready`
- Đã chạy `npm install` và `npx playwright install ffmpeg` trong `app/frontend` (ghi video)
- Kết quả chính thức chạy trên ENV-STAGING (cấu hình theo TEST_PLAN 11.0); trên localhost (PGlite, LLM trích xuất) chỉ để tham khảo

## Dữ liệu test

- Không cần dữ liệu riêng

## Các bước thực hiện

| # | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Chuẩn bị 20 tài khoản test, mỗi tài khoản 100 tài liệu | Sẵn sàng |
| 2 | k6: 20 VU, mỗi VU hỏi liên tục (nghỉ 5–10 s giữa các câu, dưới rate limit 10 câu/phút) trong 15 phút | Hoàn tất |
| 3 | Đọc kết quả | p90 ≤ 15 s; tỉ lệ lỗi < 1%; không có 5xx ngoài 503 do circuit breaker |
| 4 | Ghi CPU/RAM của api, worker, embedding, PostgreSQL trong lúc chạy | Không thành phần nào > 85% CPU kéo dài |

## Tiêu chí đạt

Đạt ngưỡng nêu ở bảng bước **trên ENV-STAGING**. Kết quả chạy trên localhost chỉ ghi nhận, không dùng cho launch gate.

## Lệnh / công cụ

- k6 (ghim phiên bản khi cài) – script đặt tại `app/perf/<id>.js`, chạy `k6 run -e BASE_URL=http://localhost:8080 app/perf/<id>.js --summary-export logs/summary.json`

## Nhiệm vụ của agent (bắt buộc)

Agent thực hiện test case này **trên ứng dụng tại http://localhost:8080/** và phải tạo đủ bằng chứng sau trong thư mục **`./test_reports/PERF-002_hai-muoi-nguoi-hoi-dong-thoi/`** (tính từ thư mục gốc repo):

| Artifact | Vị trí | Yêu cầu |
|---|---|---|
| Test report | `test_reports/PERF-002_hai-muoi-nguoi-hoi-dong-thoi/report.md` (+ `result.json`) | Kết luận ĐẠT / KHÔNG ĐẠT / CẦN NGƯỜI XÁC NHẬN / BỊ CHẶN; bản build (commit); môi trường; bảng kết quả từng bước có link ảnh; link video; lỗi phát hiện |
| Ảnh chụp màn hình | `test_reports/PERF-002_hai-muoi-nguoi-hoi-dong-thoi/screenshots/NN-<bước>.png` | Ít nhất **1 ảnh cho mỗi bước** ở bảng trên, và 1 ảnh tại thời điểm lỗi nếu có |
| Video | `test_reports/PERF-002_hai-muoi-nguoi-hoi-dong-thoi/video/*.webm` | Ghi **toàn bộ quá trình test** từ bước 1 tới bước cuối, không cắt |
| Log | `test_reports/PERF-002_hai-muoi-nguoi-hoi-dong-thoi/logs/` | Output lệnh / request–response API / log ứng dụng liên quan |

**Quy trình:**

1. **Kiểm tra môi trường:** mở http://localhost:8080/ và gọi `GET http://localhost:8080/api/v1/readyz`, phải nhận `{"status":"ready"}`. Nếu không được, chạy `node evidence/app.ts start` trong `app/frontend` (lần đầu trên máy: chạy `run.py --sample` một lần để sinh PDF mẫu). Nếu vẫn không được, tạo report với kết luận **BỊ CHẶN – môi trường**, kèm ảnh/log lỗi, rồi dừng.
2. **Chạy công cụ** nêu ở mục *Lệnh / công cụ* qua bộ ghi dòng lệnh: `node evidence/record-cli.ts --tc PERF-002_hai-muoi-nguoi-hoi-dong-thoi --title "Hai mươi người hỏi đồng thời" -- <lệnh>`. Với k6/ZAP thì đặt `BASE_URL=http://localhost:8080/`.
3. Kết quả trên localhost chỉ để **tham khảo**. Ghi rõ trong report: *“Chạy trên ENV-DEV – không dùng cho launch gate”*. Kết quả chính thức chạy lại trên ENV-STAGING với cùng thư mục artifact.

**Không được:** lưu artifact ngoài thư mục trên; sửa dữ liệu của người dùng khác ngoài tài khoản test đã nêu; đánh dấu ĐẠT khi còn bước chưa thực hiện. Mỗi lần chạy lại, kết quả cũ tự chuyển sang `test_reports/_archive/`.

**Lỗi phát hiện:** ghi vào report theo mẫu `DEF-T-xxx` (bước tái hiện, mong đợi, thực tế, ảnh/video, mức độ, yêu cầu bị ảnh hưởng: NFR-007; NFR-001; G-03).
