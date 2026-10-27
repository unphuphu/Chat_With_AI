# API-023 – Kiểm tra câu hỏi không hợp lệ

| Trường | Giá trị |
|---|---|
| ID | API-023 |
| Loại | API |
| Ưu tiên | High |
| Truy vết | US-012 AC 3; E-14; E-15 |
| URL ứng dụng | http://localhost:8080/ |
| Cách thực hiện | Tự động – Playwright trên trình duyệt, ghi bằng `app/frontend/evidence/fixture.ts` |
| Test tự động hiện có | `test_question_validation`; spec mẫu `testcases/API-023_*.spec.ts` |
| Trạng thái chu kỳ C1 | Đạt (tự động; spec bằng chứng đạt 26/10) |
| Thư mục artifact | `./test_reports/API-023_kiem-tra-cau-hoi-khong-hop-le/` |
| Nguồn | [TEST_PLAN.md v0.2](../TEST_PLAN.md) |

## Mục tiêu

Xác nhận câu hỏi trống, quá 2.000 ký tự, hoặc gửi vào hội thoại không tồn tại đều bị từ chối, và giao diện không cho gửi câu trống.

## Điều kiện tiên quyết

- Ứng dụng chạy tại http://localhost:8080/ (khởi động bằng `node evidence/app.ts start` trong `app/frontend`, hoặc `run.py` trong `app/`); `GET /api/v1/readyz` trả `ready`
- Đã chạy `npm install` và `npx playwright install ffmpeg` trong `app/frontend` (ghi video)
- Tài khoản mẫu **P1** – Nguyễn Lan (lan.nguyen@congty.vn, nhóm `aichat-users`)
- Có PDF mẫu trong `app/sample-pdfs/` (`hop-dong-A.pdf`, `chinh-sach-ban-hang-2026.pdf`, `bang-gia-Q4.pdf`, `ho-so-scan-2019.pdf`, `hop-dong-mat-khau.pdf`, `hop-dong-khoa-in.pdf`, `hong.pdf`, `bao-gia.docx`, `gia-mao.pdf`, `qua-nhieu-trang.pdf`)

## Dữ liệu test

- Không cần dữ liệu riêng

## Các bước thực hiện

| # | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Đăng nhập P1, đảm bảo có ít nhất 1 tài liệu Sẵn sàng | Có tài liệu Sẵn sàng |
| 2 | `GET /api/v1/conversations/current` | 200, có id |
| 3 | POST câu hỏi chỉ có khoảng trắng | 422 `empty_question`; Header `content-type: application/problem+json`; body có `type`, `title`, `status`, `code`, `request_id` |
| 4 | POST câu hỏi 2.001 ký tự | 422 `question_too_long` |
| 5 | POST vào hội thoại có id ngẫu nhiên | 404 |
| 6 | Trên giao diện: gõ khoảng trắng vào ô hỏi | Nút *Gửi* bị vô hiệu |

## Tiêu chí đạt

Mọi bước đạt kết quả mong đợi; không có lỗi Critical/High mới.

## Nhiệm vụ của agent (bắt buộc)

Agent thực hiện test case này **trên ứng dụng tại http://localhost:8080/** và phải tạo đủ bằng chứng sau trong thư mục **`./test_reports/API-023_kiem-tra-cau-hoi-khong-hop-le/`** (tính từ thư mục gốc repo):

| Artifact | Vị trí | Yêu cầu |
|---|---|---|
| Test report | `test_reports/API-023_kiem-tra-cau-hoi-khong-hop-le/report.md` (+ `result.json`) | Kết luận ĐẠT / KHÔNG ĐẠT / CẦN NGƯỜI XÁC NHẬN / BỊ CHẶN; bản build (commit); môi trường; bảng kết quả từng bước có link ảnh; link video; lỗi phát hiện |
| Ảnh chụp màn hình | `test_reports/API-023_kiem-tra-cau-hoi-khong-hop-le/screenshots/NN-<bước>.png` | Ít nhất **1 ảnh cho mỗi bước** ở bảng trên, và 1 ảnh tại thời điểm lỗi nếu có |
| Video | `test_reports/API-023_kiem-tra-cau-hoi-khong-hop-le/video/*.webm` | Ghi **toàn bộ quá trình test** từ bước 1 tới bước cuối, không cắt |
| Log | `test_reports/API-023_kiem-tra-cau-hoi-khong-hop-le/logs/` | Output lệnh / request–response API / log ứng dụng liên quan |

**Quy trình:**

1. **Kiểm tra môi trường:** mở http://localhost:8080/ và gọi `GET http://localhost:8080/api/v1/readyz`, phải nhận `{"status":"ready"}`. Nếu không được, chạy `node evidence/app.ts start` trong `app/frontend` (lần đầu trên máy: chạy `run.py --sample` một lần để sinh PDF mẫu). Nếu vẫn không được, tạo report với kết luận **BỊ CHẶN – môi trường**, kèm ảnh/log lỗi, rồi dừng.
2. **Viết spec** `app/frontend/testcases/API-023_kiem-tra-cau-hoi-khong-hop-le.spec.ts`, import `test`/`expect` từ `../evidence/fixture`. Mỗi dòng ở bảng *Các bước thực hiện* là một lời gọi `ev.step('<thao tác>', '<kết quả mong đợi>', async () => {…})`. Dùng `ev.login('p1'|'p2'|'admin'|'outsider')` để đăng nhập và `ev.api(method, '/api/v1/…', {json|multipart})` để gọi API (dùng cookie phiên của trình duyệt, tự thêm `X-CSRF-Token`). Spec mẫu: `testcases/E2E-002_*.spec.ts` (giao diện) và `testcases/API-023_*.spec.ts` (API).
3. **Chạy:** trong `app/frontend`, chạy `npx playwright test -c playwright.testcases.config.ts API-023_kiem-tra-cau-hoi-khong-hop-le`. Fixture tự ghi video của mọi tab, chụp ảnh sau mỗi bước (kể cả khi lỗi), và ghi `report.md`/`result.json` vào `test_reports/API-023_kiem-tra-cau-hoi-khong-hop-le/`.

**Không được:** lưu artifact ngoài thư mục trên; sửa dữ liệu của người dùng khác ngoài tài khoản test đã nêu; đánh dấu ĐẠT khi còn bước chưa thực hiện. Mỗi lần chạy lại, kết quả cũ tự chuyển sang `test_reports/_archive/`.

**Lỗi phát hiện:** ghi vào report theo mẫu `DEF-T-xxx` (bước tái hiện, mong đợi, thực tế, ảnh/video, mức độ, yêu cầu bị ảnh hưởng: US-012 AC 3; E-14; E-15).
