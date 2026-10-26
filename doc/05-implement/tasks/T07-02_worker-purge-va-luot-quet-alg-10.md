# T07-02 – Worker purge và lượt quét (ALG-10)

| Trường | Giá trị |
|---|---|
| Lát | VS-7 – Xóa tài liệu (Lát 2) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T07-01](T07-01_api-xoa-tai-lieu-alg-12.md), [T03-01](T03-01_hang-doi-job-va-vong-lap-worker-alg-11.md) |
| Story | US-011 |
| Tài liệu tham chiếu | BLUEPRINT ALG-10; DATABASE_DESIGN A.6 (`fn_pending_purges`, `fn_purge_lag_max_seconds`); PRD NFR-013 |

## Mục tiêu

Xóa thật file gốc ≤ 24 h, dọn object mồ côi, đo độ trễ purge.

## Phạm vi file

- `backend/worker/handlers/purge.py`
- `backend/worker/schedule.py` (lượt quét mỗi giờ)
- `backend/tests/integration/test_purge.py`

## Các bước gợi ý

1. Đúng ALG-10; metric `purge_lag_seconds`.

## Tiêu chí hoàn thành

- [ ] Test: sau purge, object không còn, `purged_at` có giá trị
- [ ] Test: tài liệu bị sót job → lượt quét enqueue lại
- [ ] Test: object không có document, tuổi > 1 h → bị xóa; tuổi < 1 h → giữ
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k purge
```
