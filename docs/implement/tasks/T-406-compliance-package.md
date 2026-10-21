# T-406 — Lập hồ sơ tuân thủ dữ liệu AI để IT/Bảo mật ký duyệt (AC-020) ⛔

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 4 |
| **Loại** | Quy trình |
| **User story** | US-E2 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 1,5 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-208, OQ-006 |
| **Mở khóa (task chờ task này)** | T-410 |
| **Người thực hiện** | _chưa giao_ (đề xuất: Tech Lead soạn, IT/Bảo mật duyệt) |
| **Trạng thái** | To do — **bị chặn bởi OQ-006** |

## 1. Mục tiêu

Có một hồ sơ mô tả đầy đủ, kiểm chứng được cách hệ thống xử lý nội dung tài liệu (gửi tới dịch vụ AI, lưu trữ, log), và **văn bản ký xác nhận của IT/Bảo mật** rằng cách xử lý đáp ứng chính sách OQ-006 — đóng AC-020 và điều kiện launch gate "Tuân thủ dữ liệu".

## 2. Bối cảnh

- BR-020 / AC-020 (BRD): "IT/Bảo mật xác nhận bằng văn bản rằng cách xử lý dữ liệu đáp ứng chính sách đã được xác định ở OQ-006." Phương pháp: Inspection/Review. [Implement_plan §7.2](../Implement_plan.md#72-ac--loại-kiểm-thử): "Review thủ công: IT ký hồ sơ T-406".
- PRD §5.1: **blocker cứng** của launch gate. US-E2: không có màn hình.
- Nội dung kỹ thuật dựa trên SAD §4.1.5 (bảo vệ dữ liệu khi dùng AI), §2.3 (lưu giữ), §4.1.7 (mối đe dọa), §4.3 (log); cấu hình nhà cung cấp thật từ [T-208](./T-208-real-ai-adapters-reindex.md); biên bản bảo mật từ [T-405](./T-405-security-hardening.md).
- **Làm được trước khi có OQ-006:** dựng khung hồ sơ, điền mọi phần không phụ thuộc nhà cung cấp (mục 4: phần 1, 2, 5, 6, 7). **Chỉ hoàn tất và ký được** sau khi OQ-006 có kết quả và T-208 đã cấu hình theo đó.

## 3. Phạm vi

**Trong phạm vi**
- Soạn hồ sơ (mục 4), thu thập bằng chứng, tổ chức buổi review, thu chữ ký, lưu trữ.
- Test hợp đồng kiểm chứng "dữ liệu gửi đi" (payload tới `LlmPort`/`EmbeddingPort`).
- Danh sách điều kiện phải ký lại.

**Ngoài phạm vi** (để tránh làm thừa)
- Ra quyết định chính sách OQ-006 (thuộc IT/Bảo mật); đàm phán hợp đồng với nhà cung cấp.
- Đánh giá pháp lý chuyên sâu (DPIA đầy đủ) — chỉ thực hiện nếu IT/Pháp chế yêu cầu khi review.

## 4. Thiết kế chi tiết

**Sản phẩm bàn giao** `[Proposed]` đường dẫn:

| Sản phẩm | Vị trí |
|---|---|
| Hồ sơ tuân thủ (phiên bản có số, ví dụ v1.0) | `docs/compliance/AI_Data_Processing_Package.md` |
| Thư mục bằng chứng (ảnh cấu hình, trích hợp đồng, kết quả test) | `docs/compliance/evidence/` (bản nhạy cảm lưu kho tài liệu IT, chỉ để liên kết) |
| Biên bản ký duyệt | `docs/compliance/AC-020_signoff.md` + bản ký (PDF/email) lưu kho IT |
| Test hợp đồng payload | `backend/tests/contract/test_ai_payload_minimization.py` |

**Mục lục hồ sơ (bắt buộc đủ 9 phần)**

| # | Phần | Nội dung bắt buộc | Nguồn | Phụ thuộc OQ-006 |
|---|---|---|---|---|
| 1 | Luồng dữ liệu tới AI | Sơ đồ (mermaid) trình duyệt → API → dịch vụ embedding/LLM; Worker → embedding; ranh giới Z1/Z2/Z3 | SAD §2.0, §3.2.1, §3.2.2 | Không |
| 2 | Dữ liệu gửi đi | Bảng theo từng lời gọi: `EmbeddingPort.embed` (văn bản chunk khi lập chỉ mục; câu hỏi khi hỏi), `LlmPort.rewrite` (≤ `HISTORY_TURNS` lượt + câu hỏi), `LlmPort.generate` (chỉ thị, tối đa `RETRIEVAL_K` đoạn + tên tài liệu + trang, câu hỏi). Khẳng định **không** gửi: tệp PDF, tên/ID người dùng, email | SAD §4.1.5, prompt v1 (T-206) | Không |
| 3 | Nhà cung cấp và nơi xử lý | Tên nhà cung cấp, dịch vụ, mô hình (`LLM_MODEL`, `LLM_REWRITE_MODEL`, `EMBEDDING_MODEL`), vùng/khu vực xử lý, endpoint | T-208 | **Có** `[TBD: OQ-006]` |
| 4 | Thời gian lưu giữ phía nhà cung cấp và cấu hình "không dùng để huấn luyện" | Trích điều khoản hợp đồng/chính sách, ảnh chụp cấu hình tài khoản, ngày kiểm tra | T-208, hợp đồng | **Có** `[TBD: OQ-006]` |
| 5 | Lưu trữ trong hệ thống | Bảng: dữ liệu → nơi lưu (PostgreSQL, S3) → mã hóa → thời gian lưu (SAD §2.3 mặc định, `[TBD: OQ-019]`) → cơ chế xóa (purge ≤ 24 giờ, T-407) | SAD §2.3, §4.1.2 | Không |
| 6 | Danh mục log và telemetry | (a) trường log JSON (SAD §4.3); (b) 11 sự kiện `usage_event` và thuộc tính (PRD §5.2); (c) hành động `audit_log`; (d) trace/metric — kèm kết quả test canary của T-405/T-404 chứng minh không có nội dung | SAD §4.3, §4.1.6, PRD §5.2 | Không (PRD §5.2 yêu cầu IT xác nhận phạm vi log) |
| 7 | Mối đe dọa và biện pháp | Bảng SAD §4.1.7 + trạng thái thực hiện + bằng chứng (test, biên bản T-405); chống prompt injection; LLM không có công cụ | SAD §4.1.4, §4.1.5, §4.1.7 | Không |
| 8 | Bí mật và truy cập | Khóa API trong secret manager, ai có quyền đọc, xoay vòng; quyền đọc `audit_log` cho IT | SAD §4.1.3, §4.1.6 | Một phần |
| 9 | Rủi ro còn lại và điều kiện | Rủi ro chấp nhận (ví dụ không mã hóa cấp ứng dụng, SAD §4.1.2; cô lập mạng tiến trình con nếu chưa đạt); điều kiện IT đặt ra | SAD §4.1.2, T-405 | Có |

**Test hợp đồng "dữ liệu gửi đi"** (`test_ai_payload_minimization.py`): bọc adapter thật bằng transport HTTP ghi lại (không gọi mạng); chạy một lượt tải lên + hỏi với người dùng tên `CANARY-USER` và tệp `CANARY-FILE.pdf`; khẳng định body gửi đi không chứa tên người dùng, `user_id`, tên tệp đầy đủ (nếu chính sách yêu cầu), byte `%PDF-`; số đoạn ≤ `RETRIEVAL_K` (+ đoạn kề). Kết quả đính kèm phần 2.

**Quy trình ký duyệt**

| Bước | Việc | Người | Đầu ra |
|---|---|---|---|
| 1 | Nhận kết quả OQ-006 bằng văn bản, trích yêu cầu thành checklist | Tech Lead + IT/Bảo mật | Checklist chính sách |
| 2 | Đối chiếu cấu hình T-208 với checklist | Tech Lead | Bảng "Yêu cầu → Cách đáp ứng → Bằng chứng" |
| 3 | Hoàn tất hồ sơ v1.0, gửi trước buổi review ≥ 2 ngày làm việc `[Proposed]` | Tech Lead | Hồ sơ + bằng chứng |
| 4 | Buổi review (60 phút): đi qua 9 phần, demo test payload/canary trên staging | Tech Lead, IT/Bảo mật, (Pháp chế nếu IT yêu cầu), Business Owner dự | Danh sách điểm cần sửa |
| 5 | Sửa và phát hành v1.x | Tech Lead | Hồ sơ cuối |
| 6 | Ký xác nhận bằng văn bản: tên, chức danh, ngày, phiên bản hồ sơ, phiên bản phần mềm (git SHA), điều kiện kèm theo | IT/Bảo mật | `AC-020_signoff.md` + bản ký |
| 7 | Cập nhật trạng thái AC-020 trong hồ sơ launch gate | QA | Mục "Tuân thủ dữ liệu" ở T-410 = Đạt |

**Điều kiện phải ký lại** (ghi trong biên bản): đổi nhà cung cấp/mô hình/vùng xử lý; thêm dữ liệu gửi tới AI (ví dụ bật `token` streaming, thay prompt có thêm trường); thêm trường log/sự kiện; đổi thời gian lưu giữ; đổi `AI_PROVIDER`.

## 5. Các bước thực hiện

1. (Không chờ OQ-006) Dựng khung hồ sơ 9 phần, điền phần 1, 2, 5, 6, 7; viết và chạy test payload với `FakeLlm` (kiểm cấu trúc payload).
2. (Không chờ OQ-006) Gom biên bản T-405, kết quả test canary T-404/T-405 vào `evidence/`.
3. Khi OQ-006 có kết quả: trích checklist chính sách (bước 1 quy trình); nếu chính sách cấm gửi ra ngoài → báo Tech Lead/PO ngay (ảnh hưởng T-208: phương án tự lưu trữ, SAD §4.1.5).
4. Sau T-208: điền phần 3, 4, 8, 9; chạy lại test payload với adapter thật (transport ghi lại).
5. Thực hiện bước 3–7 của quy trình ký duyệt.

## 6. Tiêu chí chấp nhận

- [ ] Hồ sơ có đủ 9 phần ở bảng mục 4; mọi khẳng định có liên kết bằng chứng (test, ảnh cấu hình, điều khoản).
- [ ] Mỗi yêu cầu trong checklist OQ-006 có một dòng "Cách đáp ứng + Bằng chứng"; không còn dòng "chưa đáp ứng" không có điều kiện được IT chấp nhận.
- [ ] Test `test_ai_payload_minimization.py` pass với adapter thật (transport ghi lại) và chạy trong CI với `FakeLlm`.
- [ ] Có văn bản ký của IT/Bảo mật ghi phiên bản hồ sơ và git SHA được duyệt (AC-020).
- [ ] Danh sách "điều kiện phải ký lại" được ghi trong biên bản và trong runbook phát hành.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Contract | Payload `generate`/`rewrite`/`embed` khi hỏi | Không có tên/ID người dùng, không có byte PDF; số đoạn ≤ `RETRIEVAL_K` + đoạn kề |
| Contract | Payload `embed` khi lập chỉ mục | Chỉ văn bản chunk |
| Review | IT/Bảo mật đối chiếu hồ sơ với cấu hình staging | Không có sai khác |
| Review | Log/sự kiện thực tế trên staging so với phần 6 | Không có trường ngoài danh mục |

## 8. Cấu hình

Không thêm biến. Hồ sơ phải ghi giá trị thực của: `AI_PROVIDER`, `LLM_MODEL`, `LLM_REWRITE_MODEL`, `EMBEDDING_MODEL`, `EMBEDDING_DIM`, `HISTORY_TURNS`, `RETRIEVAL_K`, `LOG_LEVEL`, `OTEL_EXPORTER_OTLP_ENDPOINT` ([Implement_plan §3.3](../Implement_plan.md#33-biến-môi-trường)), và thời gian lưu giữ (`[TBD: OQ-019]`, T-407).

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| OQ-006 chưa có kết quả (hạn BRD 2026-10-30) | Không ký được → launch gate không đóng | Làm trước các phần không phụ thuộc; Tech Lead nhắc hạn hằng tuần |
| Chính sách cấm gửi dữ liệu ra ngoài | Phải dùng mô hình tự lưu trữ; đo lại chất lượng CMP-17 | Báo ngay; T-208/T-310 làm lại với adapter tự lưu trữ |
| OQ-019 (thời gian lưu giữ) chưa chốt | Phần 5 chỉ có giá trị mặc định | Ghi `[TBD: OQ-019]` + mặc định SAD §2.3; IT có thể chốt ngay tại buổi review |
| IT yêu cầu quét mã độc (ClamAV) | Phát sinh việc | Ghi thành điều kiện, ước lượng riêng |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §5.5 (T-406), §7.2, §8, §9.1
- [SAD](../../design/SAD.md) §2.3, §3.2, §4.1.2–§4.1.7, §4.3
- [User_Stories](../../design/User_Stories.md) US-E2
- [PRD](../../requirements/PRD.md) §5.1, §5.2 · [BRD](../../requirements/BRD.md) BR-020, AC-020, OQ-006
- Task liên quan: [T-206](./T-206-prompt-v1.md), [T-208](./T-208-real-ai-adapters-reindex.md), [T-404](./T-404-observability.md), [T-405](./T-405-security-hardening.md), [T-407](./T-407-retention-cleanup.md), [T-410](./T-410-launch-gate-uat.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)) ở phần áp dụng được (test hợp đồng merge, CI xanh).
- [ ] Bản ký AC-020 được lưu ở kho tài liệu IT và liên kết từ hồ sơ launch gate (T-410).
