# ACC-006 – Trạng thái không chỉ dựa vào màu

| Trường | Giá trị |
|---|---|
| ID | ACC-006 |
| Loại | Accessibility |
| Ưu tiên | Medium |
| Truy vết | WCAG 1.4.1; PRD 4.1 |
| URL ứng dụng | http://localhost:8080/ |
| Cách thực hiện | Bán tự động – Playwright điều khiển trình duyệt và ghi bằng chứng; bước có đánh dấu 👤 cần người đánh giá |
| Test tự động hiện có | – (thủ công qua ảnh hướng dẫn) |
| Trạng thái chu kỳ C1 | Đạt (thủ công) |
| Thư mục artifact | `./test_reports/ACC-006_trang-thai-khong-chi-dua-vao-mau/` |
| Nguồn | [TEST_PLAN.md v0.2](../TEST_PLAN.md) |

## Mục tiêu

Xác nhận trạng thái tài liệu và loại câu trả lời phân biệt được bằng biểu tượng + chữ, không chỉ bằng màu.

## Điều kiện tiên quyết

- Ứng dụng chạy tại http://localhost:8080/ (khởi động bằng `node evidence/app.ts start` trong `app/frontend`, hoặc `run.py` trong `app/`); `GET /api/v1/readyz` trả `ready`
- Đã chạy `npm install` và `npx playwright install ffmpeg` trong `app/frontend` (ghi video)
- Tài khoản mẫu **P2** – Trần Minh (minh.tran@congty.vn, nhóm `aichat-users`)
- Dùng tài khoản P2 và xóa hết tài liệu của P2 ở bước đầu (để không ảnh hưởng dữ liệu demo của P1)
- Có PDF mẫu trong `app/sample-pdfs/` (`hop-dong-A.pdf`, `chinh-sach-ban-hang-2026.pdf`, `bang-gia-Q4.pdf`, `ho-so-scan-2019.pdf`, `hop-dong-mat-khau.pdf`, `hop-dong-khoa-in.pdf`, `hong.pdf`, `bao-gia.docx`, `gia-mao.pdf`, `qua-nhieu-trang.pdf`)

## Dữ liệu test

- Không cần dữ liệu riêng

## Các bước thực hiện

| # | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Đăng nhập P2 (`ev.login('p2')`), xóa tài liệu cũ | Màn hình chính, danh sách rỗng |
| 2 | Tạo đủ 3 trạng thái: Đang xử lý, Sẵn sàng, Thất bại (scan) | Mỗi dòng có biểu tượng + chữ trạng thái |
| 3 | `page.emulateMedia({ forcedColors: 'active' })` (chế độ tương phản cao), chụp ảnh | Vẫn phân biệt được trạng thái |
| 4 | 👤 Xem ảnh ở thang xám | Phân biệt được *Sẵn sàng* / *Thất bại* / *Chưa đủ thông tin* bằng chữ |

## Tiêu chí đạt

Mọi bước đạt kết quả mong đợi; không có lỗi Critical/High mới.

## Nhiệm vụ của agent (bắt buộc)

Agent thực hiện test case này **trên ứng dụng tại http://localhost:8080/** và phải tạo đủ bằng chứng sau trong thư mục **`./test_reports/ACC-006_trang-thai-khong-chi-dua-vao-mau/`** (tính từ thư mục gốc repo):

| Artifact | Vị trí | Yêu cầu |
|---|---|---|
| Test report | `test_reports/ACC-006_trang-thai-khong-chi-dua-vao-mau/report.md` (+ `result.json`) | Kết luận ĐẠT / KHÔNG ĐẠT / CẦN NGƯỜI XÁC NHẬN / BỊ CHẶN; bản build (commit); môi trường; bảng kết quả từng bước có link ảnh; link video; lỗi phát hiện |
| Ảnh chụp màn hình | `test_reports/ACC-006_trang-thai-khong-chi-dua-vao-mau/screenshots/NN-<bước>.png` | Ít nhất **1 ảnh cho mỗi bước** ở bảng trên, và 1 ảnh tại thời điểm lỗi nếu có |
| Video | `test_reports/ACC-006_trang-thai-khong-chi-dua-vao-mau/video/*.webm` | Ghi **toàn bộ quá trình test** từ bước 1 tới bước cuối, không cắt |
| Log | `test_reports/ACC-006_trang-thai-khong-chi-dua-vao-mau/logs/` | Output lệnh / request–response API / log ứng dụng liên quan |

**Quy trình:**

1. **Kiểm tra môi trường:** mở http://localhost:8080/ và gọi `GET http://localhost:8080/api/v1/readyz`, phải nhận `{"status":"ready"}`. Nếu không được, chạy `node evidence/app.ts start` trong `app/frontend` (lần đầu trên máy: chạy `run.py --sample` một lần để sinh PDF mẫu). Nếu vẫn không được, tạo report với kết luận **BỊ CHẶN – môi trường**, kèm ảnh/log lỗi, rồi dừng.
2. **Viết spec** `app/frontend/testcases/ACC-006_trang-thai-khong-chi-dua-vao-mau.spec.ts`, import `test`/`expect` từ `../evidence/fixture`. Mỗi dòng ở bảng *Các bước thực hiện* là một lời gọi `ev.step('<thao tác>', '<kết quả mong đợi>', async () => {…})`. Dùng `ev.login('p1'|'p2'|'admin'|'outsider')` để đăng nhập và `ev.api(method, '/api/v1/…', {json|multipart})` để gọi API (dùng cookie phiên của trình duyệt, tự thêm `X-CSRF-Token`). Spec mẫu: `testcases/E2E-002_*.spec.ts` (giao diện) và `testcases/API-023_*.spec.ts` (API).
3. **Chạy:** trong `app/frontend`, chạy `npx playwright test -c playwright.testcases.config.ts ACC-006_trang-thai-khong-chi-dua-vao-mau`. Fixture tự ghi video của mọi tab, chụp ảnh sau mỗi bước (kể cả khi lỗi), và ghi `report.md`/`result.json` vào `test_reports/ACC-006_trang-thai-khong-chi-dua-vao-mau/`.
4. **Bước cần người đánh giá (👤):** gọi `ev.step(…, { review: true })` để report đánh dấu *Cần người xác nhận*. Người đánh giá xem ảnh/video, điền *Kết quả thực tế* vào `report.md` và đổi kết luận. Nếu bước cần công cụ ngoài trình duyệt (NVDA, so sánh với `html_design`), quay toàn màn hình bằng Xbox Game Bar (Win + Alt + R) hoặc OBS và lưu vào `video/` của test case.

**Không được:** lưu artifact ngoài thư mục trên; sửa dữ liệu của người dùng khác ngoài tài khoản test đã nêu; đánh dấu ĐẠT khi còn bước chưa thực hiện. Mỗi lần chạy lại, kết quả cũ tự chuyển sang `test_reports/_archive/`.

**Lỗi phát hiện:** ghi vào report theo mẫu `DEF-T-xxx` (bước tái hiện, mong đợi, thực tế, ảnh/video, mức độ, yêu cầu bị ảnh hưởng: WCAG 1.4.1; PRD 4.1).
