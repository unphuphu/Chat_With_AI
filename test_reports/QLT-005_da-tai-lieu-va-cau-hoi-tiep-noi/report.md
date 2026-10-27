# Test report – QLT-005: Đa tài liệu và câu hỏi tiếp nối

| Trường | Giá trị |
|---|---|
| Test case | [QLT-005](../../doc/07-verification/test_cases/QLT-005_da-tai-lieu-va-cau-hoi-tiep-noi.md) |
| Kết luận | **BỊ CHẶN** |
| Bắt đầu | 2026-10-27T15:15:15.503Z |
| Kết thúc | 2026-10-27T15:15:24.302Z (8.8 s) |
| Cách thực hiện | Không thực thi – bị chặn (evidence/blocked.ts) |
| URL ứng dụng | http://localhost:8080/ |
| Bản build | 166929f + thay đổi chưa commit trong app/ |
| Trình duyệt | Microsoft Edge (Playwright, channel msedge) |
| Hệ điều hành | win32 x64 |

## Kết quả từng bước

| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|---|
| 1 | Kiểm tra điều kiện thực thi | ≥ 20 câu đa tài liệu + 10 cặp tiếp nối; triển khai US-015. | Chưa có bộ câu hỏi chuẩn + đáp án (DEP-005 / T06-03) và tài liệu dự án thật do PO cung cấp; chưa có LLM thật. US-015 (câu hỏi tiếp nối) chưa triển khai (OQ-012). | Bị chặn | [ảnh](screenshots/01-ly-do-bi-chan.png) |

## Video

- [QLT-005-blocked.webm](video/QLT-005-blocked.webm)

## Ảnh chụp màn hình

![Bước 1 – Kiểm tra điều kiện thực thi](screenshots/01-ly-do-bi-chan.png)

## Log

- (không có)

## Ghi chú / lỗi phát hiện

- Bị chặn: Chưa có bộ câu hỏi chuẩn + đáp án (DEP-005 / T06-03) và tài liệu dự án thật do PO cung cấp; chưa có LLM thật. US-015 (câu hỏi tiếp nối) chưa triển khai (OQ-012).
- Cần: ≥ 20 câu đa tài liệu + 10 cặp tiếp nối; triển khai US-015.
