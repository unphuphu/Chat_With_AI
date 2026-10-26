# T00-01 – Khởi tạo monorepo và công cụ

| Trường | Giá trị |
|---|---|
| Lát | VS-0 – Nền tảng chạy được (Lát 1) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | – |
| Story | – (nền tảng / phi chức năng) |
| Tài liệu tham chiếu | BLUEPRINT 3.1 (cấu trúc thư mục); BLUEPRINT 3.3 (quy tắc tầng); SAD ADR-002, ADR-003 |

## Mục tiêu

Tạo cấu trúc repo theo BLUEPRINT 3.1 và bộ lệnh chuẩn để mọi task sau dùng chung.

## Phạm vi file

- `backend/` (pyproject.toml với uv, ruff, mypy strict, pytest, import-linter)
- `backend/app/{api/v1,modules,ports,adapters,infra}/__init__.py`, `backend/worker/`
- `embedding-service/` (pyproject riêng)
- `frontend/` (Vite + React 18 + TypeScript strict, vitest, eslint, prettier)
- `Makefile`, `.editorconfig`, `.gitignore`, `.pre-commit-config.yaml`
- `README.md` (cách chạy)

## Các bước gợi ý

1. Tạo cây thư mục đúng BLUEPRINT 3.1 (chỉ file rỗng/`__init__.py`).
2. Cấu hình `ruff` (line 110), `mypy --strict` cho `app/`, `pytest` với marker `integration`, `e2e`.
3. Thêm `.importlinter` với 5 hợp đồng ở BLUEPRINT 3.3 (sẽ xanh vì chưa có mã).
4. Tạo Makefile: `lint`, `typecheck`, `test-unit`, `test-int`, `e2e`, `up`, `down`, `fmt`.
5. Frontend: `pnpm create vite` template react-ts, bật `strict`, thêm vitest.

## Tiêu chí hoàn thành

- [ ] `make lint typecheck test-unit` chạy thành công trên repo trống
- [ ] `pnpm -C frontend build` thành công
- [ ] `lint-imports` chạy và xanh
- [ ] README mô tả yêu cầu máy (Python 3.12, Node 20, Docker) và các lệnh make
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make lint typecheck test-unit
pnpm -C frontend build && pnpm -C frontend test
```

## Ngoài phạm vi

- Không viết mã nghiệp vụ
- Không cấu hình CI (T00-07)

## Kết quả triển khai

**Done** – Mã trong `app/`; pip + npm + `run.py` thay uv/pnpm/make; ruff, mypy strict, import-linter chạy sạch.
