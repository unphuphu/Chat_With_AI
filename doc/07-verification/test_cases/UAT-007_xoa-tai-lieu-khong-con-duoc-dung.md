# UAT-007 – Xóa tài liệu không còn được dùng

| Trường | Giá trị |
|---|---|
| ID | UAT-007 |
| Loại | Acceptance |
| Ưu tiên | P0 |
| Truy vết | AC-07; US-010; US-011 |
| URL ứng dụng | http://localhost:8080/ |
| Cách thực hiện | Bán tự động – Playwright điều khiển trình duyệt và ghi bằng chứng; bước có đánh dấu 👤 cần người đánh giá |
| Test tự động hiện có | – |
| Trạng thái chu kỳ C1 | Chưa chạy |
| Thư mục artifact | `./test_reports/UAT-007_xoa-tai-lieu-khong-con-duoc-dung/` |
| Nguồn | [TEST_PLAN.md v0.2](../TEST_PLAN.md) |

## Mục tiêu

Người dùng xác nhận sau khi xóa tài liệu, câu trả lời không còn dùng tài liệu đó.

## Điều kiện tiên quyết

- Ứng dụng chạy tại http://localhost:8080/ (khởi động bằng `node evidence/app.ts start` trong `app/frontend`, hoặc `run.py` trong `app/`); `GET /api/v1/readyz` trả `ready`
- Đã chạy `npm install` và `npx playwright install ffmpeg` trong `app/frontend` (ghi video)
- ENV-STAGING

## Dữ liệu test

- Không cần dữ liệu riêng

## Các bước thực hiện

| # | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Hỏi câu chỉ có đáp án trong tài liệu X | Có nguồn X |
| 2 | Xóa X (xác nhận) | X biến mất; nguồn cũ thành *(đã xóa)* |
| 3 | Hỏi lại cùng câu | Không có thông tin hoặc nguồn từ X; *Chưa đủ thông tin* nếu không tài liệu nào khác có |
| 4 | 👤 Người dùng xác nhận | Đạt |

## Tiêu chí đạt

Mọi bước đạt và **người dùng nghiệp vụ / PO ký xác nhận** trong report; ý kiến được ghi lại.

## Nhiệm vụ của agent (bắt buộc)

Agent thực hiện test case này **trên ứng dụng tại http://localhost:8080/** và phải tạo đủ bằng chứng sau trong thư mục **`./test_reports/UAT-007_xoa-tai-lieu-khong-con-duoc-dung/`** (tính từ thư mục gốc repo):

| Artifact | Vị trí | Yêu cầu |
|---|---|---|
| Test report | `test_reports/UAT-007_xoa-tai-lieu-khong-con-duoc-dung/report.md` (+ `result.json`) | Kết luận ĐẠT / KHÔNG ĐẠT / CẦN NGƯỜI XÁC NHẬN / BỊ CHẶN; bản build (commit); môi trường; bảng kết quả từng bước có link ảnh; link video; lỗi phát hiện |
| Ảnh chụp màn hình | `test_reports/UAT-007_xoa-tai-lieu-khong-con-duoc-dung/screenshots/NN-<bước>.png` | Ít nhất **1 ảnh cho mỗi bước** ở bảng trên, và 1 ảnh tại thời điểm lỗi nếu có |
| Video | `test_reports/UAT-007_xoa-tai-lieu-khong-con-duoc-dung/video/*.webm` | Ghi **toàn bộ quá trình test** từ bước 1 tới bước cuối, không cắt |
| Log | `test_reports/UAT-007_xoa-tai-lieu-khong-con-duoc-dung/logs/` | Output lệnh / request–response API / log ứng dụng liên quan |

**Quy trình:**

1. **Kiểm tra môi trường:** mở http://localhost:8080/ và gọi `GET http://localhost:8080/api/v1/readyz`, phải nhận `{"status":"ready"}`. Nếu không được, chạy `node evidence/app.ts start` trong `app/frontend` (lần đầu trên máy: chạy `run.py --sample` một lần để sinh PDF mẫu). Nếu vẫn không được, tạo report với kết luận **BỊ CHẶN – môi trường**, kèm ảnh/log lỗi, rồi dừng.
2. **Viết spec** `app/frontend/testcases/UAT-007_xoa-tai-lieu-khong-con-duoc-dung.spec.ts`, import `test`/`expect` từ `../evidence/fixture`. Mỗi dòng ở bảng *Các bước thực hiện* là một lời gọi `ev.step('<thao tác>', '<kết quả mong đợi>', async () => {…})`. Dùng `ev.login('p1'|'p2'|'admin'|'outsider')` để đăng nhập và `ev.api(method, '/api/v1/…', {json|multipart})` để gọi API (dùng cookie phiên của trình duyệt, tự thêm `X-CSRF-Token`). Spec mẫu: `testcases/E2E-002_*.spec.ts` (giao diện) và `testcases/API-023_*.spec.ts` (API).
3. **Chạy:** trong `app/frontend`, chạy `npx playwright test -c playwright.testcases.config.ts UAT-007_xoa-tai-lieu-khong-con-duoc-dung`. Fixture tự ghi video của mọi tab, chụp ảnh sau mỗi bước (kể cả khi lỗi), và ghi `report.md`/`result.json` vào `test_reports/UAT-007_xoa-tai-lieu-khong-con-duoc-dung/`.
4. **Bước cần người đánh giá (👤):** gọi `ev.step(…, { review: true })` để report đánh dấu *Cần người xác nhận*. Người đánh giá xem ảnh/video, điền *Kết quả thực tế* vào `report.md` và đổi kết luận. Nếu bước cần công cụ ngoài trình duyệt (NVDA, so sánh với `html_design`), quay toàn màn hình bằng Xbox Game Bar (Win + Alt + R) hoặc OBS và lưu vào `video/` của test case.

**Không được:** lưu artifact ngoài thư mục trên; sửa dữ liệu của người dùng khác ngoài tài khoản test đã nêu; đánh dấu ĐẠT khi còn bước chưa thực hiện. Mỗi lần chạy lại, kết quả cũ tự chuyển sang `test_reports/_archive/`.

**Lỗi phát hiện:** ghi vào report theo mẫu `DEF-T-xxx` (bước tái hiện, mong đợi, thực tế, ảnh/video, mức độ, yêu cầu bị ảnh hưởng: AC-07; US-010; US-011).
