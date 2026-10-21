# T-000 — Tổ chức kick-off kỹ thuật và chốt biên bản quyết định

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 0 |
| **Loại** | Quy trình |
| **User story** | — nền tảng |
| **Ưu tiên** | P0 |
| **Ước lượng** | 0,5 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | — |
| **Mở khóa (task chờ task này)** | T-001, T-002, T-003, T-004, T-005, T-006, T-007, T-008, T-009 |
| **Người thực hiện** | _chưa giao_ (Tech Lead chủ trì) |
| **Trạng thái** | To do |

## 1. Mục tiêu

Sau buổi kick-off, đội có **một biên bản quyết định duy nhất** xác nhận (hoặc thay đổi có lý do) các lựa chọn công nghệ ở [Implement_plan §1.2](../Implement_plan.md#12-các-quyết-định-coi-như-đã-chốt-cho-việc-code), phân vai rõ ràng cho từng task Sprint 0, thống nhất quy trình làm việc, và một danh sách OQ có người đuổi theo + hạn chót. Không ai phải hỏi lại "dùng thư viện gì / ai làm gì / hỏi ai" trong Sprint 0.

## 2. Bối cảnh

- SAD ghi nhiều lựa chọn là `[Proposed]` ([SAD §6](../../design/SAD.md#6-bộ-công-nghệ-tham-chiếu-proposed)); Implement_plan §1.2 coi chúng là mặc định **chờ Tech Lead xác nhận ở T-000**.
- Điều kiện để SAD chuyển `Approved` ([SAD §8.3](../../design/SAD.md#83-trạng-thái)) gồm: chốt OQ-006, OQ-018; chạy SP-01, SP-03; đội xác nhận bộ công nghệ (đặc biệt giấy phép thư viện PDF).
- Nhiều OQ chặn các sprint sau ([Implement_plan §9.1](../Implement_plan.md#91-quyết-định-cần-có-và-ảnh-hưởng-tới-lập-trình)); mốc OQ-006/OQ-018 là 2026-11-09 (trước Sprint 2).
- Có các điểm thiết kế chưa có story ([User_Stories §10](../../design/User_Stories.md#10-phần-thiết-kế-vượt-ra-ngoài-user-story-hiện-có)) cần PO xác nhận trước khi nhận task tương ứng.

## 3. Phạm vi

**Trong phạm vi**
- Xác nhận từng dòng bảng §1.2 (Backend, Frontend, CSDL, Hàng đợi, Lưu tệp, Trích PDF, Xác thực, Trả lời, Kiểm thử).
- Xác nhận giả định đội §1.3 và giao người cho T-001…T-009.
- Thống nhất quy trình: nhánh/PR/review (§4.3), DoR (§4.4), DoD (§4.5), nhịp sprint, nơi theo dõi task.
- Chọn nền tảng CI (GitHub Actions theo `.github/workflows/ci.yml` hoặc CI của tổ chức).
- Lập danh sách OQ cần đuổi theo, người phụ trách, hạn, task bị chặn.
- Ghi nhận các điểm cần PO xác nhận (retry tài liệu, tìm kiếm lịch sử, token trong báo cáo, điều hướng ADMIN).

**Ngoài phạm vi**
- Ra quyết định kinh doanh thay cho người phụ trách OQ (chỉ ghi nhận và đuổi theo).
- Chọn nhà cung cấp AI (chờ OQ-006, làm ở T-208).
- Thiết kế chi tiết từng module (thuộc từng task).

## 4. Thiết kế chi tiết

**Sản phẩm đầu ra:** `docs/implement/decisions/T-000-kickoff-record.md` `[Proposed]` (đường dẫn), cấu trúc:

```markdown
# Biên bản kick-off kỹ thuật — <ngày>
## 1. Người tham dự và vai trò
## 2. Xác nhận lựa chọn công nghệ (Implement_plan §1.2)
| Hạng mục | Lựa chọn trong plan | Kết luận (Giữ/Đổi) | Lý do nếu đổi | Task bị ảnh hưởng |
## 3. Phân công Sprint 0
| Task | Người | Người review |
## 4. Quy trình làm việc
## 5. Danh sách OQ cần đuổi theo
| OQ | Câu hỏi | Người phụ trách | Hạn | Task bị chặn | Nếu chưa có thì làm gì |
## 6. Điểm cần PO xác nhận
## 7. Rủi ro và hành động tiếp theo
```

**Bảng 2 — các dòng bắt buộc xác nhận** (lấy nguyên §1.2):

| Hạng mục | Lựa chọn | Điểm cần kiểm khi xác nhận |
|---|---|---|
| Backend | Python 3.12, FastAPI + Uvicorn, Pydantic v2, SQLAlchemy 2 (async), Alembic | Công cụ quản lý gói Python `[Proposed: uv]` |
| Frontend | React 18 + TypeScript, Vite, TanStack Query, React Router, pdf.js | Giấy phép pdf.js Apache-2.0 `[Verify]` |
| CSDL | PostgreSQL 16 + pgvector, `unaccent` | pgvector ≥ 0.8 nếu dùng quét lặp; hỗ trợ trên dịch vụ PG quản lý `[Verify]` |
| Hàng đợi | Bảng `job` + `FOR UPDATE SKIP LOCKED` | — |
| Lưu tệp | S3-compatible (MinIO local) | — |
| Trích PDF | `pypdfium2`; **không** PyMuPDF (AGPL) trừ khi Pháp chế duyệt | Kết luận cuối sau SP-03 ([T-008](./T-008-spike-sp03-pdf-extraction.md)) |
| Xác thực | OIDC qua `IdentityPort`; dev dùng `DevIdentity` | Chờ OQ-018 |
| Trả lời | JSON có cấu trúc → `CitationValidator` → `final`; không phát `token` | AD-07; SP-02 |
| Kiểm thử | pytest, Testcontainers, Vitest + Testing Library, Playwright | Docker có sẵn trên runner CI |

**Bảng 5 — OQ phải có trong danh sách** (người phụ trách và hạn lấy từ BRD §12 / SDD §6.2 / PRD; kick-off chỉ xác nhận tên người cụ thể):

| OQ | Nội dung ngắn | Người phụ trách (theo nguồn) | Hạn (theo nguồn) | Task/sprint bị ảnh hưởng |
|---|---|---|---|---|
| OQ-001 | Sponsor, Business Owner, reviewer chính thức | Quản lý giao yêu cầu | 2026-10-23 | Mọi phê duyệt |
| OQ-004 | Sponsor duyệt tính năng BA đề xuất | Sponsor | 2026-10-26 | Phạm vi C6, C7, B1/B2, D2, F1, F2 |
| OQ-005 | Ngân sách, thời hạn | Sponsor | 2026-10-26 | Lộ trình §5.0 |
| OQ-006 | Chính sách dữ liệu AI | IT/Bảo mật | 2026-10-30 | T-208, T-406 (chặn cứng) |
| OQ-007 | Mục tiêu MET-001…004 | Sponsor | 2026-10-30 | T-402, launch gate |
| OQ-008 | Bộ câu hỏi kiểm thử + PDF mẫu | Business Owner | 2026-11-06 | T-009, T-211, T-310 |
| OQ-009 | Ngôn ngữ | Business Owner | 2026-10-26 | T-206, T-308, chọn mô hình embedding |
| OQ-010 | Tỷ lệ PDF scan/bảng biểu | BA + Đội PTKD | 2026-10-30 | T-008 |
| OQ-011 | Phân quyền, quyền xóa | Sponsor + IT/Bảo mật | 2026-10-30 | T-006, T-106 |
| OQ-013 | Giới hạn tệp | Business Owner + Đội phát triển | 2026-11-06 | T-002 (nginx), T-103 |
| OQ-014 | Ngưỡng thời gian trả lời | Business Owner | 2026-11-06 | T-309, launch gate |
| OQ-015 | Số người dùng | Sponsor | 2026-10-30 | T-401 |
| OQ-016 | Tên sản phẩm chính thức | Sponsor/Marketing nội bộ | 2026-11-06 | T-005 (nhãn UI) |
| OQ-017 | Khả dụng, giờ hỗ trợ | Sponsor + Vận hành | 2026-11-06 | T-408, T-409 |
| OQ-018 | Identity Provider | IT/Bảo mật | 2026-10-30 | T-006 (adapter OIDC) |
| OQ-019 | Thời gian lưu giữ | IT/Bảo mật + Pháp chế | 2026-11-06 | T-407 |
| OQ-020 | Trình duyệt, accessibility | Business Owner | 2026-11-06 | T-005, phạm vi E2E |

**Bảng 6 — điểm cần PO xác nhận:** (1) nút "Thử lại" + `POST /api/v1/documents/{id}/retry` ([T-112](./T-112-retry-failed-document.md)); (2) tìm kiếm trong lịch sử ([T-304](./T-304-history-screen.md)); (3) chỉ số token, "Không tìm thấy", "Hữu ích" trong báo cáo tuần ([T-402](./T-402-weekly-report-screen.md)); (4) thanh điều hướng của vai trò `ADMIN` (thiết kế chỉ có MEMBER và SPONSOR — [T-005](./T-005-frontend-skeleton.md)); (5) cột "Số trang" trong thư viện.

## 5. Các bước thực hiện

1. Tech Lead gửi trước 1 ngày: Implement_plan, SAD §6–§8, bảng §1.2, bảng OQ ở trên.
2. Họp 2 giờ `[Estimate]`: đi qua bảng §1.2, ghi Giữ/Đổi; nếu Đổi thì ghi task bị ảnh hưởng.
3. Xác nhận cơ cấu đội §1.3 và giao người + người review cho T-001…T-009.
4. Thống nhất quy trình §4.3–§4.5, chọn CI, chọn công cụ theo dõi task.
5. Với mỗi OQ: xác nhận tên người cụ thể và kênh liên lạc; Tech Lead (hoặc BA) là người đuổi theo.
6. Ghi biên bản theo cấu trúc mục 4, commit vào `docs/implement/decisions/`, mở PR để người tham dự review.
7. Tạo nhắc việc theo hạn từng OQ; báo cáo trạng thái OQ ở mỗi buổi daily/sprint review.

## 6. Tiêu chí chấp nhận

- [ ] Biên bản tồn tại tại đường dẫn đã chọn và được merge vào `main`.
- [ ] 9/9 dòng của bảng §1.2 có kết luận Giữ/Đổi; mọi dòng Đổi có lý do và danh sách task bị ảnh hưởng.
- [ ] 10/10 task T-000…T-009 có người thực hiện và người review.
- [ ] Bảng OQ liệt kê ít nhất 17 OQ ở mục 4, mỗi OQ có tên người cụ thể, hạn, task bị chặn.
- [ ] Có 5 điểm cần PO xác nhận, mỗi điểm có người hỏi và hạn trả lời.
- [ ] Nền tảng CI đã chọn và ghi lại.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Review | Người tham dự review PR biên bản | ≥ 2 người approve (Tech Lead + 1 dev) |
| Review | Đối chiếu bảng OQ với BRD §12 và SDD §6.2 | Không thiếu OQ đang `Open` có ảnh hưởng tới task |
| Theo dõi | Sprint review Sprint 0 | Trạng thái từng OQ được cập nhật trong biên bản |

## 8. Cấu hình

Không thêm biến môi trường. Biên bản ghi rõ các giá trị `[Default]` đang dùng (`MAX_UPLOAD_MB=50`, `MAX_PAGES=500`, `RELEVANCE_THRESHOLD=0.30`, `EMBEDDING_DIM=384`, `AUTH_MODE=dev`, `AI_PROVIDER=fake`) và OQ sẽ thay thế chúng.

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| OQ-001 chưa có người phê duyệt | Không ai ký các quyết định kinh doanh | Ghi người phê duyệt tạm do Quản lý giao yêu cầu chỉ định |
| Đội thực tế khác §1.3 | Ước lượng sprint lệch | Giữ thứ tự sprint, giãn thời gian (§1.3) |
| Pháp chế chưa xem giấy phép thư viện PDF | Có thể phải đổi thư viện | Dùng `pypdfium2`; SP-03 so với `pdfminer.six` |
| Hạn OQ-006/OQ-018 trượt sau 2026-11-09 | T-208 dời sang sprint sau | Tiếp tục với `FakeLlm`/`DevIdentity` (§9.1) |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §1.2, §1.3, §4.3–§4.5, §5.1, §9
- [SAD](../../design/SAD.md) §6, §7, §8.2, §8.3
- [Blueprint_Design](../../design/Blueprint_Design.md) §6.1, §6.2
- [User_Stories](../../design/User_Stories.md) §10, §11
- [BRD](../../requirements/BRD.md) §12

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)) ở phần áp dụng được cho task quy trình (merge, review).
- [ ] Biên bản được gửi tới Sponsor/Business Owner kèm danh sách OQ.
