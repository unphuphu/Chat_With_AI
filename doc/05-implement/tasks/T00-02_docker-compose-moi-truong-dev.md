# T00-02 – docker-compose môi trường dev

| Trường | Giá trị |
|---|---|
| Lát | VS-0 – Nền tảng chạy được (Lát 1) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T00-01](T00-01_khoi-tao-monorepo-va-cong-cu.md) |
| Story | – (nền tảng / phi chức năng) |
| Tài liệu tham chiếu | SAD 9.1 (Phương án B – nội bộ); BLUEPRINT 3.6.6 (biến môi trường); DATABASE_DESIGN A.0 |

## Mục tiêu

Một lệnh `make up` dựng đủ hạ tầng dev: PostgreSQL 16 + pgvector, MinIO, IdP OIDC giả lập.

## Phạm vi file

- `deploy/docker-compose.dev.yml`
- `deploy/postgres/init/00_roles.sql` (6 vai trò ở đầu schema.sql, mật khẩu dev)
- `.env.example`
- `Makefile` (up/down/psql/logs)

## Các bước gợi ý

1. Service `db`: image `pgvector/pgvector:pg16`, volume, healthcheck `pg_isready`; script init tạo vai trò.
2. Service `minio` + job tạo bucket `aichat-docs` (tắt versioning – SAD 8.2).
3. Service `idp`: `ghcr.io/navikt/mock-oauth2-server` cấu hình claim `groups` = [`aichat-users`] cho user `p1`, không có nhóm cho user `outsider`.
4. `.env.example` liệt kê mọi biến ở BLUEPRINT 3.6.6 với giá trị dev; bí mật để `change-me`.

## Tiêu chí hoàn thành

- [ ] `make up` khởi động 3 service healthy trong ≤ 60 s
- [ ] `make psql` vào được bằng `app_migrator`; `SELECT extversion FROM pg_extension WHERE extname='vector'` ≥ 0.8
- [ ] Bucket tồn tại, versioning tắt
- [ ] Discovery `http://localhost:8090/default/.well-known/openid-configuration` trả JSON
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make up && docker compose -f deploy/docker-compose.dev.yml ps
make psql -c "select extversion from pg_extension where extname='vector'"
```

## Ngoài phạm vi

- Không chứa service ứng dụng (thêm ở T00-04, T00-06)
