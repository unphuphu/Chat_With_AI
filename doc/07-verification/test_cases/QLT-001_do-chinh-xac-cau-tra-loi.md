# QLT-001 – Độ chính xác câu trả lời

| Trường | Giá trị |
|---|---|
| ID | QLT-001 |
| Loại | Chất lượng câu trả lời |
| Ưu tiên | High |
| Truy vết | NFR-003; MET-002; G-02; TR-01 |
| URL ứng dụng | http://localhost:8080/ |
| Cách thực hiện | Tự động/bán tự động – kết quả chính thức cần ENV-STAGING; trên localhost chỉ để tham khảo |
| Test tự động hiện có | – |
| Trạng thái chu kỳ C1 | Bị chặn (DEP-005) |
| Thư mục artifact | `./test_reports/QLT-001_do-chinh-xac-cau-tra-loi/` |
| Nguồn | [TEST_PLAN.md v0.2](../TEST_PLAN.md) |

## Mục tiêu

Đo tỉ lệ câu trả lời đúng trên ≥ 50 câu hỏi có đáp án trong tài liệu.

## Điều kiện tiên quyết

- Ứng dụng chạy tại http://localhost:8080/ (khởi động bằng `node evidence/app.ts start` trong `app/frontend`, hoặc `run.py` trong `app/`); `GET /api/v1/readyz` trả `ready`
- Đã chạy `npm install` và `npx playwright install ffmpeg` trong `app/frontend` (ghi video)
- Bộ câu hỏi chuẩn DEP-005 (`test-data/questions.csv`: id, loại [trong tài liệu / đa tài liệu / ngoài tài liệu / tiếp nối], câu hỏi, đáp án chuẩn, tài liệu + trang nguồn) – **chưa có, chờ PO**
- Kết quả chính thức chạy trên ENV-STAGING (cấu hình theo TEST_PLAN 11.0); trên localhost (PGlite, LLM trích xuất) chỉ để tham khảo
- Tài liệu dự án thật – lưu ngoài repo, xóa sau nghiệm thu

## Dữ liệu test

- Không cần dữ liệu riêng

## Các bước thực hiện

| # | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Tải bộ tài liệu dự án thật đã được PO duyệt vào tài khoản test | Mọi tài liệu Sẵn sàng |
| 2 | Chạy script đánh giá (T06-03): gửi từng câu hỏi loại "trong tài liệu", lưu câu trả lời + nguồn vào `logs/answers.csv` | ≥ 50 dòng |
| 3 | 👤 2 người dùng nghiệp vụ chấm độc lập: Đúng / Đúng một phần / Sai / Bịa | Bảng chấm `logs/grading.csv` |
| 4 | Tính tỉ lệ Đúng (bất đồng → người thứ 3 quyết định) | ≥ 80% |

## Tiêu chí đạt

Đạt ngưỡng nêu ở bảng bước **trên ENV-STAGING**. Kết quả chạy trên localhost chỉ ghi nhận, không dùng cho launch gate.

## Lệnh / công cụ

- Script đánh giá `app/backend/scripts/eval_rag.py` (cần viết – T06-03): đọc CSV, gọi API qua phiên đăng nhập như `smoke.py`, ghi kết quả

## Nhiệm vụ của agent (bắt buộc)

Agent thực hiện test case này **trên ứng dụng tại http://localhost:8080/** và phải tạo đủ bằng chứng sau trong thư mục **`./test_reports/QLT-001_do-chinh-xac-cau-tra-loi/`** (tính từ thư mục gốc repo):

| Artifact | Vị trí | Yêu cầu |
|---|---|---|
| Test report | `test_reports/QLT-001_do-chinh-xac-cau-tra-loi/report.md` (+ `result.json`) | Kết luận ĐẠT / KHÔNG ĐẠT / CẦN NGƯỜI XÁC NHẬN / BỊ CHẶN; bản build (commit); môi trường; bảng kết quả từng bước có link ảnh; link video; lỗi phát hiện |
| Ảnh chụp màn hình | `test_reports/QLT-001_do-chinh-xac-cau-tra-loi/screenshots/NN-<bước>.png` | Ít nhất **1 ảnh cho mỗi bước** ở bảng trên, và 1 ảnh tại thời điểm lỗi nếu có |
| Video | `test_reports/QLT-001_do-chinh-xac-cau-tra-loi/video/*.webm` | Ghi **toàn bộ quá trình test** từ bước 1 tới bước cuối, không cắt |
| Log | `test_reports/QLT-001_do-chinh-xac-cau-tra-loi/logs/` | Output lệnh / request–response API / log ứng dụng liên quan |

**Quy trình:**

1. **Kiểm tra môi trường:** mở http://localhost:8080/ và gọi `GET http://localhost:8080/api/v1/readyz`, phải nhận `{"status":"ready"}`. Nếu không được, chạy `node evidence/app.ts start` trong `app/frontend` (lần đầu trên máy: chạy `run.py --sample` một lần để sinh PDF mẫu). Nếu vẫn không được, tạo report với kết luận **BỊ CHẶN – môi trường**, kèm ảnh/log lỗi, rồi dừng.
2. **Chạy công cụ** nêu ở mục *Lệnh / công cụ* qua bộ ghi dòng lệnh: `node evidence/record-cli.ts --tc QLT-001_do-chinh-xac-cau-tra-loi --title "Độ chính xác câu trả lời" -- <lệnh>`. Với k6/ZAP thì đặt `BASE_URL=http://localhost:8080/`.
3. Kết quả trên localhost chỉ để **tham khảo**. Ghi rõ trong report: *“Chạy trên ENV-DEV – không dùng cho launch gate”*. Kết quả chính thức chạy lại trên ENV-STAGING với cùng thư mục artifact.

**Không được:** lưu artifact ngoài thư mục trên; sửa dữ liệu của người dùng khác ngoài tài khoản test đã nêu; đánh dấu ĐẠT khi còn bước chưa thực hiện. Mỗi lần chạy lại, kết quả cũ tự chuyển sang `test_reports/_archive/`.

**Lỗi phát hiện:** ghi vào report theo mẫu `DEF-T-xxx` (bước tái hiện, mong đợi, thực tế, ảnh/video, mức độ, yêu cầu bị ảnh hưởng: NFR-003; MET-002; G-02; TR-01).
