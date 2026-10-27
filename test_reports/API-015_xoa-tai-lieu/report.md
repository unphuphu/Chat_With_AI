# Test report – API-015: Xóa tài liệu

| Trường | Giá trị |
|---|---|
| Test case | [API-015](../../doc/07-verification/test_cases/API-015_xoa-tai-lieu.md) |
| Kết luận | **ĐẠT** |
| Bắt đầu | 2026-10-27T14:15:22.911Z |
| Kết thúc | 2026-10-27T14:15:35.102Z (12.2 s) |
| Cách thực hiện | Tự động – Playwright (app/frontend/evidence/fixture.ts) |
| URL ứng dụng | http://localhost:8080/ |
| Bản build | 166929f + thay đổi chưa commit trong app/ |
| Trình duyệt | Microsoft Edge (Playwright, channel msedge) |
| Hệ điều hành | win32 x64 |
| Spec | app/frontend/testcases/API-015_xoa-tai-lieu.spec.ts |

## Kết quả từng bước

| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|---|
| 1 | Đăng nhập P2, tải hop-dong-A.pdf và chờ Sẵn sàng | Dòng Sẵn sàng | Như mong đợi | Đạt | [ảnh](screenshots/01-dang-nhap-p2-tai-hop-dong-a-pdf-va-cho-san-sang.png) |
| 2 | DELETE /documents/{id} | 204 | Như mong đợi | Đạt | [ảnh](screenshots/02-delete-documents-id.png) |
| 3 | GET /documents | Không còn tài liệu; documents_used=0 | Như mong đợi | Đạt | [ảnh](screenshots/03-get-documents.png) |
| 4 | DELETE lần 2 | 404 not_found | Như mong đợi | Đạt | [ảnh](screenshots/04-delete-lan-2.png) |

## Video

- [API-015-app.webm](video/API-015-app.webm)
- [API-015-page2.webm](video/API-015-page2.webm)

## Ảnh chụp màn hình

![Bước 1 – Đăng nhập P2, tải hop-dong-A.pdf và chờ Sẵn sàng](screenshots/01-dang-nhap-p2-tai-hop-dong-a-pdf-va-cho-san-sang.png)
![Bước 2 – DELETE /documents/{id}](screenshots/02-delete-documents-id.png)
![Bước 3 – GET /documents](screenshots/03-get-documents.png)
![Bước 4 – DELETE lần 2](screenshots/04-delete-lan-2.png)

## Log

- [api.log](logs/api.log)

## Ghi chú / lỗi phát hiện

- (không có)
