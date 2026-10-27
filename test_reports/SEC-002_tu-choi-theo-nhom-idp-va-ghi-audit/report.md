# Test report – SEC-002: Từ chối theo nhóm IdP và ghi audit

| Trường | Giá trị |
|---|---|
| Test case | [SEC-002](../../doc/07-verification/test_cases/SEC-002_tu-choi-theo-nhom-idp-va-ghi-audit.md) |
| Kết luận | **ĐẠT** |
| Bắt đầu | 2026-10-27T15:45:31.338Z |
| Kết thúc | 2026-10-27T15:45:46.448Z (15.1 s) |
| Cách thực hiện | Tự động – Playwright (app/frontend/evidence/fixture.ts) |
| URL ứng dụng | http://localhost:8080/ |
| Bản build | 166929f + thay đổi chưa commit trong app/ |
| Trình duyệt | Microsoft Edge (Playwright, channel msedge) |
| Hệ điều hành | win32 x64 |
| Spec | app/frontend/testcases/SEC-002_tu-choi-theo-nhom-idp-va-ghi-audit.spec.ts |

## Kết quả từng bước

| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|---|
| 1 | Đăng nhập Người ngoài nhóm | Trang /access-denied | Như mong đợi | Đạt | [ảnh](screenshots/01-dang-nhap-nguoi-ngoai-nhom.png) |
| 2 | Đọc cookie | Không có cookie sid | Cookie hiện có: (không có) | Đạt | [ảnh](screenshots/02-doc-cookie.png) |
| 3 | Kiểm tra audit: chạy pytest test_outsider_denied_and_audited | 1 passed – có 1 bản ghi login_denied | [32m[32m[1m1 passed[0m[32m in 3.55s[0m[0m | Đạt | [ảnh](screenshots/03-kiem-tra-audit-chay-pytest-test-outsider-denied-an.png) |

## Video

- [SEC-002-app.webm](video/SEC-002-app.webm)

## Ảnh chụp màn hình

![Bước 1 – Đăng nhập Người ngoài nhóm](screenshots/01-dang-nhap-nguoi-ngoai-nhom.png)
![Bước 2 – Đọc cookie](screenshots/02-doc-cookie.png)
![Bước 3 – Kiểm tra audit: chạy pytest test_outsider_denied_and_audited](screenshots/03-kiem-tra-audit-chay-pytest-test-outsider-denied-an.png)

## Log

- (không có)

## Ghi chú / lỗi phát hiện

- (không có)
