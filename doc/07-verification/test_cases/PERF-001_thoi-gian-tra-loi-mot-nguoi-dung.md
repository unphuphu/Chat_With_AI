# PERF-001 – Thời gian trả lời một người dùng

| Trường | Giá trị |
|---|---|
| ID | PERF-001 |
| Loại | Performance |
| Ưu tiên | High |
| Truy vết | NFR-001; G-03 |
| URL ứng dụng | http://localhost:8080/ |
| Cách thực hiện | Tự động/bán tự động – kết quả chính thức cần ENV-STAGING; trên localhost chỉ để tham khảo |
| Test tự động hiện có | – |
| Trạng thái chu kỳ C1 | Bị chặn (staging) |
| Thư mục artifact | `./test_reports/PERF-001_thoi-gian-tra-loi-mot-nguoi-dung/` |
| Nguồn | [TEST_PLAN.md v0.2](../TEST_PLAN.md) |

## Mục tiêu

Đo p50/p90 thời gian trả lời trên 50 câu hỏi với tài khoản có 100 tài liệu Sẵn sàng.

## Điều kiện tiên quyết

- Ứng dụng chạy tại http://localhost:8080/ (khởi động bằng `node evidence/app.ts start` trong `app/frontend`, hoặc `run.py` trong `app/`); `GET /api/v1/readyz` trả `ready`
- Đã chạy `npm install` và `npx playwright install ffmpeg` trong `app/frontend` (ghi video)
- Bộ câu hỏi chuẩn DEP-005 (`test-data/questions.csv`: id, loại [trong tài liệu / đa tài liệu / ngoài tài liệu / tiếp nối], câu hỏi, đáp án chuẩn, tài liệu + trang nguồn) – **chưa có, chờ PO**
- Kết quả chính thức chạy trên ENV-STAGING (cấu hình theo TEST_PLAN 11.0); trên localhost (PGlite, LLM trích xuất) chỉ để tham khảo

## Dữ liệu test

- Không cần dữ liệu riêng

## Các bước thực hiện

| # | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Chuẩn bị tài khoản test có 100 tài liệu Sẵn sàng (script tải hàng loạt) | `GET /me` → documents_used = 100 |
| 2 | Chạy k6: 1 VU gửi lần lượt 50 câu hỏi từ bộ câu hỏi chuẩn, đo thời gian từ gửi tới khi nhận phản hồi hoàn chỉnh | 50 phản hồi 200 |
| 3 | Đọc `logs/summary.json` | p50 ≤ 8 s, p90 ≤ 15 s |
| 4 | Đối chiếu với `latency_ms` trong analytics `answer_returned` | Sai lệch < 10% |

## Tiêu chí đạt

Đạt ngưỡng nêu ở bảng bước **trên ENV-STAGING**. Kết quả chạy trên localhost chỉ ghi nhận, không dùng cho launch gate.

## Lệnh / công cụ

- k6 (ghim phiên bản khi cài) – script đặt tại `app/perf/<id>.js`, chạy `k6 run -e BASE_URL=http://localhost:8080 app/perf/<id>.js --summary-export logs/summary.json`

## Nhiệm vụ của agent (bắt buộc)

Agent thực hiện test case này **trên ứng dụng tại http://localhost:8080/** và phải tạo đủ bằng chứng sau trong thư mục **`./test_reports/PERF-001_thoi-gian-tra-loi-mot-nguoi-dung/`** (tính từ thư mục gốc repo):

| Artifact | Vị trí | Yêu cầu |
|---|---|---|
| Test report | `test_reports/PERF-001_thoi-gian-tra-loi-mot-nguoi-dung/report.md` (+ `result.json`) | Kết luận ĐẠT / KHÔNG ĐẠT / CẦN NGƯỜI XÁC NHẬN / BỊ CHẶN; bản build (commit); môi trường; bảng kết quả từng bước có link ảnh; link video; lỗi phát hiện |
| Ảnh chụp màn hình | `test_reports/PERF-001_thoi-gian-tra-loi-mot-nguoi-dung/screenshots/NN-<bước>.png` | Ít nhất **1 ảnh cho mỗi bước** ở bảng trên, và 1 ảnh tại thời điểm lỗi nếu có |
| Video | `test_reports/PERF-001_thoi-gian-tra-loi-mot-nguoi-dung/video/*.webm` | Ghi **toàn bộ quá trình test** từ bước 1 tới bước cuối, không cắt |
| Log | `test_reports/PERF-001_thoi-gian-tra-loi-mot-nguoi-dung/logs/` | Output lệnh / request–response API / log ứng dụng liên quan |

**Quy trình:**

1. **Kiểm tra môi trường:** mở http://localhost:8080/ và gọi `GET http://localhost:8080/api/v1/readyz`, phải nhận `{"status":"ready"}`. Nếu không được, chạy `node evidence/app.ts start` trong `app/frontend` (lần đầu trên máy: chạy `run.py --sample` một lần để sinh PDF mẫu). Nếu vẫn không được, tạo report với kết luận **BỊ CHẶN – môi trường**, kèm ảnh/log lỗi, rồi dừng.
2. **Chạy công cụ** nêu ở mục *Lệnh / công cụ* qua bộ ghi dòng lệnh: `node evidence/record-cli.ts --tc PERF-001_thoi-gian-tra-loi-mot-nguoi-dung --title "Thời gian trả lời một người dùng" -- <lệnh>`. Với k6/ZAP thì đặt `BASE_URL=http://localhost:8080/`.
3. Kết quả trên localhost chỉ để **tham khảo**. Ghi rõ trong report: *“Chạy trên ENV-DEV – không dùng cho launch gate”*. Kết quả chính thức chạy lại trên ENV-STAGING với cùng thư mục artifact.

**Không được:** lưu artifact ngoài thư mục trên; sửa dữ liệu của người dùng khác ngoài tài khoản test đã nêu; đánh dấu ĐẠT khi còn bước chưa thực hiện. Mỗi lần chạy lại, kết quả cũ tự chuyển sang `test_reports/_archive/`.

**Lỗi phát hiện:** ghi vào report theo mẫu `DEF-T-xxx` (bước tái hiện, mong đợi, thực tế, ảnh/video, mức độ, yêu cầu bị ảnh hưởng: NFR-001; G-03).
