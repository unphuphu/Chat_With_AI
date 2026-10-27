# UT-015 – Xác thực id_token OIDC

| Trường | Giá trị |
|---|---|
| ID | UT-015 |
| Loại | Unit |
| Ưu tiên | Critical |
| Truy vết | US-023; NFR-010; SEC-001 |
| URL ứng dụng | http://localhost:8080/ |
| Cách thực hiện | Tự động – dòng lệnh, ghi bằng `app/frontend/evidence/record-cli.ts` |
| Test tự động hiện có | – (cần viết) |
| Trạng thái chu kỳ C1 | Chưa chạy |
| Thư mục artifact | `./test_reports/UT-015_xac-thuc-id-token-oidc/` |
| Nguồn | [TEST_PLAN.md v0.2](../TEST_PLAN.md) |

## Mục tiêu

Xác nhận adapter OIDC từ chối id_token sai issuer, sai audience, sai nonce, hết hạn, hoặc sai chữ ký; và xử lý được khi JWKS xoay khóa.

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
| 2 | Chạy `tests/unit/test_oidc.py` qua bộ ghi bằng chứng | pytest báo `passed`, mã thoát 0 |
| 3 | Đối chiếu: token hợp lệ (RS256, khóa trong JWKS giả) → IdTokenClaims đúng email/groups | Đúng |
| 4 | Đối chiếu: sai `iss`, sai `aud`, sai `nonce`, `exp` quá hạn, ký bằng khóa khác → IdentityError | Đúng |
| 5 | Đối chiếu: `kid` mới không có trong cache → tải lại JWKS một lần rồi xác thực được | Test đạt |

## Tiêu chí đạt

Mọi bước đạt kết quả mong đợi; không có lỗi Critical/High mới.

## Nhiệm vụ của agent (bắt buộc)

Agent thực hiện test case này **trên ứng dụng tại http://localhost:8080/** và phải tạo đủ bằng chứng sau trong thư mục **`./test_reports/UT-015_xac-thuc-id-token-oidc/`** (tính từ thư mục gốc repo):

| Artifact | Vị trí | Yêu cầu |
|---|---|---|
| Test report | `test_reports/UT-015_xac-thuc-id-token-oidc/report.md` (+ `result.json`) | Kết luận ĐẠT / KHÔNG ĐẠT / CẦN NGƯỜI XÁC NHẬN / BỊ CHẶN; bản build (commit); môi trường; bảng kết quả từng bước có link ảnh; link video; lỗi phát hiện |
| Ảnh chụp màn hình | `test_reports/UT-015_xac-thuc-id-token-oidc/screenshots/NN-<bước>.png` | Ít nhất **1 ảnh cho mỗi bước** ở bảng trên, và 1 ảnh tại thời điểm lỗi nếu có |
| Video | `test_reports/UT-015_xac-thuc-id-token-oidc/video/*.webm` | Ghi **toàn bộ quá trình test** từ bước 1 tới bước cuối, không cắt |
| Log | `test_reports/UT-015_xac-thuc-id-token-oidc/logs/` | Output lệnh / request–response API / log ứng dụng liên quan |

**Quy trình:**

1. **Kiểm tra môi trường:** mở http://localhost:8080/ và gọi `GET http://localhost:8080/api/v1/readyz`, phải nhận `{"status":"ready"}`. Nếu không được, chạy `node evidence/app.ts start` trong `app/frontend` (lần đầu trên máy: chạy `run.py --sample` một lần để sinh PDF mẫu). Nếu vẫn không được, tạo report với kết luận **BỊ CHẶN – môi trường**, kèm ảnh/log lỗi, rồi dừng.
2. **Viết test trước:** test tự động chưa có. Viết `app/backend/tests/unit/test_oidc.py` (tạo khóa RSA bằng `cryptography`, ký bằng PyJWT, giả lập discovery/JWKS bằng `httpx.MockTransport`), kiểm tra đúng các kết quả mong đợi ở bảng *Các bước thực hiện*.
3. **Chạy lệnh qua bộ ghi bằng chứng:** trong `app/frontend`, chạy:

   ```bash
   node evidence/record-cli.ts --tc UT-015_xac-thuc-id-token-oidc --title "Xác thực id_token OIDC" --cwd ../backend \
     --expect "Lệnh kết thúc với mã 0" -- .venv/Scripts/python.exe -m pytest -v -p no:cacheprovider tests/unit/test_oidc.py
   ```

   Bộ ghi hiển thị output trên một trang Edge và quay video, chụp ảnh khi kết thúc, lưu log và ghi `report.md`.
4. **Bổ sung report:** mở `test_reports/UT-015_xac-thuc-id-token-oidc/report.md`, đối chiếu output với từng dòng ở bảng *Các bước thực hiện*, ghi kết quả từng dòng vào mục *Ghi chú / lỗi phát hiện*.

**Không được:** lưu artifact ngoài thư mục trên; sửa dữ liệu của người dùng khác ngoài tài khoản test đã nêu; đánh dấu ĐẠT khi còn bước chưa thực hiện. Mỗi lần chạy lại, kết quả cũ tự chuyển sang `test_reports/_archive/`.

**Lỗi phát hiện:** ghi vào report theo mẫu `DEF-T-xxx` (bước tái hiện, mong đợi, thực tế, ảnh/video, mức độ, yêu cầu bị ảnh hưởng: US-023; NFR-010; SEC-001).
