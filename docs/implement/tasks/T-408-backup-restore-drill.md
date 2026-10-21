# T-408 — Cấu hình sao lưu và diễn tập khôi phục trên staging

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 4 |
| **Loại** | DevOps |
| **User story** | — nền tảng (launch gate "Diễn tập khôi phục sao lưu thành công") |
| **Ưu tiên** | P0 |
| **Ước lượng** | 1 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-407, T-409 |
| **Mở khóa (task chờ task này)** | T-410 |
| **Người thực hiện** | _chưa giao_ (DevOps/BE + Tech Lead chứng kiến) |
| **Trạng thái** | To do |

## 1. Mục tiêu

Staging có sao lưu PostgreSQL hằng ngày + lưu trữ WAL liên tục (PITR) và kho tệp có versioning/sao chép; đội đã **diễn tập khôi phục** về một thời điểm, đo được RPO/RTO thực tế, chạy lại purge tài liệu `DELETED` sau khôi phục, và lưu biên bản bằng chứng cho launch gate.

## 2. Bối cảnh

- SAD §2.3 (Sao lưu: hằng ngày + WAL/PITR; kho tệp versioning hoặc sao chép), §4.2 (RPO ≤ 15 phút, RTO ≤ 4 giờ `[Proposed — TBD: OQ-017]`; diễn tập trước khi ra mắt và mỗi quý; khôi phục có thể "làm sống lại" dữ liệu đã purge → chạy lại danh sách `DELETED` để purge).
- Cảnh báo (7) "sao lưu thất bại" của [T-404](./T-404-observability.md) cần metric từ task này.
- [T-407](./T-407-retention-cleanup.md) cung cấp lệnh `python -m app.ingestion.ops repurge-deleted`; [T-409](./T-409-staging-deployment.md) cung cấp môi trường staging.
- [Implement_plan §8](../Implement_plan.md#8-launch-gate-điều-kiện-lên-production): "Diễn tập khôi phục sao lưu thành công".

## 3. Phạm vi

**Trong phạm vi**
- Bật/kiểm cấu hình sao lưu CSDL (PITR) và kho tệp trên staging; mã hóa bản sao lưu.
- Metric `backup_last_success_timestamp_seconds` cho cảnh báo (7).
- Runbook khôi phục; một lần diễn tập có biên bản.

**Ngoài phạm vi** (để tránh làm thừa)
- Chọn hạ tầng production / HA nhiều node, standby replication (SAD §4.2 — sau MVP).
- Diễn tập hằng quý sau ra mắt (ghi lịch trong runbook, không làm trong task này).

## 4. Thiết kế chi tiết

**Sản phẩm bàn giao** `[Proposed]` đường dẫn:

| Sản phẩm | Vị trí |
|---|---|
| Runbook sao lưu/khôi phục | `docs/implement/runbooks/backup_restore.md` |
| Biên bản diễn tập | `docs/implement/runbooks/drills/<YYYY-MM-DD>-restore-drill.md` |
| Script kiểm tra sau khôi phục | `deploy/scripts/post_restore_check.sh` |
| Metric sao lưu | textfile collector/pushgateway: `backup_last_success_timestamp_seconds`, `backup_last_duration_seconds` |

**Cấu hình sao lưu**

| Thành phần | Cách làm | Ghi chú |
|---|---|---|
| PostgreSQL | Dịch vụ quản lý: bật PITR + backup hằng ngày, giữ ≥ 7 ngày `[Proposed]`. Tự quản: `pgBackRest` hoặc `WAL-G` `[Proposed]`, `archive_mode=on`, `archive_timeout=300` (đáp ứng RPO 15 phút), base backup hằng ngày lên bucket riêng | `[Verify]` hỗ trợ pgvector của dịch vụ khi khôi phục |
| Object storage | Bật versioning trên bucket tài liệu hoặc sao chép sang bucket khác; lifecycle hết hạn phiên bản không hiện hành sau `[TBD: OQ-019]` ngày | Xem rủi ro "tệp đã purge sống lại" |
| Mã hóa | Bản sao lưu mã hóa lưu trữ (SAD §4.1.2) | |
| Bí mật | Thông tin truy cập kho sao lưu trong secret manager | SAD §4.1.3 |

**Kịch bản diễn tập** (trên staging, bằng dữ liệu mẫu DEP-001):

| Bước | Việc | Ghi nhận |
|---|---|---|
| 0 | Chuẩn bị: tải 4 PDF (A, B, C, E) → `READY`; hỏi 2 câu; xóa C và chờ purge xong (chunk = 0, tệp S3 không còn) | id tài liệu, thời điểm |
| 1 | Dừng Worker; xóa E qua API (E `DELETED`, job `purge_document` còn `queued`, chunk còn); ghi mốc `T_marker` (ví dụ tải PDF D — bản ghi `document` mới) | `T_marker` |
| 2 | Chờ ≥ `archive_timeout`; chọn `T_target` = sau `T_marker`; bật lại Worker → E được purge (tệp S3 của E bị xóa); sau đó xóa B, ghi `T_delete_B` (> `T_target`) | `T_target`, `T_delete_B` |
| 3 | Kỳ vọng sau khôi phục về `T_target`: E là ca "đã purge nhưng sống lại" (CSDL có chunk, S3 không còn tệp); B là ca "xóa sau mốc khôi phục" | |
| 4 | Bắt đầu đồng hồ RTO: dừng API/Worker (hoặc trỏ sang CSDL mới); khôi phục PITR về `T_target` vào instance mới | `T_start` |
| 5 | Trỏ `DATABASE_URL` sang instance khôi phục; chạy `alembic current` (phiên bản lược đồ khớp mã) | |
| 6 | **Chạy lại purge:** `python -m app.ingestion.ops repurge-deleted --dry-run` → kiểm danh sách → chạy thật → chờ worker xong | Danh sách id |
| 7 | Khởi động API/Worker; `post_restore_check.sh` | `T_end` (RTO = `T_end − T_start`) |
| 8 | Kiểm dữ liệu: D (bản ghi mốc) còn (RPO đạt); C và E `DELETED`, 0 chunk sau bước 6, purge E không lỗi dù tệp S3 đã mất (lũy đẳng); B quay lại `READY` (đúng với `T_target`) nhưng tệp S3 đã bị purge → `post_restore_check.sh` phải báo B là "không khác `DELETED` mà thiếu tệp"; runbook: xóa lại B qua API (ADMIN) và ghi vào biên bản | |
| 9 | Kiểm chức năng: đăng nhập, danh sách thư viện, hỏi 1 câu về A có trích dẫn, mở tệp A, báo cáo tuần chạy | |
| 10 | Khôi phục staging về trạng thái vận hành bình thường; viết biên bản | |

**`post_restore_check.sh`** kiểm: `/health/ready` = 200; `SELECT count(*) FROM document GROUP BY status`; số chunk của tài liệu `DELETED` = 0 (sau purge); mỗi `document` khác `DELETED` có đối tượng S3 tồn tại (`HEAD`); phân vùng `usage_event` tháng hiện tại tồn tại; `job` `running` cũ đã được vòng quét đưa về `queued`.

**Biên bản diễn tập (mẫu bắt buộc)**: ngày giờ; người thực hiện/chứng kiến; phiên bản phần mềm (git SHA) và lược đồ (Alembic revision); id bản sao lưu cơ sở; `T_marker`, `T_target`, thời điểm WAL cuối được áp dụng; **RPO đo được** (= `T_lỗi giả định − thời điểm giao dịch cuối khôi phục được`) và **RTO đo được**; kết quả từng bước 4–9 (Đạt/Không đạt); số tài liệu được purge lại; sự cố gặp phải và cách xử lý; việc cần làm tiếp; chữ ký Tech Lead + phụ trách vận hành.

## 5. Các bước thực hiện

1. Xác định hạ tầng CSDL staging (quản lý hay tự quản) từ T-409; bật sao lưu theo bảng cấu hình.
2. Bật versioning/sao chép bucket; đặt lifecycle cho phiên bản không hiện hành.
3. Xuất metric `backup_last_success_timestamp_seconds` sau mỗi lần sao lưu thành công; kiểm cảnh báo (7) của T-404 kích hoạt khi tắt sao lưu > 26 giờ (thử bằng `promtool` + giả lập).
4. Viết runbook khôi phục (lệnh cụ thể cho công cụ đã chọn, cách trỏ ứng dụng sang instance mới, cách quay lại).
5. Viết `post_restore_check.sh`.
6. Thực hiện diễn tập theo bảng kịch bản; đo RPO/RTO.
7. Viết biên bản; mở ticket cho mọi bước "Không đạt"; cập nhật runbook theo bài học.

## 6. Tiêu chí chấp nhận

- [ ] Staging có sao lưu cơ sở hằng ngày + WAL liên tục; bản sao lưu được mã hóa; lần sao lưu gần nhất < 26 giờ.
- [ ] Cảnh báo (7) `BackupFailed` kích hoạt trong thử nghiệm khi không có sao lưu thành công > 26 giờ.
- [ ] Diễn tập khôi phục PITR thành công; **RPO đo được ≤ 15 phút và RTO đo được ≤ 4 giờ** (`[Proposed]`, `[TBD: OQ-017]`), hoặc chênh lệch được ghi và Business Owner chấp nhận.
- [ ] Sau khôi phục và `repurge-deleted`: 100% tài liệu `DELETED` có 0 chunk và không còn tệp S3 truy cập được qua `GET /documents/{id}/file`.
- [ ] `post_restore_check.sh` pass; luồng hỏi trên tài liệu `READY` trả câu trả lời có trích dẫn.
- [ ] Biên bản diễn tập đủ mọi trường của mẫu, có chữ ký, được liên kết từ hồ sơ launch gate (T-410).

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Rules | `promtool test rules` cho `BackupFailed` | Kích hoạt/không kích hoạt đúng |
| Thủ công | Khôi phục PITR về `T_target` | Bản ghi mốc còn; dữ liệu sau `T_target` không có |
| Thủ công | Tài liệu C (đã purge trước sao lưu) | Vẫn `DELETED`, không có chunk/tệp |
| Thủ công | Tài liệu E (`DELETED`, chunk "sống lại", tệp S3 đã mất) | Sau `repurge-deleted`: 0 chunk, job `succeeded` |
| Thủ công | Tài liệu B (xóa sau `T_target`) | `post_restore_check.sh` liệt kê B (thiếu tệp S3); sau khi xóa lại theo runbook, check pass |
| Thủ công | `post_restore_check.sh` | Exit 0 |
| Thủ công | Hỏi 1 câu về A | `ANSWERED`, trích dẫn đúng trang |

## 8. Cấu hình

| Biến / thiết lập | Giá trị | Ghi chú |
|---|---|---|
| `DATABASE_URL` | trỏ instance khôi phục khi diễn tập | [Implement_plan §3.3](../Implement_plan.md#33-biến-môi-trường) |
| `S3_ENDPOINT`, `S3_BUCKET` | như staging | Versioning bật |
| `archive_timeout` | `300` s `[Proposed]` | Theo RPO 15 phút |
| Thời gian giữ sao lưu | ≥ 7 ngày `[Proposed]` | `[TBD: OQ-017, OQ-019]` |
| RPO / RTO | 15 phút / 4 giờ `[Proposed]` | `[TBD: OQ-017]` |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| OQ-017 chưa chốt RPO/RTO | Không biết mục tiêu thật | Dùng mặc định SAD; báo số đo cho Business Owner |
| Xóa tài liệu sau `T_target` bị mất khi khôi phục (tài liệu "sống lại" ở `READY`) | Vi phạm BRU-002 nếu không xử lý | Nếu purge đã chạy: phát hiện qua "thiếu tệp S3" (`post_restore_check.sh`). Nếu purge chưa chạy: đối chiếu hành động xóa sau `T_target` từ kho log tập trung (nếu có) và xóa lại thủ công. Ghi rủi ro này vào hồ sơ T-406 |
| Versioning S3 giữ bản tệp đã purge | "Xóa vật lý ≤ 24 giờ" không đạt hoàn toàn | Lifecycle hết hạn phiên bản không hiện hành; IT chốt thời hạn |
| Dịch vụ CSDL quản lý không hỗ trợ pgvector đúng phiên bản khi khôi phục | Khôi phục thất bại | Kiểm `[Verify]` trước diễn tập |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §5.5 (T-408), §8, §9.1 (OQ-017, OQ-019)
- [SAD](../../design/SAD.md) §2.3 (Sao lưu, lưu giữ), §4.1.2, §4.1.3, §4.2 (Sao lưu & khôi phục), §4.3 (cảnh báo 7)
- [Blueprint_Design](../../design/Blueprint_Design.md) QAS-10, OQ-017
- Task liên quan: [T-404](./T-404-observability.md), [T-406](./T-406-compliance-package.md), [T-407](./T-407-retention-cleanup.md), [T-409](./T-409-staging-deployment.md), [T-410](./T-410-launch-gate-uat.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)) ở phần áp dụng được (script merge, CI xanh).
- [ ] Runbook có lịch diễn tập hằng quý sau ra mắt và người chịu trách nhiệm.
