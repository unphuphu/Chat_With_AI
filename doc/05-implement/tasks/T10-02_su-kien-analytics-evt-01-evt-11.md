# T10-02 – Sự kiện analytics EVT-01…EVT-11

| Trường | Giá trị |
|---|---|
| Lát | VS-10 – Vận hành và đo lường (Lát 2) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T07-01](T07-01_api-xoa-tai-lieu-alg-12.md), [T04-04](T04-04_hoi-thoai-va-api-dat-cau-hoi-alg-08-co-ban.md), [T06-01](T06-01_duong-chua-du-thong-tin-day-du.md) |
| Story | – (nền tảng / phi chức năng) |
| Tài liệu tham chiếu | PRD 5.2; BLUEPRINT 3.5.3; DATABASE_DESIGN A.5 (view báo cáo); API_DESIGN AD-12 |

## Mục tiêu

Ghi 11 sự kiện với thuộc tính đúng, `actor_hash`, không có nội dung; view báo cáo chạy được.

## Phạm vi file

- `backend/app/modules/events/analytics.py`
- `backend/tests/integration/test_analytics.py`

## Các bước gợi ý

1. Whitelist thuộc tính theo bảng 3.5.3; `actor_hash` = HMAC-SHA256(user_id, `ACTOR_HASH_KEY`).
2. EVT-09 `citation_clicked` để lại cho T11-04 (endpoint mở file); task này hiện thực 10 sự kiện còn lại.

## Tiêu chí hoàn thành

- [ ] Test: 10 sự kiện (trừ EVT-09) có đúng khóa thuộc tính
- [ ] Test: thêm khóa `question` → bị chặn ở ứng dụng và ở CHECK CSDL
- [ ] Test: `vw_report_daily_questions` trả số liệu đúng với dữ liệu giả
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k analytics
```
