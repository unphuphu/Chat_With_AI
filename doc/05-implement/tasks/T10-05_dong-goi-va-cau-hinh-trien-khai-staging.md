# T10-05 – Đóng gói và cấu hình triển khai staging

| Trường | Giá trị |
|---|---|
| Lát | VS-10 – Vận hành và đo lường (Lát 2) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Ready (giả định)** |
| Phụ thuộc | [T00-07](T00-07_pipeline-ci.md), [T10-03](T10-03_giam-sat-trace-metric-dashboard-canh-bao.md) |
| Story | – (nền tảng / phi chức năng) |
| Tài liệu tham chiếu | SAD 9.1, 9.2, ADR-013; DATABASE_DESIGN A.10 (sao lưu, tham số) |

## Mục tiêu

Image production cho api/worker/embedding/web và cấu hình staging chạy được với một lệnh.

## Phạm vi file

- `backend/Dockerfile`, `embedding-service/Dockerfile`, `frontend/Dockerfile` (multi-stage, user không phải root)
- `deploy/staging/` (compose hoặc manifest theo hạ tầng được chọn)
- `docs/runbook.md` (triển khai, rollback, khôi phục CSDL, xoay vòng bí mật)

## Các bước gợi ý

1. Rolling update, migration chạy trước như job riêng (expand/contract).
2. Bí mật từ secret manager/biến môi trường, không nằm trong image.
3. Tài nguyên theo SAD 9.2.

## Tiêu chí hoàn thành

- [ ] Triển khai staging từ đầu bằng runbook thành công
- [ ] Rollback về bản trước trong ≤ 10 phút (diễn tập, ghi lại)
- [ ] Quét image (trivy) không có Critical
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
trivy image aichat-api:latest
```

## Ngoài phạm vi

- Hạ tầng production cụ thể chờ OQ-005, OQ-203
