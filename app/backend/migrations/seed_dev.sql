-- =============================================================================
-- Dữ liệu mẫu cho môi trường phát triển – KHÔNG chạy ở staging/production
-- Tài liệu: DATABASE_DESIGN.md mục A.9
-- Chạy sau schema.sql, bằng vai trò app_migrator, với: SET app.env = 'dev';
-- =============================================================================

DO $$
BEGIN
    IF coalesce(current_setting('app.env', true), '') <> 'dev' THEN
        RAISE EXCEPTION 'seed_dev.sql chỉ chạy khi app.env = dev';
    END IF;
END $$;

BEGIN;

-- Người dùng và workspace cá nhân
INSERT INTO app_user (id, idp_subject, email, role) VALUES
    ('00000000-0000-4000-8000-000000000001', 'dev|p1', 'p1.dev@example.local', 'user'),
    ('00000000-0000-4000-8000-000000000002', 'dev|p2', 'p2.dev@example.local', 'user'),
    ('00000000-0000-4000-8000-000000000003', 'dev|admin', 'admin.dev@example.local', 'admin');

INSERT INTO workspace (id, kind, personal_owner_id) VALUES
    ('10000000-0000-4000-8000-000000000001', 'personal', '00000000-0000-4000-8000-000000000001'),
    ('10000000-0000-4000-8000-000000000002', 'personal', '00000000-0000-4000-8000-000000000002'),
    ('10000000-0000-4000-8000-000000000003', 'personal', '00000000-0000-4000-8000-000000000003');

INSERT INTO membership (workspace_id, user_id, role) VALUES
    ('10000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000001', 'owner'),
    ('10000000-0000-4000-8000-000000000002', '00000000-0000-4000-8000-000000000002', 'owner'),
    ('10000000-0000-4000-8000-000000000003', '00000000-0000-4000-8000-000000000003', 'owner');

-- Tài liệu của P1 ở ba trạng thái (US-006, E-03).
-- READY phải được tạo qua PROCESSING → READY để qua trigger chuyển trạng thái.
INSERT INTO document (id, workspace_id, client_file_id, file_name, size_bytes, page_count, status,
                      failure_code, storage_key, sha256, uploaded_by) VALUES
    ('20000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000001',
     '30000000-0000-4000-8000-000000000001', 'hop-dong-A.pdf', 1048576, 12, 'PROCESSING', NULL,
     'ws/10000000-0000-4000-8000-000000000001/doc/20000000-0000-4000-8000-000000000001.pdf',
     sha256('hop-dong-A'::bytea), '00000000-0000-4000-8000-000000000001'),
    ('20000000-0000-4000-8000-000000000002', '10000000-0000-4000-8000-000000000001',
     '30000000-0000-4000-8000-000000000002', 'bang-gia.pdf', 524288, 3, 'PROCESSING', NULL,
     'ws/10000000-0000-4000-8000-000000000001/doc/20000000-0000-4000-8000-000000000002.pdf',
     sha256('bang-gia'::bytea), '00000000-0000-4000-8000-000000000001'),
    ('20000000-0000-4000-8000-000000000003', '10000000-0000-4000-8000-000000000001',
     '30000000-0000-4000-8000-000000000003', 'scan-01.pdf', 2097152, 5, 'FAILED', 'R-03',
     'ws/10000000-0000-4000-8000-000000000001/doc/20000000-0000-4000-8000-000000000003.pdf',
     sha256('scan-01'::bytea), '00000000-0000-4000-8000-000000000001');

-- Đoạn mẫu cho hop-dong-A.pdf. Vector hằng (1024 × 0,03125) có chuẩn L2 = 1 – chỉ để
-- giao diện hiển thị được trích dẫn, KHÔNG dùng để đánh giá chất lượng truy xuất.
INSERT INTO chunk (document_id, workspace_id, page_number, chunk_index, token_count, content, embedding_model, embedding) VALUES
    ('20000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000001', 4, 0, 24,
     'Điều 5. Thanh toán: Bên B thanh toán trong vòng 30 ngày kể từ ngày nhận hóa đơn hợp lệ.',
     'bge-m3@v1', array_fill(0.03125::real, ARRAY[1024])::vector),
    ('20000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000001', 7, 1, 20,
     'Điều 9. Hiệu lực: Hợp đồng có hiệu lực 24 tháng kể từ ngày ký.',
     'bge-m3@v1', array_fill(0.03125::real, ARRAY[1024])::vector);

UPDATE document SET status = 'READY', ready_at = now()
WHERE id = '20000000-0000-4000-8000-000000000001';

COMMIT;   -- trigger hoãn (deferred) kiểm tra bất biến chunk ⇔ READY tại đây
