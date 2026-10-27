# Test report – QLT-004: Từ chối đúng câu hỏi ngoài tài liệu

| Trường | Giá trị |
|---|---|
| Test case | [QLT-004](../../doc/07-verification/test_cases/QLT-004_tu-choi-dung-cau-hoi-ngoai-tai-lieu.md) |
| Kết luận | **BỊ CHẶN** |
| Bắt đầu | 2026-10-27T15:15:06.137Z |
| Kết thúc | 2026-10-27T15:15:12.508Z (6.4 s) |
| Cách thực hiện | Không thực thi – bị chặn (evidence/blocked.ts) |
| URL ứng dụng | http://localhost:8080/ |
| Bản build | 166929f + thay đổi chưa commit trong app/ |
| Trình duyệt | Microsoft Edge (Playwright, channel msedge) |
| Hệ điều hành | win32 x64 |

## Kết quả từng bước

| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|---|
| 1 | Kiểm tra điều kiện thực thi | ≥ 20 câu hỏi ngoài tài liệu trong bộ câu hỏi chuẩn. | Chưa có bộ câu hỏi chuẩn + đáp án (DEP-005 / T06-03) và tài liệu dự án thật do PO cung cấp; chưa có LLM thật. | Bị chặn | [ảnh](screenshots/01-ly-do-bi-chan.png) |

## Video

- [QLT-004-blocked.webm](video/QLT-004-blocked.webm)

## Ảnh chụp màn hình

![Bước 1 – Kiểm tra điều kiện thực thi](screenshots/01-ly-do-bi-chan.png)

## Log

- (không có)

## Ghi chú / lỗi phát hiện

- Bị chặn: Chưa có bộ câu hỏi chuẩn + đáp án (DEP-005 / T06-03) và tài liệu dự án thật do PO cung cấp; chưa có LLM thật.
- Cần: ≥ 20 câu hỏi ngoài tài liệu trong bộ câu hỏi chuẩn.
