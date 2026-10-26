# T10-03 – Giám sát: trace, metric, dashboard, cảnh báo

| Trường | Giá trị |
|---|---|
| Lát | VS-10 – Vận hành và đo lường (Lát 2) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Partial** |
| Phụ thuộc | [T04-04](T04-04_hoi-thoai-va-api-dat-cau-hoi-alg-08-co-ban.md), [T03-05](T03-05_pipeline-ingest-va-ghi-chi-muc-alg-04.md) |
| Story | – (nền tảng / phi chức năng) |
| Tài liệu tham chiếu | SAD 8.3; BLUEPRINT QA-13; DATABASE_DESIGN A.10 (truy vấn giám sát) |

## Mục tiêu

Có đủ metric, trace và cảnh báo ở SAD 8.3 trên môi trường dev/staging.

## Phạm vi file

- `backend/app/infra/telemetry.py` (OpenTelemetry, prometheus-client)
- `deploy/observability/` (otel-collector, prometheus, grafana dashboards JSON, alert rules)
- `deploy/docker-compose.dev.yml` (profile `obs`)

## Các bước gợi ý

1. Span cho embed, truy xuất, LLM, kiểm tra trích dẫn, các giai đoạn ingest; trace nối API → job qua `trace_parent`.
2. Metric đúng tên SAD 8.3; 3 dashboard; 7 cảnh báo.

## Tiêu chí hoàn thành

- [ ] Chạy luồng lát 1 → Grafana hiển thị p50/p90 trả lời, độ sâu hàng đợi, lỗi theo mã R
- [ ] Trace một câu hỏi thấy đủ span
- [ ] Log không chứa trường cấm (test T00-04 vẫn xanh)
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
docker compose --profile obs up && make e2e -- slice1-journey.spec.ts
```

## Kết quả triển khai

**Partial** – Chỉ có `/metrics` (Prometheus) và log JSON có request_id; chưa có trace, dashboard, cảnh báo.
