# INT-015 – Adapter tích hợp thật (OIDC, blob, embedding, LLM)

| Trường | Giá trị |
|---|---|
| ID | INT-015 |
| Loại | Integration |
| Ưu tiên | High |
| Truy vết | SI-005; US-023; NFR-011 |
| URL ứng dụng | http://localhost:8080/ |
| Cách thực hiện | Tự động/bán tự động – kết quả chính thức cần ENV-STAGING; trên localhost chỉ để tham khảo |
| Test tự động hiện có | – (cần viết) |
| Trạng thái chu kỳ C1 | Một phần (smoke đạt 26/10) |
| Thư mục artifact | `./test_reports/INT-015_adapter-tich-hop-that-oidc-blob-embedding-llm/` |
| Nguồn | [TEST_PLAN.md v0.2](../TEST_PLAN.md) |

## Mục tiêu

Xác nhận các adapter thật hoạt động với dịch vụ thật: OIDC (IdP giả lập chạy thật), lưu file cục bộ, embedding HTTP, Anthropic.

## Điều kiện tiên quyết

- Backend venv `app/backend/.venv` đã cài `requirements.txt`; có Node.js (test tự khởi động PostgreSQL PGlite trong bộ nhớ)
- Đã chạy `npm install` và `npx playwright install ffmpeg` trong `app/frontend` (ghi video)
- Ứng dụng chạy tại http://localhost:8080/ (khởi động bằng `node evidence/app.ts start` trong `app/frontend`, hoặc `run.py` trong `app/`); `GET /api/v1/readyz` trả `ready` (để ghi bản build đang kiểm thử)

## Dữ liệu test

- `app/sample-pdfs/` (smoke tự tải 3 PDF vào tài khoản P1)

## Các bước thực hiện

| # | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Kiểm tra môi trường tại http://localhost:8080/ và ghi commit đang kiểm thử | readyz = ready; report có mã commit |
| 2 | Chạy `scripts/smoke.py http://localhost:8080` qua bộ ghi bằng chứng | pytest báo `passed`, mã thoát 0 |
| 3 | Đối chiếu smoke: đăng nhập OIDC qua http://localhost:8080 → IdP :8090 thành công | `login ok` |
| 4 | Đối chiếu smoke: tải 3 PDF → READY (blob local); 3 câu hỏi có kết quả ANSWERED/INSUFFICIENT | Đúng |
| 5 | (staging) Chạy lại với `EMBEDDING_PROVIDER=http` (bge-m3) và `LLM_PROVIDER=anthropic` | Câu trả lời có nguồn, không lỗi 503 |

## Tiêu chí đạt

Mọi bước đạt kết quả mong đợi; không có lỗi Critical/High mới.

## Lệnh / công cụ

- `node evidence/record-cli.ts --tc <thư mục> --title "…" --cwd ../backend -- .venv/Scripts/python.exe scripts/smoke.py http://localhost:8080`

## Ghi chú

- Phần embedding HTTP và Anthropic cần endpoint/API key được IT/Security duyệt – chỉ chạy trên ENV-STAGING

## Nhiệm vụ của agent (bắt buộc)

Agent thực hiện test case này **trên ứng dụng tại http://localhost:8080/** và phải tạo đủ bằng chứng sau trong thư mục **`./test_reports/INT-015_adapter-tich-hop-that-oidc-blob-embedding-llm/`** (tính từ thư mục gốc repo):

| Artifact | Vị trí | Yêu cầu |
|---|---|---|
| Test report | `test_reports/INT-015_adapter-tich-hop-that-oidc-blob-embedding-llm/report.md` (+ `result.json`) | Kết luận ĐẠT / KHÔNG ĐẠT / CẦN NGƯỜI XÁC NHẬN / BỊ CHẶN; bản build (commit); môi trường; bảng kết quả từng bước có link ảnh; link video; lỗi phát hiện |
| Ảnh chụp màn hình | `test_reports/INT-015_adapter-tich-hop-that-oidc-blob-embedding-llm/screenshots/NN-<bước>.png` | Ít nhất **1 ảnh cho mỗi bước** ở bảng trên, và 1 ảnh tại thời điểm lỗi nếu có |
| Video | `test_reports/INT-015_adapter-tich-hop-that-oidc-blob-embedding-llm/video/*.webm` | Ghi **toàn bộ quá trình test** từ bước 1 tới bước cuối, không cắt |
| Log | `test_reports/INT-015_adapter-tich-hop-that-oidc-blob-embedding-llm/logs/` | Output lệnh / request–response API / log ứng dụng liên quan |

**Quy trình:**

1. **Kiểm tra môi trường:** mở http://localhost:8080/ và gọi `GET http://localhost:8080/api/v1/readyz`, phải nhận `{"status":"ready"}`. Nếu không được, chạy `node evidence/app.ts start` trong `app/frontend` (lần đầu trên máy: chạy `run.py --sample` một lần để sinh PDF mẫu). Nếu vẫn không được, tạo report với kết luận **BỊ CHẶN – môi trường**, kèm ảnh/log lỗi, rồi dừng.
2. **Chạy công cụ** nêu ở mục *Lệnh / công cụ* qua bộ ghi dòng lệnh: `node evidence/record-cli.ts --tc INT-015_adapter-tich-hop-that-oidc-blob-embedding-llm --title "Adapter tích hợp thật (OIDC, blob, embedding, LLM)" -- <lệnh>`. Với k6/ZAP thì đặt `BASE_URL=http://localhost:8080/`.
3. Kết quả trên localhost chỉ để **tham khảo**. Ghi rõ trong report: *“Chạy trên ENV-DEV – không dùng cho launch gate”*. Kết quả chính thức chạy lại trên ENV-STAGING với cùng thư mục artifact.

**Không được:** lưu artifact ngoài thư mục trên; sửa dữ liệu của người dùng khác ngoài tài khoản test đã nêu; đánh dấu ĐẠT khi còn bước chưa thực hiện. Mỗi lần chạy lại, kết quả cũ tự chuyển sang `test_reports/_archive/`.

**Lỗi phát hiện:** ghi vào report theo mẫu `DEF-T-xxx` (bước tái hiện, mong đợi, thực tế, ảnh/video, mức độ, yêu cầu bị ảnh hưởng: SI-005; US-023; NFR-011).
