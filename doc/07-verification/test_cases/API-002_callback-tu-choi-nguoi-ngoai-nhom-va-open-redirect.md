# API-002 – Callback từ chối người ngoài nhóm và open redirect

| Trường | Giá trị |
|---|---|
| ID | API-002 |
| Loại | API |
| Ưu tiên | Critical |
| Truy vết | US-023; SEC-002; SEC-003 |
| URL ứng dụng | http://localhost:8080/ |
| Cách thực hiện | Tự động – Playwright trên trình duyệt, ghi bằng `app/frontend/evidence/fixture.ts` |
| Test tự động hiện có | `test_outsider_denied_and_audited`, `test_open_redirect_blocked` |
| Trạng thái chu kỳ C1 | Đạt (tự động) |
| Thư mục artifact | `./test_reports/API-002_callback-tu-choi-nguoi-ngoai-nhom-va-open-redirect/` |
| Nguồn | [TEST_PLAN.md v0.2](../TEST_PLAN.md) |

## Mục tiêu

Xác nhận người không thuộc nhóm bị chuyển tới /access-denied, và `return_to` ra ngoài origin bị bỏ qua.

## Điều kiện tiên quyết

- Ứng dụng chạy tại http://localhost:8080/ (khởi động bằng `node evidence/app.ts start` trong `app/frontend`, hoặc `run.py` trong `app/`); `GET /api/v1/readyz` trả `ready`
- Đã chạy `npm install` và `npx playwright install ffmpeg` trong `app/frontend` (ghi video)
- Tài khoản mẫu **P1** – Nguyễn Lan (lan.nguyen@congty.vn, nhóm `aichat-users`)
- Tài khoản mẫu **Người ngoài nhóm** (khach@congty.vn, không thuộc nhóm nào)

## Dữ liệu test

- Không cần dữ liệu riêng

## Các bước thực hiện

| # | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Mở http://localhost:8080/api/v1/auth/login?return_to=https://evil.example rồi chọn P1 | Sau callback về http://localhost:8080/ (không tới evil.example) |
| 2 | Đăng xuất; mở http://localhost:8080/ và chọn *Người ngoài nhóm* | URL `/access-denied`; trang *Bạn chưa được cấp quyền* |
| 3 | `GET /api/v1/me` trong phiên trình duyệt đó | 401 `unauthenticated` – không có phiên |

## Tiêu chí đạt

Mọi bước đạt kết quả mong đợi; không có lỗi Critical/High mới.

## Nhiệm vụ của agent (bắt buộc)

Agent thực hiện test case này **trên ứng dụng tại http://localhost:8080/** và phải tạo đủ bằng chứng sau trong thư mục **`./test_reports/API-002_callback-tu-choi-nguoi-ngoai-nhom-va-open-redirect/`** (tính từ thư mục gốc repo):

| Artifact | Vị trí | Yêu cầu |
|---|---|---|
| Test report | `test_reports/API-002_callback-tu-choi-nguoi-ngoai-nhom-va-open-redirect/report.md` (+ `result.json`) | Kết luận ĐẠT / KHÔNG ĐẠT / CẦN NGƯỜI XÁC NHẬN / BỊ CHẶN; bản build (commit); môi trường; bảng kết quả từng bước có link ảnh; link video; lỗi phát hiện |
| Ảnh chụp màn hình | `test_reports/API-002_callback-tu-choi-nguoi-ngoai-nhom-va-open-redirect/screenshots/NN-<bước>.png` | Ít nhất **1 ảnh cho mỗi bước** ở bảng trên, và 1 ảnh tại thời điểm lỗi nếu có |
| Video | `test_reports/API-002_callback-tu-choi-nguoi-ngoai-nhom-va-open-redirect/video/*.webm` | Ghi **toàn bộ quá trình test** từ bước 1 tới bước cuối, không cắt |
| Log | `test_reports/API-002_callback-tu-choi-nguoi-ngoai-nhom-va-open-redirect/logs/` | Output lệnh / request–response API / log ứng dụng liên quan |

**Quy trình:**

1. **Kiểm tra môi trường:** mở http://localhost:8080/ và gọi `GET http://localhost:8080/api/v1/readyz`, phải nhận `{"status":"ready"}`. Nếu không được, chạy `node evidence/app.ts start` trong `app/frontend` (lần đầu trên máy: chạy `run.py --sample` một lần để sinh PDF mẫu). Nếu vẫn không được, tạo report với kết luận **BỊ CHẶN – môi trường**, kèm ảnh/log lỗi, rồi dừng.
2. **Viết spec** `app/frontend/testcases/API-002_callback-tu-choi-nguoi-ngoai-nhom-va-open-redirect.spec.ts`, import `test`/`expect` từ `../evidence/fixture`. Mỗi dòng ở bảng *Các bước thực hiện* là một lời gọi `ev.step('<thao tác>', '<kết quả mong đợi>', async () => {…})`. Dùng `ev.login('p1'|'p2'|'admin'|'outsider')` để đăng nhập và `ev.api(method, '/api/v1/…', {json|multipart})` để gọi API (dùng cookie phiên của trình duyệt, tự thêm `X-CSRF-Token`). Spec mẫu: `testcases/E2E-002_*.spec.ts` (giao diện) và `testcases/API-023_*.spec.ts` (API).
3. **Chạy:** trong `app/frontend`, chạy `npx playwright test -c playwright.testcases.config.ts API-002_callback-tu-choi-nguoi-ngoai-nhom-va-open-redirect`. Fixture tự ghi video của mọi tab, chụp ảnh sau mỗi bước (kể cả khi lỗi), và ghi `report.md`/`result.json` vào `test_reports/API-002_callback-tu-choi-nguoi-ngoai-nhom-va-open-redirect/`.

**Không được:** lưu artifact ngoài thư mục trên; sửa dữ liệu của người dùng khác ngoài tài khoản test đã nêu; đánh dấu ĐẠT khi còn bước chưa thực hiện. Mỗi lần chạy lại, kết quả cũ tự chuyển sang `test_reports/_archive/`.

**Lỗi phát hiện:** ghi vào report theo mẫu `DEF-T-xxx` (bước tái hiện, mong đợi, thực tế, ảnh/video, mức độ, yêu cầu bị ảnh hưởng: US-023; SEC-002; SEC-003).
