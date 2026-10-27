# UI-001 – So sánh giao diện với thiết kế

| Trường | Giá trị |
|---|---|
| ID | UI-001 |
| Loại | UI/UX |
| Ưu tiên | Medium |
| Truy vết | html_design S01–S11; OBJ-003 |
| URL ứng dụng | http://localhost:8080/ |
| Cách thực hiện | Bán tự động – Playwright điều khiển trình duyệt và ghi bằng chứng; bước có đánh dấu 👤 cần người đánh giá |
| Test tự động hiện có | – (ảnh trong `guide/images`) |
| Trạng thái chu kỳ C1 | Đạt sơ bộ (thủ công) |
| Thư mục artifact | `./test_reports/UI-001_so-sanh-giao-dien-voi-thiet-ke/` |
| Nguồn | [TEST_PLAN.md v0.2](../TEST_PLAN.md) |

## Mục tiêu

Xác nhận 11 màn hình triển khai khớp thiết kế về bố cục, chữ và trạng thái.

## Điều kiện tiên quyết

- Ứng dụng chạy tại http://localhost:8080/ (khởi động bằng `node evidence/app.ts start` trong `app/frontend`, hoặc `run.py` trong `app/`); `GET /api/v1/readyz` trả `ready`
- Đã chạy `npm install` và `npx playwright install ffmpeg` trong `app/frontend` (ghi video)
- Tài khoản mẫu **P1** – Nguyễn Lan (lan.nguyen@congty.vn, nhóm `aichat-users`)
- Tài khoản mẫu **P2** – Trần Minh (minh.tran@congty.vn, nhóm `aichat-users`)
- Có PDF mẫu trong `app/sample-pdfs/` (`hop-dong-A.pdf`, `chinh-sach-ban-hang-2026.pdf`, `bang-gia-Q4.pdf`, `ho-so-scan-2019.pdf`, `hop-dong-mat-khau.pdf`, `hop-dong-khoa-in.pdf`, `hong.pdf`, `bao-gia.docx`, `gia-mao.pdf`, `qua-nhieu-trang.pdf`)

## Dữ liệu test

- Không cần dữ liệu riêng

## Các bước thực hiện

| # | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Với mỗi màn hình S01–S11: mở thiết kế `doc/04-design/html_design/Sxx_*.html` và tái tạo trạng thái tương ứng trên http://localhost:8080/ | Có 2 ảnh cùng kích thước 1440×900 cho mỗi màn hình |
| 2 | Ghép ảnh thiết kế/thực tế cạnh nhau (lưu `screenshots/Sxx-so-sanh.png`) | 11 ảnh so sánh |
| 3 | 👤 Designer đánh giá từng cặp: bố cục, chữ, trạng thái | Khớp; khác biệt được ghi lại kèm mức độ |

## Tiêu chí đạt

Mọi bước đạt kết quả mong đợi; không có lỗi Critical/High mới.

## Nhiệm vụ của agent (bắt buộc)

Agent thực hiện test case này **trên ứng dụng tại http://localhost:8080/** và phải tạo đủ bằng chứng sau trong thư mục **`./test_reports/UI-001_so-sanh-giao-dien-voi-thiet-ke/`** (tính từ thư mục gốc repo):

| Artifact | Vị trí | Yêu cầu |
|---|---|---|
| Test report | `test_reports/UI-001_so-sanh-giao-dien-voi-thiet-ke/report.md` (+ `result.json`) | Kết luận ĐẠT / KHÔNG ĐẠT / CẦN NGƯỜI XÁC NHẬN / BỊ CHẶN; bản build (commit); môi trường; bảng kết quả từng bước có link ảnh; link video; lỗi phát hiện |
| Ảnh chụp màn hình | `test_reports/UI-001_so-sanh-giao-dien-voi-thiet-ke/screenshots/NN-<bước>.png` | Ít nhất **1 ảnh cho mỗi bước** ở bảng trên, và 1 ảnh tại thời điểm lỗi nếu có |
| Video | `test_reports/UI-001_so-sanh-giao-dien-voi-thiet-ke/video/*.webm` | Ghi **toàn bộ quá trình test** từ bước 1 tới bước cuối, không cắt |
| Log | `test_reports/UI-001_so-sanh-giao-dien-voi-thiet-ke/logs/` | Output lệnh / request–response API / log ứng dụng liên quan |

**Quy trình:**

1. **Kiểm tra môi trường:** mở http://localhost:8080/ và gọi `GET http://localhost:8080/api/v1/readyz`, phải nhận `{"status":"ready"}`. Nếu không được, chạy `node evidence/app.ts start` trong `app/frontend` (lần đầu trên máy: chạy `run.py --sample` một lần để sinh PDF mẫu). Nếu vẫn không được, tạo report với kết luận **BỊ CHẶN – môi trường**, kèm ảnh/log lỗi, rồi dừng.
2. **Viết spec** `app/frontend/testcases/UI-001_so-sanh-giao-dien-voi-thiet-ke.spec.ts`, import `test`/`expect` từ `../evidence/fixture`. Mỗi dòng ở bảng *Các bước thực hiện* là một lời gọi `ev.step('<thao tác>', '<kết quả mong đợi>', async () => {…})`. Dùng `ev.login('p1'|'p2'|'admin'|'outsider')` để đăng nhập và `ev.api(method, '/api/v1/…', {json|multipart})` để gọi API (dùng cookie phiên của trình duyệt, tự thêm `X-CSRF-Token`). Spec mẫu: `testcases/E2E-002_*.spec.ts` (giao diện) và `testcases/API-023_*.spec.ts` (API).
3. **Chạy:** trong `app/frontend`, chạy `npx playwright test -c playwright.testcases.config.ts UI-001_so-sanh-giao-dien-voi-thiet-ke`. Fixture tự ghi video của mọi tab, chụp ảnh sau mỗi bước (kể cả khi lỗi), và ghi `report.md`/`result.json` vào `test_reports/UI-001_so-sanh-giao-dien-voi-thiet-ke/`.
4. **Bước cần người đánh giá (👤):** gọi `ev.step(…, { review: true })` để report đánh dấu *Cần người xác nhận*. Người đánh giá xem ảnh/video, điền *Kết quả thực tế* vào `report.md` và đổi kết luận. Nếu bước cần công cụ ngoài trình duyệt (NVDA, so sánh với `html_design`), quay toàn màn hình bằng Xbox Game Bar (Win + Alt + R) hoặc OBS và lưu vào `video/` của test case.

**Không được:** lưu artifact ngoài thư mục trên; sửa dữ liệu của người dùng khác ngoài tài khoản test đã nêu; đánh dấu ĐẠT khi còn bước chưa thực hiện. Mỗi lần chạy lại, kết quả cũ tự chuyển sang `test_reports/_archive/`.

**Lỗi phát hiện:** ghi vào report theo mẫu `DEF-T-xxx` (bước tái hiện, mong đợi, thực tế, ảnh/video, mức độ, yêu cầu bị ảnh hưởng: html_design S01–S11; OBJ-003).
