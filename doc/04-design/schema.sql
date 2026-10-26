-- =============================================================================
-- AI Chat với tài liệu PDF – MVP
-- Schema PostgreSQL 16 + pgvector (>= 0.8)
-- Tài liệu: doc/04-design/DATABASE_DESIGN.md (giải thích), BLUEPRINT.md 3.5
-- Phiên bản: 0.3 – 2026-10-24
--   0.1  bản đầu
--   0.2  xóa đoạn khi xóa mềm; hàm cho purge; workspace.personal_owner_id
--   0.3  quy ước đặt tên (DATABASE_DESIGN mục A.0); document.client_file_id (API AD-06);
--        chunk.embedding_model; view; trigger bảo vệ bất biến; COMMENT; audit_event, analytics_event
--
-- Quy ước:
--   * Mọi bảng chứa dữ liệu người dùng có cột workspace_id và bật Row-Level Security.
--   * Ngưỡng nghiệp vụ (20 MB, 300 trang, 10 file, 100 tài liệu, 2.000 ký tự) KHÔNG đặt trong CHECK
--     – chúng là cấu hình ứng dụng (BLUEPRINT 3.6.6).
--   * Chạy bởi vai trò app_migrator (chủ sở hữu schema, có BYPASSRLS) qua Alembic revision 0001.
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- -----------------------------------------------------------------------------
-- Vai trò (DBA tạo một lần; mật khẩu lấy từ secret manager)
-- -----------------------------------------------------------------------------
-- CREATE ROLE app_migrator           LOGIN BYPASSRLS;   -- sở hữu schema; chỉ dùng khi migrate
-- CREATE ROLE app_api                LOGIN NOBYPASSRLS;
-- CREATE ROLE app_worker             LOGIN NOBYPASSRLS;
-- CREATE ROLE app_maintenance        LOGIN NOBYPASSRLS;
-- CREATE ROLE app_readonly_audit     LOGIN NOBYPASSRLS;  -- IT/Security tra cứu nhật ký (US-C02)
-- CREATE ROLE app_readonly_analytics LOGIN NOBYPASSRLS;  -- PO/BI xem báo cáo (PRD 5.2)

-- -----------------------------------------------------------------------------
-- Kiểu liệt kê
-- -----------------------------------------------------------------------------
CREATE TYPE document_status AS ENUM ('PROCESSING', 'READY', 'FAILED');
CREATE TYPE failure_code    AS ENUM ('R-01', 'R-02', 'R-03', 'R-04');
CREATE TYPE message_status  AS ENUM ('PENDING', 'ANSWERED', 'INSUFFICIENT', 'FAILED');
CREATE TYPE job_kind        AS ENUM ('ingest_document', 'purge_document');
CREATE TYPE job_status      AS ENUM ('QUEUED', 'RUNNING', 'DONE', 'FAILED', 'CANCELLED');
CREATE TYPE user_role       AS ENUM ('user', 'admin');
CREATE TYPE workspace_kind  AS ENUM ('personal', 'shared');

-- -----------------------------------------------------------------------------
-- Phạm vi workspace cho RLS. NULL khi chưa đặt → mọi so sánh = NULL → không thấy hàng nào.
-- -----------------------------------------------------------------------------
CREATE FUNCTION fn_current_workspace() RETURNS uuid
    LANGUAGE sql STABLE
    AS $$ SELECT NULLIF(current_setting('app.workspace_id', true), '')::uuid $$;

-- =============================================================================
-- Danh tính (không chứa dữ liệu tài liệu → không bật RLS)
-- =============================================================================
CREATE TABLE app_user (
    id             uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    idp_subject    text        NOT NULL,
    email          text        NOT NULL,
    role           user_role   NOT NULL DEFAULT 'user',
    created_at     timestamptz NOT NULL DEFAULT now(),
    last_login_at  timestamptz,
    CONSTRAINT uq_app_user_idp_subject UNIQUE (idp_subject)
);

CREATE TABLE workspace (
    id                 uuid           PRIMARY KEY DEFAULT gen_random_uuid(),
    kind               workspace_kind NOT NULL DEFAULT 'personal',
    personal_owner_id  uuid           REFERENCES app_user(id) ON DELETE CASCADE,
    created_at         timestamptz    NOT NULL DEFAULT now(),
    CONSTRAINT uq_workspace_personal_owner UNIQUE (personal_owner_id),
    CONSTRAINT ck_workspace_personal_has_owner CHECK ((kind = 'personal') = (personal_owner_id IS NOT NULL))
);

CREATE TABLE membership (
    workspace_id uuid NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    user_id      uuid NOT NULL REFERENCES app_user(id)  ON DELETE CASCADE,
    role         text NOT NULL DEFAULT 'owner',
    PRIMARY KEY (workspace_id, user_id),
    CONSTRAINT ck_membership_role CHECK (role IN ('owner', 'member'))
);
CREATE INDEX idx_membership_user ON membership (user_id);

CREATE TABLE session (
    id                   uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              uuid        NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    workspace_id         uuid        NOT NULL REFERENCES workspace(id),
    token_hash           bytea       NOT NULL,
    csrf_token_hash      bytea       NOT NULL,
    created_at           timestamptz NOT NULL DEFAULT now(),
    last_seen_at         timestamptz NOT NULL DEFAULT now(),
    idle_expires_at      timestamptz NOT NULL,
    absolute_expires_at  timestamptz NOT NULL,
    CONSTRAINT uq_session_token_hash UNIQUE (token_hash),
    CONSTRAINT ck_session_hash_length CHECK (octet_length(token_hash) = 32 AND octet_length(csrf_token_hash) = 32),
    CONSTRAINT ck_session_expiry_order CHECK (idle_expires_at <= absolute_expires_at)
);
CREATE INDEX idx_session_expiry ON session (idle_expires_at);
CREATE INDEX idx_session_user   ON session (user_id);

-- =============================================================================
-- Tải lên và tài liệu
-- =============================================================================
CREATE TABLE upload_batch (
    id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id     uuid        NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    created_by       uuid        NOT NULL REFERENCES app_user(id),
    remaining_slots  int         NOT NULL,
    created_at       timestamptz NOT NULL DEFAULT now(),
    expires_at       timestamptz NOT NULL,
    CONSTRAINT ck_upload_batch_slots CHECK (remaining_slots >= 0),
    CONSTRAINT ck_upload_batch_expiry CHECK (expires_at > created_at)
);
CREATE INDEX idx_upload_batch_workspace_expires ON upload_batch (workspace_id, expires_at);

CREATE TABLE document (
    id               uuid            PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id     uuid            NOT NULL REFERENCES workspace(id),
    batch_id         uuid            REFERENCES upload_batch(id) ON DELETE SET NULL,
    client_file_id   uuid            NOT NULL,
    file_name        text            NOT NULL,
    size_bytes       bigint          NOT NULL,
    page_count       int             NOT NULL,
    status           document_status NOT NULL DEFAULT 'PROCESSING',
    failure_code     failure_code,
    storage_key      text            NOT NULL,
    sha256           bytea           NOT NULL,
    uploaded_by      uuid            NOT NULL REFERENCES app_user(id),
    uploaded_at      timestamptz     NOT NULL DEFAULT now(),
    ready_at         timestamptz,
    deleted_at       timestamptz,
    purged_at        timestamptz,
    CONSTRAINT uq_document_storage_key       UNIQUE (storage_key),
    CONSTRAINT uq_document_batch_client_file UNIQUE (batch_id, client_file_id),
    CONSTRAINT ck_document_file_name         CHECK (char_length(file_name) BETWEEN 1 AND 255),
    CONSTRAINT ck_document_size              CHECK (size_bytes > 0),
    CONSTRAINT ck_document_page_count        CHECK (page_count > 0),
    CONSTRAINT ck_document_sha256            CHECK (octet_length(sha256) = 32),
    CONSTRAINT ck_document_failure_iff_failed CHECK ((status = 'FAILED') = (failure_code IS NOT NULL)),
    CONSTRAINT ck_document_ready_at          CHECK ((status = 'READY') = (ready_at IS NOT NULL)),
    CONSTRAINT ck_document_purged_after_deleted CHECK (purged_at IS NULL OR deleted_at IS NOT NULL)
);
CREATE INDEX idx_document_workspace_status ON document (workspace_id, status, uploaded_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_document_pending_purge    ON document (deleted_at) WHERE deleted_at IS NOT NULL AND purged_at IS NULL;

CREATE TABLE chunk (
    id               uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id      uuid         NOT NULL REFERENCES document(id) ON DELETE CASCADE,
    workspace_id     uuid         NOT NULL,
    page_number      int          NOT NULL,
    chunk_index      int          NOT NULL,
    token_count      int          NOT NULL,
    content          text         NOT NULL,
    tsv              tsvector     GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED,
    embedding_model  text         NOT NULL,
    embedding        vector(1024) NOT NULL,
    CONSTRAINT uq_chunk_document_index UNIQUE (document_id, chunk_index),
    CONSTRAINT ck_chunk_page_number   CHECK (page_number >= 1),
    CONSTRAINT ck_chunk_index         CHECK (chunk_index >= 0),
    CONSTRAINT ck_chunk_token_count   CHECK (token_count > 0),
    CONSTRAINT ck_chunk_content       CHECK (char_length(content) > 0)
);
CREATE INDEX idx_chunk_embedding_hnsw     ON chunk USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX idx_chunk_tsv_gin            ON chunk USING gin (tsv);
CREATE INDEX idx_chunk_workspace_document ON chunk (workspace_id, document_id);

-- =============================================================================
-- Hàng đợi tác vụ (SAD ADR-006)
-- =============================================================================
CREATE TABLE job (
    id               bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    kind             job_kind    NOT NULL,
    document_id      uuid        NOT NULL REFERENCES document(id),
    workspace_id     uuid        NOT NULL,
    status           job_status  NOT NULL DEFAULT 'QUEUED',
    attempts         int         NOT NULL DEFAULT 0,
    run_after        timestamptz NOT NULL DEFAULT now(),
    locked_until     timestamptz,
    last_error_code  text,
    trace_parent     text,
    created_at       timestamptz NOT NULL DEFAULT now(),
    finished_at      timestamptz,
    CONSTRAINT ck_job_attempts CHECK (attempts >= 0),
    CONSTRAINT ck_job_finished CHECK ((status IN ('DONE', 'FAILED', 'CANCELLED')) = (finished_at IS NOT NULL))
);
CREATE INDEX idx_job_claim ON job (run_after) WHERE status IN ('QUEUED', 'RUNNING');
CREATE UNIQUE INDEX uq_job_active_per_document_kind ON job (document_id, kind) WHERE status IN ('QUEUED', 'RUNNING');
CREATE INDEX idx_job_finished ON job (finished_at) WHERE finished_at IS NOT NULL;

-- =============================================================================
-- Hội thoại (giữ trong phiên – NFR-024)
-- =============================================================================
CREATE TABLE conversation (
    id            uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id    uuid        NOT NULL REFERENCES session(id) ON DELETE CASCADE,
    workspace_id  uuid        NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_conversation_session ON conversation (session_id);

CREATE TABLE message (
    id                 uuid           PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id    uuid           NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
    workspace_id       uuid           NOT NULL,
    client_request_id  uuid           NOT NULL,
    question           text           NOT NULL,
    answer             text,
    status             message_status NOT NULL DEFAULT 'PENDING',
    error_code         text,
    attempt            int            NOT NULL DEFAULT 1,
    latency_ms         int,
    created_at         timestamptz    NOT NULL DEFAULT now(),
    updated_at         timestamptz    NOT NULL DEFAULT now(),
    CONSTRAINT uq_message_conversation_request UNIQUE (conversation_id, client_request_id),
    CONSTRAINT ck_message_question  CHECK (char_length(question) >= 1),
    CONSTRAINT ck_message_attempt   CHECK (attempt >= 1),
    CONSTRAINT ck_message_answer    CHECK (status <> 'ANSWERED' OR answer IS NOT NULL),
    CONSTRAINT ck_message_error     CHECK ((status = 'FAILED') = (error_code IS NOT NULL))
);
CREATE INDEX idx_message_conversation_created ON message (conversation_id, created_at);

CREATE TABLE citation (
    id                      uuid     PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id              uuid     NOT NULL REFERENCES message(id) ON DELETE CASCADE,
    workspace_id            uuid     NOT NULL,
    document_id             uuid     NOT NULL REFERENCES document(id),
    document_name_snapshot  text     NOT NULL,
    page_number             int,
    ordinal                 smallint NOT NULL,
    CONSTRAINT uq_citation_message_ordinal UNIQUE (message_id, ordinal),
    CONSTRAINT ck_citation_page    CHECK (page_number IS NULL OR page_number >= 1),
    CONSTRAINT ck_citation_ordinal CHECK (ordinal BETWEEN 1 AND 8)
);

-- =============================================================================
-- Giới hạn tần suất (BLUEPRINT DD-04)
-- =============================================================================
CREATE TABLE rate_limit_counter (
    user_id       uuid        NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    bucket        text        NOT NULL,
    window_start  timestamptz NOT NULL,
    count         int         NOT NULL,
    PRIMARY KEY (user_id, bucket, window_start),
    CONSTRAINT ck_rate_limit_bucket CHECK (bucket IN ('question', 'upload_file')),
    CONSTRAINT ck_rate_limit_count  CHECK (count >= 1)
);
CREATE INDEX idx_rate_limit_counter_window ON rate_limit_counter (window_start);

-- =============================================================================
-- Nhật ký kiểm toán – phân vùng theo tháng (NFR-012, NFR-023). Không có nội dung.
-- =============================================================================
CREATE TABLE audit_event (
    id            uuid        NOT NULL DEFAULT gen_random_uuid(),
    at            timestamptz NOT NULL DEFAULT now(),
    actor_id      uuid,
    workspace_id  uuid,
    action        text        NOT NULL,
    target_type   text,
    target_id     uuid,
    outcome       text        NOT NULL DEFAULT 'success',
    request_id    uuid,
    PRIMARY KEY (id, at),
    CONSTRAINT ck_audit_event_action CHECK (action IN (
        'login', 'login_denied', 'logout', 'document_upload', 'document_reject',
        'document_delete', 'document_reprocess', 'question_asked', 'access_denied')),
    CONSTRAINT ck_audit_event_outcome CHECK (outcome IN ('success', 'denied', 'error'))
) PARTITION BY RANGE (at);
CREATE INDEX idx_audit_event_actor_at ON audit_event (actor_id, at);
CREATE INDEX idx_audit_event_target   ON audit_event (target_id) WHERE target_id IS NOT NULL;

CREATE FUNCTION fn_ensure_audit_partition(p_month date) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE
    v_start date := date_trunc('month', p_month)::date;
    v_name  text := format('audit_event_%s', to_char(v_start, 'YYYY_MM'));
BEGIN
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_event FOR VALUES FROM (%L) TO (%L)',
        v_name, v_start, (v_start + interval '1 month')::date);
END $$;

CREATE FUNCTION fn_drop_audit_partitions_before(p_cutoff date) RETURNS int
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE
    r record;
    n int := 0;
BEGIN
    -- Chỉ xóa phân vùng mà TOÀN BỘ khoảng thời gian nằm trước p_cutoff
    FOR r IN
        SELECT c.relname,
               to_date(right(c.relname, 7), 'YYYY_MM') AS month_start
        FROM pg_inherits i
        JOIN pg_class c ON c.oid = i.inhrelid
        WHERE i.inhparent = 'audit_event'::regclass
    LOOP
        IF (r.month_start + interval '1 month')::date <= p_cutoff THEN
            EXECUTE format('DROP TABLE %I', r.relname);
            n := n + 1;
        END IF;
    END LOOP;
    RETURN n;
END $$;

SELECT fn_ensure_audit_partition(date_trunc('month', now())::date);
SELECT fn_ensure_audit_partition((date_trunc('month', now()) + interval '1 month')::date);

-- =============================================================================
-- Sự kiện analytics (PRD 5.2) – không có nội dung; actor_hash = HMAC-SHA256(user_id)
-- =============================================================================
CREATE TABLE analytics_event (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    at          timestamptz NOT NULL DEFAULT now(),
    event_name  text        NOT NULL,
    actor_hash  bytea,
    properties  jsonb       NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT ck_analytics_event_name CHECK (event_name IN (
        'document_upload_started', 'document_upload_rejected',
        'document_processing_completed', 'document_processing_failed',
        'document_deleted', 'question_submitted', 'answer_returned',
        'answer_failed', 'citation_clicked', 'question_retried', 'access_denied')),
    CONSTRAINT ck_analytics_event_no_content CHECK (
        NOT (properties ?| ARRAY['question', 'answer', 'content', 'file_name', 'email']))
);
CREATE INDEX idx_analytics_event_name_at ON analytics_event (event_name, at);
CREATE INDEX idx_analytics_event_at      ON analytics_event (at);

-- =============================================================================
-- Trigger
-- =============================================================================

-- Cập nhật updated_at của message
CREATE FUNCTION fn_trg_set_updated_at() RETURNS trigger
    LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END $$;

CREATE TRIGGER trg_message_set_updated_at_before_update
    BEFORE UPDATE ON message
    FOR EACH ROW EXECUTE FUNCTION fn_trg_set_updated_at();

-- Chỉ cho phép các chuyển trạng thái hợp lệ của tài liệu (SAD 5.4)
CREATE FUNCTION fn_trg_document_status_transition() RETURNS trigger
    LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.status = OLD.status THEN
        RETURN NEW;
    END IF;
    IF (OLD.status = 'PROCESSING' AND NEW.status IN ('READY', 'FAILED'))
       OR (OLD.status = 'FAILED' AND NEW.status = 'PROCESSING') THEN
        RETURN NEW;
    END IF;
    RAISE EXCEPTION 'invalid document status transition % -> % (document %)', OLD.status, NEW.status, OLD.id
        USING ERRCODE = 'check_violation';
END $$;

CREATE TRIGGER trg_document_status_transition_before_update
    BEFORE UPDATE OF status ON document
    FOR EACH ROW EXECUTE FUNCTION fn_trg_document_status_transition();

-- Bất biến "đoạn tồn tại ⇔ tài liệu READY và chưa xóa" (BLUEPRINT 3.2.3), kiểm tra lúc COMMIT
CREATE FUNCTION fn_trg_chunk_requires_ready_document() RETURNS trigger
    LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM document d
                   WHERE d.id = NEW.document_id AND d.status = 'READY' AND d.deleted_at IS NULL) THEN
        RAISE EXCEPTION 'chunk % belongs to document % that is not READY or is deleted', NEW.id, NEW.document_id
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NULL;
END $$;

CREATE CONSTRAINT TRIGGER trg_chunk_ready_document_after_insert
    AFTER INSERT ON chunk
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION fn_trg_chunk_requires_ready_document();

CREATE FUNCTION fn_trg_document_chunks_consistent() RETURNS trigger
    LANGUAGE plpgsql AS $$
BEGIN
    IF (NEW.status <> 'READY' OR NEW.deleted_at IS NOT NULL)
       AND EXISTS (SELECT 1 FROM chunk c WHERE c.document_id = NEW.id) THEN
        RAISE EXCEPTION 'document % is not READY or is deleted but still has chunks', NEW.id
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NULL;
END $$;

CREATE CONSTRAINT TRIGGER trg_document_chunks_consistent_after_update
    AFTER UPDATE OF status, deleted_at ON document
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION fn_trg_document_chunks_consistent();

-- =============================================================================
-- View (security_invoker: RLS áp dụng theo người gọi, không theo chủ sở hữu view)
-- =============================================================================
CREATE VIEW vw_document_list WITH (security_invoker = true) AS
SELECT d.id, d.workspace_id, d.file_name, d.status, d.failure_code,
       (d.failure_code = 'R-04') IS TRUE AS retryable,
       d.page_count, d.size_bytes, d.uploaded_at, d.ready_at
FROM document d
WHERE d.deleted_at IS NULL;

CREATE VIEW vw_workspace_quota WITH (security_invoker = true) AS
SELECT w.id AS workspace_id,
       (SELECT count(*) FROM document d
         WHERE d.workspace_id = w.id AND d.deleted_at IS NULL)                     AS documents_used,
       (SELECT coalesce(sum(b.remaining_slots), 0) FROM upload_batch b
         WHERE b.workspace_id = w.id AND b.expires_at > now())                     AS reserved_slots
FROM workspace w;

-- Báo cáo (chỉ đọc analytics_event – không có nội dung, không có RLS)
CREATE VIEW vw_report_daily_questions AS
SELECT date_trunc('day', at)::date                                                AS day,
       count(*) FILTER (WHERE event_name = 'question_submitted')                    AS questions,
       count(*) FILTER (WHERE event_name = 'answer_returned' AND properties->>'status' = 'ANSWERED')     AS answered,
       count(*) FILTER (WHERE event_name = 'answer_returned' AND properties->>'status' = 'INSUFFICIENT') AS insufficient,
       count(*) FILTER (WHERE event_name = 'answer_failed')                         AS failed,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY (properties->>'latency_ms')::int)
           FILTER (WHERE event_name = 'answer_returned')                           AS latency_p50_ms,
       percentile_cont(0.9) WITHIN GROUP (ORDER BY (properties->>'latency_ms')::int)
           FILTER (WHERE event_name = 'answer_returned')                           AS latency_p90_ms
FROM analytics_event
WHERE event_name IN ('question_submitted', 'answer_returned', 'answer_failed')
GROUP BY 1;

CREATE VIEW vw_report_daily_ingestion AS
SELECT date_trunc('day', at)::date                                                AS day,
       count(*) FILTER (WHERE event_name = 'document_processing_completed')         AS completed,
       count(*) FILTER (WHERE event_name = 'document_processing_failed')            AS failed,
       count(*) FILTER (WHERE event_name = 'document_processing_failed' AND properties->>'failure_code' = 'R-03') AS failed_scanned,
       percentile_cont(0.9) WITHIN GROUP (ORDER BY (properties->>'duration_ms')::int)
           FILTER (WHERE event_name = 'document_processing_completed')             AS duration_p90_ms
FROM analytics_event
WHERE event_name IN ('document_processing_completed', 'document_processing_failed')
GROUP BY 1;

CREATE VIEW vw_report_weekly_active_users AS
SELECT date_trunc('week', at)::date AS week,
       count(DISTINCT actor_hash)   AS active_users
FROM analytics_event
WHERE event_name = 'question_submitted' AND actor_hash IS NOT NULL
GROUP BY 1;

-- =============================================================================
-- Row-Level Security
-- =============================================================================
ALTER TABLE upload_batch ENABLE ROW LEVEL SECURITY;  ALTER TABLE upload_batch FORCE ROW LEVEL SECURITY;
ALTER TABLE document     ENABLE ROW LEVEL SECURITY;  ALTER TABLE document     FORCE ROW LEVEL SECURITY;
ALTER TABLE chunk        ENABLE ROW LEVEL SECURITY;  ALTER TABLE chunk        FORCE ROW LEVEL SECURITY;
ALTER TABLE job          ENABLE ROW LEVEL SECURITY;  ALTER TABLE job          FORCE ROW LEVEL SECURITY;
ALTER TABLE conversation ENABLE ROW LEVEL SECURITY;  ALTER TABLE conversation FORCE ROW LEVEL SECURITY;
ALTER TABLE message      ENABLE ROW LEVEL SECURITY;  ALTER TABLE message      FORCE ROW LEVEL SECURITY;
ALTER TABLE citation     ENABLE ROW LEVEL SECURITY;  ALTER TABLE citation     FORCE ROW LEVEL SECURITY;

CREATE POLICY pol_upload_batch_ws_isolation ON upload_batch TO app_api, app_worker
    USING (workspace_id = fn_current_workspace()) WITH CHECK (workspace_id = fn_current_workspace());
CREATE POLICY pol_document_ws_isolation ON document TO app_api, app_worker
    USING (workspace_id = fn_current_workspace()) WITH CHECK (workspace_id = fn_current_workspace());
CREATE POLICY pol_chunk_ws_isolation ON chunk TO app_api, app_worker
    USING (workspace_id = fn_current_workspace()) WITH CHECK (workspace_id = fn_current_workspace());
CREATE POLICY pol_conversation_ws_isolation ON conversation TO app_api
    USING (workspace_id = fn_current_workspace()) WITH CHECK (workspace_id = fn_current_workspace());
CREATE POLICY pol_message_ws_isolation ON message TO app_api
    USING (workspace_id = fn_current_workspace()) WITH CHECK (workspace_id = fn_current_workspace());
CREATE POLICY pol_citation_ws_isolation ON citation TO app_api
    USING (workspace_id = fn_current_workspace()) WITH CHECK (workspace_id = fn_current_workspace());

-- job: API chỉ thấy job của workspace mình; worker cần lấy job của mọi workspace
-- (bảng job chỉ chứa ID và trạng thái, không có nội dung – BLUEPRINT DD-03)
CREATE POLICY pol_job_ws_isolation ON job TO app_api
    USING (workspace_id = fn_current_workspace()) WITH CHECK (workspace_id = fn_current_workspace());
CREATE POLICY pol_job_worker_claim ON job TO app_worker USING (true) WITH CHECK (true);

-- Bảo trì: chính sách áp cho mọi lệnh (DELETE có WHERE cũng cần qua chính sách SELECT);
-- GRANT giới hạn app_maintenance ở SELECT/DELETE.
CREATE POLICY pol_upload_batch_maintenance ON upload_batch TO app_maintenance
    USING (expires_at < now() - interval '1 day');
CREATE POLICY pol_job_maintenance ON job TO app_maintenance
    USING (status IN ('DONE', 'CANCELLED', 'FAILED') AND finished_at < now() - interval '7 days');

-- =============================================================================
-- Hàm cho lượt quét purge (BLUEPRINT ALG-10): đọc liên workspace nhưng chỉ trả ID/số liệu.
-- SECURITY DEFINER chạy với quyền app_migrator (có BYPASSRLS, vì bảng FORCE RLS).
-- =============================================================================
CREATE FUNCTION fn_pending_purges(p_older_than interval)
    RETURNS TABLE (document_id uuid, workspace_id uuid)
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT d.id, d.workspace_id
    FROM document d
    WHERE d.deleted_at IS NOT NULL
      AND d.purged_at IS NULL
      AND d.deleted_at < now() - p_older_than
      AND NOT EXISTS (SELECT 1 FROM job j
                      WHERE j.document_id = d.id AND j.kind = 'purge_document'
                        AND j.status IN ('QUEUED', 'RUNNING'))
$$;

CREATE FUNCTION fn_purge_lag_max_seconds() RETURNS double precision
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT coalesce(max(extract(epoch FROM now() - deleted_at)), 0)::double precision
    FROM document WHERE deleted_at IS NOT NULL AND purged_at IS NULL
$$;

-- =============================================================================
-- Quyền (tối thiểu cần thiết)
-- =============================================================================
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO app_api, app_worker, app_maintenance, app_readonly_audit, app_readonly_analytics;

REVOKE EXECUTE ON FUNCTION fn_ensure_audit_partition(date), fn_drop_audit_partitions_before(date),
                           fn_pending_purges(interval), fn_purge_lag_max_seconds() FROM PUBLIC;

GRANT SELECT, INSERT, UPDATE         ON app_user, workspace, membership           TO app_api;
GRANT SELECT, INSERT, UPDATE, DELETE ON session                                   TO app_api;
GRANT SELECT, INSERT, UPDATE         ON upload_batch, document                    TO app_api;
GRANT SELECT, DELETE                 ON chunk                                     TO app_api;   -- xóa mềm (ALG-12)
GRANT SELECT, INSERT, UPDATE         ON job                                       TO app_api;
GRANT SELECT, INSERT                 ON conversation                              TO app_api;
GRANT SELECT, INSERT, UPDATE         ON message                                   TO app_api;
GRANT SELECT, INSERT                 ON citation                                  TO app_api;
GRANT SELECT, INSERT, UPDATE         ON rate_limit_counter                        TO app_api;
GRANT INSERT                         ON audit_event, analytics_event              TO app_api;
GRANT SELECT                         ON vw_document_list, vw_workspace_quota      TO app_api;

GRANT SELECT, UPDATE                 ON document                                  TO app_worker;
GRANT SELECT, INSERT, DELETE         ON chunk                                     TO app_worker;
GRANT SELECT, INSERT, UPDATE         ON job                                       TO app_worker;
GRANT INSERT                         ON audit_event, analytics_event              TO app_worker;
GRANT EXECUTE ON FUNCTION fn_pending_purges(interval), fn_purge_lag_max_seconds() TO app_worker;

GRANT SELECT, DELETE                 ON session, upload_batch, job                TO app_maintenance;
GRANT SELECT, DELETE                 ON rate_limit_counter, analytics_event       TO app_maintenance;
GRANT EXECUTE ON FUNCTION fn_ensure_audit_partition(date), fn_drop_audit_partitions_before(date) TO app_maintenance;

GRANT SELECT ON audit_event TO app_readonly_audit;
GRANT SELECT ON vw_report_daily_questions, vw_report_daily_ingestion, vw_report_weekly_active_users,
                analytics_event TO app_readonly_analytics;

-- Ghi chú:
-- * Xóa session CASCADE sang conversation → message → citation. Hành động khóa ngoại chạy với
--   quyền chủ sở hữu bảng và không bị RLS chặn, nên app_maintenance không cần quyền trên ba bảng này.
-- * fn_current_workspace() để mặc định EXECUTE cho PUBLIC (hàm chỉ đọc cấu hình phiên).

-- =============================================================================
-- Mô tả (data dictionary trong CSDL)
-- =============================================================================
COMMENT ON TABLE app_user           IS 'Người dùng, tạo khi đăng nhập OIDC lần đầu; vai trò lấy từ nhóm IdP';
COMMENT ON TABLE workspace          IS 'Phạm vi cách ly dữ liệu; MVP: mỗi người một workspace cá nhân (SAD ADR-012)';
COMMENT ON TABLE session            IS 'Phiên đăng nhập; chỉ lưu SHA-256 của cookie sid và csrf_token';
COMMENT ON TABLE upload_batch       IS 'Chỗ đặt cho một lần tải nhiều file (BLUEPRINT ALG-01)';
COMMENT ON TABLE document           IS 'Metadata tài liệu PDF; file gốc ở object storage theo storage_key';
COMMENT ON TABLE chunk              IS 'Đoạn văn bản trong một trang + vector + tsvector. Bất biến: chỉ tồn tại khi document READY và chưa xóa';
COMMENT ON TABLE job                IS 'Hàng đợi tác vụ worker (ingest, purge); lấy bằng FOR UPDATE SKIP LOCKED';
COMMENT ON TABLE conversation       IS 'Hội thoại gắn với phiên; xóa theo phiên (NFR-024)';
COMMENT ON TABLE message            IS 'Câu hỏi/câu trả lời; idempotent theo (conversation_id, client_request_id)';
COMMENT ON TABLE citation           IS 'Nguồn trích dẫn của câu trả lời; giữ bản chụp tên tài liệu';
COMMENT ON TABLE rate_limit_counter IS 'Bộ đếm cửa sổ cố định cho giới hạn tần suất (BLUEPRINT ALG-09)';
COMMENT ON TABLE audit_event        IS 'Nhật ký kiểm toán, phân vùng theo tháng, không chứa nội dung (NFR-012)';
COMMENT ON TABLE analytics_event    IS 'Sự kiện sản phẩm EVT-01…EVT-11, không chứa nội dung (PRD 5.2)';

COMMENT ON COLUMN document.client_file_id    IS 'UUID do SPA sinh cho mỗi file; cùng batch_id → PUT idempotent (API AD-06)';
COMMENT ON COLUMN document.storage_key       IS 'ws/{workspace_id}/doc/{document_id}.pdf';
COMMENT ON COLUMN document.page_count        IS 'Số trang đếm lúc nhận file (pypdf)';
COMMENT ON COLUMN document.deleted_at        IS 'Xóa mềm: từ thời điểm này tài liệu và đoạn không còn được truy xuất';
COMMENT ON COLUMN document.purged_at         IS 'Thời điểm file gốc bị xóa thật khỏi object storage (≤ 24 h sau deleted_at)';
COMMENT ON COLUMN chunk.page_number          IS 'Số thứ tự trang trong file PDF, bắt đầu từ 1';
COMMENT ON COLUMN chunk.embedding_model      IS 'Định danh mô hình + phiên bản tạo vector, vd. bge-m3@v1; truy xuất chỉ so vector cùng mô hình';
COMMENT ON COLUMN chunk.embedding            IS 'Vector 1024 chiều float32, chuẩn hóa L2';
COMMENT ON COLUMN message.client_request_id  IS 'UUID do SPA sinh cho mỗi câu hỏi; dùng lại khi Gửi lại';
COMMENT ON COLUMN analytics_event.actor_hash IS 'HMAC-SHA256(user_id, ACTOR_HASH_KEY)';
