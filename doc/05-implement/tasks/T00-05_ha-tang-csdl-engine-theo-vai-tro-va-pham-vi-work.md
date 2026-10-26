# T00-05 – Hạ tầng CSDL: engine theo vai trò và phạm vi workspace

| Trường | Giá trị |
|---|---|
| Lát | VS-0 – Nền tảng chạy được (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T00-03](T00-03_migration-0001-tu-schema-sql-va-fixture-csdl-cho.md), [T00-04](T00-04_khung-api-settings-loi-rfc-9457-request-id-healt.md) |
| Story | – (nền tảng / phi chức năng) |
| Tài liệu tham chiếu | BLUEPRINT 3.2.3 (bất biến), 3.3; SAD 5.1 (vai trò CSDL); DATABASE_DESIGN A.10 (PgBouncer, LISTEN) |

## Mục tiêu

Mọi truy cập dữ liệu tài liệu đi qua `workspace_scope()` – không thể vô tình truy vấn ngoài phạm vi.

## Phạm vi file

- `backend/app/infra/db.py`
- `backend/tests/integration/test_db_scope.py`

## Các bước gợi ý

1. Async engine (psycopg 3) theo URL vai trò (`DATABASE_URL_API`, `_WORKER`, `_MAINTENANCE`), pool 10.
2. Context manager `workspace_scope(session, ws_id)` mở transaction và `SET LOCAL app.workspace_id`.
3. Helper `scoped_execute` ném `WorkspaceScopeMissing` nếu gọi trên bảng có RLS khi chưa đặt scope (kiểm tra `current_setting`).
4. Phiên kết nối đặt `TimeZone=UTC`.

## Tiêu chí hoàn thành

- [ ] Test: trong scope P1 đọc được tài liệu P1, không thấy P2
- [ ] Test: gọi helper không có scope → `WorkspaceScopeMissing`
- [ ] Test: `SET LOCAL` không rò sang transaction kế tiếp trên cùng kết nối pool
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k db_scope
```

## Ngoài phạm vi

- Không viết repository nghiệp vụ

## Kết quả triển khai

**Done** – `Database.tx(role, workspace_id)` với `SET LOCAL ROLE` + `app.workspace_id`; test không rò phạm vi.
