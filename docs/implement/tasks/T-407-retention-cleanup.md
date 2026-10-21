# T-407 — Triển khai lưu giữ và dọn dẹp dữ liệu định kỳ

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 4 |
| **Loại** | Backend |
| **User story** | — nền tảng (BR-007/BRU-002, QAS-06; chính sách lưu giữ SAD §2.3) |
| **Ưu tiên** | P0 |
| **Ước lượng** | 1,5 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-101, T-106 |
| **Mở khóa (task chờ task này)** | T-408 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Worker tự chạy định kỳ các việc dọn dẹp: xóa phiên hết hạn, bảo đảm mọi tài liệu `DELETED` được purge vật lý trong ≤ 24 giờ, tạo trước/bỏ phân vùng tháng của `usage_event`, xóa đối tượng mồ côi trong S3. Mọi thời hạn đọc từ cấu hình với mặc định SAD §2.3, chờ chốt `[TBD: OQ-019]`.

## 2. Bối cảnh

- SAD §2.3 "Chính sách lưu giữ dữ liệu": tài liệu đã xóa ≤ 24 giờ; hội thoại "thời gian thử nghiệm + 90 ngày" `[Proposed]`; `usage_event` 13 tháng, phân vùng theo tháng; `audit_log` 12 tháng, chỉ ghi thêm; phiên hết hạn tuyệt đối 12 giờ, rảnh 60 phút.
- SAD §3.2.2 "Điểm nhất quán": tệp đã ghi S3 nhưng giao dịch lỗi → tệp mồ côi → vòng dọn xóa đối tượng không có `document` sau 24 giờ.
- SAD §3.2.3: purge giữ bản ghi `document` (`DELETED`) và `citation` cũ.
- Hạ tầng sẵn có: `JobQueue` ([T-101](./T-101-job-queue.md)), job `purge_document` ([T-106](./T-106-delete-document-purge.md)). Kết quả dùng cho bước "chạy lại purge sau khôi phục" ở [T-408](./T-408-backup-restore-drill.md).

## 3. Phạm vi

**Trong phạm vi**
- Bộ lập lịch nhẹ trong Worker (enqueue việc định kỳ vào bảng `job`, không trùng).
- 4 loại việc: `cleanup_sessions`, `ensure_document_purge`, `maintain_usage_event_partitions`, `cleanup_orphan_files`.
- Lệnh vận hành `python -m app.ingestion.ops repurge-deleted` (dùng ở T-408).
- Metric và log cho từng việc.

**Ngoài phạm vi** (để tránh làm thừa)
- Xóa hội thoại tự động: thời hạn phụ thuộc ngày kết thúc thử nghiệm (`[TBD: OQ-005]`, `[TBD: OQ-019]`) → chỉ để cấu hình `CONVERSATION_RETENTION_DAYS` **tắt mặc định**, không viết job ở MVP `[Proposed]`; tính năng người dùng tự xóa hội thoại không có story.
- Xóa `audit_log` > 12 tháng: vai trò `cwd_app` không có `DELETE` (SAD §4.1.6, T-405) → quy trình vận hành bằng vai trò chủ sở hữu, ghi vào runbook, không phải job ứng dụng.
- Lưu giữ log kỹ thuật (thuộc nền tảng log của tổ chức).

## 4. Thiết kế chi tiết

**File cần tạo/sửa**

| File | Nội dung |
|---|---|
| `backend/app/jobs/scheduler.py` | `PeriodicTask(type, interval_s)`, `Scheduler.tick()` |
| `backend/app/access/cleanup.py` | handler `cleanup_sessions` (module `access` sở hữu bảng `session`) |
| `backend/app/ingestion/retention.py` | handler `ensure_document_purge`, `cleanup_orphan_files` |
| `backend/app/analytics/partitions.py` | handler `maintain_usage_event_partitions` |
| `backend/app/ingestion/ops.py` | CLI `repurge-deleted` |
| `backend/app/ports/file_store.py` (T-102) | thêm `list_objects(prefix: str, older_than: datetime) -> AsyncIterator[ObjectInfo]` `[Proposed]` |
| `backend/app/adapters/s3/file_store.py` | cài đặt `list_objects` bằng `ListObjectsV2` phân trang |
| `backend/app/worker.py` | gọi `Scheduler.tick()` mỗi vòng (≤ 1 lần/60 s) |
| `backend/tests/integration/retention/…` | test |

**Lập lịch không trùng** `[Proposed]`: mỗi `tick()` với từng `PeriodicTask`, chỉ enqueue nếu chưa có job cùng `type` ở trạng thái `queued`/`running` và lần `succeeded` gần nhất cũ hơn `interval_s`. Dùng `pg_advisory_xact_lock(hashtext('scheduler'))` để nhiều worker không cùng enqueue.

```sql
SELECT 1 FROM job
WHERE type = :type AND (status IN ('queued','running')
   OR (status = 'succeeded' AND locked_at > now() - make_interval(secs => :interval_s)))
LIMIT 1;
```

| Việc | Chu kỳ `[Default]` | Hành vi |
|---|---|---|
| `cleanup_sessions` | 15 phút | `DELETE FROM session WHERE expires_at < now() OR last_seen_at < now() - make_interval(mins => :idle_min)` theo lô 1.000 dòng |
| `ensure_document_purge` | 1 giờ | Tìm tài liệu `DELETED` còn chunk hoặc còn tệp mà không có job `purge_document` đang chờ/chạy → enqueue `purge_document`; tài liệu quá `DOCUMENT_PURGE_SLA_H` vẫn chưa sạch → log `WARNING` + metric |
| `maintain_usage_event_partitions` | 1 ngày | Tạo phân vùng cho tháng hiện tại + `USAGE_EVENT_PARTITIONS_AHEAD` tháng tới (nếu chưa có); `DETACH` rồi `DROP` phân vùng có tháng kết thúc trước `now() - USAGE_EVENT_RETENTION_MONTHS` |
| `cleanup_orphan_files` | 1 ngày | Liệt kê đối tượng `documents/` cũ hơn `ORPHAN_FILE_MIN_AGE_H`; khóa không ứng với `document.file_ref` nào **hoặc** ứng với tài liệu `DELETED` đã purge → xóa |

```sql
-- ensure_document_purge: tài liệu cần purge lại
SELECT d.id FROM document d
WHERE d.status = 'DELETED'
  AND (EXISTS (SELECT 1 FROM chunk c WHERE c.document_id = d.id) OR d.purged_at IS NULL)   -- purged_at: xem ghi chú
  AND NOT EXISTS (SELECT 1 FROM job j WHERE j.type = 'purge_document'
                  AND j.payload->>'document_id' = d.id::text AND j.status IN ('queued','running'));
```

Ghi chú: `document.file_ref` là `NOT NULL` (SAD §3.1) nên không dùng được để biết "tệp đã xóa". Đề xuất `[Proposed]`: thêm cột `purged_at timestamptz` (migration expand, tương thích ngược); `purge_document` (T-106) đặt `purged_at = now()` khi đã xóa xong chunk + tệp.

```sql
-- maintain_usage_event_partitions (ví dụ tháng 2026-11)
CREATE TABLE IF NOT EXISTS usage_event_2026_11 PARTITION OF usage_event
  FOR VALUES FROM ('2026-11-01 00:00+00') TO ('2026-12-01 00:00+00');
GRANT SELECT, INSERT ON usage_event_2026_11 TO cwd_app;   -- nếu áp dụng tách vai trò của T-405
-- bỏ phân vùng hết hạn
ALTER TABLE usage_event DETACH PARTITION usage_event_2025_09;
DROP TABLE usage_event_2025_09;
```

Tên phân vùng `usage_event_YYYY_MM`, ranh giới theo UTC. Nếu T-004 có phân vùng `DEFAULT`, việc này vẫn tạo phân vùng tháng trước khi tháng bắt đầu để không dồn vào `DEFAULT`. Thao tác DDL cần quyền chủ sở hữu bảng → handler chạy với kết nối `MIGRATION_DATABASE_URL` `[Proposed]` (hoặc vai trò riêng chỉ có quyền tạo phân vùng).

**Bất biến:** mọi handler lũy đẳng (chạy lại không lỗi, không xóa nhầm); `cleanup_orphan_files` **không bao giờ** xóa đối tượng của tài liệu có trạng thái khác `DELETED`; mỗi lần chạy xóa tối đa `ORPHAN_FILE_MAX_PER_RUN` đối tượng.

**CLI `repurge-deleted`** (T-408): `python -m app.ingestion.ops repurge-deleted [--dry-run]` → enqueue `purge_document` cho **mọi** tài liệu `DELETED` (bỏ qua điều kiện "còn dữ liệu"), in số lượng; `--dry-run` chỉ in danh sách id.

**Metric** (đăng ký trong registry của T-404) `[Proposed]`: `retention_deleted_total{kind=sessions|orphan_files|partitions}`, `documents_purge_overdue` (gauge — số tài liệu quá SLA). Log mỗi lần chạy: `job_type`, `deleted_count`, `duration_ms` (không có tên tệp).

## 5. Các bước thực hiện

1. Thêm cấu hình mục 8 vào settings + `.env.example`.
2. Migration thêm `document.purged_at`; sửa `purge_document` (T-106) đặt `purged_at` khi hoàn tất.
3. Viết `Scheduler` + test không trùng (2 worker cùng tick).
4. Viết 4 handler + `FileStorePort.list_objects` (adapter S3 + `FakeFileStore`).
5. Viết CLI `repurge-deleted`.
6. Đăng ký metric; viết test tích hợp (Testcontainers PostgreSQL + MinIO).
7. Ghi runbook ngắn: lịch chạy, cách xem metric, quy trình dọn `audit_log` 12 tháng bằng vai trò chủ sở hữu.

## 6. Tiêu chí chấp nhận

- [ ] Phiên có `expires_at` đã qua hoặc rảnh > `SESSION_IDLE_MIN` bị xóa trong ≤ 15 phút; phiên còn hạn không bị ảnh hưởng.
- [ ] Tài liệu `DELETED` mà job `purge_document` đã `failed` được enqueue lại trong ≤ 1 giờ; sau khi worker chạy: 0 chunk, đối tượng S3 không còn, `purged_at` có giá trị, bản ghi `document` và `citation` vẫn còn.
- [ ] Tài liệu `DELETED` > `DOCUMENT_PURGE_SLA_H` chưa sạch làm `documents_purge_overdue > 0` và có log `WARNING`.
- [ ] Luôn tồn tại phân vùng `usage_event` cho tháng hiện tại và `USAGE_EVENT_PARTITIONS_AHEAD` tháng tới; phân vùng cũ hơn `USAGE_EVENT_RETENTION_MONTHS` bị bỏ; báo cáo tuần (T-401) vẫn chạy đúng sau khi thêm/bỏ phân vùng.
- [ ] Đối tượng S3 mồ côi cũ hơn 24 giờ bị xóa; đối tượng mồ côi < 24 giờ và đối tượng của tài liệu `READY/PROCESSING/UPLOADED/FAILED/NOT_EXTRACTABLE` không bị xóa.
- [ ] Hai worker chạy song song không tạo job định kỳ trùng.
- [ ] `repurge-deleted --dry-run` in đúng danh sách; chạy thật enqueue 1 job/tài liệu `DELETED`.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `Scheduler.tick()` khi đã có job `queued` cùng loại | Không enqueue |
| Unit | Tính tên/ranh giới phân vùng tháng 12 → tháng 1 | `usage_event_2026_12`, `[2026-12-01, 2027-01-01)` |
| Integration | 3 phiên: hết hạn, rảnh 61 phút, còn hạn | Xóa 2, giữ 1 |
| Integration | Tài liệu `DELETED`, job purge `failed` | Được enqueue lại và purge sạch |
| Integration | Tài liệu `DELETED` đã purge | Không enqueue lại (lũy đẳng) |
| Integration | Phân vùng 14 tháng trước có dữ liệu | Bị bỏ; phân vùng 12 tháng trước còn |
| Integration | S3: 1 mồ côi 25 giờ, 1 mồ côi 2 giờ, 1 của tài liệu `READY` | Chỉ xóa cái đầu |
| Integration | Hai tiến trình gọi `tick()` đồng thời | 1 job mỗi loại |
| Integration | Tạo phân vùng khi đã tồn tại | Không lỗi |

## 8. Cấu hình

Tất cả `[Proposed]` tên biến; giá trị là mặc định SAD §2.3, `[TBD: OQ-019]`:

| Biến | `[Default]` | Ghi chú |
|---|---|---|
| `SESSION_ABSOLUTE_TTL_H` | `12` | Dùng chung với T-006 nếu T-006 đã đặt tên khác thì dùng tên của T-006 |
| `SESSION_IDLE_MIN` | `60` | như trên |
| `DOCUMENT_PURGE_SLA_H` | `24` | QAS-06 |
| `USAGE_EVENT_RETENTION_MONTHS` | `13` | |
| `USAGE_EVENT_PARTITIONS_AHEAD` | `2` | |
| `ORPHAN_FILE_MIN_AGE_H` | `24` | SAD §3.2.2 |
| `ORPHAN_FILE_MAX_PER_RUN` | `1000` | Giới hạn an toàn |
| `CONVERSATION_RETENTION_DAYS` | trống (tắt) | `[TBD: OQ-005, OQ-019]` |
| `MIGRATION_DATABASE_URL` | — | Cho DDL phân vùng (T-405) |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| OQ-019 chưa chốt | Thời hạn có thể đổi | Mọi thời hạn qua cấu hình |
| Hội thoại "thử nghiệm + 90 ngày" phụ thuộc ngày kết thúc thử nghiệm (OQ-005) | Không viết được job đúng | Tắt mặc định; bổ sung khi có quyết định |
| `audit_log` 12 tháng mâu thuẫn với "không có DELETE" của `cwd_app` | Không dọn bằng ứng dụng | Runbook với vai trò chủ sở hữu; hoặc phân vùng `audit_log` theo tháng ở bản sau `[Proposed]` |
| S3 bật versioning (SAD §2.3 sao lưu) giữ phiên bản cũ của tệp đã xóa | "Xóa vật lý ≤ 24 giờ" không thực sự đạt | Thêm lifecycle rule hết hạn phiên bản không hiện hành; chốt thời hạn với IT ở T-406/T-408 |
| DDL phân vùng cần quyền cao | Rủi ro dùng vai trò mạnh trong worker | Vai trò riêng chỉ có quyền trên `usage_event` `[Proposed]` |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §5.5 (T-407), §6.1 (`usage_event`, `session`), §6.3, §9.1 (OQ-019)
- [SAD](../../design/SAD.md) §2.3, §3.2.2, §3.2.3, §4.1.6
- [Blueprint_Design](../../design/Blueprint_Design.md) QAS-06, bảng phân loại dữ liệu (thời gian lưu `[TBD: OQ-019]`)
- Task liên quan: [T-006](./T-006-auth-session-dev-identity.md), [T-101](./T-101-job-queue.md), [T-102](./T-102-file-store-s3-adapter.md), [T-106](./T-106-delete-document-purge.md), [T-404](./T-404-observability.md), [T-405](./T-405-security-hardening.md), [T-408](./T-408-backup-restore-drill.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Runbook lưu giữ (lịch, metric, quy trình `audit_log`) được Tech Lead duyệt; giá trị thời hạn đưa vào hồ sơ T-406 phần 5.
