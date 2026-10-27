# Master Test Plan (MTP)
# MVP – Ứng dụng AI Chat với tài liệu PDF

| Trường | Giá trị |
|---|---|
| Mã tài liệu | TP-AICHAT-001 |
| Phiên bản | 0.3 |
| Trạng thái | **Draft** |
| Ngày | 2026-10-27 |
| Chuẩn áp dụng | IEEE 829-2008 (Software Test Documentation) |
| Template | [doc/templates/testPlan_prompt.md](../templates/testPlan_prompt.md) |
| Tài liệu đầu vào | BRD v0.2 · PRD v0.2 · USER_STORIES v0.1 · USE_CASE v0.1 · SAD v0.4 · BLUEPRINT v0.3 · API_DESIGN v0.1 (+ openapi.yaml) · DATABASE_DESIGN v0.1 · html_design S01–S11 · PLAN v0.1 |
| Đối tượng hệ thống | Bản demo trong `app/`. Chu kỳ C1: commit `166929f` cộng 3 thay đổi chưa commit (xem mục 3.1) |
| Người soạn | QA Architect – `[TBD: OQ-007]` |
| Người review | Product Owner, Tech Lead, IT/Security, Designer |
| Người phê duyệt | QA Lead, Product Owner – `[TBD: OQ-007]` |

**Lịch sử phiên bản**

| Phiên bản | Ngày | Tác giả | Tóm tắt thay đổi |
|---|---|---|---|
| 0.1 | 2026-10-26 | QA | Bản nháp đầu tiên. Ghi kết quả chu kỳ kiểm thử tự động đầu tiên trên bản demo (49/49 test backend, 2/2 E2E đạt, độ phủ mã backend 78%) |
| 0.3 | 2026-10-27 | QA | Thêm Phụ lục D – kết quả thực thi chu kỳ C2 trên 130 test case (103 đạt, 6 cần người xác nhận, 21 bị chặn, 0 không đạt), kèm 12 lỗi phát hiện khi chạy (DEF-T-007…DEF-T-018; 8 đã sửa). Thêm 8 test tự động backend (66 test), công cụ bằng chứng `app/frontend/evidence/` |
| 0.2 | 2026-10-26 | QA | Sửa theo review `Test_Plan_IEEE_829_Checklist.xlsx` (TP-DEF-001…013): thêm tổng quan hệ thống (2.0); định danh bản build (3.1); quy tắc chấm rủi ro và ưu tiên thống nhất (A.7, 4.1); phân chia tự động/thủ công và kiểm thử khám phá (6.3); gắn ưu tiên cho E2E (6.1.3); thêm 7 test case để phủ 100% AC và trường hợp biên; người quản lý dữ liệu test và người duyệt kết quả (12.0); điều kiện khởi tạo lại môi trường (8.0); kích thước staging và quy tắc phiên bản công cụ (11.0); liên kết lịch với OQ-015 (14.0); điều kiện đo NFR-001 (PERF-001); công việc kiểm thử lại lỗi (10.0) |

**Quy ước trong tài liệu**

- ID yêu cầu dùng chung với các tài liệu nguồn: `BR-xxx` (BRD), `US-xxx`, `NFR-xxx`, `E-xx`, `EVT-xx` (PRD), `AC-0x` (kịch bản nghiệm thu intake / BRD MET-006), `ALG-xx` (BLUEPRINT), `T..-..` (PLAN).
- ID kiểm thử: `UT` unit · `INT` tích hợp · `API` hợp đồng API · `E2E` hệ thống · `UAT` nghiệm thu · `PERF` hiệu năng · `SEC` bảo mật · `ACC` trợ năng · `UI` giao diện · `QLT` chất lượng câu trả lời · `REG` bộ hồi quy.
- **Trạng thái thực thi** của từng test case:
  - **Đạt (tự động)**: có test tự động và test đó đạt trong chu kỳ ngày 26/10/2026.
  - **Đạt (thủ công)**: đã kiểm tra bằng tay hoặc bằng smoke test.
  - **Chưa chạy**: đã thiết kế nhưng chưa thực thi.
  - **Bị chặn**: thiếu dữ liệu, hạ tầng, hoặc còn câu hỏi mở.
- `[Đề xuất QA]` = giá trị QA đề xuất, cần PO hoặc Tech Lead xác nhận.

---

## Mục lục

- [Phần A – Phân tích tài liệu đầu vào](#phần-a--phân-tích-tài-liệu-đầu-vào)
- [Phần B – Kế hoạch kiểm thử theo IEEE 829](#phần-b--kế-hoạch-kiểm-thử-theo-ieee-829)
  - 1.0 Định danh · 2.0 Giới thiệu · 3.0 Đối tượng kiểm thử · 4.0 Tính năng được kiểm thử · 5.0 Tính năng không kiểm thử
  - 6.0 Cách tiếp cận · 7.0 Tiêu chí đạt/không đạt · 8.0 Tạm dừng và tiếp tục · 9.0 Sản phẩm bàn giao · 10.0 Công việc kiểm thử
  - 11.0 Môi trường · 12.0 Trách nhiệm · 13.0 Nhân sự và đào tạo · 14.0 Lịch trình · 15.0 Rủi ro và dự phòng · 16.0 Phê duyệt
- [Phụ lục A – Ma trận truy vết yêu cầu → test case](#phụ-lục-a--ma-trận-truy-vết-yêu-cầu--test-case)
- [Phụ lục B – Kết quả chu kỳ 1 và khoảng trống](#phụ-lục-b--kết-quả-chu-kỳ-1-26102026-và-khoảng-trống)
- [Phụ lục C – Đối chiếu bố cục IEEE 829](#phụ-lục-c--đối-chiếu-bố-cục-ieee-829)
- [Phụ lục D – Kết quả thực thi chu kỳ C2](#phụ-lục-d--kết-quả-thực-thi-chu-kỳ-c2-27102026)

---

# Phần A – Phân tích tài liệu đầu vào

## A.1 Danh mục tài liệu đầu vào

| Loại tài liệu | Tên tài liệu | Phiên bản | Nguồn | Thông tin chính dùng cho kiểm thử |
|---|---|---|---|---|
| Intake / BRD gốc | [BRD_MVP_AI_Chat_PDF.md](../01-intake/BRD_MVP_AI_Chat_PDF.md) | – | Sponsor/BA | 7 kịch bản nghiệm thu AC-01…AC-07 |
| BRD | [BRD.md](../02-requirements/BRD.md) | 0.2 | BA | BR-001…BR-029, MET-001…MET-007, RSK-001…RSK-008 |
| SRS/PRD | [PRD.md](../02-requirements/PRD.md) | 0.2 | PM/BA | 27 user story kèm AC, NFR-001…NFR-024, E-01…E-19, EVT-01…EVT-11, launch gate G-01…G-09 |
| User Stories | [USER_STORIES.md](../03-analysis/USER_STORIES.md) | 0.1 | Product | Chi tiết story, AC dạng Given/When/Then, liên kết màn hình |
| Use case | [USE_CASE_DIAGRAM.md](../03-analysis/USE_CASE_DIAGRAM.md) | 0.1 | BA | Tác nhân P1, IdP, dịch vụ AI; ranh giới hệ thống |
| SAD (IEEE 1016) | [SAD.md](../04-design/SAD.md) | 0.4 | Kiến trúc | Thành phần, ADR, luồng chính, chiến lược bảo mật |
| Blueprint (IEEE 1016) | [BLUEPRINT.md](../04-design/BLUEPRINT.md) | 0.3 | Kiến trúc | Thuật toán ALG-01…ALG-12, máy trạng thái, bảng truy vết test (mục cuối) |
| UI/UX | [html_design/](../04-design/html_design/index.html) S01–S11 | theo BLUEPRINT v0.3 | Designer | Trạng thái từng màn hình, luồng, yêu cầu trợ năng |
| API | [API_DESIGN.md](../04-design/API_DESIGN.md) + [openapi.yaml](../04-design/openapi.yaml) | 0.1 | Dev | 15 thao tác, mã lỗi RFC 9457 theo `code`, idempotency, rate limit |
| CSDL | [DATABASE_DESIGN.md](../04-design/DATABASE_DESIGN.md) + [schema.sql](../04-design/schema.sql) | 0.1 | Dev | RLS theo workspace, trigger bất biến, vai trò CSDL |
| Kế hoạch phát triển | [PLAN.md](../05-implement/PLAN.md) + `tasks/*.md` | 0.1 | Dev | 12 lát dọc VS-0…VS-11, 59 task, trạng thái Done/Partial/Deferred |
| Mã nguồn + test | [app/](../../app/README.md) | 26/10/2026 | Dev | 49 test backend, 2 E2E Playwright, smoke `scripts/smoke.py` |

## A.2 Yêu cầu trích từ BRD/PRD

### A.2.1 Yêu cầu chức năng (theo epic)

| Nhóm | Requirement ID | Loại | Mô tả ngắn | Ưu tiên | Nguồn |
|---|---|---|---|---|---|
| EP-01 Tiếp nhận | US-001…US-004 | Functional | Tải một/nhiều PDF; từ chối file không phải PDF, quá dung lượng, quá số trang | P0 | BR-001…BR-004 |
| EP-02 Xử lý & quản lý | US-005…US-008, US-010, US-011 | Functional | Tự xử lý; danh sách + trạng thái; thông báo Sẵn sàng; lý do thất bại; xóa; tài liệu đã xóa không được dùng | P0 | BR-005…BR-011 |
| | US-009 | Functional | Xử lý lại khi thất bại R-04 | P1 | BR-009 |
| EP-03 Hỏi đáp | US-012…US-014, US-016 | Functional | Hỏi tự nhiên; chỉ dựa trên tài liệu Sẵn sàng; nhiều câu trong phiên; "chưa đủ thông tin" | P0 | BR-012…BR-015 |
| | US-015 | Functional | Câu hỏi tiếp nối hiểu ngữ cảnh | P1 | BR-014 (chờ OQ-012) |
| EP-04 Đa tài liệu | US-017 | Functional | Tổng hợp từ nhiều tài liệu | P0 | BR-017 |
| | US-018 / US-019 | Functional | Nêu mâu thuẫn / giới hạn nhóm tài liệu | P1 / P2 | BR-018 / OQ-018 |
| EP-05 Nguồn | US-020, US-021 | Functional | Tên tài liệu, số trang đúng | P0 | BR-019, BR-020 |
| | US-022 | Functional | Mở tài liệu gốc tại trang | P1 | BR-021 (chờ OQ-014) |
| EP-06 Truy cập | US-023, US-024 | Functional + Security | Chỉ người được cấp quyền; cách ly tài liệu giữa người dùng | P0 | BR-022, BR-023 |
| EP-07 Phản hồi & lỗi | US-025, US-026 | Functional | Chỉ báo đang xử lý/đang soạn; báo lỗi tải lên/câu hỏi | P0 | BR-024, BR-027 |
| | US-027 | Functional | Gửi lại câu hỏi lỗi bằng một thao tác | P1 | BR-028 |

Tổng: **21 story P0, 5 story P1, 1 story P2**. Mỗi story có từ 1 tới 3 AC trong PRD mục 3.2–3.8.

### A.2.2 Yêu cầu phi chức năng

| Requirement ID | Loại | Ngưỡng | Ưu tiên kiểm thử | Phương pháp (PRD) |
|---|---|---|---|---|
| NFR-001 | Hiệu năng | Thời gian trả lời p90 ≤ 15 s, p50 ≤ 8 s | High | Test – đo trên bộ câu hỏi, 100 tài liệu/người dùng |
| NFR-002 | Hiệu năng | Xử lý file 20 MB/300 trang ≤ 3 phút | High | Test – PDF mẫu |
| NFR-003 | Chất lượng AI | Độ chính xác câu trả lời ≥ 80% | High | Test – người dùng nghiệp vụ chấm |
| NFR-004 | Chất lượng AI | Đúng tên tài liệu nguồn ≥ 90% | High | Đối chiếu PDF gốc |
| NFR-018 | Chất lượng AI | Đúng số trang ≥ 85% | High | Đối chiếu PDF gốc |
| NFR-005 | Chất lượng AI | Từ chối đúng ≥ 90% trên câu hỏi ngoài tài liệu | High | Bộ câu hỏi "ngoài tài liệu" |
| NFR-006, NFR-019, NFR-020, NFR-021 | Ràng buộc | ≤ 20 MB/file, ≤ 10 file/lần, ≤ 100 tài liệu/người, ≤ 300 trang/file | High | Test biên |
| NFR-007 | Hiệu năng | Đạt NFR-001 với 20 người hỏi đồng thời | Medium | Load test |
| NFR-008 | Khả dụng | ≥ 80% người thử tự hoàn thành tải → hỏi → xem nguồn trong ≤ 5 phút | Medium | Usability test ≥ 5 người |
| NFR-009, NFR-022 | Bảo mật | HTTPS TLS ≥ 1.2; mã hóa khi lưu | High | Security review |
| NFR-010 | Bảo mật | Không truy cập chéo tài liệu bằng bất kỳ cách nào; không truy cập ẩn danh | **Critical** | Kiểm thử phân quyền + xâm nhập |
| NFR-011 | Bảo mật/riêng tư | Chỉ gửi đoạn được chọn tới nhà cung cấp AI đã duyệt | High | Inspection dữ liệu gửi đi |
| NFR-012, NFR-023 | Kiểm toán | Ghi ai tải/xóa/hỏi, lúc nào; lưu ≥ 90 ngày | Medium | Inspection |
| NFR-013 | Dữ liệu | File gốc + dữ liệu trích xuất bị xóa ≤ 24 h sau khi người dùng xóa | High | Test + Inspection |
| NFR-014, NFR-024 | Dữ liệu | Tài liệu lưu tới khi xóa; hội thoại giữ trong phiên, mất khi đăng xuất/hết phiên | Medium | Test |
| NFR-015 | Vận hành | 99% trong giờ làm việc | Low (sau go-live) | Giám sát |
| NFR-016 | Ngôn ngữ | Giao diện tiếng Việt; hỏi đáp Việt/Anh; trả lời theo ngôn ngữ câu hỏi | Medium | Test |
| NFR-017 | Tương thích | 2 phiên bản mới nhất Chrome/Edge, ≥ 1280 px | Medium | Test tương thích |

### A.2.3 Quy tắc nghiệp vụ

| Requirement ID | Loại | Mô tả | Ưu tiên | Nguồn |
|---|---|---|---|---|
| BRL-01 | Business rule | Mã lý do thất bại R-01…R-04; **chỉ R-04 được xử lý lại** | High | PRD 3.3 |
| BRL-02 | Business rule | Chọn N+1 file → **không tải file nào** | High | US-002 AC 2 |
| BRL-03 | Business rule | Lẫn file hợp lệ và không hợp lệ → nhận file hợp lệ, liệt kê file bị từ chối kèm lý do | High | US-002 AC 3 |
| BRL-04 | Business rule | Câu trả lời "chưa đủ thông tin" không kèm nguồn | High | US-016 |
| BRL-05 | Business rule | Không xác định được số trang → chỉ hiện tên tài liệu, không hiện số trang giả | High | US-021 AC 2 |
| BRL-06 | Business rule | Câu hỏi ≤ 2.000 ký tự; câu hỏi trống/khoảng trắng không được gửi | Medium | E-14, E-15 |
| BRL-07 | Business rule | Sự kiện analytics không chứa nội dung câu hỏi, câu trả lời, tài liệu | High | PRD 5.2 |
| BRL-08 | Business rule | Trùng tên file vẫn nhận, phân biệt bằng thời điểm tải lên | Low | E-12 |

## A.3 Thành phần thiết kế (SAD/BLUEPRINT – IEEE 1016)

| Design view | Thành phần | Loại | Giao diện | Máy trạng thái | Phụ thuộc | Trọng tâm kiểm thử |
|---|---|---|---|---|---|---|
| Composition | `api` (FastAPI), `worker`, SPA React, `devdb` (PostgreSQL + pgvector), IdP OIDC, blob store | Tiến trình/dịch vụ | HTTP `/api/v1`, SQL, OIDC | – | PostgreSQL, IdP, LLM, embedding | Tích hợp đầu-cuối, khởi động/dừng |
| Component & Connector | `identity`, `documents`, `ingestion`, `retrieval`, `qa`, `events`, `audit` | Module nghiệp vụ | Ports: BlobPort, EmbeddingPort, LlmPort, IdentityPort | Document, Message | Adapters | Unit qua fake adapter; import-linter giữ ranh giới tầng |
| Interaction | ALG-01 lô tải 4 pha → ALG-02 kiểm tra PDF → ALG-03/04 ingest → ALG-05 truy xuất RRF → ALG-06 sinh và kiểm tra trích dẫn → ALG-08 hỏi đáp idempotent | Luồng tuần tự | SSE `document.status_changed`, `quota.changed`, `session.expiring` | – | Job queue | Thứ tự commit, idempotency, hủy khi xóa |
| Information | `document`, `chunk`, `job`, `conversation`, `message`, `citation`, `session`, `audit_event`, `analytics_event`, `rate_limit_counter` | Schema SQL | RLS theo `app.workspace_id` | – | pgvector HNSW, tsvector | Bất biến: chunk chỉ tồn tại khi document READY và chưa xóa; RLS |
| Interface | 15 thao tác OpenAPI | REST + SSE | Cookie phiên + CSRF double-submit | – | – | Hợp đồng, mã lỗi, header |
| State dynamics | Document: PROCESSING → READY / FAILED(R-01…R-04); FAILED(R-04) → PROCESSING; * → deleted → purged | State machine | Worker, API | Có | – | Chuyển trạng thái hợp lệ/không hợp lệ (READY → PROCESSING bị chặn bằng trigger) |
| State dynamics | Message: PENDING → ANSWERED / INSUFFICIENT / FAILED; FAILED → PENDING (gửi lại) | State machine | API | Có | – | Gửi lại, PENDING quá hạn hiển thị FAILED |
| State dynamics | Circuit breaker LLM: CLOSED → OPEN → HALF_OPEN | State machine | Answerer | Có | Clock | Ngưỡng 5 lỗi/60 s, mở 30 s |

## A.4 Thành phần UI/UX (html_design S01–S11)

| Màn hình | Thành phần | Tương tác | Trạng thái cần kiểm | Trợ năng | Luồng |
|---|---|---|---|---|---|
| S01 Màn hình chính – trống | Khu tài liệu, ô hỏi khóa | Kéo thả, chọn file | Trống, ô hỏi khóa kèm lý do | Lý do khóa bằng chữ, không chỉ màu | Đăng nhập → S01 |
| S02 Đang tải lên | Hàng đợi tải lên, thanh tiến độ | Tải lại, đóng thông báo | Đang tải x%, đang chờ, không nhận, tải lên thất bại | `role=progressbar`, `aria-valuenow` | S01 → S02 |
| S03 Trạng thái tài liệu | Dòng tài liệu, thông báo | Xử lý lại, xóa | Đang xử lý, Sẵn sàng, Thất bại + lý do | Biểu tượng + chữ (WCAG 1.4.1); `aria-live` | S02 → S03 |
| S04 Hỏi đáp có trích dẫn | Câu hỏi, câu trả lời, nút [n], chip nguồn | Gửi (Enter), bấm nguồn | Đang soạn, có nguồn, đa tài liệu, mâu thuẫn, chưa đủ thông tin | Nút có `aria-label`; tắt hiệu ứng khi `prefers-reduced-motion` | S03 → S04 |
| S05 Lỗi khi hỏi | Thẻ lỗi, đếm ngược | Gửi lại | 503/504, 429 đếm ngược, nguồn đã xóa, sắp hết phiên | `role=alert` | S04 → S05 |
| S06 Trình xem PDF | Dialog, iframe | Đóng, Esc | Mở đúng trang | `aria-modal`, focus quay về nút đã bấm | S04 → S06 |
| S07 Xác nhận xóa | Alertdialog | Hủy (mặc định), Xóa | Đang xóa | Focus mặc định ở Hủy | S03 → S07 |
| S08 Giới hạn tải lên | Cảnh báo | – | Quá 10 file, sắp hết hạn mức | `role=alert` / `status` | S01 → S08 |
| S09 Chưa được cấp quyền | Thẻ thông báo | Đăng nhập lại | – | Không lộ dữ liệu ứng dụng | Đăng nhập → S09 |
| S10 Lỗi đăng nhập | Thẻ + mã tham chiếu | Thử lại | – | – | Đăng nhập → S10 |
| S11 Phiên hết hạn | Thẻ + đếm ngược | Đăng nhập ngay | – | – | Mọi màn hình → S11 |

## A.5 Thành phần API (openapi.yaml)

| Endpoint | Method | Request | Response | Mã lỗi | Xác thực |
|---|---|---|---|---|---|
| `/auth/login` | GET | `return_to` | 302 → IdP | – | Không |
| `/auth/callback` | GET | `code`, `state` | 302 → `/`, `/access-denied`, `/login-error` | – | Không |
| `/auth/logout` | POST | – | 204 | 401, 403 `csrf_invalid` | Có + CSRF |
| `/me` | GET | – | `Me` (user, hạn mức, `limits`) | 401 | Có |
| `/upload-batches` | POST | `files[{name,size_bytes}]` | 201 `batch_id` | 401, 403, 422 `too_many_files` / `quota_exceeded` | Có + CSRF |
| `/upload-batches/{batch_id}/files/{client_file_id}` | PUT | multipart `file` | 201 mới / 200 đã có `Document` | 401, 403, 404 `batch_expired`, 409 `batch_full`, 413, 422 `not_pdf`/`too_large`/`too_many_pages`/`encrypted`, 429, 503 | Có + CSRF |
| `/documents` | GET | – | `items[]`, hạn mức | 401 | Có |
| `/documents/{id}` | DELETE | – | 204 | 401, 403, 404 | Có + CSRF |
| `/documents/{id}/reprocess` | POST | – | 202 `Document` | 401, 403, 404, 409 `not_retryable` | Có + CSRF |
| `/documents/{id}/file` | GET | `from`, `page` | 200 PDF | 401, 404, 410 `deleted` | Có |
| `/conversations/current` | GET | – | `Conversation` | 401 | Có |
| `/conversations/{id}/messages` | POST | `client_request_id`, `question` | 200 `Answer` | 401, 403, 404, 409 `no_ready_documents`/`request_in_progress`, 422 `empty_question`/`question_too_long`/`idempotency_mismatch`, 429, 503, 504 | Có + CSRF |
| `/events` | GET | – | SSE | 401 | Có |
| `/healthz`, `/readyz` | GET | – | 200 / 503 | – | Không |

## A.6 User story và tiêu chí chấp nhận

Nội dung AC đầy đủ nằm ở PRD mục 3.2–3.8. Bảng dưới đây chỉ tóm tắt những gì cần kiểm thử; test case tương ứng nằm ở [Phụ lục A](#phụ-lục-a--ma-trận-truy-vết-yêu-cầu--test-case).

| Story | Mô tả rút gọn | Số AC | Ưu tiên | Phụ thuộc / ghi chú |
|---|---|---|---|---|
| US-001 | Tải một PDF, thấy tiến độ | 2 | P0 | – |
| US-002 | Tải nhiều PDF (≤ 10), N+1 → không tải file nào, lẫn file hợp lệ/không hợp lệ | 3 | P0 | OQ-003 |
| US-003 | Từ chối file không phải PDF | 1 | P0 | – |
| US-004 | Từ chối file quá dung lượng/số trang, thông báo nêu số liệu | 2 | P0 | OQ-003 |
| US-005 | Tự xử lý trong NFR-002 | 1 | P0 | – |
| US-006 | Danh sách + trạng thái + thời điểm; trạng thái trống | 2 | P0 | – |
| US-007 | Thông báo Sẵn sàng, không cần tải lại trang | 1 | P0 | SSE |
| US-008 | Thất bại + lý do (hỏng, mật khẩu, scan) | 2 | P0 | OQ-013 |
| US-009 | Xử lý lại chỉ với R-04 | 2 | P1 | – |
| US-010 | Xóa có xác nhận; xóa khi đang xử lý thì hủy xử lý | 2 | P0 | – |
| US-011 | Tài liệu đã xóa không được dùng để trả lời | 1 | P0 | – |
| US-012 | Hỏi tự nhiên Việt/Anh; ô hỏi khóa khi chưa có tài liệu Sẵn sàng; không gửi câu trống | 3 | P0 | OQ-011 |
| US-013 | Chỉ dùng tài liệu Sẵn sàng | 2 | P0 | – |
| US-014 | 5 câu liên tiếp trong cùng khung hội thoại | 1 | P0 | – |
| US-015 | Câu hỏi tiếp nối | 2 | P1 | **Bị chặn – OQ-012** |
| US-016 | "Chưa đủ thông tin", không kèm nguồn; đạt NFR-005 | 2 | P0 | DEP-005 |
| US-017 | Tổng hợp 2 tài liệu, trích dẫn cả 2; MET-003 ≥ 80% | 2 | P0 | DEP-005 |
| US-018 | Nêu mâu thuẫn kèm nguồn từng giá trị | 1 | P1 | Cần LLM thật |
| US-019 | Giới hạn nhóm tài liệu | 1 | P2 | **Ngoài phạm vi – OQ-018** |
| US-020 | Đúng tên file trong nguồn | 1 | P0 | – |
| US-021 | Đúng số trang; không hiện trang giả | 2 | P0 | – |
| US-022 | Mở tài liệu gốc đúng trang; nguồn đã xóa → báo đã xóa | 3 | P1 | OQ-014 |
| US-023 | Người không có quyền bị từ chối; hết phiên giữ câu đang soạn | 2 | P0 | – |
| US-024 | Người dùng B không thấy tài liệu của A | 2 | P0 | OQ-002 |
| US-025 | Chỉ báo đang soạn/đang xử lý, khóa ô hỏi khi chờ | 2 | P0 | – |
| US-026 | Báo lỗi tải lên (nút Tải lại) và lỗi câu hỏi tại chỗ | 2 | P0 | – |
| US-027 | Gửi lại một thao tác, lặp lại được | 2 | P1 | – |

## A.7 Đánh giá rủi ro

Điểm rủi ro = Khả năng (1–5) × Tác động (1–5), thang 1–25. Mức rủi ro:

- **Critical**: tác động = 5 về **lộ hoặc mất dữ liệu**, bất kể khả năng (một sự cố đã đủ chặn go-live, MET-007 = 0).
- **Cao**: điểm ≥ 15.
- **Trung bình**: điểm từ 10 tới 14.
- **Thấp**: điểm ≤ 9.

Rủi ro Critical và Cao bắt buộc có test tự động trong bộ hồi quy.

| Risk ID | Mô tả rủi ro | Khả năng | Tác động | Điểm | Mức | Chiến lược giảm thiểu bằng kiểm thử | Nguồn |
|---|---|---|---|---|---|---|---|
| TR-01 | AI trả lời sai hoặc bịa thông tin không có trong tài liệu (kể cả dùng tài liệu đã xóa hoặc chưa Sẵn sàng) | 3 | 5 | 15 | **Cao** | Bộ câu hỏi chuẩn QLT; test kiểm tra trích dẫn (mã lạ bị loại → INSUFFICIENT); cổng ngưỡng; test tài liệu đã xóa/đang xử lý không được dùng | RSK-001 |
| TR-02 | Lộ tài liệu giữa người dùng (lỗi phân quyền, gọi API trực tiếp) | 2 | 5 | 10 | **Critical** (lộ dữ liệu) | Test cách ly mức API **và** mức CSDL (RLS); test IDOR mọi endpoint có `{id}`; pentest | RSK-002, NFR-010 |
| TR-03 | Nội dung tài liệu/câu hỏi lọt vào log, analytics hoặc gửi ra ngoài quá mức | 3 | 4 | 12 | Trung bình | Test không lộ nội dung trong analytics/audit/log; kiểm tra prompt chỉ chứa đoạn được chọn, không chứa tên file/ID | RSK-002, NFR-011 |
| TR-04 | PDF trích xuất kém (bảng, nhiều cột, tiếng Việt lỗi dấu) | 4 | 3 | 12 | Trung bình | Bộ PDF thật đa dạng (TS-03); kiểm tra NFC; chấm số trang NFR-018 | RSK-003, RSK-004 |
| TR-05 | Vượt NFR-001 khi dùng LLM thật có suy luận (timeout 10 s) | 4 | 3 | 12 | Trung bình | PERF-001 với LLM thật; theo dõi p50/p90; điều chỉnh `LLM_TIMEOUT_S`/`ANSWER_BUDGET_S` | NFR-001 |
| TR-06 | CSDL dev (PGlite) khác PostgreSQL thật: một kết nối, lỗi giao thức với message lớn | 4 | 3 | 12 | Trung bình | Chạy integration trên PostgreSQL thật (`TEST_DATABASE_URL`, CI); test tài liệu lớn 40 trang | Phát hiện 26/10 |
| TR-07 | Xóa tài liệu không xóa hết dữ liệu (chunk, file gốc) trong 24 h | 2 | 4 | 8 | Thấp | Test purge + sweep; inspection blob store | NFR-013 |
| TR-08 | Tải lên lặp do mất mạng tạo tài liệu trùng, tốn hạn mức | 3 | 2 | 6 | Thấp | Test idempotency `client_file_id`; E2E Tải lại | E-04 |
| TR-09 | Chưa có bộ câu hỏi chuẩn (DEP-005) → không đo được G-02 | 5 | 4 | 20 | **Cao** | Chặn launch gate G-02; leo thang PO; QA soạn bản nháp bộ câu hỏi | DEP-005, OQ-009 |
| TR-10 | Nhiều câu hỏi mở (OQ-002/003/009/012/013/014) làm thay đổi tiêu chí | 4 | 3 | 12 | Trung bình | Đánh dấu test case "Bị chặn"; tham số hóa giới hạn qua cấu hình | PRD 7.1 |

---

# Phần B – Kế hoạch kiểm thử theo IEEE 829

## 1.0 Định danh kế hoạch kiểm thử (IEEE 829 §5.1)

| Thuộc tính | Giá trị |
|---|---|
| Document ID | TP-AICHAT-001-v0.2 |
| Tên | AI Chat PDF – Master Test Plan |
| Phiên bản | 0.2 |
| Ngày phát hành | 2026-10-26 |
| Trạng thái | Draft |
| Phân loại | Nội bộ (Internal) |
| Người soạn | QA – `[TBD: OQ-007]` |
| Người phê duyệt | QA Lead, Product Owner |

## 2.0 Giới thiệu (IEEE 829 §5.2)

### Tổng quan phần mềm được kiểm thử

AI Chat PDF là ứng dụng web nội bộ. Người dùng (P1) tải các file PDF của dự án lên, rồi đặt câu hỏi bằng ngôn
ngữ tự nhiên. Hệ thống trả lời **chỉ dựa trên nội dung các tài liệu đã Sẵn sàng của chính người đó**, kèm tên tài
liệu và số trang để kiểm chứng. Khi tài liệu không có thông tin, hệ thống trả lời "chưa đủ thông tin" thay vì đoán.

Kiến trúc (SAD v0.4) gồm:
- SPA React;
- API FastAPI kèm worker chạy nền: kiểm tra PDF, trích văn bản, chia đoạn, tạo embedding, ghi chỉ mục;
- PostgreSQL + pgvector, có Row-Level Security cách ly dữ liệu theo người dùng;
- đăng nhập OIDC qua IdP của công ty, và dịch vụ LLM bên ngoài.

Câu trả lời được tạo theo kiểu RAG: kết hợp tìm kiếm vector với full-text, rồi kiểm tra trích dẫn trước khi
trả về.

Tài liệu này là kế hoạch kiểm thử tổng thể (MTP) cho bản MVP, bao gồm cả các chu kỳ trên bản demo hiện có lẫn
staging và nghiệm thu.

### 2.1 Mục đích

Kế hoạch kiểm thử tổng thể (MTP) này nhằm:

- xác định chiến lược kiểm thử cho MVP AI Chat PDF, từ unit tới nghiệm thu;
- xác định các mức, loại và chu kỳ kiểm thử;
- phân công vai trò, trách nhiệm và lịch trình;
- đặt tiêu chí vào/ra cho từng giai đoạn và tiêu chí đạt cho launch gate (PRD 5.1);
- xác định môi trường, công cụ và dữ liệu cần dùng;
- truy vết từ yêu cầu (BR/US/NFR/E) tới test case và test tự động.

### 2.2 Phạm vi

**Trong phạm vi:**

- Kiểm thử chức năng 27 user story (21 P0, 5 P1, 1 P2 – trong đó US-019 ngoài phạm vi, US-015 bị chặn).
- Kiểm thử hợp đồng và hành vi của 15 thao tác API, gồm mã lỗi, idempotency, rate limit, CSRF.
- Kiểm thử tích hợp CSDL: RLS, trigger bất biến, job queue, purge.
- Kiểm thử hệ thống đầu-cuối trên trình duyệt (Edge/Chrome) cho các màn hình S01–S11 và trường hợp biên E-01…E-19.
- Kiểm thử chất lượng câu trả lời (NFR-003/004/005/018) trên bộ câu hỏi chuẩn.
- Kiểm thử phi chức năng: hiệu năng (NFR-001/002/007), bảo mật (NFR-009…013, 022, 023), trợ năng, tương thích (NFR-016/017), khả dụng (NFR-008).
- Kiểm thử hồi quy tự động cho mỗi thay đổi mã.
- Kiểm thử nghiệm thu 7 kịch bản AC-01…AC-07 (MET-006).

**Ngoài phạm vi:**

- US-019 (giới hạn câu hỏi trong nhóm tài liệu) – P2, chờ OQ-018.
- OCR cho PDF scan – không thuộc MVP (OQ-013); chỉ kiểm thử việc báo thất bại R-03.
- Kiểm thử bản thân nhà cung cấp AI và IdP của công ty (trách nhiệm nhà cung cấp/IT); chỉ kiểm thử phần tích hợp.
- Stress test vượt 2 lần tải mục tiêu (> 40 người dùng đồng thời).
- Thiết bị di động, màn hình < 1280 px (NFR-017).
- Kiểm thử xâm nhập chuyên sâu: do IT/Security thực hiện riêng; MTP chỉ yêu cầu kết quả.

### 2.3 Mục tiêu

| Objective ID | Mục tiêu | Tiêu chí thành công | Truy vết |
|---|---|---|---|
| OBJ-001 | Xác nhận toàn bộ yêu cầu chức năng | 100% AC của 21 story P0 đạt; story P1 không bị chặn đạt | US-001…US-027, G-01 |
| OBJ-002 | Xác nhận hợp đồng API | 100% thao tác trong `openapi.yaml` có test; mọi mã lỗi đã khai báo có ít nhất 1 test | API-001…API-031 |
| OBJ-003 | Xác nhận giao diện theo thiết kế | 11/11 màn hình S01–S11 có test và khớp trạng thái thiết kế | UI-001…UI-011 |
| OBJ-004 | Xác nhận trợ năng | WCAG 2.1 AA cho luồng chính, không lỗi axe mức serious/critical | ACC-001…ACC-007 |
| OBJ-005 | Xác nhận hiệu năng | NFR-001 (p90 ≤ 15 s), NFR-002 (≤ 3 phút), NFR-007 (20 người đồng thời) | PERF-001…PERF-005, G-03 |
| OBJ-006 | Xác nhận bảo mật | Không lỗ hổng Critical/High; 0 sự cố truy cập chéo (MET-007) | SEC-001…SEC-012, G-04 |
| OBJ-007 | Xác nhận chất lượng câu trả lời | NFR-003 ≥ 80%, NFR-004 ≥ 90%, NFR-018 ≥ 85%, NFR-005 ≥ 90% | QLT-001…QLT-005, G-02 |
| OBJ-008 | Xác nhận nghiệm thu | 7/7 kịch bản AC-01…AC-07 đạt | UAT-001…UAT-007, MET-006 |

### 2.4 Tài liệu tham chiếu

| Tài liệu | Phiên bản | Nguồn |
|---|---|---|
| BRD-AICHAT-001 | 0.2 | BA |
| PRD-AICHAT-001 | 0.2 | PM/BA |
| US-AICHAT-001 (User Stories) | 0.1 | Product |
| SAD-AICHAT-001 | 0.4 | Kiến trúc |
| BLUEPRINT-AICHAT-001 | 0.3 | Kiến trúc |
| API-DESIGN-AICHAT-001 + openapi.yaml | 0.1 | Dev |
| DB-DESIGN-AICHAT-001 + schema.sql | 0.1 | Dev |
| html_design S01–S11 | theo BLUEPRINT v0.3 | Designer |
| PLAN-AICHAT-001 | 0.1 | Dev |
| [Hướng dẫn cài đặt](../../guide/HUONG_DAN_CAI_DAT.md), [Hướng dẫn sử dụng](../../guide/HUONG_DAN_SU_DUNG.md) | 26/10/2026 | Dev |
| IEEE 829-2008 Software and System Test Documentation | 2008 | IEEE |
| [Test_Plan_IEEE_829_Checklist.xlsx](../templates/Test_Plan_IEEE_829_Checklist.xlsx) | – | QA |

## 3.0 Đối tượng kiểm thử (IEEE 829 §5.3)

### 3.1 Phần mềm được kiểm thử

| Item ID | Tên | Phiên bản | Nguồn | Hình thức |
|---|---|---|---|---|
| SI-001 | API backend (FastAPI) – `app/backend/app` | 0.1.0 | Dev | REST `/api/v1` + SSE |
| SI-002 | Worker xử lý tài liệu, purge, bảo trì – `app/backend/worker` | 0.1.0 | Dev | Tiến trình nền (chạy trong API ở chế độ `DB_MODE=single`) |
| SI-003 | Ứng dụng web SPA – `app/frontend` | 0.1.0 | Dev | React + TypeScript (Vite) |
| SI-004 | Schema CSDL – `app/backend/migrations/sql/0001_initial.sql` | schema v0.3 | Dev | PostgreSQL 16+/PGlite 17.5 + pgvector 0.8 |
| SI-005 | Adapter tích hợp: OIDC, blob (local/memory), embedding (hashing/HTTP), LLM (extractive/Anthropic/fake) | 0.1.0 | Dev | Python |
| SI-006 | Cấu hình – `app/.env`, `app/backend/app/infra/settings.py` | 0.1.0 | Dev | ENV |
| SI-007 | Môi trường dev: `app/devdb` (PGlite), `app/backend/devidp` (IdP giả lập), `app/run.py` | 0.1.0 | Dev | Node.js / Python |
| SI-008 | Tài liệu người dùng – `guide/` | 26/10/2026 | Dev | Markdown |

**Định danh bản build**

- Mỗi chu kỳ kiểm thử gắn với **một commit git** của repo, ghi trong nhật ký thực thi (Phụ lục B).
- Từ chu kỳ C2 trở đi, bản đưa vào kiểm thử phải là commit sạch (không còn thay đổi chưa commit), có tag dạng
  `test-C2-YYYYMMDD`.
- Bản đưa lên staging được định danh bằng tag image container (T10-05).

| Chu kỳ | Bản build |
|---|---|
| C1 (26/10/2026) | Commit `166929f`, cộng 3 thay đổi chưa commit: `app/devdb/server.mjs` (gom message giao thức), `app/backend/app/infra/db.py` (tắt auto-prepare), `app/backend/tests/integration/test_documents.py` (INT-004). Các bản sửa này cần được commit trước C2 |

### 3.2 Tài sản kiểm thử

| Artifact ID | Tên | Định dạng | Vị trí |
|---|---|---|---|
| TA-001 | Test case (tài liệu này, Phụ lục A) | Markdown | `doc/07-verification/TEST_PLAN.md` |
| TA-002 | Dữ liệu test: PDF mẫu sinh tự động (hợp đồng, chính sách, bảng giá, scan, có mật khẩu, khóa in, hỏng, docx, PDF giả, quá trang) | PDF | `app/backend/tests/fixtures/pdfgen.py` → `app/sample-pdfs/` |
| TA-003 | Seed dữ liệu dev (2 người dùng, 3 tài liệu, RLS) | SQL | `app/backend/migrations/seed_dev.sql` |
| TA-004 | Test tự động backend (unit + integration) | pytest | `app/backend/tests/` |
| TA-005 | Test E2E trên trình duyệt | Playwright | `app/frontend/e2e/demo.spec.ts` |
| TA-006 | Smoke test đầu-cuối | Python | `app/backend/scripts/smoke.py` |
| TA-007 | Bản giả (fake): FakeIdp, FakeLlm, MemoryBlobStore, HashingEmbedding (có `fail_times`) | Python | `tests/conftest.py`, `app/adapters/` |
| TA-008 | Bộ câu hỏi chuẩn (≥ 50 trong tài liệu, ≥ 20 đa tài liệu, ≥ 20 ngoài tài liệu, 10 cặp tiếp nối) | CSV/JSON | **Chưa có – DEP-005, T06-03** |
| TA-009 | Kịch bản load test | k6 | **Chưa có – T10-06** |

## 4.0 Tính năng được kiểm thử (IEEE 829 §5.4)

### 4.1 Ma trận ưu tiên

**Quy tắc xếp ưu tiên kiểm thử** (kết hợp ưu tiên story với rủi ro A.7):

| Ưu tiên kiểm thử | Điều kiện |
|---|---|
| **Critical** | Có rủi ro mức Critical liên quan |
| **High** | Story P0 (hoặc NFR thuộc launch gate) **và** có rủi ro liên quan ≥ 12 điểm |
| **Medium** | Story P0 không có rủi ro ≥ 12; hoặc story P1 có rủi ro ≥ 12 |
| **Low** | Các trường hợp còn lại |

| Ưu tiên | Tính năng | Story | Yêu cầu | Rủi ro liên quan (điểm) |
|---|---|---|---|---|
| **Critical** | F-06 Truy cập và cách ly dữ liệu | US-023, US-024 (P0) | BR-022, BR-023, NFR-010 | TR-02 (Critical), TR-03 (12) |
| **High** | F-04 Hỏi đáp có căn cứ, chưa đủ thông tin | US-012, US-013, US-016 (P0) | BR-012…BR-016, NFR-003, NFR-005 | TR-09 (20), TR-01 (15), TR-05 (12) |
| **High** | F-07 Tổng hợp nhiều tài liệu, mâu thuẫn | US-017 (P0), US-018 (P1) | BR-017, BR-018 | TR-09 (20), TR-01 (15) |
| **High** | F-05 Nguồn tham chiếu (tên, trang) | US-020, US-021 (P0) | BR-019, BR-020, NFR-004, NFR-018 | TR-01 (15), TR-04 (12) |
| **High** | F-03 Xóa tài liệu và loại khỏi câu trả lời | US-010, US-011 (P0) | BR-010, BR-011, NFR-013 | TR-01 (15), TR-07 (8) |
| **High** | F-02 Xử lý và trạng thái tài liệu | US-005…US-008 (P0) | BR-005…BR-008, NFR-002 | TR-04 (12), TR-06 (12) |
| **High** | F-01 Tiếp nhận tài liệu và giới hạn | US-001…US-004 (P0) | BR-001…BR-004, NFR-006, NFR-019…NFR-021 | TR-06 (12), TR-08 (6) |
| **High** | F-08 Phản hồi và xử lý lỗi, gửi lại | US-025, US-026 (P0), US-027 (P1) | BR-024, BR-027, BR-028 | TR-05 (12) |
| **High** | F-10 Kiểm toán và analytics | – (NFR của G-04, G-07) | NFR-012, NFR-023, EVT-01…EVT-11 | TR-03 (12) |
| **Medium** | F-12 Hội thoại trong phiên | US-014 (P0), US-015 (P1) | BR-014, NFR-024 | – |
| **Medium** | F-11 Mở tài liệu gốc tại trang | US-022 (P1) | BR-021 | TR-04 (12) |
| **Low** | F-09 Xử lý lại tài liệu | US-009 (P1) | BR-009 | – (có cách tránh: tải lại file) |

### 4.2 Ma trận loại kiểm thử theo tính năng

| Tính năng | Unit | Integration | System (E2E) | Acceptance | Regression | Performance | Security | Accessibility |
|---|---|---|---|---|---|---|---|---|
| F-01 Tiếp nhận | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| F-02 Xử lý | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| F-03 Xóa | – | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ |
| F-04 Hỏi đáp | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| F-05 Nguồn | ✓ | ✓ | ✓ | ✓ | ✓ | – | – | ✓ |
| F-06 Truy cập | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ |
| F-07 Đa tài liệu | ✓ | ✓ | ✓ | ✓ | ✓ | – | – | – |
| F-08 Lỗi, gửi lại | ✓ | ✓ | ✓ | ✓ | ✓ | – | – | ✓ |
| F-09 Xử lý lại | – | ✓ | ✓ | – | ✓ | – | ✓ | – |
| F-10 Kiểm toán | ✓ | ✓ | – | – | ✓ | – | ✓ | – |
| F-11 Xem tài liệu gốc | – | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ |
| F-12 Hội thoại | – | ✓ | ✓ | ✓ | ✓ | – | – | – |

### 4.3 Mô tả tính năng

| Feature ID | Tính năng | Mô tả | Điểm cần kiểm thử | AC |
|---|---|---|---|---|
| F-01 | Tiếp nhận tài liệu | Kéo thả / chọn nhiều PDF, lô tải lên 4 pha (ALG-01), kiểm tra PDF trong sandbox (ALG-02) | Tiến độ; giới hạn 10 file / 20 MB / 300 trang / 100 tài liệu; từ chối docx, PDF giả, có mật khẩu; idempotency khi tải lại | US-001…US-004 AC |
| F-02 | Xử lý và trạng thái | Worker trích văn bản, chia đoạn trong trang, embedding, ghi chỉ mục (ALG-03/04); SSE trạng thái | PROCESSING → READY/FAILED; R-01/R-03/R-04; retry/backoff; thông báo không tải lại trang | US-005…US-008 AC |
| F-03 | Xóa tài liệu | Xóa mềm + xóa chunk + hủy ingest + purge ≤ 24 h (ALG-10/12) | Xác nhận trước khi xóa; câu hỏi sau khi xóa không dùng tài liệu đã xóa; purge file gốc; sweep job bị sót | US-010, US-011 AC |
| F-04 | Hỏi đáp | Truy xuất lai vector + full-text + RRF (ALG-05), cổng ngưỡng, sinh câu trả lời có kiểm tra trích dẫn (ALG-06), idempotent theo `client_request_id` (ALG-08) | Chỉ dùng tài liệu READY; "chưa đủ thông tin"; câu hỏi trống/quá dài; idempotency; Việt/Anh | US-012, US-013, US-016 AC |
| F-05 | Nguồn tham chiếu | Đánh số lại [n] theo thứ tự xuất hiện; chip "tên · tr.X"; bản chụp tên tài liệu | Đúng tên, đúng trang; mã nguồn lạ bị loại | US-020, US-021 AC |
| F-06 | Truy cập và cách ly | OIDC + PKCE, phiên cookie, CSRF, RLS theo workspace | Người ngoài nhóm bị từ chối; hết phiên; IDOR; RLS khi thiếu scope | US-023, US-024 AC |
| F-07 | Đa tài liệu | Câu trả lời trích nhiều tài liệu; cờ `conflict` | Trích cả 2 tài liệu; nêu mâu thuẫn | US-017, US-018 AC |
| F-08 | Phản hồi và lỗi | Chỉ báo đang soạn; thẻ lỗi 503/504; 429 đếm ngược; circuit breaker; gửi lại | Lỗi hiển thị tại chỗ; gửi lại giữ nguyên câu hỏi; không gửi trùng | US-025…US-027 AC |
| F-09 | Xử lý lại | `POST /documents/{id}/reprocess` | Chỉ R-04; 409 với R-01…R-03 | US-009 AC |
| F-10 | Kiểm toán và analytics | `audit_event`, `analytics_event` với whitelist thuộc tính | Có đủ sự kiện; không chứa nội dung | NFR-012, BRL-07 |
| F-11 | Xem tài liệu gốc | Dialog trình xem PDF của trình duyệt, `#page=N` | Đúng trang; tài liệu đã xóa → 410 + "(đã xóa)" | US-022 AC |
| F-12 | Hội thoại | Một hội thoại theo phiên | Giữ khi tải lại trang; mất khi đăng xuất | US-014 AC, NFR-024 |

## 5.0 Tính năng không kiểm thử (IEEE 829 §5.5)

| Feature ID | Tính năng | Lý do | Rủi ro | Kế hoạch |
|---|---|---|---|---|
| F-13 | US-019 Giới hạn câu hỏi trong nhóm tài liệu | P2, chưa có yêu cầu chốt (OQ-018), không triển khai | Thấp | Lập test case khi OQ-018 đóng |
| F-14 | US-015 Câu hỏi tiếp nối | Bị chặn theo PLAN (T11-05, OQ-012); chưa triển khai | Trung bình | Thực hiện QLT-005 (10 cặp tiếp nối) khi có triển khai + bộ câu hỏi |
| F-15 | OCR PDF scan | Ngoài phạm vi MVP (OQ-013) | Trung bình (ASM-001) | Chỉ kiểm thử báo R-03; theo dõi EVT-04 sau go-live |
| F-16 | Nội bộ nhà cung cấp AI và IdP công ty | Trách nhiệm bên thứ ba | Thấp | Kiểm thử phần tích hợp + hợp đồng nhà cung cấp (NFR-011) |
| F-17 | Giao diện di động, < 1280 px | Ngoài NFR-017 | Thấp | – |
| F-18 | Dashboard giám sát, cảnh báo (T10-03 phần chưa làm) | Chưa triển khai (chỉ có `/metrics`) | Trung bình | Kiểm thử khi triển khai staging (T10-05) |

## 6.0 Cách tiếp cận (IEEE 829 §5.6)

### 6.1 Các mức và loại kiểm thử

#### 6.1.1 Unit testing

| Thuộc tính | Mô tả |
|---|---|
| Nhóm phụ trách | Dev |
| Công cụ | pytest 9, pytest-asyncio, hypothesis (property-based), coverage.py |
| Mục tiêu độ phủ | ≥ 80% dòng mã backend toàn bộ; ≥ 90% cho `app/modules/**` `[Đề xuất QA]` |
| Điều kiện vào | Mã hoàn thành, qua ruff + mypy strict + import-linter |
| Điều kiện ra | 100% unit test đạt; độ phủ đạt mục tiêu |
| Trọng tâm | Thuật toán thuần: chia đoạn, chuẩn hóa văn bản, kiểm tra PDF, kiểm tra và đánh số trích dẫn, circuit breaker, embedding, bộ trả lời trích xuất, lọc log, kiểm tra cấu hình |
| Giả lập | Không cần CSDL; đồng hồ giả cho circuit breaker |

| Test Case ID | Đối tượng | Mô tả | Kết quả mong đợi | Test tự động | Trạng thái |
|---|---|---|---|---|---|
| UT-001 | Chunker (ALG-04) | Property: mỗi đoạn ≤ max token, không rỗng, đếm token khớp, chỉ số liên tiếp, mọi từ của trang được phủ | Thỏa với 60 dữ liệu ngẫu nhiên | `test_chunker_properties` | Đạt (tự động) |
| UT-002 | Chunker | Đoạn không vượt ranh giới trang | Mỗi đoạn thuộc đúng 1 trang | `test_chunk_never_spans_pages` | Đạt (tự động) |
| UT-003 | Extractor (ALG-03) | Chuẩn hóa NFC, nối từ gạch nối cuối dòng, gộp khoảng trắng | Văn bản chuẩn hóa đúng | `test_normalize` | Đạt (tự động) |
| UT-004 | Extractor + inspector | PDF hợp lệ 3 trang; scan → R-03; có mật khẩu → `encrypted`; quá trang; quá dung lượng | Phân loại đúng | `test_extract_and_inspect` | Đạt (tự động) |
| UT-005 | validate_output (ALG-06) | Loại mã nguồn lạ, đánh số lại theo thứ tự xuất hiện, gộp khoảng trắng | `"A [1]. B [2]. C [1]."` | `test_validate_renumbers_and_drops_invalid` | Đạt (tự động) |
| UT-006 | validate_output | Trạng thái insufficient; chỉ còn mã lạ | INSUFFICIENT | `test_validate_insufficient_cases` | Đạt (tự động) |
| UT-007 | Prompt | Nội dung nguồn chứa thẻ `</source>` bị escape (chống prompt injection qua tài liệu) | Không phá cấu trúc prompt | `test_prompt_escapes_sources` | Đạt (tự động) |
| UT-008 | Circuit breaker (ALG-07) | CLOSED → OPEN sau ngưỡng → từ chối → HALF_OPEN sau thời gian mở → CLOSED | Đúng chu trình | `test_circuit_breaker_cycle` | Đạt (tự động) |
| UT-009 | Embedding hashing | 1024 chiều, chuẩn hóa L2, câu bỏ dấu gần câu có dấu hơn câu khác chủ đề | Đúng | `test_hash_embedding` | Đạt (tự động) |
| UT-010 | Bộ trả lời trích xuất | Chọn câu chứa đáp án, trích đúng S# | `citations == ["S2"]` | `test_extractive_llm` | Đạt (tự động) |
| UT-011 | Lọc log (NFR-011) | Bỏ khóa question/answer/file_name/email… khỏi bản ghi log | Không còn nội dung | `test_redact_forbidden` | Đạt (tự động) |
| UT-012 | Settings | Production còn bí mật mặc định → lỗi; overlap ≥ target → lỗi | Ném lỗi | `test_settings_validation` | Đạt (tự động) |
| UT-013 | Rate limit cửa sổ cố định (ALG-09) | Biên cửa sổ, header RateLimit-*, Retry-After | Đúng | – (gián tiếp qua INT) | Chưa chạy (unit riêng) |
| UT-014 | Adapter Anthropic | Ánh xạ lỗi SDK → LlmRateLimited/Unavailable/Timeout; refusal → insufficient; `max_tokens` → InvalidOutput | Đúng ánh xạ | – | Chưa chạy |
| UT-015 | Adapter OIDC | Xác thực id_token: sai issuer/audience/nonce/chữ ký, JWKS xoay khóa | Từ chối đúng | – | Chưa chạy |

#### 6.1.2 Integration testing

| Thuộc tính | Mô tả |
|---|---|
| Nhóm phụ trách | Dev, QA |
| Công cụ | pytest + httpx `ASGITransport` (gọi API trong tiến trình), PostgreSQL thật qua PGlite trong bộ nhớ hoặc `TEST_DATABASE_URL` |
| Phạm vi | API ↔ module ↔ CSDL (RLS, trigger), worker ↔ job queue, purge ↔ blob store, bảo trì định kỳ |
| Điều kiện vào | Unit test đạt; migration chạy được |
| Điều kiện ra | 100% test tích hợp đạt trên **cả PGlite và PostgreSQL 16+ thật** (CI) |
| Trọng tâm | Bất biến dữ liệu, cách ly, idempotency, thứ tự commit, hủy khi xóa, retry |

| Test Case ID | Phạm vi | Loại | Kiểm tra | Kết quả mong đợi | Test tự động | Trạng thái |
|---|---|---|---|---|---|---|
| INT-001 | Schema + RLS | Positive/Negative | Seed dev; P1 thấy 3 tài liệu, P2 thấy 0, không đặt scope thấy 0; chèn chunk cho tài liệu PROCESSING → CheckViolation; READY → PROCESSING → CheckViolation | Đúng | `test_schema_invariants_and_rls` | Đạt (tự động) |
| INT-002 | Phạm vi workspace | Negative | `SET LOCAL` không rò sang transaction sau | Thiếu scope → `WorkspaceScopeMissing` | `test_set_local_does_not_leak` | Đạt (tự động) |
| INT-003 | Ingest đầu-cuối | Positive | Upload → job → READY; chunk có đúng trang | 3 đoạn / 3 trang | `test_upload_process_ask` | Đạt (tự động) |
| INT-004 | Ingest tài liệu lớn | Boundary | 40 trang, ≥ 40 đoạn kèm vector, message INSERT vượt nhiều gói TCP 64 KB | READY; CSDL vẫn hoạt động | `test_ingest_large_document` | Đạt (tự động) |
| INT-005 | Ingest + lỗi tạm thời | Negative | Embedding lỗi liên tục → retry/backoff → R-04 sau `INGEST_MAX_ATTEMPTS` | FAILED R-04, `retryable=true` | `test_reprocess_only_r04` | Đạt (tự động) |
| INT-006 | Xóa khi đang xử lý | Negative | Xóa trước khi worker chạy | Job ingest CANCELLED, purge DONE, 0 chunk | `test_delete_during_processing_cancels` | Đạt (tự động) |
| INT-007 | Purge | Positive | Sau xóa: chunk bị xóa ngay; worker purge xóa file gốc | Blob không còn | `test_delete_purge_and_answers_exclude` | Đạt (tự động) |
| INT-008 | Sweep purge bị sót | Recovery | Job purge bị mất, tài liệu đã xóa > 1 giờ → sweep enqueue lại | `purged_at` có giá trị | `test_maintenance_tasks` | Đạt (tự động) |
| INT-009 | Bảo trì | Positive | Hết hạn phiên, dọn bảng, phân vùng audit | Phiên hết hạn → 401 | `test_maintenance_tasks` | Đạt (tự động) |
| INT-010 | Truy xuất + bộ trả lời trích xuất | Positive | Hỏi điều khoản thanh toán | Trả lời "30 ngày", nguồn trang 2 | `test_extractive_answer_cites_correct_page` | Đạt (tự động) |
| INT-011 | Truy xuất đa tài liệu | Positive | "Giá gói Premium là bao nhiêu?" với ngưỡng dev 0.45 | Trích cả bảng giá Q4 và chính sách 2026, nêu 2 giá | `test_extractive_multi_document_price` | Đạt (tự động) |
| INT-012 | Cổng ngưỡng | Negative | Ngưỡng 0.99 | INSUFFICIENT, không gọi LLM | `test_gate_skips_llm` | Đạt (tự động) |
| INT-013 | Circuit breaker + API | Negative | 5 lỗi LLM liên tiếp | 503 kèm Retry-After, không gọi LLM khi mạch mở | `test_circuit_breaker_opens` | Đạt (tự động) |
| INT-014 | Hợp đồng OpenAPI | Contract | Mọi path/method trong `openapi.yaml` có trong OpenAPI sinh từ FastAPI | 0 thao tác thiếu | `test_openapi_matches_contract` | Đạt (tự động) |
| INT-015 | Adapter thật | Positive | OIDC với IdP thật, blob local, embedding HTTP, Anthropic | Hoạt động | smoke + E2E (OIDC, blob local); còn lại chưa | Một phần |
| INT-016 | PostgreSQL thật (CI) | Compatibility | Chạy toàn bộ INT trên `pgvector/pgvector:pg17` với `DB_MODE=pool` | 100% đạt | CI `app/.github/workflows/ci.yml` | Chưa chạy |
| INT-017 | Chỉ dùng tài liệu Sẵn sàng (US-013 AC 1) | Negative | Tài liệu Y đang xử lý (job chưa chạy), Z Sẵn sàng; hỏi câu chỉ có trong Y | Không dùng và không trích dẫn Y; INSUFFICIENT nếu Z không có thông tin | – | Chưa chạy |
| INT-018 | Sự kiện analytics đầy đủ (G-07) | Positive | Chạy luồng tải → từ chối → Sẵn sàng → thất bại → hỏi → lỗi → gửi lại → bấm nguồn → xóa → truy cập chéo | Ghi đủ 11 sự kiện EVT-01…EVT-11 với đúng tên và chỉ các thuộc tính trong whitelist | – | Chưa chạy |

#### 6.1.3 System testing (E2E)

| Thuộc tính | Mô tả |
|---|---|
| Nhóm phụ trách | QA |
| Công cụ | Playwright 1.49 (`channel: msedge`), smoke script Python |
| Phạm vi | Luồng nghiệp vụ đầu-cuối qua trình duyệt, đăng nhập OIDC thật (IdP giả lập) |
| Điều kiện vào | Integration test đạt; `run.py --sample` chạy, 4 dịch vụ sẵn sàng |
| Điều kiện ra | 100% E2E P0 đạt; không lỗi Critical/High mở |
| Trọng tâm | Hành trình người dùng, trạng thái giao diện, SSE |

Ưu tiên của E2E lấy theo ưu tiên story mà nó kiểm. Tiêu chí "100% E2E P0 đạt" ở mục 7.0 áp dụng cho các dòng có ưu tiên **P0**.

| Test Case ID | Ưu tiên | Hành trình | Các bước | Kết quả mong đợi | Tự động | Trạng thái |
|---|---|---|---|---|---|---|
| E2E-001 | P0 | Đăng nhập → tải PDF → Sẵn sàng → hỏi → xem nguồn → xóa | 1. Đăng nhập P2; 2. Tải hợp đồng + scan + docx; 3. Chờ trạng thái; 4. Hỏi thanh toán; 5. Hỏi ngoài tài liệu; 6. Bấm nguồn; 7. Esc; 8. Xóa hợp đồng | docx "không phải PDF"; scan Thất bại R-03; trả lời 30 ngày + chip `hop-dong-A.pdf · tr.2`; "Chưa đủ thông tin"; trình xem trang 2, PDF hợp lệ; nguồn chuyển "(đã xóa)" | `demo.spec.ts` | Đạt (tự động) |
| E2E-002 | P0 | Người ngoài nhóm | Đăng nhập tài khoản không thuộc nhóm | Trang "Bạn chưa được cấp quyền" | `demo.spec.ts` | Đạt (tự động) |
| E2E-003 | P0 | Smoke qua proxy | OIDC → tải 3 PDF → READY → 3 câu hỏi | ANSWERED có nguồn / đa tài liệu / INSUFFICIENT | `scripts/smoke.py` | Đạt (thủ công, 26/10) |
| E2E-004 | P0 | Tải nhiều file song song (US-002) | Chọn 10 PDF hợp lệ | Tối đa 3 tải song song, cả 10 vào danh sách | – | Chưa chạy |
| E2E-005 | P0 | Mất mạng khi tải lên (E-04, US-026) | Chặn request PUT bằng `page.route`; bấm Tải lại | "Tải lên thất bại" + Tải lại; không tạo trùng | – | Chưa chạy |
| E2E-006 | P1 | Rate limit câu hỏi (S05) | Gửi 11 câu/phút | Cảnh báo + đếm ngược, giữ nội dung ô hỏi, tự mở khóa | – | Chưa chạy |
| E2E-007 | P0 | Lỗi AI và Gửi lại (S05, US-026/027) | LLM không phản hồi | Thẻ lỗi tại vị trí câu trả lời; Gửi lại thành công | – | Chưa chạy |
| E2E-008 | P0 | Hết phiên (S11, E-17, US-023) | Phiên hết hạn giữa chừng khi đang gõ câu hỏi | Trang S11; sau đăng nhập, câu hỏi đang soạn hiện lại | – | Chưa chạy |
| E2E-009 | P0 | Tải lại trang (E-18, US-006) | Tải lại giữa phiên | Danh sách và hội thoại còn | – | Chưa chạy |
| E2E-010 | P1 | Xử lý lại R-04 (US-009) | Lỗi embedding tạm thời → Thất bại R-04 → Xử lý lại | Nút chỉ có với R-04; trạng thái về Sẵn sàng | – | Chưa chạy |
| E2E-011 | P0 | Vượt hạn mức (S08, US-002) | Chọn 12 file; tài khoản 98/100 | Không file nào tải lên; cảnh báo sắp hết hạn mức | Chụp ảnh hướng dẫn | Đạt (thủ công) |
| E2E-012 | P0 | PDF có một phần là ảnh scan (E-11) | Tải PDF 3 trang: 2 trang chữ, 1 trang ảnh; hỏi về trang chữ, rồi hỏi về trang ảnh | Sẵn sàng; câu về trang chữ có nguồn; câu về trang ảnh → "Chưa đủ thông tin" | – | Chưa chạy |
| E2E-013 | P0 | Trùng tên file (E-12, US-006) | Tải `hop-dong-A.pdf` hai lần ở hai lô | Cả hai được nhận, phân biệt bằng thời điểm tải lên; xóa một bản không ảnh hưởng bản kia | – | Chưa chạy |
| E2E-014 | P0 | 5 câu hỏi liên tiếp (US-014) | Sau câu trả lời đầu, gửi thêm 5 câu | 6 lượt hiển thị đúng thứ tự trong cùng khung, không cần tải lại | – | Chưa chạy |

#### 6.1.4 Acceptance testing

| Thuộc tính | Mô tả |
|---|---|
| Nhóm phụ trách | PO, người dùng nghiệp vụ (P1), QA hỗ trợ |
| Công cụ | Thực hiện thủ công theo kịch bản, ghi biên bản |
| Phạm vi | 7 kịch bản nghiệm thu AC-01…AC-07 (intake §7, BRD MET-006) + AC của 21 story P0 |
| Điều kiện vào | System test đạt; môi trường staging; dữ liệu là tài liệu dự án thật đã được phép dùng |
| Điều kiện ra | 7/7 kịch bản đạt; PO ký biên bản |

| Test Case ID | Kịch bản / Story | Tình huống | Tiêu chí chấp nhận | Kết quả |
|---|---|---|---|---|
| UAT-001 | AC-01 / US-001, US-005 | Tải lên một PDF hợp lệ | Xuất hiện với trạng thái Đang xử lý, có tiến độ, chuyển Sẵn sàng ≤ 3 phút | Chưa chạy (demo: đạt sơ bộ) |
| UAT-002 | AC-02 / US-003 | Tải file .docx và file đuôi .pdf giả | Thông báo nêu tên file và "không phải file PDF hợp lệ", không vào danh sách | Chưa chạy (demo: đạt sơ bộ) |
| UAT-003 | AC-03 / US-012, US-013 | Hỏi câu có đáp án trong tài liệu Sẵn sàng | Câu trả lời dựa trên tài liệu, khớp nội dung, có nguồn | Chưa chạy |
| UAT-004 | AC-04 / US-017 | Hỏi câu cần tổng hợp 2 tài liệu | Nêu thông tin từ cả 2 và trích dẫn cả 2 | Chưa chạy |
| UAT-005 | AC-05 / US-016 | Hỏi nội dung không có trong tài liệu | "Chưa đủ thông tin", không kèm nguồn | Chưa chạy |
| UAT-006 | AC-06 / US-020, US-021, US-022 | Kiểm tra nguồn câu trả lời | Đúng tên tài liệu và số trang; bấm mở đúng trang | Chưa chạy |
| UAT-007 | AC-07 / US-010, US-011 | Xóa tài liệu rồi hỏi lại câu chỉ có trong tài liệu đó | Không còn dùng hoặc trích dẫn tài liệu đã xóa | Chưa chạy |
| UAT-008 | NFR-008 | 5 người dùng lần đầu, không hướng dẫn | ≥ 80% hoàn thành tải → hỏi → xem nguồn trong ≤ 5 phút | Chưa chạy |

#### 6.1.5 Regression testing

| Thuộc tính | Mô tả |
|---|---|
| Nhóm phụ trách | Dev (chạy trên máy), QA (giám sát kết quả CI) |
| Công cụ | pytest, Playwright, CI GitHub Actions |
| Phạm vi | Toàn bộ test tự động; bắt buộc với mọi thay đổi ở `app/` |
| Kích hoạt | Mỗi commit/PR; trước mỗi lần demo hoặc phát hành |
| Cách làm | Chạy lint → unit → integration → build frontend → E2E |
| Tần suất | Mỗi lần build |

| Suite ID | Phạm vi | Số test | Thời gian | Tự động |
|---|---|---|---|---|
| REG-001 | Lint/kiểu/ranh giới: ruff, mypy strict, import-linter, `tsc` | 4 công cụ | ~1 phút | ✓ |
| REG-002 | Unit backend | 12 | ~3 giây | ✓ |
| REG-003 | Integration backend (API + CSDL + worker), gồm 6 trường hợp từ chối file tham số hóa | 37 | ~65 giây | ✓ |
| REG-004 | E2E trình duyệt | 2 | ~20 giây | ✓ (cần `run.py` chạy) |
| REG-005 | Smoke đầu-cuối sau khi triển khai | 1 kịch bản / 3 câu hỏi | ~10 giây | ✓ |
| REG-006 | Chất lượng câu trả lời trên bộ câu hỏi chuẩn | ≥ 100 câu | `[TBD]` | Chưa có (DEP-005) |

#### 6.1.6 Performance testing

| Thuộc tính | Mô tả |
|---|---|
| Nhóm phụ trách | Tech Lead, QA |
| Công cụ | k6 (API), Playwright trace / Lighthouse (giao diện), sự kiện EVT-03/EVT-07 để đo thời gian |
| Loại | Load, endurance ngắn, đo đơn lẻ |
| Điều kiện vào | Staging với PostgreSQL thật (`DB_MODE=pool`), LLM và embedding thật, 100 tài liệu/người dùng |
| Điều kiện ra | NFR-001, NFR-002, NFR-007 đạt |
| Chỉ số | p50/p90 thời gian trả lời, thời gian ingest, tỷ lệ lỗi, CPU/RAM worker |

| Scenario ID | Loại | Người dùng | Thời lượng | Chỉ tiêu | SLA |
|---|---|---|---|---|---|
| PERF-001 | Load – hỏi đáp | 1 | 50 câu từ bộ câu hỏi chuẩn, tài khoản có **100 tài liệu Sẵn sàng** (điều kiện đo của NFR-001); thời gian tính từ lúc gửi tới khi nhận câu trả lời hoàn chỉnh | p90 ≤ 15 s, p50 ≤ 8 s (NFR-001) | NFR-001 |
| PERF-002 | Load – hỏi đồng thời | 20 | 15 phút | NFR-001 giữ nguyên, lỗi < 1% (NFR-007) | NFR-007 |
| PERF-003 | Xử lý file biên | 1 | 1 file 20 MB / 300 trang | ≤ 3 phút (NFR-002) | NFR-002 |
| PERF-004 | Xử lý hàng loạt | 5 | 5 × 10 file | Không job kẹt; hàng đợi giảm dần | – |
| PERF-005 | Endurance ngắn | 10 | 2 giờ | Bộ nhớ worker tăng < 10%, không rò kết nối | – |
| PERF-006 | Giao diện | – | – | LCP < 2,5 s trên máy văn phòng; danh sách 100 tài liệu cuộn mượt | – |

> **Ghi chú:** môi trường demo hiện dùng PGlite (một kết nối) và bộ trả lời trích xuất, nên **không đại diện cho hiệu năng thật**. Trên môi trường này, smoke test đo được ~2 giây cho mỗi câu trả lời và vài giây cho mỗi tài liệu mẫu; kết quả chỉ để tham khảo, không dùng cho launch gate G-03.

#### 6.1.7 Security testing

| Thuộc tính | Mô tả |
|---|---|
| Nhóm phụ trách | IT/Security, QA |
| Công cụ | Test tự động pytest (phân quyền, CSRF, header); OWASP ZAP (DAST); `pip-audit`, `npm audit` (phụ thuộc); review mã |
| Loại | SAST, DAST, kiểm thử phân quyền, review cấu hình |
| Điều kiện vào | Bản build trên staging có HTTPS |
| Điều kiện ra | Không lỗ hổng Critical/High; 0 truy cập chéo (MET-007) |

| Test Case ID | Hạng mục | Mô tả | Kết quả mong đợi | Test tự động | Trạng thái |
|---|---|---|---|---|---|
| SEC-001 | Xác thực | Gọi API không có phiên; đăng xuất rồi gọi lại | 401 `unauthenticated` | `test_login_me_logout`, `test_unauthenticated_and_csrf` | Đạt (tự động) |
| SEC-002 | Nhóm IdP | Người không thuộc `aichat-users`/`aichat-admins` | Chuyển `/access-denied`, ghi audit `login_denied` | `test_outsider_denied_and_audited` | Đạt (tự động) |
| SEC-003 | Open redirect | `return_to=https://evil.example` | Chuyển về `/` | `test_open_redirect_blocked` | Đạt (tự động) |
| SEC-004 | CSRF | POST/PUT/DELETE không có `X-CSRF-Token` | 403 `csrf_invalid` | `test_unauthenticated_and_csrf`, `test_login_me_logout` | Đạt (tự động) |
| SEC-005 | IDOR / cách ly (NFR-010) | P2 liệt kê, mở file, xóa, hỏi trên hội thoại của P1 | Không thấy; 404; ghi `access_denied` | `test_isolation_between_users` | Đạt (tự động) |
| SEC-006 | RLS mức CSDL | Vai trò `app_api` thiếu/sai `app.workspace_id` | 0 hàng | `test_schema_invariants_and_rls`, `test_set_local_does_not_leak` | Đạt (tự động) |
| SEC-007 | Dữ liệu gửi tới AI (NFR-011) | Prompt chỉ chứa đoạn được chọn; không chứa tên file, ID tài liệu | Đúng | `test_upload_process_ask` | Đạt (tự động) |
| SEC-008 | Không lộ nội dung (BRL-07) | Analytics, audit, log không chứa câu hỏi, tên file, email | Không có | `test_no_content_in_analytics`, `test_redact_forbidden` | Đạt (tự động) |
| SEC-009 | Kiểm tra file tải lên | File giả PDF, PDF hỏng, file quá lớn; kiểm tra chạy trong sandbox có giới hạn thời gian/bộ nhớ | Từ chối; không làm sập API | `test_rejections`, `test_too_large` | Đạt (tự động) |
| SEC-010 | Prompt injection qua tài liệu | Tài liệu chứa "bỏ qua hướng dẫn…", thẻ `</source>` | Không phá cấu trúc prompt; mã nguồn lạ bị loại | `test_prompt_escapes_sources`, `test_invalid_citation_repaired_or_insufficient` | Đạt một phần (tự động) |
| SEC-011 | Header bảo mật, cookie | CSP, `nosniff`, `X-Frame-Options` (SAMEORIGIN cho file PDF), `Cache-Control: no-store`; cookie HttpOnly/SameSite/Secure | Đúng cấu hình | Một phần (`test_view_file`) | Đạt một phần |
| SEC-012 | Mã hóa truyền/lưu (NFR-009, NFR-022) | TLS ≥ 1.2; mã hóa ổ đĩa/blob | Đạt chuẩn IT/Security | – | Bị chặn (chưa có staging) |
| SEC-013 | Rate limit (ALG-09) | Vượt 10 câu/phút, 30 file/giờ | 429 + Retry-After | `test_rate_limit_questions` | Đạt (tự động, phần câu hỏi) |
| SEC-014 | Quét phụ thuộc | `pip-audit`, `npm audit` | Không lỗ hổng High/Critical | – | Chưa chạy |
| SEC-015 | DAST | OWASP ZAP baseline trên staging | Không cảnh báo High | – | Bị chặn (chưa có staging) |

#### 6.1.8 Accessibility testing

| Thuộc tính | Mô tả |
|---|---|
| Nhóm phụ trách | QA, Designer |
| Công cụ | `@axe-core/playwright`, NVDA + Edge, kiểm tra bàn phím thủ công |
| Chuẩn | WCAG 2.1 AA |
| Điều kiện vào | Giao diện ổn định (S01–S11 đã triển khai) |
| Điều kiện ra | Không lỗi axe mức serious/critical; luồng chính dùng được chỉ bằng bàn phím |

| Test Case ID | Hạng mục | Mô tả | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|
| ACC-001 | Bàn phím | Tab qua toàn bộ luồng: chọn file, gửi câu hỏi (Enter, Shift + Enter), mở nguồn, đóng trình xem (Esc), xóa | Làm được không cần chuột; có liên kết "Bỏ qua tới nội dung chính" | Chưa chạy |
| ACC-002 | Trình đọc màn hình | Trạng thái tài liệu, câu trả lời mới, lỗi được đọc (`aria-live`, `role=alert`, `role=status`) | Được thông báo | Chưa chạy |
| ACC-003 | Tương phản | Màu chữ/nền ở cả giao diện sáng và tối | ≥ 4,5:1 cho chữ thường | Chưa chạy |
| ACC-004 | ARIA | Nhãn nút biểu tượng (xóa, đóng), `role=progressbar`, `aria-modal`, `aria-busy` | Đúng | Đạt một phần (E2E dùng nhãn ARIA để định vị) |
| ACC-005 | Quản lý focus | Dialog xóa: focus mặc định ở Hủy; đóng trình xem: focus về nút nguồn đã bấm | Đúng | Chưa chạy |
| ACC-006 | Không chỉ dựa vào màu | Trạng thái = biểu tượng + chữ (WCAG 1.4.1) | Đúng | Đạt (thủ công, xem ảnh hướng dẫn) |
| ACC-007 | Giảm chuyển động | `prefers-reduced-motion` tắt hiệu ứng xoay/ba chấm | Tắt | Chưa chạy |

#### 6.1.9 UI/UX testing

| Thuộc tính | Mô tả |
|---|---|
| Nhóm phụ trách | QA, Designer |
| Công cụ | So sánh trực quan với `html_design`, Playwright screenshot, kiểm tra thủ công |
| Phạm vi | S01–S11 trên Edge và Chrome, 1280–1920 px, giao diện sáng/tối |
| Điều kiện vào | Giao diện đã triển khai, thiết kế đã chốt |
| Điều kiện ra | Mọi trạng thái thiết kế có mặt; Designer chấp thuận |

| Test Case ID | Hạng mục | Mô tả | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|
| UI-001 | So sánh thiết kế | S01–S11 so với `html_design` | Bố cục, chữ, trạng thái khớp | Đạt sơ bộ (thủ công – ảnh trong `guide/images`) |
| UI-002 | Độ rộng màn hình | 1280, 1440, 1920 px | Không cuộn ngang; hai khu vực luôn hiển thị | Chưa chạy |
| UI-003 | Trạng thái thành phần | Nút: thường/hover/disabled/đang gửi; ô hỏi khóa | Đủ trạng thái | Đạt một phần |
| UI-004 | Trạng thái lỗi/trống | E-01, E-02, E-03, thẻ lỗi, "Không nhận", "Thất bại" | Đủ | Đạt một phần (E-03 chưa kiểm) |
| UI-005 | Trạng thái chờ | Thanh tiến độ, Đang xử lý, ba chấm "đang soạn" | Hiển thị | Đạt (E2E + ảnh) |
| UI-006 | Thông báo | Toast Sẵn sàng/Thất bại tự ẩn ≤ 5 s, không che ô hỏi | Đúng | Đạt sơ bộ (thủ công) |
| UI-007 | Bộ đếm ký tự | 0/2.000 → cảnh báo khi chạm 2.000; không nhập quá (E-15) | Đúng | Đạt một phần (E2E kiểm `0/2.000`) |
| UI-008 | Giao diện tối | Theo hệ điều hành | Đủ tương phản, không lỗi màu | Chưa chạy |
| UI-009 | Tương thích trình duyệt (NFR-017) | 2 phiên bản mới nhất Chrome và Edge | Hoạt động như nhau | Đạt một phần (Edge) |
| UI-010 | Ngôn ngữ (NFR-016) | Giao diện tiếng Việt; hỏi tiếng Anh → trả lời tiếng Anh | Đúng | Chưa chạy |
| UI-011 | Nguồn không có số trang (US-021 AC 2, BRL-05) | Câu trả lời có trích dẫn với `page_number = null` (giả lập qua API) | Chip chỉ hiện tên tài liệu, không hiện "tr." | Chưa chạy |

#### 6.1.10 API testing

| Thuộc tính | Mô tả |
|---|---|
| Nhóm phụ trách | Dev, QA |
| Công cụ | pytest + httpx; đối chiếu `openapi.yaml` |
| Phạm vi | 15 thao tác công khai |
| Điều kiện vào | API chạy được; `openapi.yaml` đã chốt |
| Điều kiện ra | Mọi thao tác và mọi mã lỗi đã khai báo có test; lỗi theo RFC 9457 (`application/problem+json`, có `code`, `request_id`) |

| Test Case ID | Endpoint | Method | Loại | Kiểm tra | Test tự động | Trạng thái |
|---|---|---|---|---|---|---|
| API-001 | `/auth/login`, `/auth/callback` | GET | Functional | 302 tới IdP; callback đặt cookie `sid` (HttpOnly) và `csrf_token`; đăng nhập lại không tạo workspace thứ hai | `test_login_me_logout` | Đạt |
| API-002 | `/auth/callback` | GET | Negative | Người ngoài nhóm → `/access-denied`; `return_to` ngoài origin → `/` | `test_outsider_denied_and_audited`, `test_open_redirect_blocked` | Đạt |
| API-003 | `/auth/callback` | GET | Negative | `state` sai/hết hạn → `/login-error?ref=` | – | Chưa chạy |
| API-004 | `/auth/logout` | POST | Functional/Negative | 204 khi có CSRF; 403 khi thiếu | `test_login_me_logout` | Đạt |
| API-005 | `/me` | GET | Functional | email, hạn mức, `limits` | `test_login_me_logout` | Đạt |
| API-006 | `/upload-batches` | POST | Negative | 11 file → 422 `too_many_files` | `test_batch_limits` | Đạt |
| API-007 | `/upload-batches` | POST | Boundary | Còn 1 chỗ, xin 2 → 422 `quota_exceeded`, `remaining=1` | `test_batch_limits` | Đạt |
| API-008 | `…/files/{client_file_id}` | PUT | Functional | 201 `Document` PROCESSING, `page_count` đúng | `test_upload_process_ask` | Đạt |
| API-009 | `…/files/{client_file_id}` | PUT | Idempotent | Gửi lại cùng `client_file_id` → 200 cùng `id`; lô hết chỗ → 409 `batch_full` | `test_upload_idempotent_and_batch_slots` | Đạt |
| API-010 | `…/files/{client_file_id}` | PUT | Negative | scan (nhận, R-03 khi xử lý), quá trang, mật khẩu, hỏng, docx, PDF giả → 422 với `code` đúng, kiểu `application/problem+json` | `test_rejections` (6 trường hợp) | Đạt |
| API-011 | `…/files/{client_file_id}` | PUT | Boundary | Quá 2 MB (cấu hình test) → 422 `too_large`; PDF khóa in (mật khẩu rỗng) được nhận | `test_too_large`, `test_encrypted_without_user_password_is_accepted` | Đạt |
| API-012 | `…/files/{client_file_id}` | PUT | Negative | Lô hết hạn → 404 `batch_expired`; body quá lớn → 413; sandbox bận → 503 | – | Chưa chạy |
| API-013 | `…/files/{client_file_id}` | PUT | Negative | Vượt 30 file/giờ → 429 | – | Chưa chạy |
| API-014 | `/documents` | GET | Functional | `items`, `documents_used`, `documents_limit` | `test_upload_process_ask` | Đạt |
| API-015 | `/documents/{id}` | DELETE | Functional/Negative | 204; xóa lần 2 → 404 | `test_delete_purge_and_answers_exclude` | Đạt |
| API-016 | `/documents/{id}/reprocess` | POST | Functional/Negative | R-04 → 202 PROCESSING; READY → 409 `not_retryable` | `test_reprocess_only_r04` | Đạt |
| API-017 | `/documents/{id}/file` | GET | Functional | 200 PDF, `Content-Disposition` có tên file, `X-Frame-Options: SAMEORIGIN` | `test_view_file` | Đạt |
| API-018 | `/documents/{id}/file` | GET | Negative | Đã xóa → 410 `deleted`; người khác → 404 | `test_delete_purge_and_answers_exclude`, `test_isolation_between_users` | Đạt |
| API-019 | `/conversations/current` | GET | Functional | Cùng hội thoại sau khi tải lại; lượt hỏi có trích dẫn | `test_upload_process_ask` | Đạt |
| API-020 | `/conversations/{id}/messages` | POST | Functional | 200 ANSWERED, `answer` dùng [n], `citations` có tên + trang | `test_upload_process_ask` | Đạt |
| API-021 | `/conversations/{id}/messages` | POST | Negative | Chưa có tài liệu Sẵn sàng → 409 `no_ready_documents` | `test_upload_process_ask` | Đạt |
| API-022 | `/conversations/{id}/messages` | POST | Idempotent | Cùng `client_request_id` → cùng kết quả, LLM gọi 1 lần; khác câu hỏi → 422 `idempotency_mismatch` | `test_idempotent_ask` | Đạt |
| API-023 | `/conversations/{id}/messages` | POST | Negative | Câu trống → 422 `empty_question`; 2.001 ký tự → 422 `question_too_long`; hội thoại lạ → 404 | `test_question_validation` | Đạt |
| API-024 | `/conversations/{id}/messages` | POST | Negative | LLM lỗi → 503 `ai_unavailable` + Retry-After; quá ngân sách → 504 `ai_timeout` | `test_ai_failure_then_resend`, `test_ai_timeout` | Đạt |
| API-025 | `/conversations/{id}/messages` | POST | Recovery | Gửi lại sau FAILED → ANSWERED, `attempt=2`, EVT-10 | `test_ai_failure_then_resend` | Đạt |
| API-026 | `/conversations/{id}/messages` | POST | Negative | Vượt 10 câu/phút → 429 `rate_limited` + Retry-After | `test_rate_limit_questions` | Đạt |
| API-027 | `/conversations/{id}/messages` | POST | Negative | Request trùng đang chạy → 409 `request_in_progress` | – | Chưa chạy |
| API-028 | `/events` | GET | Functional | SSE `document.status_changed`, `quota.changed`, `session.expiring`, ping 25 s | – (độ phủ mã 39%) | Chưa chạy (tự động) |
| API-029 | `/healthz`, `/readyz` | GET | Functional | 200; `readyz` 503 khi mất CSDL | – (thủ công 200) | Đạt một phần |
| API-030 | Hợp đồng | – | Contract | Mọi thao tác trong `openapi.yaml` tồn tại | `test_openapi_matches_contract` | Đạt |
| API-031 | `/documents/{id}/file` | GET | Functional | Nguồn không có số trang (US-022 AC 2): mở không có `page` → SPA mở trang 1 | – | Chưa chạy |

#### 6.1.11 Kiểm thử chất lượng câu trả lời (bổ sung – đặc thù hệ thống RAG)

| Thuộc tính | Mô tả |
|---|---|
| Nhóm phụ trách | QA, người dùng nghiệp vụ (chấm điểm), Tech Lead |
| Công cụ | Bộ câu hỏi chuẩn DEP-005; script chạy hàng loạt (T06-03, DE-22); bảng chấm điểm |
| Điều kiện vào | Bộ câu hỏi + đáp án chuẩn + tài liệu dự án thật đã được PO duyệt; LLM và embedding sẽ dùng cho production |
| Điều kiện ra | Đạt G-02 |

| Test Case ID | Chỉ số | Cách đo | Ngưỡng | Trạng thái |
|---|---|---|---|---|
| QLT-001 | Độ chính xác câu trả lời (NFR-003, MET-002) | Người dùng nghiệp vụ chấm đúng/sai ≥ 50 câu trong tài liệu | ≥ 80% | Bị chặn – DEP-005 |
| QLT-002 | Đúng tên tài liệu nguồn (NFR-004) | Đối chiếu nguồn với PDF gốc | ≥ 90% | Bị chặn – DEP-005 |
| QLT-003 | Đúng số trang (NFR-018) | Mở PDF gốc tại trang được trích dẫn | ≥ 85% | Bị chặn – DEP-005 |
| QLT-004 | Từ chối đúng (NFR-005) | ≥ 20 câu ngoài tài liệu | ≥ 90% "Chưa đủ thông tin" | Bị chặn – DEP-005 |
| QLT-005 | Trả lời đầy đủ đa tài liệu (MET-003) / tiếp nối (US-015) | ≥ 20 câu đa tài liệu; 10 cặp tiếp nối | ≥ 80% / ≥ 8/10 | Bị chặn – DEP-005, OQ-012 |

### 6.2 Chiến lược thực thi

**Thứ tự thực thi trong một chu kỳ** (mỗi bước chỉ chạy khi bước trước đạt):

```text
REG-001 lint/kiểu ─► REG-002 unit ─► REG-003 integration (PGlite) ─► CI: integration trên PostgreSQL thật
      ─► build frontend ─► run.py ─► REG-005 smoke ─► REG-004 E2E ─► E2E thủ công / UI / ACC
      ─► (staging) PERF, SEC DAST, QLT ─► UAT
```

**Chu kỳ kiểm thử**

| Chu kỳ | Mục tiêu | Môi trường | Bao gồm |
|---|---|---|---|
| C1 – Demo (đã thực hiện 26/10/2026) | Xác nhận lát 1 và các lát đã làm | Máy dev + PGlite + LLM trích xuất | REG-001…REG-005 |
| C2 – Hoàn thiện chức năng | Đóng các test case "Chưa chạy" mức chức năng | Máy dev + CI PostgreSQL thật | E2E-004…E2E-010, API-003/012/013/027/028, UT-013…UT-015, ACC, UI |
| C3 – Staging | Phi chức năng và chất lượng câu trả lời | Staging (HTTPS, PostgreSQL, LLM + embedding thật) | PERF, SEC-012/014/015, QLT, INT-015 |
| C4 – Nghiệm thu | Ký nghiệm thu | Staging | UAT-001…UAT-008, kiểm thử hồi quy toàn bộ |

**Quản lý lỗi**

| Mức | Định nghĩa | Ví dụ | Thời hạn xử lý `[Đề xuất QA]` |
|---|---|---|---|
| Critical | Lộ dữ liệu, mất dữ liệu, hệ thống không dùng được | Truy cập chéo tài liệu; CSDL ngừng hoạt động | Chặn phát hành; sửa ngay |
| High | Một AC P0 không đạt, không có cách tránh | Tài liệu đã xóa vẫn được trích dẫn | Sửa trong chu kỳ |
| Medium | AC P1 không đạt, hoặc có cách tránh | Thông báo thiếu số liệu | Trước UAT |
| Low | Thẩm mỹ, chữ | Lệch khoảng cách | Theo kế hoạch |

Lỗi được ghi với ID `DEF-T-xxx`, gồm các mục: bước tái hiện, kết quả mong đợi, kết quả thực tế, log/ảnh, môi trường, mức độ, và yêu cầu bị ảnh hưởng.

### 6.3 Phân chia tự động – thủ công

**Nguyên tắc:**
- Mọi test có kết quả xác định được bằng máy đều phải tự động hóa và chạy trong CI ở mỗi commit/PR.
- Test cần môi trường thật (staging, LLM thật, tải lớn) vẫn tự động hóa, nhưng chạy theo chu kỳ ngoài CI.
- Chỉ những việc cần đánh giá của con người mới làm thủ công: so sánh trực quan, trình đọc màn hình, chấm chất lượng câu trả lời, nghiệm thu.

| Loại | Tổng | Tự động – trong CI (mỗi commit) | Tự động – ngoài CI (theo chu kỳ) | Thủ công |
|---|---|---|---|---|
| UT | 15 | 15 | – | – |
| INT | 18 | 17 | 1 (INT-015 adapter thật, staging) | – |
| API | 31 | 31 | – | – |
| E2E | 14 | 13 (job E2E khởi động `run.py`) | 1 (E2E-003 smoke sau mỗi lần triển khai) | – |
| SEC | 15 | 13 (gồm SEC-014 `pip-audit`/`npm audit`) | 1 (SEC-015 ZAP trên staging) | 1 (SEC-012 review cấu hình TLS/mã hóa) |
| ACC | 7 | 3 (ACC-003/004/007 bằng axe) | – | 4 (ACC-001/002/005/006: bàn phím, NVDA) |
| UI | 11 | 7 (UI-002/003/005/007/009/010/011) | – | 4 (UI-001/004/006/008: so sánh trực quan) |
| PERF | 6 | – | 6 (k6 trên staging) | – |
| QLT | 5 | – | 5 (script chạy bộ câu hỏi; **người dùng nghiệp vụ chấm điểm**) | – |
| UAT | 8 | – | – | 8 |
| **Tổng** | **130** | **99 (76%)** | **14 (11%)** | **17 (13%)** |

Hiện trạng C1: đã tự động và đạt 51 test (49 pytest + 2 Playwright); CI chưa chạy (TT-02).

**Kiểm thử khám phá:** 3 phiên, mỗi phiên 90 phút, thực hiện ở chu kỳ C2 và lặp lại ở C3 với tài liệu thật. Người
thực hiện ghi ghi chú phiên (mục tiêu, việc đã thử, lỗi phát hiện), và mỗi lỗi tìm được phải kèm một test tự
động để hồi quy.

| Phiên | Mục tiêu khám phá |
|---|---|
| EX-01 Tài liệu bất thường | PDF có bảng/nhiều cột, file gần 20 MB/300 trang, tên file có dấu, ký tự đặc biệt hoặc rất dài, PDF tạo từ máy quét có lớp OCR |
| EX-02 Câu hỏi khó | Câu mơ hồ, so sánh, phủ định, lẫn Việt–Anh, câu chứa lệnh kiểu prompt injection, câu hỏi về bảng số liệu |
| EX-03 Phiên và đồng thời | Hai tab cùng lúc (xóa ở tab này, hỏi ở tab kia), mạng chập chờn, hết phiên giữa lúc tải lên, tải lại trang khi đang chờ câu trả lời |

**Dữ liệu kiểm thử**

- Chỉ dùng PDF sinh tự động (`pdfgen.py`) cho test tự động.
- PDF thật của dự án chỉ dùng ở chu kỳ C3/C4, phải được PO cho phép, không đưa vào repo.
- Môi trường test không chứa dữ liệu thật khác ngoài các file đó.

## 7.0 Tiêu chí đạt/không đạt (IEEE 829 §5.7)

| Mức | Đạt khi | Không đạt khi |
|---|---|---|
| Test case | Kết quả thực tế khớp kết quả mong đợi ở mọi bước | Có bất kỳ sai khác nào; hoặc test không ổn định (lúc đạt lúc không qua 3 lần chạy) |
| Unit / Integration | 100% đạt; độ phủ backend ≥ 80% | Có test hỏng; độ phủ giảm so với chu kỳ trước |
| Hệ thống | 100% E2E có ưu tiên P0 (mục 6.1.3) đạt; 0 lỗi Critical/High mở; lỗi Medium mở ≤ 3 và mỗi lỗi đã có PO chấp thuận `[Đề xuất QA]` | Có E2E P0 hỏng |
| Test case bị chặn | Ở launch gate không được còn test case P0 "Bị chặn". Test case P1/P2 bị chặn được PO chấp thuận bằng văn bản | Còn test case P0 bị chặn |
| Bảo mật | 0 Critical/High; SEC-005/006 đạt | Có truy cập chéo, hoặc lỗ hổng High chưa xử lý |
| Hiệu năng | NFR-001, NFR-002, NFR-007 đạt trên staging | Vượt ngưỡng |
| Chất lượng câu trả lời | QLT-001…QLT-004 đạt ngưỡng | Dưới ngưỡng |
| Phát hành (launch gate) | G-01…G-09 (PRD 5.1) đều đạt và có người xác nhận | Bất kỳ gate nào chưa đạt |

## 8.0 Tiêu chí tạm dừng và tiếp tục (IEEE 829 §5.8)

| Tạm dừng khi | Tiếp tục khi |
|---|---|
| Smoke test (REG-005) hỏng: không đăng nhập, không tải lên, hoặc không hỏi được | Bản sửa (commit mới) được triển khai; smoke đạt |
| Phát hiện lỗi Critical về cách ly dữ liệu | Đã sửa, có test hồi quy SEC-005/006 mới, IT/Security xác nhận |
| Môi trường không ổn định: CSDL ngừng (ví dụ DEF-T-004), dịch vụ không khởi động, > 20% test lỗi vì môi trường | Đã tìm ra nguyên nhân và có bản sửa. Môi trường được **khởi tạo lại** theo các bước dưới đây, rồi chạy lại smoke đạt |
| Thay đổi yêu cầu lớn: OQ đóng làm đổi AC | Test case đã được cập nhật và review |
| Chất lượng câu trả lời (QLT) giảm > 10 điểm phần trăm sau khi đổi mô hình hoặc prompt | Đã phân tích nguyên nhân; chạy lại toàn bộ bộ câu hỏi |

**Khởi tạo lại môi trường trước khi tiếp tục:**

- **ENV-DEV:**
  1. Dừng `run.py`.
  2. Xóa `app/.data/` (CSDL, file đã tải lên, khóa IdP).
  3. Chạy `run.py --sample`.
  4. Chạy smoke test.
- **ENV-TEST:** mỗi lần chạy pytest tự tạo CSDL mới trong bộ nhớ, nên không cần thao tác gì.
- **ENV-STAGING:**
  1. Khôi phục CSDL và object storage từ bản chụp sạch.
  2. Triển khai lại đúng tag image đang kiểm thử.
  3. Chạy smoke test.

Sau khi khởi tạo lại, chạy lại **toàn bộ** test của chu kỳ đang dở, không chỉ chạy lại các test đã lỗi.

## 9.0 Sản phẩm bàn giao (IEEE 829 §5.9)

| Sản phẩm | Mô tả | Thời điểm | Trạng thái |
|---|---|---|---|
| Master Test Plan | Tài liệu này | Trước C2 | Draft v0.1 |
| Test case | Phần 6.1 + Phụ lục A; **chi tiết từng test case (130 file)** tại [test_cases/](test_cases/README.md), sinh bằng `_build_test_cases.py` | Cùng MTP | Draft |
| Bằng chứng thực thi | Mỗi test case: `test_reports/<tên test case>/` gồm `report.md`, `result.json`, ảnh chụp mỗi bước, video toàn bộ quá trình, log. Công cụ: `app/frontend/evidence/` | Mỗi lần chạy | 3 test case mẫu đã có (E2E-002, API-023, UT-001) |
| Test script tự động | `app/backend/tests/`, `app/frontend/e2e/`, `scripts/smoke.py` | Liên tục | 49 + 2 + 1 |
| Dữ liệu test | `pdfgen.py`, `seed_dev.sql`; bộ câu hỏi chuẩn | C2 / C3 | Bộ câu hỏi chưa có |
| Nhật ký thực thi | Kết quả pytest, Playwright, CI theo chu kỳ | Mỗi chu kỳ | C1 – Phụ lục B |
| Báo cáo lỗi | Danh sách DEF-T-xxx | Liên tục | Phụ lục B (PB.3) |
| Báo cáo độ phủ | coverage.py (backend) | Mỗi chu kỳ | C1: 78% |
| Báo cáo tổng kết (Test Summary Report) | Kết quả so với tiêu chí mục 7 | Cuối C4 | Chưa có |
| Biên bản nghiệm thu | UAT-001…UAT-008, chữ ký PO | Cuối C4 | Chưa có |

## 10.0 Công việc kiểm thử (IEEE 829 §5.10)

| # | Công việc | Phụ thuộc | Người thực hiện | Ước lượng `[Đề xuất QA]` |
|---|---|---|---|---|
| TT-01 | Review và phê duyệt MTP (dùng `Test_Plan_IEEE_829_Checklist.xlsx`) | – | QA Lead, PO | 0,5 ngày |
| TT-02 | Chạy CI trên PostgreSQL thật (chép `ci.yml` ra gốc repo) | T00-07 | Dev | 0,5 ngày |
| TT-03 | Viết unit test còn thiếu UT-013…UT-015 | – | Dev | 1 ngày |
| TT-04 | Viết API test còn thiếu API-003/012/013/027/028 | – | Dev/QA | 1 ngày |
| TT-05 | Viết E2E-004…E2E-010 | TT-02 | QA | 2 ngày |
| TT-06 | Kiểm thử trợ năng ACC-001…ACC-007 (axe + NVDA) | – | QA | 1 ngày |
| TT-07 | Kiểm thử UI/tương thích UI-002…UI-010 | – | QA, Designer | 1 ngày |
| TT-08 | Soạn bộ câu hỏi chuẩn + đáp án (DEP-005) | Tài liệu dự án thật | PO, người dùng nghiệp vụ, QA | 3 ngày |
| TT-09 | Script đánh giá chất lượng câu trả lời (T06-03) | TT-08 | Dev | 1 ngày |
| TT-10 | Dựng staging (T10-05) | Hạ tầng | Dev/DevOps | 2 ngày |
| TT-11 | PERF-001…PERF-006 (T10-06) | TT-10 | Tech Lead, QA | 2 ngày |
| TT-12 | SEC-012/014/015 | TT-10 | IT/Security | 2 ngày |
| TT-13 | QLT-001…QLT-005 | TT-08, TT-09, TT-10 | QA, người dùng nghiệp vụ | 2 ngày |
| TT-14 | UAT + usability (UAT-001…UAT-008) | TT-11…TT-13 | PO, người dùng | 2 ngày |
| TT-15 | Báo cáo tổng kết, xác nhận launch gate | TT-14 | QA Lead | 0,5 ngày |
| TT-16 | Commit các bản sửa của C1, gắn tag build `test-C2-…` (mục 3.1) | – | Dev | 0,1 ngày |
| TT-17 | Viết test tự động cho các test case thêm ở v0.2 (E2E-012…014, INT-017, INT-018, UI-011, API-031) | TT-05 | QA, Dev | 1,5 ngày |
| TT-18 | Kiểm thử lại và đóng lỗi (DEF-T-001…003 sau khi sửa hoặc khi PO quyết định); chạy lại bộ hồi quy | Bản sửa | QA | 0,5 ngày mỗi chu kỳ |
| TT-19 | 3 phiên kiểm thử khám phá EX-01…EX-03 (mục 6.3) | TT-05 | QA | 1 ngày |

## 11.0 Nhu cầu môi trường (IEEE 829 §5.11)

| Môi trường | Thành phần | Mục đích | Hiện trạng |
|---|---|---|---|
| ENV-DEV (máy dev) | Windows 10/11, Python ≥ 3.12 (đã kiểm với 3.14), Node.js ≥ 20, Edge; `run.py`: PGlite 17.5 + pgvector 0.8 (cổng 54329), IdP giả lập (8090), API + worker (8000), Vite (8080); LLM trích xuất, embedding hashing | Unit, integration, E2E, demo | **Sẵn sàng** |
| ENV-TEST (trong test) | PGlite trong bộ nhớ, cổng ngẫu nhiên; FakeIdp, FakeLlm, MemoryBlobStore | Test tự động cô lập | **Sẵn sàng** |
| ENV-CI | GitHub Actions Ubuntu, `pgvector/pgvector:pg17`, Python 3.12, Node 22, font DejaVu | Hồi quy trên PostgreSQL thật | Đã viết, **chưa chạy** |
| ENV-STAGING | HTTPS, PostgreSQL 16+ (`DB_MODE=pool`), object storage S3, IdP thật của công ty (nhóm `aichat-users`), LLM được IT/Security duyệt, embedding bge-m3 | PERF, SEC, QLT, UAT | **Chưa có** (T10-05) |

**Tài nguyên ENV-STAGING:** để kết quả PERF có giá trị cho G-03, staging phải có cùng cấu hình với production theo
SAD 9.2:

| Thành phần | Cấu hình |
|---|---|
| api | 2 bản × 1 vCPU / 1 GB |
| worker | 1 bản × 2 vCPU / 4 GB |
| embedding bge-m3 | 2 bản × 4 vCPU / 8 GB, hoặc 1 GPU T4/L4 nếu SPIKE-02 yêu cầu |
| PostgreSQL | 2 vCPU / 8 GB, SSD 100 GB |
| object storage | ~10 GB |

Ngoài ra cần dữ liệu tải: 20 tài khoản thử, mỗi tài khoản 100 tài liệu (NFR-001, NFR-007). Nếu staging nhỏ hơn
cấu hình trên, kết quả PERF chỉ dùng để tham khảo và phải ghi rõ trong báo cáo.

**Dữ liệu giả lập:**
- FakeIdp, FakeLlm (theo kịch bản: lỗi, chậm, mã nguồn lạ), HashingEmbedding (`fail_times`) và MemoryBlobStore (`fail`) dùng cho mọi test tự động.
- Không dùng LLM thật trong CI, để kết quả ổn định và không tốn chi phí.

| Công cụ | Phiên bản | Dùng cho |
|---|---|---|
| pytest / pytest-asyncio / hypothesis | 9.1 / 1.4 / 6.170 | Unit, integration, property |
| coverage.py | 7.10 | Độ phủ mã |
| ruff / mypy / import-linter | 0.17 / 2.4 strict / 2.15 | Phân tích tĩnh |
| Playwright | 1.49 (Edge) | E2E, ảnh chụp |
| k6 | Bản ổn định mới nhất tại thời điểm C3 | Load test |
| OWASP ZAP, pip-audit, npm audit | Bản ổn định mới nhất tại thời điểm chạy | Bảo mật |
| axe-core (`@axe-core/playwright`), NVDA | Bản ổn định mới nhất tại thời điểm C2 | Trợ năng |

Các công cụ chưa có trong repo sẽ được **ghim phiên bản** khi thêm vào (`requirements.txt` hoặc `package.json`).
Phiên bản đã dùng được ghi vào nhật ký thực thi của từng chu kỳ để kết quả tái hiện được.

## 12.0 Trách nhiệm (IEEE 829 §5.12)

| Vai trò | Trách nhiệm |
|---|---|
| QA Lead | Sở hữu MTP; điều phối chu kỳ; quyết định tạm dừng/tiếp tục; báo cáo tổng kết; xác nhận G-01, G-06 |
| QA Engineer | Thiết kế và thực thi test case hệ thống, UI, trợ năng; ghi lỗi; duy trì E2E |
| Developer | Unit/integration test; sửa lỗi; giữ bộ hồi quy xanh; CI |
| Tech Lead | Môi trường staging; hiệu năng (G-03); theo dõi sự kiện (G-07); quyết định kỹ thuật khi PGlite và PostgreSQL khác nhau |
| Product Owner | Chốt OQ; cung cấp tài liệu dự án và bộ câu hỏi chuẩn (DEP-005); nghiệm thu (G-01, G-08); phê duyệt MTP |
| Người dùng nghiệp vụ (P1) | Chấm chất lượng câu trả lời (G-02); tham gia usability (G-05) và UAT |
| Designer | Xác nhận UI so với thiết kế; khả dụng (G-05) |
| IT/Security | Kiểm thử bảo mật, phê duyệt nhà cung cấp AI, xác nhận NFR-009…013/022/023 (G-04) |

**Phân công theo việc**

| Việc | Viết / thực hiện | Quản lý | Review kết quả |
|---|---|---|---|
| Unit, integration, API test | Developer | Developer | QA Engineer (review PR test), Tech Lead |
| E2E, UI, trợ năng, kiểm thử khám phá | QA Engineer | QA Engineer | QA Lead |
| Dữ liệu test tổng hợp (`pdfgen.py`, `seed_dev.sql`, kịch bản FakeLlm) | Developer | **QA Engineer** – giữ danh mục file mẫu và mục đích của từng file | QA Lead |
| Tài liệu dự án thật cho C3/C4 | Product Owner (chọn và cho phép dùng) | **QA Engineer** – lưu ngoài repo, xóa sau nghiệm thu | IT/Security (phân loại dữ liệu) |
| Bộ câu hỏi chuẩn + đáp án (DEP-005) | PO và người dùng nghiệp vụ; QA soạn nháp | **QA Lead** – quản lý phiên bản | Người dùng nghiệp vụ (chấm), PO (duyệt) |
| Hiệu năng | Tech Lead | Tech Lead | QA Lead, PO |
| Bảo mật | IT/Security | IT/Security | IT/Security Lead |
| Nghiệm thu | Người dùng nghiệp vụ | QA Lead (biên bản) | Product Owner (ký) |
| Kết quả CI hằng ngày | – (tự động) | Developer trực build | QA Lead (theo dõi xu hướng, độ ổn định) |

## 13.0 Nhân sự và đào tạo (IEEE 829 §5.13)

| Nhu cầu | Số người | Kỹ năng / đào tạo cần |
|---|---|---|
| QA Engineer | 1 | Playwright, pytest; hiểu RAG (truy xuất, trích dẫn, ngưỡng); đọc [Hướng dẫn cài đặt](../../guide/HUONG_DAN_CAI_DAT.md) để tự dựng môi trường |
| Developer | 1–2 | FastAPI, psycopg, PostgreSQL RLS, React |
| Người chấm chất lượng | 2–3 người dùng nghiệp vụ | Hướng dẫn chấm điểm 30 phút: thế nào là "đúng", "đúng một phần", "bịa"; cách đối chiếu số trang |
| Người tham gia usability | ≥ 5 | Không đào tạo trước (đo khả năng tự dùng, NFR-008) |
| IT/Security | 1 | OWASP ASVS cho ứng dụng web có LLM |

## 14.0 Lịch trình (IEEE 829 §5.14)

Lịch dưới đây là `[Đề xuất QA]`, tính theo ngày làm việc.

**Liên hệ với kế hoạch dự án:**
- BRD chưa có ngày go-live và ngân sách (`[TBD: OQ-015]`). Lịch này giả định go-live **sau** M6.
- Khi OQ-015 được chốt, nếu go-live sớm hơn M6, PO phải chọn giữa lùi go-live hoặc thu hẹp C3 (chỉ chạy PERF-001/003, SEC-012/015, QLT-001/004), và ghi lại rủi ro.
- Lịch cũng bám theo PLAN v0.1: C2 tương ứng việc hoàn tất các task Partial/Deferred của VS-5…VS-11; C3 cần T06-03, T10-05 và T10-06.
- Ngày thật phụ thuộc DEP-005 (bộ câu hỏi) và T10-05 (staging).

| Mốc | Nội dung | Bắt đầu | Kết thúc | Điều kiện |
|---|---|---|---|---|
| M0 | C1 – kiểm thử tự động bản demo | 2026-10-26 | 2026-10-26 | **Hoàn thành** |
| M1 | Phê duyệt MTP v1.0 | 2026-10-27 | 2026-10-28 | Review checklist IEEE 829 |
| M2 | C2 – hoàn thiện chức năng + CI | 2026-10-28 | 2026-11-06 | TT-02…TT-07, TT-16, TT-17, TT-19 (≈ 9,1 ngày công; 2 người song song) |
| M3 | Có bộ câu hỏi chuẩn + staging | 2026-10-28 | 2026-11-06 | TT-08, TT-10 (song song M2) |
| M4 | C3 – hiệu năng, bảo mật, chất lượng | 2026-11-09 | 2026-11-13 | M3 |
| M5 | C4 – UAT + usability | 2026-11-16 | 2026-11-18 | M4 đạt |
| M6 | Báo cáo tổng kết, quyết định launch gate | 2026-11-19 | 2026-11-19 | G-01…G-09 |

## 15.0 Rủi ro và dự phòng (IEEE 829 §5.15)

| Rủi ro kế hoạch | Khả năng | Tác động | Dự phòng |
|---|---|---|---|
| Không có bộ câu hỏi chuẩn đúng hạn (TR-09) | Cao | Cao – không đo được G-02 | QA soạn bản nháp từ PDF mẫu; PO chỉ duyệt và bổ sung; nếu trễ, lùi M4 và báo Sponsor |
| Chưa có staging | Trung bình | Cao – chặn C3/C4 | Chạy PERF sơ bộ trên máy dev với PostgreSQL thật (Docker trên máy khác) để phát hiện sớm |
| PGlite che giấu hoặc tạo ra lỗi khác với PostgreSQL thật (TR-06) | Cao | Trung bình | Bắt buộc chạy CI trên PostgreSQL thật trước C3; lỗi chỉ xuất hiện trên PGlite → ghi Low trừ khi chặn demo |
| LLM thật chậm hơn ngân sách 15 s (TR-05) | Cao | Trung bình | Đo sớm PERF-001 với 10 câu; điều chỉnh effort/timeout; cân nhắc mô hình nhanh hơn (ADR-007) |
| OQ chưa đóng làm thay đổi tiêu chí | Trung bình | Trung bình | Test tham số hóa theo cấu hình (`MAX_FILE_MB`, `MAX_PAGES`…); cập nhật MTP theo phiên bản |
| Thiếu người chấm nghiệp vụ | Trung bình | Cao | Đặt lịch chấm ngay khi M3 xong; tối thiểu 2 người chấm, xử lý bất đồng bằng người thứ ba |

## 16.0 Phê duyệt (IEEE 829 §5.16)

| Vai trò | Họ tên | Chữ ký | Ngày | Ý kiến |
|---|---|---|---|---|
| QA Lead | `[TBD: OQ-007]` | | | |
| Product Owner | `[TBD: OQ-007]` | | | |
| Tech Lead | `[TBD]` | | | |
| IT/Security | `[TBD]` | | | |

**Điều kiện phê duyệt:**
- MTP chỉ được phê duyệt (Approved) khi đã có tên người phê duyệt (OQ-007), và PO đã quyết định DEF-T-002.
- Phê duyệt MTP cho phép bắt đầu chu kỳ C2. Riêng C3 và C4 cần xác nhận lại nếu phạm vi thay đổi do OQ đóng.
- Mỗi lần sửa tài liệu ở mức phiên bản chính (1.x) đều phải phê duyệt lại.

---

# Phụ lục A – Ma trận truy vết yêu cầu → test case

**Cách đọc cột Trạng thái:**
- **Đạt**: mọi AC của yêu cầu có test đạt.
- **Một phần**: có test đạt nhưng còn AC chưa kiểm.
- **Chưa chạy** / **Bị chặn** / **Ngoài phạm vi**: theo quy ước ở đầu tài liệu.

## PA.1 User story → test case

| Story | AC (PRD) | Test case | Trạng thái C1 | Ghi chú |
|---|---|---|---|---|
| US-001 | Vào danh sách với "Đang xử lý"; có tiến độ | API-008, E2E-001, UAT-001 | **Đạt** | Tiến độ kiểm qua ảnh S02 (thủ công) |
| US-002 | 10 file đều vào; N+1 → không file nào; lẫn hợp lệ/không hợp lệ | API-006, E2E-001, E2E-004, E2E-011 | **Một phần** | E2E-004 (10 file) chưa chạy |
| US-003 | docx, jpg, PDF giả → từ chối, nêu tên + lý do | API-010, E2E-001, UAT-002 | **Đạt** | |
| US-004 | Quá dung lượng/số trang → từ chối, nêu tên file, **dung lượng/số trang của file** và giới hạn | API-010, API-011 | **Một phần** | **DEF-T-001**: thông báo chưa nêu dung lượng/số trang thực tế của file |
| US-005 | Tự chuyển sang Sẵn sàng/Thất bại trong NFR-002 | INT-003, INT-004, PERF-003 | **Một phần** | Thời gian NFR-002 chưa đo ở mức biên |
| US-006 | Tên, trạng thái, thời điểm; chỉ tài liệu của mình; trạng thái trống | API-014, SEC-005, E2E-001, E2E-009, E2E-013 | **Đạt** | E2E-009, E2E-013 (trùng tên, tải lại trang) chưa chạy |
| US-007 | Đổi trạng thái + thông báo, không tải lại trang | E2E-001, API-028, UI-006 | **Một phần** | SSE chưa có test tự động riêng (API-028) |
| US-008 | Hỏng/mật khẩu → Thất bại có lý do; scan → R-03 | API-010, UT-004, E2E-001 | **Một phần** | **DEF-T-002**: PDF hỏng/có mật khẩu bị **từ chối ngay khi tải lên** (422) thay vì "Thất bại" R-01/R-02 |
| US-009 | R-04 → Xử lý lại; R-01…R-03 không có nút | INT-005, API-016, E2E-010 | **Đạt** (API) | E2E-010 chưa chạy |
| US-010 | Xác nhận trước khi xóa; xóa khi đang xử lý thì hủy | E2E-001, INT-006, API-015 | **Đạt** | |
| US-011 | Hỏi lại sau khi xóa không dùng tài liệu đã xóa | INT-007, UAT-007 | **Đạt** | Kiểm: chunk bị xóa ngay, nguồn chuyển "(đã xóa)" |
| US-012 | Hỏi Việt/Anh trong NFR-001; khóa khi chưa Sẵn sàng; không gửi câu trống | API-020, API-021, API-023, E2E-001, UI-010 | **Một phần** | Tiếng Anh, NFR-001 chưa kiểm |
| US-013 | Không dùng tài liệu Đang xử lý; dùng đúng tài liệu Sẵn sàng | API-021, INT-010, INT-017 | **Một phần** | INT-017 (Y đang xử lý, Z Sẵn sàng) chưa chạy |
| US-014 | 5 câu liên tiếp cùng khung, đúng thứ tự | E2E-001 (2 câu), API-019, E2E-014 | **Một phần** | E2E-014 (5 câu) chưa chạy |
| US-015 | Câu hỏi tiếp nối | QLT-005 | **Bị chặn** | OQ-012, chưa triển khai |
| US-016 | "Chưa đủ thông tin", không nguồn; NFR-005 | INT-012, E2E-001, QLT-004 | **Một phần** | NFR-005 bị chặn (DEP-005) |
| US-017 | Trích cả 2 tài liệu; MET-003 ≥ 80% | INT-011, QLT-005 | **Một phần** | MET-003 bị chặn |
| US-018 | Nêu mâu thuẫn, nguồn từng giá trị | INT-011 | **Một phần** | **DEF-T-003**: bộ trả lời trích xuất nêu đủ 2 giá trị và 2 nguồn nhưng không gắn cờ "không thống nhất"; cần LLM thật |
| US-019 | Giới hạn nhóm tài liệu | – | **Ngoài phạm vi** | OQ-018 |
| US-020 | Đúng tên file | API-020, INT-010, QLT-002 | **Một phần** | NFR-004 bị chặn |
| US-021 | Đúng số trang; không hiện trang giả | INT-010, QLT-003, UI-011 | **Một phần** | UI-011 (không có số trang) chưa chạy |
| US-022 | Mở đúng trang; không có trang → trang 1; đã xóa → báo đã xóa | API-017, API-018, API-031, E2E-001 | **Một phần** (2/3 AC) | API-031 (không có trang) chưa chạy |
| US-023 | Người không có quyền bị từ chối; hết phiên giữ câu đang soạn | SEC-001, SEC-002, E2E-002, E2E-008 | **Một phần** | E2E-008 chưa chạy |
| US-024 | B không thấy, không hỏi được tài liệu của A | SEC-005, SEC-006 | **Đạt** | |
| US-025 | Chỉ báo đang soạn, khóa ô hỏi; chỉ báo đang xử lý | E2E-001, UI-005 | **Đạt** | |
| US-026 | Mất mạng khi tải lên → Tải lại; lỗi câu hỏi tại chỗ | API-024, E2E-005, E2E-007 | **Một phần** | Phần giao diện chưa có E2E |
| US-027 | Gửi lại đúng câu hỏi; lặp lại được | API-025 | **Một phần** | E2E-007 chưa chạy |

## PA.2 NFR và trường hợp biên → test case

| Yêu cầu | Test case | Trạng thái C1 |
|---|---|---|
| NFR-001, NFR-007 | PERF-001, PERF-002 | Bị chặn (staging) |
| NFR-002 | PERF-003, INT-004 | Một phần (40 trang đạt trên dev; biên 300 trang/20 MB chưa đo) |
| NFR-003, NFR-004, NFR-005, NFR-018 | QLT-001…QLT-004 | Bị chặn (DEP-005) |
| NFR-006, NFR-019, NFR-020, NFR-021 | API-006, API-007, API-010, API-011 | Đạt (giới hạn tham số hóa theo cấu hình) |
| NFR-008 | UAT-008 | Chưa chạy |
| NFR-009, NFR-022 | SEC-012 | Bị chặn (staging) |
| NFR-010 | SEC-005, SEC-006, SEC-015 | Một phần (API + CSDL đạt; pentest chưa) |
| NFR-011 | SEC-007, SEC-008 | Đạt phần kỹ thuật; phê duyệt nhà cung cấp (OQ-005) chưa |
| NFR-012, NFR-023 | SEC-002, SEC-005, `test_maintenance_tasks` (phân vùng audit) | Một phần (thời gian lưu 90 ngày cấu hình, chưa inspection) |
| NFR-013 | INT-007, INT-008 | Đạt |
| NFR-014, NFR-024 | API-019, E2E-009 | Một phần |
| NFR-016 | UI-010 | Chưa chạy |
| NFR-017 | UI-009 | Một phần (Edge) |
| E-01, E-02 | E2E-001 (ô hỏi khóa), ảnh S01/S02 | Đạt |
| E-03 | UI-004 | Chưa chạy |
| E-04, E-05, E-06 | E2E-005, E2E-007, API-024 | Một phần |
| E-07, E-08 | API-006, API-010, API-011, E2E-011 | Đạt |
| E-09, E-10 | API-010, UT-004 | Một phần (DEF-T-002 với E-09) |
| E-11 | E2E-012 | Chưa chạy |
| E-12 | E2E-013 | Chưa chạy |
| E-13, E-19 | `test_citation_of_deleted_document`, API-018, E2E-001 | Đạt |
| E-14, E-15 | API-023, UI-007 | Đạt |
| E-16 | INT-012, E2E-001 | Đạt |
| E-17 | E2E-008 | Chưa chạy |
| E-18 | E2E-009, API-019 | Một phần |
| EVT-01…EVT-11 | SEC-008, INT-018, `test_ai_failure_then_resend` (EVT-10), `test_isolation_between_users` (EVT-11) | Một phần – INT-018 (đủ 11 sự kiện, G-07) chưa chạy |

## PA.3 Kịch bản nghiệm thu BRD → test case

| Kịch bản | Mô tả | Test hệ thống tương ứng (đạt C1) | UAT |
|---|---|---|---|
| AC-01 | Tải PDF hợp lệ | E2E-001, E2E-003 | UAT-001 |
| AC-02 | Tải file không phải PDF | E2E-001, API-010 | UAT-002 |
| AC-03 | Chat với tài liệu đã xử lý | E2E-001, INT-010 | UAT-003 |
| AC-04 | Tổng hợp nhiều file | E2E-003, INT-011 | UAT-004 |
| AC-05 | Hỏi nội dung không có | E2E-001, INT-012 | UAT-005 |
| AC-06 | Xem nguồn và số trang | E2E-001, API-017 | UAT-006 |
| AC-07 | Xóa tài liệu | E2E-001, INT-007 | UAT-007 |

Cả 7/7 kịch bản đều đã có test hệ thống đạt trên bản demo. Theo MET-006, việc nghiệm thu chính thức vẫn cần thực hiện UAT trên staging với tài liệu thật.

---

# Phụ lục B – Kết quả chu kỳ 1 (26/10/2026) và khoảng trống

## PB.1 Kết quả thực thi

| Bộ test | Kết quả | Ghi chú |
|---|---|---|
| ruff / mypy strict / import-linter / tsc | Sạch / 0 lỗi (66 file) / 4 hợp đồng giữ / 0 lỗi | |
| pytest backend (unit + integration, PGlite) | **49/49 đạt** (~65 giây) | 12 unit, 37 integration (gồm 6 trường hợp tham số hóa) |
| Playwright E2E (Edge) | **2/2 đạt** | `demo.spec.ts` |
| Smoke `scripts/smoke.py` | Đạt | 3 tài liệu READY; ANSWERED (trang 2), đa tài liệu, INSUFFICIENT |
| Độ phủ mã backend (coverage.py) | **78%** (2.429 câu lệnh, 546 chưa chạy) | Dưới mục tiêu 80% |

## PB.2 Khoảng trống độ phủ cần xử lý

| Thành phần | Độ phủ | Nguyên nhân | Hành động |
|---|---|---|---|
| `adapters/oidc.py`, `adapters/blob_local.py` | 0% (test tự động) | Test dùng FakeIdp, MemoryBlobStore; adapter thật chỉ chạy qua smoke/E2E | UT-015; INT-015 với IdP giả lập chạy thật |
| `adapters/llm_anthropic.py`, `adapters/embedding_http.py` | 0% | Chưa có test | UT-014; INT-015 trên staging |
| `api/v1/events.py` (SSE) | 39% | Chưa có test luồng SSE | API-028 |
| `worker/main.py` | 45% | Test gọi `drain()`, không chạy vòng lặp nền/lịch bảo trì | Test vòng lặp với `JobSignal` và thời gian giả |
| `modules/ingestion/chunker.py` | 66% | Nhánh cắt cứng câu quá dài chưa chạy | Bổ sung property test với câu > `max_tokens` |
| `infra/sandbox.py` | 68% | Nhánh timeout/vượt bộ nhớ/crash | Test sandbox với hàm treo và hàm cấp phát lớn |

## PB.3 Lỗi và sai khác phát hiện

| ID | Mức | Mô tả | Yêu cầu | Trạng thái |
|---|---|---|---|---|
| DEF-T-001 | Medium | Thông báo từ chối do quá dung lượng/số trang chỉ nêu tên file và giới hạn, **không nêu dung lượng/số trang thực tế của file** | US-004 AC 1–2 | Mở |
| DEF-T-002 | Medium (cần PO quyết định) | PRD (US-008, E-09) yêu cầu PDF hỏng/có mật khẩu chuyển "Thất bại" R-01/R-02. BLUEPRINT ALG-02 và API (`422 not_pdf/encrypted`) lại từ chối ngay khi nhận file; giao diện hiện "Không nhận" kèm lý do. Đây là sai khác giữa yêu cầu và thiết kế. Hành vi hiện tại tốt hơn (không tốn hạn mức), nhưng cần PO chấp thuận và cập nhật PRD | US-008, E-09 | Mở – chờ PO |
| DEF-T-003 | Low | Khi 2 tài liệu ghi 2 giá trị khác nhau, bộ trả lời trích xuất nêu đủ 2 giá trị kèm 2 nguồn nhưng không ghi rõ "hai tài liệu không thống nhất" (cờ `conflict` chỉ có khi dùng LLM thật) | US-018 | Mở – kiểm lại với LLM thật |
| DEF-T-004 | High (đã sửa) | Tài liệu lớn (37 trang) làm CSDL dev ngừng hoạt động: message INSERT > 64 KB bị tách gói TCP, PGlite lỗi WASM `unreachable`; devdb nuốt lỗi nên không thoát | NFR-002, môi trường | **Đã sửa** 26/10 – có INT-004 |
| DEF-T-005 | Medium (đã sửa) | Kết nối lại CSDL dev bị `DuplicatePreparedStatement` (PGlite dùng chung phiên giữa các kết nối) | Môi trường | **Đã sửa** 26/10 (tắt auto-prepare ở chế độ single) |
| DEF-T-006 | Medium (đã sửa) | Câu hỏi có hư từ ("là bao nhiêu") bị cổng ngưỡng loại vì full-text AND mọi từ | US-012, US-017 | **Đã sửa** 26/10 – có INT-011 |
| GAP-01 | – | Chưa có test case cho E-11, E-12, US-013 AC 1, US-014 (5 câu), US-021 AC 2, US-022 AC 2, G-07 | E-11, E-12, US-013, US-014, US-021, US-022, G-07 | **Đóng ở v0.2** – đã thiết kế E2E-012…014, INT-017, INT-018, UI-011, API-031; thực thi ở C2 |

---

# Phụ lục C – Đối chiếu bố cục IEEE 829

| IEEE 829 §5.x | Mục trong tài liệu |
|---|---|
| 5.1 Test plan identifier | 1.0 |
| 5.2 Introduction | 2.0 (mục đích, phạm vi, mục tiêu, tham chiếu) |
| 5.3 Test items | 3.0 |
| 5.4 Features to be tested | 4.0 |
| 5.5 Features not to be tested | 5.0 |
| 5.6 Approach | 6.0 (11 mức/loại, chiến lược thực thi, phân chia tự động – thủ công) |
| 5.7 Item pass/fail criteria | 7.0 |
| 5.8 Suspension and resumption criteria | 8.0 |
| 5.9 Test deliverables | 9.0 |
| 5.10 Testing tasks | 10.0 |
| 5.11 Environmental needs | 11.0 |
| 5.12 Responsibilities | 12.0 |
| 5.13 Staffing and training needs | 13.0 |
| 5.14 Schedule | 14.0 |
| 5.15 Risks and contingencies | 15.0 (và A.7) |
| 5.16 Approvals | 16.0 |

---

# Phụ lục D – Kết quả thực thi chu kỳ C2 (27/10/2026)

Chu kỳ C2 chạy **toàn bộ 130 test case** trên ứng dụng tại **http://localhost:8080/** (ENV-DEV: PGlite, bộ trả lời trích xuất,
Edge 156 / Chrome 156). Mỗi test case có thư mục riêng trong `test_reports/<tên test case>/` gồm `report.md`, `result.json`,
ảnh chụp từng bước, video toàn bộ quá trình và log. Bảng tổng hợp: [test_reports/README.md](../../test_reports/README.md).
Chi tiết từng test case: [test_cases/](test_cases/README.md).

## PD.1 Tổng hợp

| Loại | Tổng | Đạt | Cần người xác nhận | Bị chặn | Không đạt |
|---|---|---|---|---|---|
| UT | 15 | 15 | 0 | 0 | 0 |
| INT | 18 | 17 | 0 | 1 | 0 |
| API | 31 | 31 | 0 | 0 | 0 |
| E2E | 14 | 14 | 0 | 0 | 0 |
| SEC | 15 | 13 | 0 | 2 | 0 |
| ACC | 7 | 4 | 2 | 1 | 0 |
| UI | 11 | 7 | 4 | 0 | 0 |
| PERF | 6 | 2 | 0 | 4 | 0 |
| QLT | 5 | 0 | 0 | 5 | 0 |
| UAT | 8 | 0 | 0 | 8 | 0 |
| **Tổng** | **130** | **103** | **6** | **21** | **0** |

- **Đạt** có nghĩa mọi bước đạt trên môi trường dev. Với PERF-003, PERF-006 kết quả chỉ để tham khảo (PGlite, embedding hashing).
- **Cần người xác nhận** (ACC-001, ACC-006, UI-001, UI-004, UI-008, UI-010): phần tự động đạt, còn bước đánh giá của người
  (xem video thứ tự focus, so sánh trực quan với thiết kế, câu trả lời tiếng Anh với LLM thật, gợi ý E-03).
- **Bị chặn** (21): không thể chạy ở môi trường này. Lý do và điều kiện cần ghi trong report của từng test case.
  - INT-016: thiếu PostgreSQL thật.
  - SEC-012, SEC-015, PERF-001, 002, 004, 005: thiếu staging, k6 hoặc OWASP ZAP.
  - QLT-001…005: thiếu bộ câu hỏi chuẩn DEP-005 và LLM thật.
  - UAT-001…008: cần người dùng nghiệp vụ ký xác nhận.
  - ACC-002: cần NVDA.
- Kết quả bộ test tự động backend sau các sửa đổi: **66/66 pytest đạt**; ruff, mypy strict, import-linter, `tsc`, `vite build` đều sạch.

## PD.2 Lỗi phát hiện khi thực thi và cách xử lý

| ID | Mức | Phát hiện (test case) | Trạng thái |
|---|---|---|---|
| DEF-T-007 | Medium | Ứng dụng khởi động bằng công cụ test trả **500** cho mọi request có ghi log (vd. `/auth/callback` sai state): khi tiến trình khởi chạy thoát, `run.py` ngừng đọc đường ống log của API (API-003) | **Đã sửa**: `run.py` vẫn đọc hết đường ống kể cả khi không ghi được; `app.ts` chạy tách rời |
| DEF-T-008 | Medium | Câu hỏi đang soạn **bị mất** khi phiên hết hạn đúng lúc bấm Gửi, và không được khôi phục sau đăng nhập lại (React StrictMode gọi hàm khởi tạo hai lần, lần đầu xóa nháp) – trái US-023 AC 2 (E2E-008) | **Đã sửa** trong `ChatPanel.tsx` |
| DEF-T-009 | Medium | Body > 21 MB qua proxy dev (Vite, cổng 8080) trả **500 rỗng** thay vì 413 (API trực tiếp trả 413 đúng) (API-012) | **Đã sửa**: thêm giới hạn body tương đương `client_max_body_size` vào `vite.config.ts` |
| DEF-T-010 | Medium | Giao diện tối: nút *Xóa tài liệu* chữ trắng trên nền hồng, tương phản 2,42:1 (< 4,5:1) (ACC-003) | **Đã sửa** (`styles.css`) |
| DEF-T-011 | Low | `prefers-reduced-motion` không tắt hoạt ảnh ba chấm "đang soạn" do quy tắc CSS bị ghi đè (ACC-007) | **Đã sửa** (`styles.css`) |
| DEF-T-012 | Medium | Hộp thoại modal không có bẫy focus: Tab làm focus thoát ra phía sau hộp thoại (ACC-005) | **Đã sửa** (`Overlays.tsx`, hook `useFocusTrap`) |
| DEF-T-013 | Low | Lỗi 429 khi tải file hiển thị "Hệ thống đang bận… thử lại sau 1221 giây", gây hiểu nhầm (hạn mức 30 file/giờ) (E2E-001 lần chạy đầu) | **Đã sửa**: nêu rõ "đã tải lên quá nhiều file trong một giờ… thử lại sau khoảng N phút" |
| DEF-T-014 | Low | Hạn mức hiển thị (vd. 12/100) cộng cả chỗ đặt của lô tải lỗi trước đó trong 10 phút (ADR-014), người dùng thấy số lớn hơn số tài liệu thật (E2E-004) | Mở – chờ PO quyết định có nhả chỗ khi tải lỗi không |
| DEF-T-015 | Low | PRD E-03 yêu cầu gợi ý "kiểm tra lý do và tải file khác" khi mọi tài liệu Thất bại; ô hỏi chỉ hiện lời nhắc chung (UI-004) | Mở – chờ PO/Designer |
| DEF-T-016 | Low | Playwright `waitForLoadState('networkidle')` không dùng được vì SSE giữ kết nối mở; bước dở dang từng được ghi "Đạt" (công cụ bằng chứng) | **Đã sửa** trong `evidence/fixture.ts` |
| DEF-T-017 | Info | Bộ trả lời trích xuất trích nguyên văn nội dung tài liệu (kể cả chuỗi `</source><source id="S9">`); ký hiệu trích dẫn giả `[S9]` đã bị loại, giao diện hiển thị như chữ thường, không có XSS (SEC-010) | Không phải lỗi; kiểm thử đầy đủ cần LLM thật |
| DEF-T-018 | Info | Dev dùng chung hạn mức tải 30 file/giờ cho mỗi tài khoản mẫu nên chạy nhiều test liên tiếp làm cạn hạn mức; đợt chạy nâng tạm `RATE_FILES_PER_HOUR=1000` (đã hoàn lại) | Ghi nhận cách chạy |

DEF-T-001 (thông báo quá dung lượng chưa nêu dung lượng thực tế, API-011), DEF-T-002 (PRD và thiết kế lệch nhau về PDF hỏng/có mật
khẩu, API-010) và DEF-T-003 (bộ trả lời trích xuất không gắn cờ mâu thuẫn) **vẫn mở** như ở Phụ lục B.

## PD.3 Cách chạy lại

```bash
cd app/frontend
node evidence/app.ts start                                              # ứng dụng tại http://localhost:8080/
node evidence/run-cli-cases.ts                                          # UT, INT, SEC dòng lệnh, smoke
npx playwright test -c playwright.testcases.config.ts [tên test case]   # API, E2E, SEC, ACC, UI, PERF giao diện
node evidence/run-blocked.ts                                            # ghi report cho test case bị chặn
node evidence/summary.ts                                                # cập nhật test_reports/README.md
```

Các test case thay đổi cấu hình (`ev.restartApp`) cần ứng dụng được khởi động bằng `evidence/app.ts`. Để chạy liên tiếp nhiều test case tải
file, khởi động với `node evidence/app.ts restart RATE_FILES_PER_HOUR=1000`.

