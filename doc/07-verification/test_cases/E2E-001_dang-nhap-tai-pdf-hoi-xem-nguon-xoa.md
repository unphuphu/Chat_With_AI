# E2E-001 – Đăng nhập, tải PDF, hỏi, xem nguồn, xóa

| Trường | Giá trị |
|---|---|
| ID | E2E-001 |
| Loại | System (E2E) |
| Ưu tiên | P0 |
| Truy vết | US-001; US-003; US-008; US-012; US-016; US-020…US-022; US-010; US-011; AC-01…AC-03; AC-05…AC-07 |
| URL ứng dụng | http://localhost:8080/ |
| Cách thực hiện | Tự động – Playwright trên trình duyệt, ghi bằng `app/frontend/evidence/fixture.ts` |
| Test tự động hiện có | `app/frontend/e2e/demo.spec.ts` |
| Trạng thái chu kỳ C1 | Đạt (tự động) |
| Thư mục artifact | `./test_reports/E2E-001_dang-nhap-tai-pdf-hoi-xem-nguon-xoa/` |
| Nguồn | [TEST_PLAN.md v0.2](../TEST_PLAN.md) |

## Mục tiêu

Xác nhận luồng chính của MVP trên trình duyệt: tải lên (kèm file bị từ chối và PDF scan) → Sẵn sàng → hỏi có nguồn → chưa đủ thông tin → mở nguồn đúng trang → xóa tài liệu, nguồn chuyển *(đã xóa)*.

## Điều kiện tiên quyết

- Ứng dụng chạy tại http://localhost:8080/ (khởi động bằng `node evidence/app.ts start` trong `app/frontend`, hoặc `run.py` trong `app/`); `GET /api/v1/readyz` trả `ready`
- Có PDF mẫu trong `app/sample-pdfs/` (`hop-dong-A.pdf`, `chinh-sach-ban-hang-2026.pdf`, `bang-gia-Q4.pdf`, `ho-so-scan-2019.pdf`, `hop-dong-mat-khau.pdf`, `hop-dong-khoa-in.pdf`, `hong.pdf`, `bao-gia.docx`, `gia-mao.pdf`, `qua-nhieu-trang.pdf`)
- Đã chạy `npm install` và `npx playwright install ffmpeg` trong `app/frontend` (ghi video)
- Tài khoản mẫu **P2** – Trần Minh (minh.tran@congty.vn, nhóm `aichat-users`)
- Dùng tài khoản P2 và xóa hết tài liệu của P2 ở bước đầu (để không ảnh hưởng dữ liệu demo của P1)

## Dữ liệu test

- Không cần dữ liệu riêng

## Các bước thực hiện

| # | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Mở http://localhost:8080/, chọn *Trần Minh (P2)* trên trang IdP | Màn hình chính; góc phải hiện minh.tran@congty.vn |
| 2 | Xóa hết tài liệu cũ của P2 (biểu tượng thùng rác → *Xóa tài liệu*) | Khu vực Tài liệu: *Chưa có tài liệu nào*; ô hỏi khóa kèm lý do |
| 3 | Chọn cùng lúc `hop-dong-A.pdf`, `ho-so-scan-2019.pdf`, `bao-gia.docx` | bao-gia.docx: *Không nhận* – "không phải file PDF hợp lệ"; 2 PDF vào hàng đợi |
| 4 | Chờ xử lý xong | hop-dong-A.pdf *Sẵn sàng*; ho-so-scan-2019.pdf *Thất bại* – "…PDF scan chưa được hỗ trợ…", không có nút *Xử lý lại* |
| 5 | Gõ "Bên B thanh toán trong vòng bao nhiêu ngày?" và nhấn Enter | Chỉ báo *Đang tìm trong tài liệu…*; sau đó câu trả lời chứa "30 ngày" và chip `[1] hop-dong-A.pdf · tr.2` |
| 6 | Hỏi "Đối thủ cạnh tranh tại thị trường Nhật Bản là ai?" | Thẻ *Chưa đủ thông tin*, viền nét đứt, không có phần nguồn |
| 7 | Bấm chip `[1] hop-dong-A.pdf · tr.2` | Dialog trình xem: tiêu đề hop-dong-A.pdf, nhãn *Mở từ nguồn [1] · trang 2*, PDF hiển thị trang 2 |
| 8 | Nhấn Esc | Dialog đóng; focus quay lại chip nguồn |
| 9 | Xóa hop-dong-A.pdf (thùng rác → *Xóa tài liệu*) | Hộp xác nhận nêu "không còn được dùng để trả lời"; sau khi xóa dòng biến mất |
| 10 | Xem lại câu trả lời cũ | Chip nguồn viền nét đứt `… (đã xóa)`, không bấm được; ô hỏi khóa (không còn tài liệu Sẵn sàng) |

## Tiêu chí đạt

Mọi bước đạt kết quả mong đợi; không có lỗi Critical/High mới.

## Nhiệm vụ của agent (bắt buộc)

Agent thực hiện test case này **trên ứng dụng tại http://localhost:8080/** và phải tạo đủ bằng chứng sau trong thư mục **`./test_reports/E2E-001_dang-nhap-tai-pdf-hoi-xem-nguon-xoa/`** (tính từ thư mục gốc repo):

| Artifact | Vị trí | Yêu cầu |
|---|---|---|
| Test report | `test_reports/E2E-001_dang-nhap-tai-pdf-hoi-xem-nguon-xoa/report.md` (+ `result.json`) | Kết luận ĐẠT / KHÔNG ĐẠT / CẦN NGƯỜI XÁC NHẬN / BỊ CHẶN; bản build (commit); môi trường; bảng kết quả từng bước có link ảnh; link video; lỗi phát hiện |
| Ảnh chụp màn hình | `test_reports/E2E-001_dang-nhap-tai-pdf-hoi-xem-nguon-xoa/screenshots/NN-<bước>.png` | Ít nhất **1 ảnh cho mỗi bước** ở bảng trên, và 1 ảnh tại thời điểm lỗi nếu có |
| Video | `test_reports/E2E-001_dang-nhap-tai-pdf-hoi-xem-nguon-xoa/video/*.webm` | Ghi **toàn bộ quá trình test** từ bước 1 tới bước cuối, không cắt |
| Log | `test_reports/E2E-001_dang-nhap-tai-pdf-hoi-xem-nguon-xoa/logs/` | Output lệnh / request–response API / log ứng dụng liên quan |

**Quy trình:**

1. **Kiểm tra môi trường:** mở http://localhost:8080/ và gọi `GET http://localhost:8080/api/v1/readyz`, phải nhận `{"status":"ready"}`. Nếu không được, chạy `node evidence/app.ts start` trong `app/frontend` (lần đầu trên máy: chạy `run.py --sample` một lần để sinh PDF mẫu). Nếu vẫn không được, tạo report với kết luận **BỊ CHẶN – môi trường**, kèm ảnh/log lỗi, rồi dừng.
2. **Viết spec** `app/frontend/testcases/E2E-001_dang-nhap-tai-pdf-hoi-xem-nguon-xoa.spec.ts`, import `test`/`expect` từ `../evidence/fixture`. Mỗi dòng ở bảng *Các bước thực hiện* là một lời gọi `ev.step('<thao tác>', '<kết quả mong đợi>', async () => {…})`. Dùng `ev.login('p1'|'p2'|'admin'|'outsider')` để đăng nhập và `ev.api(method, '/api/v1/…', {json|multipart})` để gọi API (dùng cookie phiên của trình duyệt, tự thêm `X-CSRF-Token`). Spec mẫu: `testcases/E2E-002_*.spec.ts` (giao diện) và `testcases/API-023_*.spec.ts` (API).
3. **Chạy:** trong `app/frontend`, chạy `npx playwright test -c playwright.testcases.config.ts E2E-001_dang-nhap-tai-pdf-hoi-xem-nguon-xoa`. Fixture tự ghi video của mọi tab, chụp ảnh sau mỗi bước (kể cả khi lỗi), và ghi `report.md`/`result.json` vào `test_reports/E2E-001_dang-nhap-tai-pdf-hoi-xem-nguon-xoa/`.

**Không được:** lưu artifact ngoài thư mục trên; sửa dữ liệu của người dùng khác ngoài tài khoản test đã nêu; đánh dấu ĐẠT khi còn bước chưa thực hiện. Mỗi lần chạy lại, kết quả cũ tự chuyển sang `test_reports/_archive/`.

**Lỗi phát hiện:** ghi vào report theo mẫu `DEF-T-xxx` (bước tái hiện, mong đợi, thực tế, ảnh/video, mức độ, yêu cầu bị ảnh hưởng: US-001; US-003; US-008; US-012; US-016; US-020…US-022; US-010; US-011; AC-01…AC-03; AC-05…AC-07).
