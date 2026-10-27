# Test report – UI-004: Trạng thái trống và lỗi

| Trường | Giá trị |
|---|---|
| Test case | [UI-004](../../doc/07-verification/test_cases/UI-004_trang-thai-trong-va-loi.md) |
| Kết luận | **CẦN NGƯỜI XÁC NHẬN** |
| Bắt đầu | 2026-10-27T16:11:20.146Z |
| Kết thúc | 2026-10-27T16:11:42.506Z (22.4 s) |
| Cách thực hiện | Tự động – Playwright (app/frontend/evidence/fixture.ts) |
| URL ứng dụng | http://localhost:8080/ |
| Bản build | 166929f + thay đổi chưa commit trong app/ |
| Trình duyệt | Microsoft Edge (Playwright, channel msedge) |
| Hệ điều hành | win32 x64 |
| Spec | app/frontend/testcases/UI-004_trang-thai-trong-va-loi.spec.ts |

## Kết quả từng bước

| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|---|
| 1 | Chưa có tài liệu (E-01) | Chưa có tài liệu nào + hướng dẫn 3 bước; ô hỏi khóa: "Cần ít nhất một tài liệu Sẵn sàng…" | Như mong đợi | Đạt | [ảnh](screenshots/01-chua-co-tai-lieu-e-01.png) |
| 2 | Tải 1 file, chụp ngay khi đang xử lý (E-02) | Ô hỏi khóa: "Đang xử lý tài liệu, bạn có thể hỏi khi…" | Như mong đợi | Đạt | [ảnh](screenshots/02-tai-1-file-chup-ngay-khi-dang-xu-ly-e-02.png) |
| 3 | Xóa hết, chỉ tải ho-so-scan-2019.pdf (mọi tài liệu Thất bại – E-03) | Ô hỏi khóa; dòng Thất bại có lý do | Như mong đợi | Đạt | [ảnh](screenshots/03-xoa-het-chi-tai-ho-so-scan-2019-pdf-moi-tai-lieu-t.png) |
| 4 | So với PRD E-03: có gợi ý "kiểm tra lý do và tải file khác" ở ô hỏi không | Ghi nhận | Lời nhắc ở ô hỏi: "Cần ít nhất một tài liệu Sẵn sàng để bắt đầu hỏi.". PRD E-03 yêu cầu thêm gợi ý kiểm tra lý do/tải file khác → khác biệt nhỏ, cần người xác nhận. | Cần người xác nhận | [ảnh](screenshots/04-so-voi-prd-e-03-co-goi-y-kiem-tra-ly-do-va-tai-fil.png) |

## Video

- [UI-004-app.webm](video/UI-004-app.webm)

## Ảnh chụp màn hình

![Bước 1 – Chưa có tài liệu (E-01)](screenshots/01-chua-co-tai-lieu-e-01.png)
![Bước 2 – Tải 1 file, chụp ngay khi đang xử lý (E-02)](screenshots/02-tai-1-file-chup-ngay-khi-dang-xu-ly-e-02.png)
![Bước 3 – Xóa hết, chỉ tải ho-so-scan-2019.pdf (mọi tài liệu Thất bại – E-03)](screenshots/03-xoa-het-chi-tai-ho-so-scan-2019-pdf-moi-tai-lieu-t.png)
![Bước 4 – So với PRD E-03: có gợi ý "kiểm tra lý do và tải file khác" ở ô hỏi không](screenshots/04-so-voi-prd-e-03-co-goi-y-kiem-tra-ly-do-va-tai-fil.png)

## Log

- (không có)

## Ghi chú / lỗi phát hiện

- E-03: ô hỏi chỉ hiện "Cần ít nhất một tài liệu Sẵn sàng để bắt đầu hỏi." – chưa có gợi ý riêng "kiểm tra lý do và tải file khác" như PRD E-03; lý do thất bại hiển thị trên dòng tài liệu.
