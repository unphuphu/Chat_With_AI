# T-004 — Thiết lập Alembic và migration nền (bảng lõi, extension, chỉ mục)

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 0 |
| **Loại** | Backend |
| **User story** | — nền tảng |
| **Ưu tiên** | P0 |
| **Ước lượng** | 1,5 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-003 |
| **Mở khóa (task chờ task này)** | T-006, T-101, T-201 |
| **Người thực hiện** | _chưa giao_ (BE) |
| **Trạng thái** | To do |

## 1. Mục tiêu

`make migrate` tạo trên PostgreSQL 16 một lược đồ có đủ extension `vector`, `unaccent`, hàm `f_unaccent` bất biến và 7 bảng `app_user`, `session`, `document`, `chunk`, `job`, `audit_log`, `usage_event` cùng toàn bộ ràng buộc và chỉ mục; `make migrate-down` gỡ sạch. Các bảng hội thoại (`conversation`, `message`, `citation`, `feedback`) **không** thuộc task này.

## 2. Bối cảnh

- DDL nguồn: [SAD §3.1](../../design/SAD.md#31-chiến-lược-mô-hình-dữ-liệu-cốt-lõi) (`document`, `chunk`, `job`) và [Implement_plan §6.1](../Implement_plan.md#61-lược-đồ-csdl) (bảng còn lại). Mô hình thực thể: [Blueprint §3.4](../../design/Blueprint_Design.md#34-information-view).
- `document.status` là nguồn sự thật duy nhất cho "được dùng làm nguồn" (BRU-002); trạng thái theo [Blueprint §3.7](../../design/Blueprint_Design.md#37-state-dynamics-view).
- Chunk không vượt trang (DD-04) → `chunk.page NOT NULL`, `UNIQUE(document_id, page, chunk_index)`.
- `chunk.embedding_model` để không trộn không gian vector (DR-04); số chiều `vector(N)` theo `EMBEDDING_DIM`.
- `unaccent` là `STABLE` nên cột sinh `keywords` phải dùng hàm bọc `IMMUTABLE` `f_unaccent` (SAD §3.1 ghi chú, Implement_plan §6.1).
- Migration theo Expand/Contract, có bước đảo ngược ([SAD §4.2](../../design/SAD.md#42-độ-tin-cậy-và-khả-năng-chịu-lỗi)).

## 3. Phạm vi

**Trong phạm vi**
- `backend/alembic.ini`, `backend/migrations/env.py` (async), revision `0001_baseline`.
- Mô hình SQLAlchemy 2 cho 7 bảng (để repository ở task sau dùng).
- Phân vùng tháng ban đầu cho `usage_event`.
- Test tích hợp lên/xuống.

**Ngoài phạm vi**
- `conversation`, `message`, `citation`, `feedback`, RLS ([T-201](./T-201-conversation-schema.md)).
- Vai trò CSDL chỉ `INSERT/SELECT` trên `audit_log` ([T-405](./T-405-security-hardening.md)); tạo phân vùng cuốn chiếu, dọn dữ liệu ([T-407](./T-407-retention-cleanup.md)).
- Đổi số chiều vector + `reindex_all` ([T-208](./T-208-real-ai-adapters-reindex.md)).

## 4. Thiết kế chi tiết

**Tệp**

```text
backend/alembic.ini
backend/migrations/env.py                     # async engine từ Settings.DATABASE_URL; target_metadata = Base.metadata
backend/migrations/versions/0001_baseline.py  # SQL viết tay qua op.execute cho vector/tsvector/partition
backend/app/access/models.py                  # AppUser, Session
backend/app/documents/models.py               # Document
backend/app/ingestion/models.py               # Chunk (pgvector.sqlalchemy.Vector)
backend/app/jobs/models.py                    # Job
backend/app/platform/audit_models.py          # AuditLog
backend/app/analytics/models.py               # UsageEvent
backend/tests/integration/test_migrations.py
```

**DDL của `0001_baseline.upgrade()`** — giữ nguyên tên cột theo nguồn; mục ghi `[Proposed]` là bổ sung kỹ thuật tối thiểu:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Bọc unaccent thành IMMUTABLE để dùng trong cột sinh và chỉ mục [Verify]
CREATE OR REPLACE FUNCTION f_unaccent(text) RETURNS text
  LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
  AS $$ SELECT public.unaccent('public.unaccent'::regdictionary, $1) $$;

CREATE TABLE app_user (
  id uuid PRIMARY KEY,
  external_subject text UNIQUE NOT NULL,
  display_name text NOT NULL,
  role text NOT NULL CHECK (role IN ('MEMBER','SPONSOR','ADMIN')),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE session (
  id text PRIMARY KEY,                               -- 256-bit ngẫu nhiên, base64url
  user_id uuid NOT NULL REFERENCES app_user(id),
  csrf_token text NOT NULL,
  expires_at timestamptz NOT NULL,                   -- hết hạn tuyệt đối
  last_seen_at timestamptz NOT NULL                  -- tính hết hạn khi rảnh
);
CREATE INDEX session_user_idx    ON session (user_id);            -- [Proposed] thu hồi theo user
CREATE INDEX session_expires_idx ON session (expires_at);         -- [Proposed] dọn phiên (T-407)

CREATE TABLE document (
  id uuid PRIMARY KEY,
  name text NOT NULL,
  status text NOT NULL CHECK (status IN
    ('UPLOADED','PROCESSING','READY','NOT_EXTRACTABLE','FAILED','DELETED')),
  file_ref text NOT NULL,
  content_hash text NOT NULL,
  page_count int,
  size_bytes bigint NOT NULL,
  uploaded_by uuid NOT NULL REFERENCES app_user(id),
  uploaded_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  failure_reason text
);
CREATE INDEX document_status_idx   ON document (status);
CREATE INDEX document_list_idx     ON document (uploaded_at DESC, id DESC);   -- [Proposed] phân trang cursor API-03
CREATE INDEX document_dedupe_idx   ON document (uploaded_by, content_hash);   -- [Proposed] trùng content_hash 24h (SAD §2.4)

CREATE TABLE chunk (
  id uuid PRIMARY KEY,
  document_id uuid NOT NULL REFERENCES document(id),
  page int NOT NULL,                                 -- DD-04
  chunk_index int NOT NULL,
  text text NOT NULL,
  embedding_model text NOT NULL,
  embedding vector(:EMBEDDING_DIM) NOT NULL,         -- render từ Settings.EMBEDDING_DIM, mặc định 384
  keywords tsvector GENERATED ALWAYS AS (to_tsvector('simple', f_unaccent(text))) STORED,
  UNIQUE (document_id, page, chunk_index)
);
CREATE INDEX chunk_embedding_hnsw ON chunk USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
CREATE INDEX chunk_keywords_gin   ON chunk USING gin (keywords);
CREATE INDEX chunk_document_idx   ON chunk (document_id);

CREATE TABLE job (
  id uuid PRIMARY KEY,
  type text NOT NULL,                                -- ingest_document | purge_document | reindex_all
  payload jsonb NOT NULL,
  status text NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued','running','succeeded','failed')),   -- [Proposed] CHECK theo SAD §2.2
  attempts int NOT NULL DEFAULT 0,
  max_attempts int NOT NULL DEFAULT 5,
  run_after timestamptz NOT NULL DEFAULT now(),
  locked_by text,
  locked_at timestamptz,
  last_error text,
  created_at timestamptz NOT NULL DEFAULT now()      -- [Proposed] cho metric job_age_seconds (T-404)
);
CREATE INDEX job_ready_idx   ON job (run_after) WHERE status = 'queued';
CREATE INDEX job_running_idx ON job (locked_at) WHERE status = 'running';  -- [Proposed] quét việc mồ côi (T-101)

CREATE TABLE audit_log (
  id uuid PRIMARY KEY,
  user_id uuid,                                      -- null khi chưa xác thực
  action text NOT NULL,                              -- login_success, login_failed, upload, delete, access_denied, ...
  target text,
  result text NOT NULL,
  occurred_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX audit_log_time_idx ON audit_log (occurred_at);                -- [Proposed]

CREATE TABLE usage_event (
  id uuid NOT NULL,
  event_name text NOT NULL,
  user_id uuid,
  properties jsonb NOT NULL DEFAULT '{}',
  occurred_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id, occurred_at)                      -- [Proposed] PK bảng phân vùng phải chứa khóa phân vùng
) PARTITION BY RANGE (occurred_at);
CREATE INDEX usage_event_name_time_idx ON usage_event (event_name, occurred_at);  -- [Proposed] báo cáo tuần
CREATE TABLE usage_event_default PARTITION OF usage_event DEFAULT;               -- [Proposed] không mất sự kiện
-- Phân vùng tháng: tháng hiện tại + 3 tháng kế tiếp lúc chạy migration, tên usage_event_yYYYYmMM [Proposed]
```

**`downgrade()`** — đảo thứ tự: `DROP TABLE usage_event CASCADE`, `audit_log`, `job`, `chunk`, `document`, `session`, `app_user`, `DROP FUNCTION f_unaccent(text)`. Extension giữ lại (`DROP EXTENSION` có thể ảnh hưởng đối tượng khác trên CSDL dùng chung) — ghi chú trong mã.

**Quy tắc**
- `:EMBEDDING_DIM` lấy từ `get_settings()` khi chạy migration; kiểm `1 ≤ EMBEDDING_DIM ≤ 2000` (giới hạn HNSW kiểu `vector` `[Verify]`), vượt → migration dừng với thông báo rõ.
- Không có cột chủ sở hữu quyết định quyền đọc trên `document`/`chunk` (thư viện dùng chung, ASM-002).
- Mô hình SQLAlchemy không khai báo cột `keywords` là ghi được (`Computed`, chỉ đọc).
- Module chỉ truy cập bảng của mình (Implement_plan §3.1); `retrieval` được đọc `chunk` và `document`.

## 5. Các bước thực hiện

1. `alembic init` (template async), sửa `env.py` lấy URL từ `Settings`, `compare_type=True`.
2. Viết `0001_baseline.py` bằng `op.execute()` theo DDL trên; hàm `_month_partitions(now)` tạo 4 phân vùng tháng.
3. Viết mô hình SQLAlchemy cho 7 bảng (đúng tên cột, kiểu, nullable); `pgvector.sqlalchemy.Vector(settings.EMBEDDING_DIM)`.
4. Test tích hợp (Testcontainers image `pgvector/pgvector:pg16`): `upgrade head` → kiểm bảng, chỉ mục, hàm → `downgrade base` → kiểm sạch → `upgrade head` lần 2.
5. Test `f_unaccent`: `SELECT f_unaccent('Hợp đồng khung')` = `'Hop đong khung'` hoặc tương đương `[Verify]` — ghi lại kết quả thực tế cho chữ `đ`.
6. Test cột sinh: chèn chunk với text `'Điều kiện thanh toán'` → `keywords @@ plainto_tsquery('simple', f_unaccent('dieu kien'))` trả đúng dòng.
7. Test ràng buộc: chèn `document.status='ARCHIVED'` → lỗi CHECK; chèn trùng `(document_id, page, chunk_index)` → lỗi UNIQUE.
8. Chạy `make migrate` và `make migrate-down` trên compose local.

## 6. Tiêu chí chấp nhận

- [ ] `make migrate` thành công trên CSDL trống; `alembic current` = `0001_baseline`.
- [ ] `\dt` có đủ 7 bảng; `\di` có đủ chỉ mục liệt kê ở mục 4 (kể cả `chunk_embedding_hnsw` kiểu hnsw, `chunk_keywords_gin` kiểu gin, `job_ready_idx` có điều kiện).
- [ ] `f_unaccent` có `provolatile = 'i'` trong `pg_proc`.
- [ ] Truy vấn full-text bỏ dấu ở bước 6 trả đúng 1 dòng.
- [ ] `document.status` từ chối giá trị ngoài 6 trạng thái; `app_user.role` từ chối giá trị ngoài `MEMBER/SPONSOR/ADMIN`.
- [ ] Chèn `usage_event` với `occurred_at` thuộc tháng hiện tại vào đúng phân vùng tháng; ngoài 4 tháng → `usage_event_default`.
- [ ] `make migrate-down` xóa sạch 7 bảng và `f_unaccent`; `upgrade` lại lần 2 thành công.
- [ ] `EMBEDDING_DIM=2001` → migration dừng với thông báo nêu giới hạn.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Integration | upgrade → downgrade → upgrade | Không lỗi; trạng thái cuối giống lần đầu |
| Integration | Liệt kê chỉ mục từ `pg_indexes` | Khớp danh sách mục 4 |
| Integration | `keywords` với tiếng Việt có dấu, truy vấn không dấu | Khớp |
| Integration | CHECK `status`, `role`, `job.status`; UNIQUE chunk | Vi phạm → `IntegrityError` |
| Integration | Chèn vector sai số chiều (383) | Lỗi kiểu `vector` |
| Unit | `_month_partitions(datetime(2026,11,15))` | 4 phân vùng 2026-11…2027-02, biên đúng |

## 8. Cấu hình

`DATABASE_URL`, `EMBEDDING_DIM` (`384` `[Default]`; mô hình thật chọn sau **OQ-006**/SP-04 — đổi số chiều cần migration mới + `reindex_all` ở T-208).

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| SAD §3.1 ghi `vector(1536)`, plan mặc định `384` | Nhầm số chiều | Dùng `EMBEDDING_DIM` từ cấu hình; 1536 chỉ là ví dụ |
| Hàm bọc `f_unaccent` trên dịch vụ PG quản lý (quyền tạo hàm, đường dẫn từ điển) `[Verify]` | Migration lỗi trên staging | Thử trên staging sớm ở T-409; tham chiếu từ điển bằng tên đủ lược đồ `public.unaccent` |
| `unaccent` có thể không đổi `đ` → `d` | Tìm "dong" không khớp "đồng" | Ghi kết quả ở bước 5; nếu cần, `f_unaccent` thêm `replace(…, 'đ', 'd')` `[Proposed]` — quyết định cùng T-203 |
| Thời gian lưu giữ `usage_event` `[TBD: OQ-019]` | Số phân vùng cần giữ | Mặc định 13 tháng (SAD §2.3), xử lý ở T-407 |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §3.1, §6.1, §6.2, §6.3
- [SAD](../../design/SAD.md) §2.3 (chỉ mục, lưu giữ), §3.1 (DDL), §4.2 (Expand/Contract)
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.4, §3.7

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Migration có docstring nêu "có thể đảo ngược" và lý do giữ extension khi downgrade.
