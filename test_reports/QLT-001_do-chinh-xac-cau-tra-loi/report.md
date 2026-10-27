# Test report – QLT-001: Độ chính xác câu trả lời

| Trường | Giá trị |
|---|---|
| Test case | [QLT-001](../../doc/07-verification/test_cases/QLT-001_do-chinh-xac-cau-tra-loi.md) |
| Kết luận | **BỊ CHẶN** |
| Bắt đầu | 2026-10-27T15:14:37.736Z |
| Kết thúc | 2026-10-27T15:14:44.243Z (6.5 s) |
| Cách thực hiện | Không thực thi – bị chặn (evidence/blocked.ts) |
| URL ứng dụng | http://localhost:8080/ |
| Bản build | 166929f + thay đổi chưa commit trong app/ |
| Trình duyệt | Microsoft Edge (Playwright, channel msedge) |
| Hệ điều hành | win32 x64 |

## Kết quả từng bước

| # | Bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng |
|---|---|---|---|---|---|
| 1 | Kiểm tra điều kiện thực thi | Bộ câu hỏi chuẩn DEP-005 (≥ 50 câu trong tài liệu), script đánh giá app/backend/scripts/eval_rag.py, 2 người chấm nghiệp vụ. | Chưa có bộ câu hỏi chuẩn + đáp án (DEP-005 / T06-03) và tài liệu dự án thật do PO cung cấp; chưa có LLM thật. | Bị chặn | [ảnh](screenshots/01-ly-do-bi-chan.png) |

## Video

- [QLT-001-blocked.webm](video/QLT-001-blocked.webm)

## Ảnh chụp màn hình

![Bước 1 – Kiểm tra điều kiện thực thi](screenshots/01-ly-do-bi-chan.png)

## Log

- (không có)

## Ghi chú / lỗi phát hiện

- Bị chặn: Chưa có bộ câu hỏi chuẩn + đáp án (DEP-005 / T06-03) và tài liệu dự án thật do PO cung cấp; chưa có LLM thật.
- Cần: Bộ câu hỏi chuẩn DEP-005 (≥ 50 câu trong tài liệu), script đánh giá app/backend/scripts/eval_rag.py, 2 người chấm nghiệp vụ.
