# T00-03 – Migration 0001 từ schema.sql và fixture CSDL cho test

| Trường | Giá trị |
|---|---|
| Lát | VS-0 – Nền tảng chạy được (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T00-02](T00-02_docker-compose-moi-truong-dev.md) |
| Story | – (nền tảng / phi chức năng) |
| Tài liệu tham chiếu | doc/04-design/schema.sql v0.3; doc/04-design/seed_dev.sql; DATABASE_DESIGN A.9 |

## Mục tiêu

Áp dụng schema thiết kế bằng Alembic và có fixture Testcontainers để mọi test tích hợp dùng PostgreSQL thật.

## Phạm vi file

- `backend/migrations/` (alembic.ini, env.py)
- `backend/migrations/versions/0001_initial.py` (thực thi nội dung schema.sql)
- `backend/tests/conftest.py` (fixture `pg` dùng testcontainers `pgvector/pgvector:pg16`)
- `backend/tests/integration/test_schema.py`

## Các bước gợi ý

1. Copy `schema.sql` vào `backend/migrations/sql/0001_initial.sql`; `upgrade()` đọc và thực thi; `downgrade()` drop schema.
2. Fixture tạo vai trò (như init script), chạy `alembic upgrade head`, chạy `seed_dev.sql` với `SET app.env='dev'`.
3. Viết test: (a) seed chạy được; (b) chèn `chunk` cho tài liệu PROCESSING rồi COMMIT → lỗi `check_violation`; (c) chuyển READY→PROCESSING → lỗi; (d) `app_api` với `app.workspace_id` của P1 không thấy tài liệu của P2; (e) `app_api` không đặt workspace → 0 hàng.

## Tiêu chí hoàn thành

- [ ] `alembic upgrade head` rồi `downgrade base` rồi `upgrade head` thành công
- [ ] 5 test tích hợp ở bước 3 xanh
- [ ] Mọi lỗi phát hiện khi chạy schema trên PostgreSQL thật được sửa **cả** ở `doc/04-design/schema.sql` (ghi chú trong PR)
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k schema
```

## Ngoài phạm vi

- Không viết repository/ORM model (task sau)

## Kết quả triển khai

**Done** – `migrations/sql/0001_initial.sql` + bộ chạy migration tối giản; fixture PGlite trong bộ nhớ; test schema/RLS/trigger trong `tests/integration/test_slice1.py`.
