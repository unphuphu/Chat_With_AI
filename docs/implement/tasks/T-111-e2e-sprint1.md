# T-111 — Viết kiểm thử E2E Playwright cho Sprint 1 (AC-001…AC-007, AC-018)

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 1 |
| **Loại** | QA |
| **User story** | US-A1, US-A2, US-A3, US-A4, US-A5, US-B1, US-B2, US-E1 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 2 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-107, T-108, T-009 |
| **Mở khóa (task chờ task này)** | — |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Mỗi AC của Sprint 1 có ít nhất một kịch bản Playwright chạy trên toàn bộ hệ thống (proxy + API + Worker + PostgreSQL + MinIO, `AI_PROVIDER=fake`) và chạy tự động mỗi lần merge vào `main`; demo cuối sprint ([plan §5.2](../Implement_plan.md#52-sprint-1--đăng-nhập--thư-viện-us-e1-a1a5-b1-b2)) được tái hiện bằng test.

## 2. Bối cảnh

- AC → loại kiểm thử: [plan §7.2](../Implement_plan.md#72-ac--loại-kiểm-thử) (AC-001…007: E2E + tích hợp; AC-018: test route tự động + E2E).
- Nguyên văn AC: BRD (AC-001…AC-007, AC-018) và Given-When-Then trong [User_Stories](../../design/User_Stories.md) US-A1…A5, B1, B2, E1.
- Tài liệu mẫu không nhạy cảm: DEP-001 / [T-009](./T-009-sample-docs-and-eval-questions.md). Màn hình: 01, 02, 03, 09.
- Route kiểm 401 ở mức API đã có ở [T-109](./T-109-route-auth-guard-test.md); ở đây kiểm hành vi người dùng.

## 3. Phạm vi

**Trong phạm vi**
- Bộ Playwright `frontend/tests/e2e/sprint1/*.spec.ts`, fixture tại `frontend/tests/fixtures/` (đúng ghi chú "dùng PDF mẫu trong `tests/fixtures`").
- Script dựng/dọn dữ liệu: đăng nhập dev theo vai trò, xóa sạch thư viện trước mỗi tệp spec.
- Job CI `e2e` chạy khi merge `main` với `docker compose` + cấu hình E2E.
- Chụp ảnh màn hình khi lỗi, lưu artifact CI.

**Ngoài phạm vi**
- Nửa sau của AC-003, AC-004, AC-007 cần **đặt câu hỏi** (luồng hỏi đáp Sprint 2) → bổ sung ở [T-213](./T-213-e2e-sprint2.md); ở đây kiểm phần thư viện + kiểm gián tiếp bằng API (mục 4).
- So sánh ảnh pixel (QA so thủ công theo DoD).
- Hiệu năng.

## 4. Thiết kế chi tiết

**Fixture** (`frontend/tests/fixtures/`, mọi tệp không chứa dữ liệu thật)

| Tệp | Mô tả |
|---|---|
| `text-a.pdf`, `text-b.pdf`, `text-c.pdf` | PDF văn bản 2–5 trang (lấy từ bộ T-009) |
| `scan-only.pdf` | PDF chỉ chứa ảnh |
| `report.docx`, `photo.jpg`, `sheet.xlsx` | Không phải PDF |
| `fake.pdf` | Nội dung DOCX đổi đuôi `.pdf` (sai magic) |
| `at-limit.pdf`, `over-limit.pdf` | Đúng `MAX_UPLOAD_MB` / vượt 1 MB (đệm bằng comment PDF) |
| `at-pages.pdf`, `over-pages.pdf` | Đúng `MAX_PAGES` / vượt 1 trang |
| `generate_fixtures.py` | Sinh 4 tệp giới hạn theo cấu hình E2E (không commit tệp lớn) `[Proposed]` |

**Cấu hình E2E** (`deploy/.env.e2e` `[Proposed]`): `AI_PROVIDER=fake`, `AUTH_MODE=dev`, `MAX_UPLOAD_MB=2`, `MAX_PAGES=5` — giới hạn nhỏ để fixture nhẹ, giá trị thật vẫn `[TBD: OQ-013]`.

**Helper** (`frontend/tests/e2e/helpers.ts`): `loginAs(page, role)` qua màn 01 (DevIdentity), `resetLibrary(request)` (xóa mọi tài liệu qua API bằng tài khoản ADMIN), `waitForStatus(page, name, text, timeoutMs)`.

**Kịch bản**

| Spec | AC | Bước | Khẳng định |
|---|---|---|---|
| `upload-multiple.spec.ts` | AC-001 | MEMBER chọn `text-a/b/c.pdf` cùng lúc | Khay có 3 thanh tiến trình; bảng có 3 dòng mới trạng thái "Đang xử lý" hoặc "Sẵn sàng" |
| `reject-non-pdf.spec.ts` | AC-002 | Chọn `report.docx`, `photo.jpg`, `sheet.xlsx`; rồi `fake.pdf` | Mỗi tệp một dòng khay chứa "chỉ chấp nhận định dạng PDF"; bảng không có tên các tệp này; `GET /api/v1/documents` không chứa chúng |
| `status-ready.spec.ts` | AC-003 | Tải `text-a.pdf`, chờ | Badge "Sẵn sàng" có biểu tượng tick trong ≤ 120 s, không tải lại trang; `GET /documents/{id}` → `READY`, `pageCount` > 0 |
| `not-extractable.spec.ts` | AC-004 | Tải `scan-only.pdf`, chờ; tải lại trang | Badge "Không thể truy vấn" + "PDF chỉ chứa ảnh scan nên chưa thể dùng để trả lời." vẫn hiện sau tải lại; API `NOT_EXTRACTABLE` (tài liệu không phải `READY` ⇒ không được truy xuất) |
| `limits.spec.ts` | AC-005 | Màn 02/03 hiển thị giới hạn; tải `at-limit.pdf`, `over-limit.pdf`, `at-pages.pdf`, `over-pages.pdf` | Dòng giới hạn hiện "2 MB" và "5 trang"; tệp đúng giới hạn được chấp nhận; `over-limit` bị từ chối nêu "2 MB"; `over-pages` hiển thị lỗi nêu "5 trang" trên dòng tài liệu `[Proposed — theo T-104]` |
| `library-columns.spec.ts` | AC-006 | Tải 3 PDF bằng 2 người dùng khác nhau | 100% dòng có tên, người tải lên (đúng tên hiển thị), ngày tải `dd/mm/yyyy`, trạng thái |
| `delete.spec.ts` | AC-007 | Bấm xóa dòng `READY` → kiểm hộp thoại → Esc → mở lại → "Xóa tài liệu" | Hộp thoại nêu tên; focus đầu ở "Hủy"; Esc đóng và trả focus; xác nhận → dòng biến mất, toast "Đã xóa", bộ đếm giảm 1; tải lại trang vẫn không còn; `GET /documents/{id}` → `404` |
| `empty-library.spec.ts` | AC-005, US-A5 | `resetLibrary`, mở `/library` | Màn 03: "Bắt đầu bằng việc tải tài liệu lên", 3 bước, mục "Hỏi đáp" `aria-disabled="true"` |
| `auth-guard.spec.ts` | AC-018 | Ngữ cảnh trình duyệt không cookie mở `/library`, `/chat`, `/history` | Chuyển tới `/login`; DOM không chứa tên tài liệu fixture nào |
| `auth-guard.spec.ts` | AC-018 | `request` không cookie gọi `GET/POST /api/v1/documents`, `DELETE /api/v1/documents/{uuid}` | `401`, `error.code = UNAUTHENTICATED` |
| `auth-guard.spec.ts` | AC-018 | Đăng nhập dev bằng tài khoản không được cấp quyền | Bị từ chối (màn 01 biến thể "Tài khoản chưa được cấp quyền" hoặc `/error/403`), không vào được thư viện |
| `auth-guard.spec.ts` | AC-018 | SPONSOR mở `/library` | Thấy bảng nhưng không có vùng tải lên/nút xóa; `DELETE` qua API → `403` |

**Quy ước**
- Chọn phần tử theo vai trò/nhãn truy cập (`getByRole('button', { name: 'Xóa text-a.pdf' })`), không theo lớp CSS.
- Không `waitForTimeout` cố định; dùng `expect.poll`/`toHaveText` với timeout.
- Mỗi spec độc lập, gọi `resetLibrary` ở `beforeEach`.

## 5. Các bước thực hiện

1. Thêm Playwright vào `frontend/` (`@playwright/test`, Chromium), `playwright.config.ts` với `baseURL=http://localhost:8080`, `retries: 1` trên CI, `trace: 'on-first-retry'`.
2. Tạo fixture + `generate_fixtures.py`; lấy 3 PDF văn bản từ bộ T-009.
3. Tạo `deploy/.env.e2e` và lệnh `make e2e` (dựng compose, migrate, seed người dùng dev MEMBER/SPONSOR/ADMIN/không quyền, chạy Playwright).
4. Viết helper và từng spec theo bảng.
5. Thêm job CI `e2e` (khi merge `main`), lưu báo cáo HTML + ảnh lỗi.
6. Ghi trong `frontend/tests/e2e/README.md` bảng AC → spec (truy vết cho T-410).

## 6. Tiêu chí chấp nhận

- [ ] Có ít nhất 1 spec xanh cho mỗi AC: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-018.
- [ ] `make e2e` chạy từ máy sạch (sau `make up`) và hoàn tất < 10 phút.
- [ ] Job CI `e2e` chạy tự động khi merge vào `main`; lỗi làm đỏ pipeline, có artifact trace/ảnh.
- [ ] Chạy 3 lần liên tiếp không có test chập chờn (flaky).
- [ ] Không fixture nào chứa tài liệu nội bộ thật (QA xác nhận).
- [ ] Phần AC phụ thuộc hỏi đáp (AC-003, AC-004, AC-007 nửa sau) được ghi rõ là chuyển sang T-213.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| E2E | 12 kịch bản ở mục 4 | Xanh |
| E2E | Chạy song song 2 worker Playwright | Không xung đột dữ liệu (mỗi worker một người dùng dev riêng) |
| E2E (tự kiểm) | Cố tình bỏ CSRF trong client (nhánh thử) | `delete.spec.ts` đỏ — chứng minh test bắt được hồi quy |

## 8. Cấu hình

| Biến | Giá trị E2E | Ghi chú |
|---|---|---|
| `AI_PROVIDER` | `fake` | Không gọi AI thật |
| `AUTH_MODE` | `dev` | DevIdentity |
| `MAX_UPLOAD_MB`, `MAX_PAGES` | `2`, `5` `[Proposed]` | Chỉ cho E2E; thật **`[TBD: OQ-013]`** |
| `E2E_BASE_URL` | `http://localhost:8080` `[Proposed]` | |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Nửa sau AC-003/004/007 cần hỏi đáp | AC chưa đóng hoàn toàn ở Sprint 1 | Chuyển sang T-213; ghi rõ trong README truy vết |
| AC-005 phần số trang phụ thuộc cách T-104 báo lỗi (`[Proposed]`) | Spec có thể phải đổi | Cập nhật khi PO xác nhận |
| "Không nằm trong danh sách được cấp quyền" phụ thuộc DevIdentity (T-006) | Khó tạo tài khoản | Seed một người dùng dev không vai trò |
| Worker chậm trên CI | Spec AC-003 hết giờ | Timeout 120 s (QAS-02); `FakeEmbedding` |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §5.2, §7.1, §7.2, §8
- [SAD](../../design/SAD.md) §4.1.1
- [User_Stories](../../design/User_Stories.md) US-A1…A5, US-B1, US-B2, US-E1
- Màn hình: [01_login.html](../../design/html_design/01_login.html), [02_library.html](../../design/html_design/02_library.html), [03_library_empty.html](../../design/html_design/03_library_empty.html), [09_access_denied.html](../../design/html_design/09_access_denied.html)
- Task liên quan: [T-107](./T-107-library-screen.md), [T-108](./T-108-empty-library-screen.md), [T-109](./T-109-route-auth-guard-test.md), [T-009](./T-009-sample-docs-and-eval-questions.md), [T-213](./T-213-e2e-sprint2.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Bảng AC → spec trong `frontend/tests/e2e/README.md` được cập nhật.
