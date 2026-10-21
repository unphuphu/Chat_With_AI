# T-001 — Tạo monorepo, công cụ lint/format và pipeline CI

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 0 |
| **Loại** | DevOps |
| **User story** | — nền tảng |
| **Ưu tiên** | P0 |
| **Ước lượng** | 1 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-000 |
| **Mở khóa (task chờ task này)** | T-002, T-003, T-005 |
| **Người thực hiện** | _chưa giao_ (BE) |
| **Trạng thái** | To do |

## 1. Mục tiêu

Repository có cấu trúc thư mục đúng [Implement_plan §3.1](../Implement_plan.md#31-cấu-trúc-repository-monorepo), công cụ lint/format/type-check cho backend và frontend, hợp đồng phụ thuộc `import-linter`, quét bí mật `gitleaks`, và một pipeline CI chạy trên mọi PR — **xanh với các job rỗng**.

## 2. Bối cảnh

- Quy tắc phụ thuộc kiến trúc (lõi nghiệp vụ không import adapter/SDK ngoài) được **cưỡng chế bằng CI** ([SAD §1.2](../../design/SAD.md#12-mô-thức-kiến-trúc), Implement_plan §3.1).
- PR cần CI xanh gồm lint, type check, test, import-linter, gitleaks (Implement_plan §4.3).
- Quét bí mật là yêu cầu bảo mật ([SAD §4.1.3](../../design/SAD.md#413-quản-lý-bí-mật)).
- Repo hiện chỉ có `docs/`; thư mục gốc repo chính là `chat-with-docs/` trong sơ đồ §3.1.

## 3. Phạm vi

**Trong phạm vi**
- Khung thư mục `backend/`, `frontend/`, `eval/`, `deploy/`, `.github/workflows/` (rỗng hoặc tệp giữ chỗ).
- `backend/pyproject.toml`: ruff (lint + format), mypy, pytest, import-linter.
- `frontend/package.json`: eslint, prettier, TypeScript `tsc --noEmit`, Vitest (chưa có test thật).
- `.gitleaks.toml`, `.gitignore`, `.editorconfig`, mẫu PR.
- `.github/workflows/ci.yml` với các job song song.

**Ngoài phạm vi**
- Mã ứng dụng FastAPI ([T-003](./T-003-fastapi-skeleton.md)) và React ([T-005](./T-005-frontend-skeleton.md)).
- `docker-compose`, `Makefile` ([T-002](./T-002-docker-compose-local-env.md)).
- Quét lỗ hổng phụ thuộc đầy đủ và chính sách bảo mật ([T-405](./T-405-security-hardening.md)); E2E Playwright chạy khi merge ([T-111](./T-111-e2e-sprint1.md)).

## 4. Thiết kế chi tiết

**Tệp tạo mới**

```text
.editorconfig
.gitignore                       # .env, node_modules, .venv, __pycache__, dist, eval/report*.md, *.pdf ngoài tests/fixtures
.gitleaks.toml
.github/workflows/ci.yml
.github/pull_request_template.md # checklist DoD §4.5
backend/pyproject.toml
backend/app/__init__.py          # và __init__.py rỗng cho: platform, access, documents, ingestion, retrieval,
                                 # answering, conversations, feedback, analytics, jobs, ports, adapters
backend/tests/{unit,integration,contract}/__init__.py
backend/tests/unit/test_smoke.py # assert True — giữ job test xanh
frontend/package.json, tsconfig.json, .eslintrc.cjs (hoặc eslint.config.js), .prettierrc
eval/README.md                   # một dòng: xem T-009/T-211
deploy/.gitkeep
```

**`backend/pyproject.toml` — phần công cụ** (quản lý gói `[Proposed: uv]` theo kết luận T-000):

```toml
[project]
name = "chat-with-docs-backend"
requires-python = ">=3.12,<3.13"

[tool.ruff]
line-length = 100
target-version = "py312"
[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "S", "ASYNC"]   # S = bandit-lite

[tool.mypy]
python_version = "3.12"
strict = true
packages = ["app"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.importlinter]
root_package = "app"
include_external_packages = true

[[tool.importlinter.contracts]]
name = "Lõi nghiệp vụ không import adapter hay SDK bên ngoài"
type = "forbidden"
source_modules = ["app.documents", "app.ingestion", "app.retrieval", "app.answering",
                  "app.conversations", "app.feedback", "app.analytics"]
forbidden_modules = ["app.adapters", "boto3", "botocore", "aioboto3", "pypdfium2",
                     "pdfminer", "openai", "anthropic", "authlib"]

[[tool.importlinter.contracts]]
name = "Ports không phụ thuộc adapter"
type = "forbidden"
source_modules = ["app.ports"]
forbidden_modules = ["app.adapters"]
```

Danh sách `forbidden_modules` bổ sung khi thêm SDK mới (ví dụ ở [T-208](./T-208-real-ai-adapters-reindex.md)). Chỉ `app.main`, `app.worker` (composition root) và `app.adapters.*` được import adapter.

**`frontend/package.json` — scripts**

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint . --max-warnings 0",
    "format:check": "prettier --check .",
    "typecheck": "tsc --noEmit",
    "test": "vitest run --passWithNoTests"
  },
  "engines": { "node": ">=20" }
}
```

ESLint bật rule cấm `dangerouslySetInnerHTML` (`react/no-danger: error`) theo Implement_plan §4.2.

**`.github/workflows/ci.yml` — các job** (kích hoạt `pull_request` và `push` vào `main`):

| Job | Bước | Lệnh |
|---|---|---|
| `backend-lint` | cài Python 3.12 + deps | `ruff check .` · `ruff format --check .` · `mypy` |
| `backend-arch` | — | `lint-imports` |
| `backend-test` | runner có Docker (cho Testcontainers ở task sau) | `pytest -q` |
| `frontend-lint` | Node 20, `npm ci` | `npm run lint` · `npm run format:check` · `npm run typecheck` |
| `frontend-test` | — | `npm test` |
| `secrets` | — | `gitleaks detect --source . --redact` |

Cache pip/npm theo hash lockfile. Thời gian mục tiêu toàn pipeline ≤ 10 phút `[Proposed]`.

## 5. Các bước thực hiện

1. Tạo cây thư mục và `__init__.py` cho mọi package backend liệt kê ở §3.1.
2. Viết `backend/pyproject.toml` như trên; khóa phiên bản (lockfile) và commit.
3. Khởi tạo `frontend/package.json`, `tsconfig.json` (strict), cấu hình eslint/prettier; commit lockfile.
4. Thêm `.gitleaks.toml` (mặc định + allowlist `deploy/.env.example`), `.gitignore`, `.editorconfig`.
5. Viết `ci.yml` theo bảng; đẩy nhánh `feature/T-001-monorepo-ci` và mở PR.
6. Cố ý thử: thêm `import boto3` vào `app/documents/__init__.py` ở một commit tạm → `backend-arch` đỏ; xóa commit.
7. Cố ý thử: thêm chuỗi giống khóa AWS vào tệp tạm → `secrets` đỏ; xóa.
8. Bật branch protection cho `main`: yêu cầu 6 job xanh + 1 review (Tech Lead).

## 6. Tiêu chí chấp nhận

- [ ] Cây thư mục khớp §3.1 (các thư mục `backend/app/*` liệt kê đều tồn tại).
- [ ] Trên PR, 6 job `backend-lint`, `backend-arch`, `backend-test`, `frontend-lint`, `frontend-test`, `secrets` đều chạy và xanh.
- [ ] Một import `app.adapters` hoặc `boto3` từ `app.documents` làm `backend-arch` thất bại (đã chứng minh ở bước 6).
- [ ] Một bí mật giả trong mã làm job `secrets` thất bại (bước 7).
- [ ] `react/no-danger` ở mức `error`.
- [ ] Branch protection trên `main` đã bật.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| CI | PR không đổi mã | 6 job xanh |
| CI | Vi phạm hợp đồng import | `lint-imports` exit ≠ 0, nêu tên hợp đồng |
| CI | Bí mật giả (`AKIA...`) | `gitleaks` exit ≠ 0 |
| CI | Lỗi format Python/TS | `ruff format --check` / `prettier --check` đỏ |
| Unit | `tests/unit/test_smoke.py` | pass |

## 8. Cấu hình

Không thêm biến môi trường ứng dụng. CI không cần bí mật ở task này. Phiên bản: Python 3.12, Node.js 20 LTS (Implement_plan §3.2).

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Tổ chức dùng CI khác GitHub Actions (T-000) | Phải viết lại pipeline | Giữ lệnh trong từng job đơn giản để chuyển dễ; T-002 bọc lệnh vào `Makefile` |
| Runner CI không có Docker | Testcontainers (T-003 trở đi) không chạy | Xác nhận ở T-000; dùng runner tự quản nếu cần |
| `mypy --strict` gây chậm khi bắt đầu | Dev bỏ qua lỗi | Giữ strict cho `app/`; cho phép `# type: ignore[...]` có lý do |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §3.1, §4.1, §4.2, §4.3, §5.1
- [SAD](../../design/SAD.md) §1.2 (quy tắc cưỡng chế kiến trúc), §4.1.3, §6
- [T-000](./T-000-kickoff-technical-decisions.md) (chọn CI, công cụ quản lý gói)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)) ở phần áp dụng được.
- [ ] `docs/` không bị thay đổi ngoài ý muốn; README gốc (nếu có) ghi lệnh chạy lint/test.
