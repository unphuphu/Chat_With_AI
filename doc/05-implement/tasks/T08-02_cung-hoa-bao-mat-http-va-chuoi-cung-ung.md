# T08-02 – Cứng hóa bảo mật HTTP và chuỗi cung ứng

| Trường | Giá trị |
|---|---|
| Lát | VS-8 – Cách ly và bảo mật (Lát 2) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Partial** |
| Phụ thuộc | [T00-07](T00-07_pipeline-ci.md) |
| Story | US-024 |
| Tài liệu tham chiếu | SAD 8.1; API_DESIGN 2.6 (CORS tắt, Cache-Control); PRD NFR-009 |

## Mục tiêu

Header bảo mật, cookie đúng cờ, không CORS, quét phụ thuộc và bí mật.

## Phạm vi file

- `deploy/nginx/*.conf`
- `backend/app/api/middleware.py` (SecurityHeaders)
- `backend/tests/unit/test_security_headers.py`

## Các bước gợi ý

1. CSP `default-src 'self'; frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, HSTS ở proxy; `Cache-Control: private, no-store` cho API.
2. Không trả `Access-Control-*`.

## Tiêu chí hoàn thành

- [ ] Test header trên 3 endpoint
- [ ] Quét ZAP baseline (docker) không có cảnh báo High
- [ ] pip-audit / pnpm audit không có High/Critical
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-unit -k security_headers
```

## Kết quả triển khai

**Partial** – Header bảo mật, CSP, giới hạn kích thước body, cookie; chưa có quét phụ thuộc/SBOM trong CI.
