# E2E-008 – Hết phiên khi đang soạn câu hỏi

| Trường | Giá trị |
|---|---|
| ID | E2E-008 |
| Loại | System (E2E) |
| Ưu tiên | P0 |
| Truy vết | US-023 AC 2; E-17; NFR-024; S11 |
| URL ứng dụng | http://localhost:8080/ |
| Cách thực hiện | Tự động – Playwright trên trình duyệt, ghi bằng `app/frontend/evidence/fixture.ts` |
| Test tự động hiện có | – |
| Trạng thái chu kỳ C1 | Chưa chạy |
| Thư mục artifact | `./test_reports/E2E-008_het-phien-khi-dang-soan-cau-hoi/` |
| Nguồn | [TEST_PLAN.md v0.2](../TEST_PLAN.md) |

## Mục tiêu

Xác nhận khi phiên hết hạn người dùng được yêu cầu đăng nhập lại, câu hỏi đang soạn được giữ, hội thoại cũ không được giữ.

## Điều kiện tiên quyết

- Ứng dụng chạy tại http://localhost:8080/ (khởi động bằng `node evidence/app.ts start` trong `app/frontend`, hoặc `run.py` trong `app/`); `GET /api/v1/readyz` trả `ready`
- Có PDF mẫu trong `app/sample-pdfs/` (`hop-dong-A.pdf`, `chinh-sach-ban-hang-2026.pdf`, `bang-gia-Q4.pdf`, `ho-so-scan-2019.pdf`, `hop-dong-mat-khau.pdf`, `hop-dong-khoa-in.pdf`, `hong.pdf`, `bao-gia.docx`, `gia-mao.pdf`, `qua-nhieu-trang.pdf`)
- Đã chạy `npm install` và `npx playwright install ffmpeg` trong `app/frontend` (ghi video)
- Tài khoản mẫu **P2** – Trần Minh (minh.tran@congty.vn, nhóm `aichat-users`)
- Dùng tài khoản P2 và xóa hết tài liệu của P2 ở bước đầu (để không ảnh hưởng dữ liệu demo của P1)
- Test cần khởi động lại ứng dụng với biến môi trường riêng (bước ghi *Khởi động lại với …*): trong spec gọi `await ev.restartApp({ KEY: 'VALUE' })`, hoặc chạy `node evidence/app.ts restart KEY=VALUE` trong `app/frontend`. Cuối test gọi `ev.restartApp()` (không tham số) để trả cấu hình mặc định. Ứng dụng phải được khởi động bằng `node evidence/app.ts start` (không phải `run.py` chạy tay) để công cụ dừng/khởi động lại được

## Dữ liệu test

- Không cần dữ liệu riêng

## Các bước thực hiện

| # | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Khởi động lại `run.py` với `SESSION_IDLE_MIN=1` | Ứng dụng sẵn sàng |
| 2 | Mở http://localhost:8080/, chọn *Trần Minh (P2)* trên trang IdP | Màn hình chính; góc phải hiện minh.tran@congty.vn |
| 3 | Bấm *Chọn file PDF*, chọn `hop-dong-A.pdf` | Dòng file hiện tiến độ *Đang tải lên x%* → *Đang xử lý* |
| 4 | Chờ dòng hop-dong-A.pdf chuyển *Sẵn sàng* | ≤ 60 s; thông báo góc dưới trái *Tài liệu đã Sẵn sàng*, tự ẩn ≤ 5 s |
| 5 | Hỏi một câu, nhận câu trả lời; gõ (không gửi) "Hợp đồng có hiệu lực bao lâu?" | Câu hỏi nằm trong ô |
| 6 | Không thao tác 70 s, sau đó bấm *Gửi* | Chuyển tới trang *Phiên làm việc đã hết hạn*, có đếm ngược 5 s và nút *Đăng nhập ngay* |
| 7 | Bấm *Đăng nhập ngay*, chọn P2 | Màn hình chính; ô hỏi chứa sẵn "Hợp đồng có hiệu lực bao lâu?"; hội thoại mới (không còn câu trước) |

## Tiêu chí đạt

Mọi bước đạt kết quả mong đợi; không có lỗi Critical/High mới.

## Nhiệm vụ của agent (bắt buộc)

Agent thực hiện test case này **trên ứng dụng tại http://localhost:8080/** và phải tạo đủ bằng chứng sau trong thư mục **`./test_reports/E2E-008_het-phien-khi-dang-soan-cau-hoi/`** (tính từ thư mục gốc repo):

| Artifact | Vị trí | Yêu cầu |
|---|---|---|
| Test report | `test_reports/E2E-008_het-phien-khi-dang-soan-cau-hoi/report.md` (+ `result.json`) | Kết luận ĐẠT / KHÔNG ĐẠT / CẦN NGƯỜI XÁC NHẬN / BỊ CHẶN; bản build (commit); môi trường; bảng kết quả từng bước có link ảnh; link video; lỗi phát hiện |
| Ảnh chụp màn hình | `test_reports/E2E-008_het-phien-khi-dang-soan-cau-hoi/screenshots/NN-<bước>.png` | Ít nhất **1 ảnh cho mỗi bước** ở bảng trên, và 1 ảnh tại thời điểm lỗi nếu có |
| Video | `test_reports/E2E-008_het-phien-khi-dang-soan-cau-hoi/video/*.webm` | Ghi **toàn bộ quá trình test** từ bước 1 tới bước cuối, không cắt |
| Log | `test_reports/E2E-008_het-phien-khi-dang-soan-cau-hoi/logs/` | Output lệnh / request–response API / log ứng dụng liên quan |

**Quy trình:**

1. **Kiểm tra môi trường:** mở http://localhost:8080/ và gọi `GET http://localhost:8080/api/v1/readyz`, phải nhận `{"status":"ready"}`. Nếu không được, chạy `node evidence/app.ts start` trong `app/frontend` (lần đầu trên máy: chạy `run.py --sample` một lần để sinh PDF mẫu). Nếu vẫn không được, tạo report với kết luận **BỊ CHẶN – môi trường**, kèm ảnh/log lỗi, rồi dừng.
2. **Viết spec** `app/frontend/testcases/E2E-008_het-phien-khi-dang-soan-cau-hoi.spec.ts`, import `test`/`expect` từ `../evidence/fixture`. Mỗi dòng ở bảng *Các bước thực hiện* là một lời gọi `ev.step('<thao tác>', '<kết quả mong đợi>', async () => {…})`. Dùng `ev.login('p1'|'p2'|'admin'|'outsider')` để đăng nhập và `ev.api(method, '/api/v1/…', {json|multipart})` để gọi API (dùng cookie phiên của trình duyệt, tự thêm `X-CSRF-Token`). Spec mẫu: `testcases/E2E-002_*.spec.ts` (giao diện) và `testcases/API-023_*.spec.ts` (API).
3. **Chạy:** trong `app/frontend`, chạy `npx playwright test -c playwright.testcases.config.ts E2E-008_het-phien-khi-dang-soan-cau-hoi`. Fixture tự ghi video của mọi tab, chụp ảnh sau mỗi bước (kể cả khi lỗi), và ghi `report.md`/`result.json` vào `test_reports/E2E-008_het-phien-khi-dang-soan-cau-hoi/`.

**Không được:** lưu artifact ngoài thư mục trên; sửa dữ liệu của người dùng khác ngoài tài khoản test đã nêu; đánh dấu ĐẠT khi còn bước chưa thực hiện. Mỗi lần chạy lại, kết quả cũ tự chuyển sang `test_reports/_archive/`.

**Lỗi phát hiện:** ghi vào report theo mẫu `DEF-T-xxx` (bước tái hiện, mong đợi, thực tế, ảnh/video, mức độ, yêu cầu bị ảnh hưởng: US-023 AC 2; E-17; NFR-024; S11).
