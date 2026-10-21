# T-009 — Thu thập bộ PDF mẫu (DEP-001) và soạn bộ câu hỏi kiểm thử `eval/questions.yaml`

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 0 (tiếp tục tới hết Sprint 2) |
| **Loại** | QA |
| **User story** | US-C1, US-C2, US-C3, US-C4 (dữ liệu kiểm chứng) |
| **Ưu tiên** | P0 |
| **Ước lượng** | liên tục `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-000 |
| **Mở khóa (task chờ task này)** | T-111, T-211, T-310 |
| **Người thực hiện** | _chưa giao_ (QA + BA, phối hợp đội PTKD) |
| **Trạng thái** | To do |

## 1. Mục tiêu

Đội có (1) bộ PDF mẫu không nhạy cảm (hoặc đã ẩn thông tin) phục vụ phát triển, `make seed`, fixture kiểm thử và SP-03; (2) tệp `eval/questions.yaml` đúng định dạng [Implement_plan §7.3](../Implement_plan.md#73-bộ-đánh-giá-cmp-17) với **≥ 30 câu hỏi có đáp án và trang nguồn, trong đó ≥ 20 câu `not_found`**, trước cuối Sprint 2, để CMP-17 đo AC-008…AC-011.

## 2. Bối cảnh

- DEP-001 (bộ PDF mẫu) và OQ-008 (ai soạn bộ câu hỏi, bao nhiêu câu) do Business Owner phụ trách, hạn OQ-008 2026-11-06 ([BRD §10, §12](../../requirements/BRD.md)). Không có chúng thì không kiểm chứng được AC-008…AC-011.
- AC-011 yêu cầu ≥ 20 câu không có đáp án trong thư viện, ≥ 95% trả "không tìm thấy"; AC-010 ≥ 95% trích dẫn đúng tài liệu + trang; AC-009 câu hỏi có đáp án ở ≥ 2 tài liệu.
- Dữ liệu thật **không** dùng ở `dev`; `staging` dùng bộ mẫu/đã ẩn thông tin ([Blueprint §3.8](../../design/Blueprint_Design.md#38-resource--deployment-view)).
- Chất lượng câu trả lời đo bằng CMP-17 với AI thật, hằng đêm và trước phát hành ([Implement_plan §7.1](../Implement_plan.md#71-tầng-kiểm-thử)); hiệu chỉnh ngưỡng ở [T-310](./T-310-threshold-calibration.md).

## 3. Phạm vi

**Trong phạm vi**
- Danh mục tài liệu mẫu `eval/documents.yaml` `[Proposed]` và nơi lưu tệp.
- ≥ 5 PDF cho `make seed`; 20–30 PDF giao cho SP-03 ([T-008](./T-008-spike-sp03-pdf-extraction.md)).
- Fixture cho E2E Sprint 1 (`backend/tests/fixtures/`): PDF hợp lệ, PDF scan, `.docx`, `.jpg`, `.xlsx`, tệp vượt giới hạn.
- `eval/questions.yaml` theo định dạng mục 4; hướng dẫn soạn và chấm.
- `eval/validate_questions.py` `[Proposed]` kiểm định dạng (chạy trong CI).

**Ngoài phạm vi**
- Script chạy đánh giá `python -m eval.run` và báo cáo ([T-211](./T-211-eval-harness-v1.md)).
- Chọn giá trị mục tiêu MET-002 `[TBD: OQ-007]`; hiệu chỉnh ngưỡng ([T-310](./T-310-threshold-calibration.md)).
- Test hiệu năng AC-012 ([T-309](./T-309-spike-sp01-latency.md)).

## 4. Thiết kế chi tiết

**Tệp**

```text
eval/documents.yaml              # [Proposed] danh mục tài liệu mẫu
eval/questions.yaml              # bộ câu hỏi (định dạng §7.3)
eval/validate_questions.py       # [Proposed] kiểm định dạng
eval/GUIDE.md                    # hướng dẫn soạn câu hỏi + chấm thủ công (ngắn)
eval/docs/                       # PDF không nhạy cảm (được phép commit); tệp nhạy cảm ở kho hạn chế quyền
backend/tests/fixtures/          # tệp nhỏ cho test tự động
```

**`eval/documents.yaml`** `[Proposed]`:

```yaml
- file: "Hợp đồng khung đối tác A.pdf"
  pages: 24
  sha256: "…"
  sensitivity: public | anonymized | internal     # internal → không commit, không dùng ở dev
  source: "Đội PTKD — đã ẩn tên đối tác"
  approved_by: "<tên Business Owner>"
  groups: [A, B]                                   # nhóm SP-03 (T-008)
  seed: true                                       # nạp bằng make seed
```

**`eval/questions.yaml`** — trường bắt buộc giữ đúng §7.3; trường `[Proposed]` là tùy chọn để T-211 lọc theo AC:

```yaml
- id: Q001
  question: "Điều kiện thanh toán trong hợp đồng khung với đối tác A là gì?"
  expect: answered
  sources: [{ document: "Hợp đồng khung đối tác A.pdf", pages: [12] }]
  reference_answer: "3 đợt: 30% khi ký, 40% khi nghiệm thu GĐ1, 30% trong 30 ngày sau nghiệm thu cuối"
  tags: [multi_doc]        # [Proposed] multi_doc (AC-009) | table | follow_up_seed
  lang: vi                 # [Proposed] cho AC-015, giá trị theo OQ-009
- id: Q101
  question: "Chính sách bảo hành sản phẩm X là bao lâu?"
  expect: not_found
```

**Quy tắc định dạng** (kiểm bởi `validate_questions.py`):

| Quy tắc | Chi tiết |
|---|---|
| `id` | duy nhất; `Q001–Q099` cho `answered`, `Q101–Q199` cho `not_found` (theo ví dụ §7.3) |
| `expect` | `answered` hoặc `not_found` |
| `answered` | bắt buộc `sources` (≥ 1 phần tử, `pages` ≥ 1 số nguyên) và `reference_answer` không rỗng |
| `not_found` | **không** có `sources`, `reference_answer` |
| `sources.document` | trùng `file` trong `documents.yaml`; mọi `page` ∈ [1, `pages`] |
| `tags: [multi_doc]` | `sources` có ≥ 2 tài liệu khác nhau |
| Mã hóa | UTF-8, tiếng Việt dạng NFC |

**Hướng dẫn soạn (`eval/GUIDE.md`)**
- Câu `answered`: lấy từ nội dung thật của tài liệu mẫu; ghi **mọi** trang chứa thông tin; người soạn mở trang để xác nhận. Ưu tiên câu người dùng PTKD thực sự hỏi (giá, điều khoản, thời hạn, phạm vi).
- Câu `not_found`: hợp lý về chủ đề nhưng **không** có trong thư viện mẫu — gồm (a) chủ đề vắng mặt hoàn toàn, (b) "gần đúng" (đối tác/sản phẩm khác tên với tài liệu có thật), (c) chi tiết không có dù tài liệu cùng chủ đề có mặt. Người thứ hai xác nhận bằng tìm kiếm toàn văn trên bộ mẫu.
- Không đưa thông tin cá nhân hoặc bí mật kinh doanh vào câu hỏi/đáp án.
- Bảng chấm thủ công MET-002: người PTKD chấm "đạt/không đạt" nội dung so với `reference_answer` (T-211 xuất bảng).

**Fixture E2E Sprint 1** (`backend/tests/fixtures/`, mỗi tệp ≤ 1 MB trừ tệp giới hạn):

| Tệp | Dùng cho |
|---|---|
| `valid_1.pdf`, `valid_2.pdf`, `valid_3.pdf` (văn bản tiếng Việt, 2–5 trang, nội dung tự soạn) | AC-001, AC-003, AC-006, AC-007 |
| `scan_only.pdf` (chỉ ảnh) | AC-004 |
| `sample.docx`, `sample.jpg`, `sample.xlsx` | AC-002 |
| `fake_pdf.pdf` (đuôi `.pdf`, nội dung không bắt đầu bằng `%PDF-`) | kiểm chữ ký tệp (T-103) |
| Tệp ở đúng giới hạn và vượt 1 MB / 1 trang: **sinh bằng script lúc chạy test** theo `MAX_UPLOAD_MB`, `MAX_PAGES` (không commit tệp lớn) | AC-005 |

**Mốc** `[Proposed]`:

| Thời điểm | Kết quả |
|---|---|
| Cuối Sprint 0 | `documents.yaml` + ≥ 5 PDF seed; fixture Sprint 1; 20–30 PDF giao T-008; định dạng YAML được Tech Lead + QA duyệt; ≥ 10 câu nháp |
| Cuối Sprint 1 | ≥ 20 câu (≥ 10 `not_found`), có ít nhất 3 câu `multi_doc` |
| Cuối Sprint 2 | **≥ 30 câu, ≥ 20 `not_found`**, đã qua review người thứ hai; T-211 chạy được |

## 5. Các bước thực hiện

1. Gặp Business Owner (OQ-008): xác nhận người soạn, số câu tối thiểu, nguồn PDF, mức ẩn thông tin cho phép.
2. Thu thập PDF; phân loại `sensitivity`; ẩn thông tin khi cần; ghi `documents.yaml`.
3. Chọn ≥ 5 PDF `seed: true`; giao 20–30 PDF (đủ nhóm A–H) cho T-008.
4. Tạo fixture Sprint 1 và script sinh tệp giới hạn.
5. Viết `validate_questions.py` + thêm bước vào CI (job `backend-test` hoặc job riêng).
6. Soạn câu hỏi theo hướng dẫn; mỗi câu có người soạn và người xác nhận (ghi trong PR).
7. Review định kỳ mỗi sprint; cập nhật mốc trong biên bản T-000.

## 6. Tiêu chí chấp nhận

- [ ] `eval/documents.yaml` liệt kê mọi PDF mẫu với `sensitivity`, `approved_by`; không tệp `internal` nào nằm trong repo.
- [ ] `make seed` có ≥ 5 PDF để nạp (dùng từ Sprint 1).
- [ ] Fixture mục 4 có mặt trong `backend/tests/fixtures/`, script sinh tệp giới hạn chạy được.
- [ ] `python eval/validate_questions.py` exit 0 trên tệp hiện tại; vi phạm bất kỳ quy tắc ở bảng → exit ≠ 0 kèm id câu lỗi.
- [ ] Trước cuối Sprint 2: ≥ 30 câu, ≥ 20 `expect: not_found`, mỗi câu `answered` có `sources` và `reference_answer`; ≥ 3 câu `multi_doc`.
- [ ] 100% câu đã được người thứ hai xác nhận (trang nguồn mở được, câu `not_found` không có trong bộ mẫu).

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `validate_questions.py` với id trùng | exit 1, nêu id |
| Unit | Câu `answered` thiếu `sources` / trang > `pages` | exit 1 |
| Unit | Câu `not_found` có `sources` | exit 1 |
| Unit | `multi_doc` chỉ 1 tài liệu | exit 1 |
| Review | Mở ngẫu nhiên 20% câu `answered` và đối chiếu trang | 100% đúng |
| CI | Job kiểm `questions.yaml` | Chạy mỗi PR đổi `eval/` |

## 8. Cấu hình

Không có biến ứng dụng. Script sinh fixture đọc `MAX_UPLOAD_MB=50`, `MAX_PAGES=500` `[Default]` (giá trị thật theo **OQ-013**). Trường `lang` theo **OQ-009**.

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Chưa có người soạn/nguồn PDF `[TBD: OQ-008]` | Không đo được AC-008…AC-011 | QA soạn bộ tạm từ PDF mẫu (Implement_plan §9.1); không hiệu chỉnh ngưỡng chính thức |
| 30 câu với ≥ 20 `not_found` chỉ còn ~10 câu `answered` | Tỷ lệ AC-010 ≥ 95% ít ý nghĩa thống kê với ~10 câu | Đề nghị Business Owner tăng số câu `answered` (quyết định ở OQ-008); không tự đổi mục tiêu |
| Tài liệu thật nhạy cảm | Lộ dữ liệu ở dev/repo | Chỉ `public/anonymized` vào repo; `internal` chỉ ở staging sau OQ-006 |
| Ngân sách thời gian DEP-001 `[TBD: OQ-005]` | Trễ mốc | Báo trạng thái ở mỗi sprint review |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §3.2 (`make seed`), §7.1, §7.2, §7.3, §9.1
- [SAD](../../design/SAD.md) §4.3 (đánh giá chất lượng liên tục), §7 (SP-03, SP-04)
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.8 (môi trường và dữ liệu)
- [User_Stories](../../design/User_Stories.md) US-C1…US-C4
- [BRD](../../requirements/BRD.md) AC-001…AC-011, DEP-001, OQ-008

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)) ở phần áp dụng được (merge, CI xanh).
- [ ] Business Owner xác nhận bằng văn bản bộ câu hỏi dùng cho CMP-17 (ghi tên và ngày trong `eval/GUIDE.md`).
