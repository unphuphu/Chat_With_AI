# Test report – API-020: Đặt câu hỏi có trích dẫn

| Trường | Giá trị |
|---|---|
| Test case | [API-020](../../doc/07-verification/test_cases/API-020_dat-cau-hoi-co-trich-dan.md) |
| Kết luận | **ĐẠT** |
| Bắt đầu | 2026-10-27T14:16:41.061Z |
| Kết thúc | 2026-10-27T14:16:52.022Z (11.0 s) |
| Cách thực hiện | Tự động – Playwright (app/frontend/evidence/fixture.ts) |
| URL ứng dụng | http://localhost:8080/ |
| Bản build | 166929f + thay đổi chưa commit trong app/ |
| Trình duyệt | Microsoft Edge (Playwright, channel msedge) |
| Hệ điều hành | win32 x64 |
| Spec | app/frontend/testcases/API-020_dat-cau-hoi-co-trich-dan.spec.ts |

## Kết quả từng bước

| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|---|
| 1 | Đăng nhập P2, tải hop-dong-A.pdf và chờ Sẵn sàng | Dòng Sẵn sàng | Như mong đợi | Đạt | [ảnh](screenshots/01-dang-nhap-p2-tai-hop-dong-a-pdf-va-cho-san-sang.png) |
| 2 | POST /conversations/{id}/messages | 200; ANSWERED; answer chứa "30 ngày" và [1] | Như mong đợi | Đạt | [ảnh](screenshots/02-post-conversations-id-messages.png) |
| 3 | Đối chiếu citations | citations[0]: ordinal=1, hop-dong-A.pdf, page_number=2, deleted=false | Như mong đợi | Đạt | [ảnh](screenshots/03-doi-chieu-citations.png) |
| 4 | Đối chiếu latency_ms | > 0 và ≤ 15000 | latency_ms=41 | Đạt | [ảnh](screenshots/04-doi-chieu-latency-ms.png) |

## Video

- [API-020-app.webm](video/API-020-app.webm)
- [API-020-page2.webm](video/API-020-page2.webm)

## Ảnh chụp màn hình

![Bước 1 – Đăng nhập P2, tải hop-dong-A.pdf và chờ Sẵn sàng](screenshots/01-dang-nhap-p2-tai-hop-dong-a-pdf-va-cho-san-sang.png)
![Bước 2 – POST /conversations/{id}/messages](screenshots/02-post-conversations-id-messages.png)
![Bước 3 – Đối chiếu citations](screenshots/03-doi-chieu-citations.png)
![Bước 4 – Đối chiếu latency_ms](screenshots/04-doi-chieu-latency-ms.png)

## Log

- [api.log](logs/api.log)

## Ghi chú / lỗi phát hiện

- (không có)
