# T10-04 – Tác vụ bảo trì định kỳ

| Trường | Giá trị |
|---|---|
| Lát | VS-10 – Vận hành và đo lường (Lát 2) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T03-01](T03-01_hang-doi-job-va-vong-lap-worker-alg-11.md) |
| Story | – (nền tảng / phi chức năng) |
| Tài liệu tham chiếu | SAD 3.2 (tác vụ), DATABASE_DESIGN A.10 (kế hoạch bảo trì); PRD NFR-023, NFR-024 |

## Mục tiêu

Hết hạn phiên, phân vùng nhật ký, dọn dữ liệu cũ chạy tự động bằng vai trò `app_maintenance`.

## Phạm vi file

- `backend/worker/maintenance.py`
- `backend/tests/integration/test_maintenance.py`

## Các bước gợi ý

1. `expire_sessions` (15 phút, xóa lô quá 1 ngày); `ensure_audit_partition` + `drop_audit_partitions_before` (hằng ngày); xóa `analytics_event` > 180 ngày, `rate_limit_counter` > 2 h, `job` xong > 7 ngày.
2. Khóa advisory để chỉ 1 worker chạy mỗi tác vụ.

## Tiêu chí hoàn thành

- [ ] Test từng tác vụ với dữ liệu quá hạn/chưa quá hạn
- [ ] Test: 2 worker cùng chạy → tác vụ chạy 1 lần
- [ ] Phiên hết hạn bị xóa kéo theo hội thoại (NFR-024)
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k maintenance
```

## Kết quả triển khai

**Done** – Hết hạn phiên, dọn bảng, phân vùng audit; test.
