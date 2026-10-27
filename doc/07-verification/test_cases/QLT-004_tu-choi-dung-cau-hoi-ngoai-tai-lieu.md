# QLT-004 – Từ chối đúng câu hỏi ngoài tài liệu

| Trường | Giá trị |
|---|---|
| ID | QLT-004 |
| Loại | Chất lượng câu trả lời |
| Ưu tiên | High |
| Truy vết | NFR-005; MET-005; US-016; G-02 |
| URL ứng dụng | http://localhost:8080/ |
| Cách thực hiện | Tự động/bán tự động – kết quả chính thức cần ENV-STAGING; trên localhost chỉ để tham khảo |
| Test tự động hiện có | – |
| Trạng thái chu kỳ C1 | Bị chặn (DEP-005) |
| Thư mục artifact | `./test_reports/QLT-004_tu-choi-dung-cau-hoi-ngoai-tai-lieu/` |
| Nguồn | [TEST_PLAN.md v0.2](../TEST_PLAN.md) |

## Mục tiêu

Đo tỉ lệ trả lời *Chưa đủ thông tin* trên ≥ 20 câu hỏi ngoài tài liệu.

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
| 1 | Chạy script với các câu loại "ngoài tài liệu" | ≥ 20 kết quả |
| 2 | Đếm `status = INSUFFICIENT` | ≥ 90% |
| 3 | 👤 Với các câu không bị từ chối: kiểm tra có bịa thông tin không | Ghi lại từng trường hợp |

## Tiêu chí đạt

Đạt ngưỡng nêu ở bảng bước **trên ENV-STAGING**. Kết quả chạy trên localhost chỉ ghi nhận, không dùng cho launch gate.

## Lệnh / công cụ

- Script đánh giá `app/backend/scripts/eval_rag.py` (viết ở QLT-001 / T06-03) và bảng chấm `logs/grading.csv`; chạy qua `node evidence/record-cli.ts --tc <thư mục> --cwd ../backend -- .venv/Scripts/python.exe scripts/eval_rag.py …`

## Nhiệm vụ của agent (bắt buộc)

Agent thực hiện test case này **trên ứng dụng tại http://localhost:8080/** và phải tạo đủ bằng chứng sau trong thư mục **`./test_reports/QLT-004_tu-choi-dung-cau-hoi-ngoai-tai-lieu/`** (tính từ thư mục gốc repo):

| Artifact | Vị trí | Yêu cầu |
|---|---|---|
| Test report | `test_reports/QLT-004_tu-choi-dung-cau-hoi-ngoai-tai-lieu/report.md` (+ `result.json`) | Kết luận ĐẠT / KHÔNG ĐẠT / CẦN NGƯỜI XÁC NHẬN / BỊ CHẶN; bản build (commit); môi trường; bảng kết quả từng bước có link ảnh; link video; lỗi phát hiện |
| Ảnh chụp màn hình | `test_reports/QLT-004_tu-choi-dung-cau-hoi-ngoai-tai-lieu/screenshots/NN-<bước>.png` | Ít nhất **1 ảnh cho mỗi bước** ở bảng trên, và 1 ảnh tại thời điểm lỗi nếu có |
| Video | `test_reports/QLT-004_tu-choi-dung-cau-hoi-ngoai-tai-lieu/video/*.webm` | Ghi **toàn bộ quá trình test** từ bước 1 tới bước cuối, không cắt |
| Log | `test_reports/QLT-004_tu-choi-dung-cau-hoi-ngoai-tai-lieu/logs/` | Output lệnh / request–response API / log ứng dụng liên quan |

**Quy trình:**

1. **Kiểm tra môi trường:** mở http://localhost:8080/ và gọi `GET http://localhost:8080/api/v1/readyz`, phải nhận `{"status":"ready"}`. Nếu không được, chạy `node evidence/app.ts start` trong `app/frontend` (lần đầu trên máy: chạy `run.py --sample` một lần để sinh PDF mẫu). Nếu vẫn không được, tạo report với kết luận **BỊ CHẶN – môi trường**, kèm ảnh/log lỗi, rồi dừng.
2. **Chạy công cụ** nêu ở mục *Lệnh / công cụ* qua bộ ghi dòng lệnh: `node evidence/record-cli.ts --tc QLT-004_tu-choi-dung-cau-hoi-ngoai-tai-lieu --title "Từ chối đúng câu hỏi ngoài tài liệu" -- <lệnh>`. Với k6/ZAP thì đặt `BASE_URL=http://localhost:8080/`.
3. Kết quả trên localhost chỉ để **tham khảo**. Ghi rõ trong report: *“Chạy trên ENV-DEV – không dùng cho launch gate”*. Kết quả chính thức chạy lại trên ENV-STAGING với cùng thư mục artifact.

**Không được:** lưu artifact ngoài thư mục trên; sửa dữ liệu của người dùng khác ngoài tài khoản test đã nêu; đánh dấu ĐẠT khi còn bước chưa thực hiện. Mỗi lần chạy lại, kết quả cũ tự chuyển sang `test_reports/_archive/`.

**Lỗi phát hiện:** ghi vào report theo mẫu `DEF-T-xxx` (bước tái hiện, mong đợi, thực tế, ảnh/video, mức độ, yêu cầu bị ảnh hưởng: NFR-005; MET-005; US-016; G-02).
