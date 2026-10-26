# T00-07 – Pipeline CI

| Trường | Giá trị |
|---|---|
| Lát | VS-0 – Nền tảng chạy được (Lát 1) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T00-03](T00-03_migration-0001-tu-schema-sql-va-fixture-csdl-cho.md), [T00-04](T00-04_khung-api-settings-loi-rfc-9457-request-id-healt.md), [T00-06](T00-06_khung-spa-theo-thiet-ke-s01-va-client-api-sinh-t.md) |
| Story | – (nền tảng / phi chức năng) |
| Tài liệu tham chiếu | BLUEPRINT QA-10, QA-12; API_DESIGN AC-06 (oasdiff); SAD 8.1 (bí mật) |

## Mục tiêu

Mỗi pull request được kiểm tra tự động đủ các cổng chất lượng của dự án.

## Phạm vi file

- `.github/workflows/ci.yml` (hoặc tương đương nội bộ)
- `backend/scripts/check_openapi.py`

## Các bước gợi ý

1. Job backend: ruff, mypy, lint-imports, pytest unit, pytest integration (Testcontainers).
2. Job frontend: eslint, tsc, vitest, build.
3. Job contract: validate `openapi.yaml` (openapi-spec-validator + kiểm tra ví dụ); sinh OpenAPI từ FastAPI và so bằng `oasdiff breaking` (chỉ endpoint đã hiện thực).
4. Job bảo mật: gitleaks, `pip-audit`, `pnpm audit --prod` (fail ở High/Critical).
5. Cache uv/pnpm; tổng thời gian mục tiêu < 10 phút.

## Tiêu chí hoàn thành

- [ ] CI chạy xanh trên nhánh chính
- [ ] PR cố ý thêm bí mật giả → job gitleaks fail
- [ ] PR cố ý đổi kiểu trường trong FastAPI khác openapi.yaml → job contract fail
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
(trên CI) toàn bộ workflow xanh
```

## Ngoài phạm vi

- Không triển khai tự động (T10-05)
