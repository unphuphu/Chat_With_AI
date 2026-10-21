# T-213 — Viết E2E Sprint 2 (AC-008…011, AC-016 và nửa hỏi đáp của AC-003, 004, 007)

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 2 |
| **Loại** | QA |
| **User story** | US-C1, US-C2, US-C3, US-C4, US-D1 (và US-A3, A4, B2 phần hỏi đáp) |
| **Ưu tiên** | P0 |
| **Ước lượng** | 2 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-209, T-210 |
| **Mở khóa (task chờ task này)** | — |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Có bộ Playwright chạy tự động trên `main` chứng minh **luồng** hỏi đáp đúng với `FakeLlm` có kịch bản: hỏi → tiến trình → câu trả lời có trích dẫn mở đúng trang (AC-008 luồng, AC-009, AC-010), "không tìm thấy" (AC-011), hội thoại mới không mang ngữ cảnh cũ (AC-016); và nửa hỏi đáp của AC-003, AC-004, AC-007 mà T-111 để lại.

## 2. Bối cảnh

- Implement_plan §7.2: AC-008/009 = CMP-17 (AI thật) **+ E2E luồng (FakeLlm)**; AC-010 = CMP-17 + unit validator + **E2E mở đúng trang**; AC-011 = CMP-17 + unit policy; AC-016 = E2E. Chất lượng nội dung (MET-002) **không** đo ở đây — thuộc T-211.
- T-111 đã dựng hạ tầng E2E: `frontend/tests/e2e/`, fixture `frontend/tests/fixtures/`, `deploy/.env.e2e` (`AI_PROVIDER=fake`, `AUTH_MODE=dev`), helper `loginAs`, `resetLibrary`, `waitForStatus`, lệnh `make e2e`. T-111 chỉ kiểm phần thư viện của AC-003, AC-004, AC-007 và chuyển phần hỏi đáp sang task này.
- `FakeLlm` (T-007) nhận tham số `script: Callable[[LlmPrompt], LlmAnswer]`; `FakeEmbedding` dùng feature hashing theo từ (câu hỏi trùng từ với chunk → cosine cao).

## 3. Phạm vi

**Trong phạm vi**
- Bộ nạp kịch bản `FakeLlm` từ tệp YAML (`FAKE_LLM_SCRIPT`) — chỉ cho dev/E2E.
- Fixture PDF có cụm từ đánh dấu duy nhất; spec Playwright `frontend/tests/e2e/sprint2/*.spec.ts`; helper hỏi đáp.
- Kiểm bất biến API song song với UI (đọc `GET /api/v1/conversations/{id}`).

**Ngoài phạm vi** (để tránh làm thừa)
- AC-012…015, AC-017, AC-019 (T-311). Trạng thái lỗi màn 05 B–F (T-307/T-311).
- Đo chất lượng câu trả lời với AI thật (T-211).

## 4. Thiết kế chi tiết

**Kịch bản FakeLlm** (`backend/app/adapters/fake/script.py` `[Proposed]`): `build_llm()` (T-007) khi `AI_PROVIDER=fake` và có `FAKE_LLM_SCRIPT` → `FakeLlm(script=load_script(path))`. Chỉ nạp khi `APP_ENV ∈ {dev, e2e}`; môi trường khác có biến này → lỗi khởi động.

```yaml
# deploy/e2e/fake_llm_script.yaml — quy tắc đầu tiên khớp (regex trên prompt.question, không phân biệt hoa thường)
- match: "ALPHA-7"
  mode: cite_containing          # trích mọi ref có text chứa keyword; không có → answerable=false
  keyword: "ALPHA-7"
- match: "so sánh chiết khấu"
  mode: cite_each_document       # ref đầu tiên của mỗi document khác nhau trong context
- match: "id lạ"
  mode: invalid_ids              # cited_chunk_ids=["c999"] cả hai lần → NOT_FOUND (Lớp 2)
- match: ".*"
  mode: cite_containing_any_marker   # mặc định: trích ref chứa một marker [A-Z]+-\d trùng với câu hỏi; không có → answerable=false
```

`content` sinh tự động: "Theo tài liệu, … [cN]." cho từng ref được trích (kiểm được việc thay `[cN]` → `[n]` ở T-205).

**Fixture** (thêm vào `frontend/tests/fixtures/`, sinh bằng `generate_fixtures.py` của T-111 `[Proposed]`):

| Tệp | Nội dung đánh dấu (trang) |
|---|---|
| `qa-alpha.pdf` (4 trang) | Trang 2: "Điều khoản thanh toán ALPHA-7: thanh toán 3 đợt 30% – 40% – 30%." ; trang 3: "Chính sách chiết khấu ALPHA: 5%." |
| `qa-beta.pdf` (3 trang) | Trang 3: "Lịch bàn giao BETA-3: bàn giao trong 45 ngày." ; trang 1: "Chính sách chiết khấu BETA: 7%." |
| `qa-gamma.pdf` (2 trang) | Trang 1: "Điều kiện bảo hành GAMMA-5: 24 tháng." (dùng cho AC-003, AC-007) |
| `scan-only.pdf` | Có sẵn từ T-111 (`NOT_EXTRACTABLE`) |

**Helper** (`frontend/tests/e2e/chat-helpers.ts`): `seedLibrary(request, files)` (tải lên qua API + chờ `READY`), `ask(page, text)` (gõ + Enter, chờ khối trả lời cuối), `lastAnswer(page)`, `citationChips(page)`, `getConversation(request, id)`.

**Kịch bản**

| Spec | AC | Bước | Khẳng định |
|---|---|---|---|
| `ask-flow.spec.ts` | AC-008 (luồng), US-C1 | MEMBER, thư viện có `qa-alpha`; `/chat` → hỏi "Điều khoản thanh toán ALPHA-7 là gì?" | Khối "Đang tìm trong tài liệu…" xuất hiện trước câu trả lời; sau đó có câu trả lời với ≥ 1 chip "qa-alpha.pdf · trang 2"; URL thành `/chat/:id`; thanh bên có hội thoại mới; tải lại trang → câu hỏi + câu trả lời + chip còn nguyên |
| `multi-doc.spec.ts` | AC-009 (luồng) | Thư viện `qa-alpha`, `qa-beta`; hỏi "So sánh chiết khấu ALPHA và BETA" | Chip thuộc **2** tài liệu khác nhau; API: `citations` có 2 `documentId` khác nhau |
| `citation-open.spec.ts` | AC-010 | Từ câu trả lời ở `ask-flow`: bấm số hiệu `[1]` trong văn bản; quay lại; bấm chip | Cả hai cách mở `/documents/{alphaId}/view?page=2&cite=1&message=…`; viewer hiện "Trang 2 / 4", tiêu đề "qa-alpha.pdf"; có nhãn "Đoạn được trích dẫn [1]" **hoặc** banner dự phòng (T-210) |
| `citation-invariant.spec.ts` | AC-010 (bất biến) | Sau mọi spec khác, đọc `GET /api/v1/conversations` + chi tiết | Mọi tin nhắn `ANSWERED` có `citations` ≥ 1; mọi `NOT_FOUND` có `citations` = 0 |
| `not-found.spec.ts` | AC-011 | Hỏi "Chính sách nghỉ phép năm là gì?" (không có trong thư viện) | Khối NOT_FOUND: viền nét đứt, tiêu đề "Không tìm thấy thông tin trong tài liệu", không có chip, có nút "Tải tài liệu lên" |
| `not-found.spec.ts` | AC-011 (Lớp 2) | Hỏi "id lạ ALPHA-7" (kịch bản `invalid_ids`) | NOT_FOUND dù có đoạn khớp từ khóa |
| `new-conversation.spec.ts` | AC-016 | Hội thoại 1: hỏi về ALPHA-7 → có trả lời; bấm "Hội thoại mới"; hỏi "Còn gói B thì sao?" | URL `/chat` rồi `/chat/:id2` (id2 ≠ id1); luồng chỉ có 1 cặp hỏi/đáp; câu trả lời là NOT_FOUND, không chip nào trỏ `qa-alpha.pdf`; API: hội thoại id2 chỉ có 2 tin nhắn |
| `ready-then-ask.spec.ts` | AC-003 (nửa hỏi đáp) | Thư viện có `qa-alpha`; tải `qa-gamma`, `waitForStatus("Sẵn sàng")`; hỏi "Điều kiện bảo hành GAMMA-5?" | Câu trả lời có chip "qa-gamma.pdf · trang 1" |
| `not-extractable-never-cited.spec.ts` | AC-004 (nửa hỏi đáp) | Thư viện `qa-alpha` + `scan-only.pdf` (`NOT_EXTRACTABLE`); hỏi 3 câu (ALPHA-7, chiết khấu, câu ngoài thư viện) | Không `citation.documentId` nào bằng id của `scan-only.pdf` (kiểm qua API); không chip nào mang tên tệp đó |
| `deleted-then-ask.spec.ts` | AC-007 (nửa hỏi đáp) | Thư viện `qa-alpha`, `qa-gamma`; hỏi GAMMA-5 → có chip gamma; xóa `qa-gamma` ở `/library`; hội thoại mới hỏi lại câu đó | Lần 2 là NOT_FOUND, không chip gamma; hội thoại cũ vẫn hiện chip "qa-gamma.pdf · trang 1" (snapshot); bấm chip cũ → viewer báo "đã bị xóa" |

**Quy ước:** chọn phần tử theo vai trò/nhãn; không `waitForTimeout` cố định; mỗi spec gọi `resetLibrary` ở `beforeEach` (trừ `citation-invariant`, chạy cuối với `test.describe.configure({ mode: 'serial' })`); thời gian chờ `READY` ≤ 120 s như T-111.

## 5. Các bước thực hiện

1. Viết `adapters/fake/script.py` (`load_script`, 4–5 chế độ trên) + test đơn vị backend; nối vào `build_llm()`.
2. Thêm `FAKE_LLM_SCRIPT=/app/deploy/e2e/fake_llm_script.yaml` và `APP_ENV=e2e` vào `deploy/.env.e2e`; mount tệp kịch bản vào container `api`.
3. Thêm 3 fixture PDF vào `generate_fixtures.py`; kiểm bằng T-104 rằng trang và văn bản trích ra chứa đúng cụm đánh dấu.
4. Viết `chat-helpers.ts` và 9 spec theo bảng.
5. Chạy `make e2e` local 3 lần liên tiếp để phát hiện flaky; sửa chờ đợi theo trạng thái.
6. Cập nhật bảng AC → spec trong `frontend/tests/e2e/README.md` (thêm AC-008…011, AC-016, nửa sau AC-003/004/007).

## 6. Tiêu chí chấp nhận

- [ ] 9 spec ở bảng mục 4 pass trong `make e2e` trên máy sạch và trong job CI `e2e` khi merge `main`.
- [ ] Bất biến: 100% tin nhắn `ANSWERED` sinh trong bộ E2E có ≥ 1 trích dẫn; 100% `NOT_FOUND` không có trích dẫn.
- [ ] Bấm số hiệu hoặc chip mở viewer đúng `documentId` và đúng `page` của trích dẫn (AC-010, 1 thao tác).
- [ ] Không câu trả lời nào trích tài liệu `NOT_EXTRACTABLE` hoặc tài liệu đã xóa (sau thời điểm xóa).
- [ ] Hội thoại mới có id khác và không chứa tin nhắn của hội thoại trước (AC-016).
- [ ] Chạy 3 lần liên tiếp không có spec flaky.
- [ ] Cấu hình `FAKE_LLM_SCRIPT` bị từ chối khi `APP_ENV` không phải `dev`/`e2e`.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit (backend) | `load_script`: `cite_containing` không ref nào chứa keyword | `answerable=False` |
| Unit (backend) | `cite_each_document` với context 2 tài liệu | 2 ref, mỗi tài liệu 1 |
| Unit (backend) | `FAKE_LLM_SCRIPT` + `APP_ENV=staging` | Lỗi khởi động |
| E2E | 9 spec ở bảng mục 4 | Như cột "Khẳng định" |
| E2E | Chạy lại toàn bộ với `--repeat-each=3` | Không flaky |

## 8. Cấu hình

| Biến | Giá trị E2E | Ghi chú |
|---|---|---|
| `AI_PROVIDER` | `fake` | Implement_plan §3.3 |
| `AUTH_MODE` | `dev` | |
| `FAKE_LLM_SCRIPT` | `/app/deploy/e2e/fake_llm_script.yaml` | `[Proposed]` biến mới, chỉ dev/E2E |
| `APP_ENV` | `e2e` | `[Proposed]` (T-006 đã dùng `APP_ENV=dev`) |
| `RELEVANCE_THRESHOLD` | `0.30` `[Default]` | Không hiệu chỉnh ở E2E |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| E2E với FakeLlm chỉ chứng minh luồng, không chứng minh chất lượng | AC-008, AC-009, AC-011 chưa nghiệm thu đầy đủ | Nghiệm thu chất lượng bằng CMP-17 (T-211) sau T-208 `[TBD: OQ-006, OQ-008]` |
| `FakeEmbedding` trùng từ phổ biến ("là", "gì") có thể vượt ngưỡng Lớp 1 | NOT_FOUND do Lớp 2 thay vì Lớp 1 | Kịch bản trả `answerable=false` khi không có marker → vẫn NOT_FOUND; spec chỉ khẳng định kết quả, không khẳng định lớp |
| Tô đoạn trên viewer có thể rơi vào dự phòng | `citation-open` không ổn định | Chấp nhận nhãn tô **hoặc** banner dự phòng; luôn khẳng định đúng trang |
| Đánh số trích dẫn theo tin nhắn khác ảnh thiết kế `[Proposed]` (T-205) | Ảnh so sánh lệch | Spec khẳng định theo `ordinal` của API |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §5.3 (T-213), §7.1, §7.2
- [SAD](../../design/SAD.md) §3.2.1, §3.1 (snapshot, trạng thái `READY`)
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.5 (bất biến API-09), §3.7
- [User_Stories](../../design/User_Stories.md) US-A3, US-A4, US-B2, US-C1…C4, US-D1
- Màn hình: [html_design/04_chat.html](../../design/html_design/04_chat.html), [html_design/05_chat_states.html](../../design/html_design/05_chat_states.html), [html_design/06_citation_viewer.html](../../design/html_design/06_citation_viewer.html)
- Task liên quan: [T-007](./T-007-ports-and-fake-adapters.md), [T-111](./T-111-e2e-sprint1.md), [T-205](./T-205-answer-service.md), [T-209](./T-209-chat-screen-core.md), [T-210](./T-210-citation-viewer-screen.md), [T-211](./T-211-eval-harness-v1.md), [T-311](./T-311-e2e-sprint3.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Bảng AC → spec trong `frontend/tests/e2e/README.md` có đủ AC-003 (hỏi đáp), AC-004 (hỏi đáp), AC-007 (hỏi đáp), AC-008…011, AC-016.
