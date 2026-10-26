# T09-02 – Giới hạn câu hỏi và đếm ngược trên giao diện

| Trường | Giá trị |
|---|---|
| Lát | VS-9 – Lỗi, giới hạn và phiên (Lát 2) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T05-02](T05-02_gioi-han-tan-suat-alg-09-cho-tai-file.md), [T04-05](T04-05_spa-khung-chat-cau-tra-loi-va-nhan-nguon.md) |
| Story | US-026 |
| Tài liệu tham chiếu | BLUEPRINT ALG-09; html_design S05 (cảnh báo đếm ngược); API_DESIGN 3.6.3 `rate_limited` |

## Mục tiêu

10 câu hỏi/phút/người; giao diện đếm ngược và tự mở khóa, không mất nội dung ô hỏi.

## Phạm vi file

- `backend/app/api/v1/conversations.py` (gắn `rate_limit('question',…)`)
- `frontend/src/features/chat/RateLimitNotice.tsx`

## Các bước gợi ý

1. Gắn dependency; SPA đọc `Retry-After`, khóa nút Gửi, đếm ngược, mở khóa.

## Tiêu chí hoàn thành

- [ ] Test API: câu thứ 11 → 429
- [ ] E2E: câu thứ 11 → thông báo đếm ngược, nội dung ô hỏi còn nguyên, hết giờ tự mở khóa (đồng hồ giả)
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k ratelimit && make e2e -- ratelimit.spec.ts
```
