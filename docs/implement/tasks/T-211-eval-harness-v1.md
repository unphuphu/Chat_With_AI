# T-211 — Xây bộ đánh giá chất lượng CMP-17 v1

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 2 |
| **Loại** | QA |
| **User story** | US-C1, US-C2, US-C3, US-C4 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 2 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-009, T-207 |
| **Mở khóa (task chờ task này)** | T-310 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Lệnh `python -m eval.run --base-url … --out eval/report.md` chạy toàn bộ `eval/questions.yaml` qua API thật của hệ thống và xuất báo cáo: **độ chính xác trích dẫn** (AC-010), **tỷ lệ "không tìm thấy" đúng** (AC-011), bảng **chấm thủ công** nội dung cho MET-002, và so sánh với lần chạy trước để phát hiện suy giảm.

## 2. Bối cảnh

- CMP-17 (Implement_plan §7.3; SAD §4.3 "Đánh giá chất lượng liên tục"): chạy hằng đêm và trước mỗi phát hành, mỗi khi đổi prompt, mô hình hay ngưỡng.
- AC-008…AC-011 chỉ kiểm được bằng bộ câu hỏi (Implement_plan §7.2); số liệu có ý nghĩa chỉ khi chạy với **AI thật** (sau T-208, `[TBD: OQ-006]`) và bộ câu hỏi chính thức (`[TBD: OQ-008]`). Với `FakeLlm`, bộ đánh giá chỉ chạy kiểm khói.
- Định dạng `eval/questions.yaml` do T-009 quy định (giữ đúng §7.3, thêm `tags`, `lang` tùy chọn).
- Đầu vào cho T-310 (hiệu chỉnh `RELEVANCE_THRESHOLD`, `k`).

## 3. Phạm vi

**Trong phạm vi**
- Gói `eval/` : CLI, client API (đăng nhập dev, tạo hội thoại, gọi SSE), chấm tự động, xuất báo cáo Markdown + JSON, so sánh baseline.
- Chỉ số phụ: tỷ lệ trích dẫn đủ ≥ 2 tài liệu cho câu `tags: [multi_doc]` (AC-009), thời gian phản hồi P50/P90.
- Job CI kiểm khói với `FakeLlm`; mẫu lịch chạy hằng đêm (bật khi có T-208).

**Ngoài phạm vi** (để tránh làm thừa)
- Soạn câu hỏi/đáp án (T-009). Chấm nội dung tự động bằng LLM (không có trong yêu cầu).
- Chọn ngưỡng/`k` (T-310). Đo hiệu năng có tải (T-309, k6/Locust).

## 4. Thiết kế chi tiết

**File:**

```text
eval/__init__.py
eval/run.py            # CLI (argparse), điều phối
eval/client.py         # EvalClient: login, create_conversation, ask (SSE)
eval/scoring.py        # thuần hàm, test được
eval/report.py         # Markdown + JSON
eval/tests/test_scoring.py, test_sse.py
eval/results/          # JSON từng lần chạy (gitignore) [Proposed]
```

**CLI:**

```text
python -m eval.run --base-url http://localhost:8080 --out eval/report.md
    [--questions eval/questions.yaml] [--baseline eval/results/<lần trước>.json]
    [--filter-tag multi_doc] [--concurrency 1] [--label "v1+fake"]
    [--min-citation-accuracy 0.95] [--min-not-found 0.95]
```

Mã thoát: `0` đạt; `1` dưới ngưỡng `--min-*` (dùng làm cổng phát hành); `2` lỗi hạ tầng (không đăng nhập được, > 10% câu lỗi).

**Client** — đăng nhập theo luồng dev của T-006: `GET /api/v1/auth/login?devSubject=<EVAL_DEV_SUBJECT>` theo chuyển hướng tới callback để nhận cookie `cwd_session`, rồi `GET /api/v1/auth/session` lấy `csrfToken`. Môi trường không phải dev: nhận cookie phiên qua `EVAL_SESSION_COOKIE` `[Proposed]`.
Mỗi câu hỏi: `POST /api/v1/conversations` (một hội thoại mới cho mỗi câu, để không có lịch sử) → `POST /api/v1/conversations/{id}/messages` với `{"question": …}` → đọc SSE (`httpx` stream, tách theo dòng trống) tới `final` hoặc `error`; đo thời gian từ lúc gửi tới `final`. Lỗi `429` → chờ theo `Retry-After` rồi thử lại tối đa 3 lần; `--concurrency` mặc định 1 để không vượt `RATE_LIMIT_QUESTIONS_PER_MIN`.

**Chấm tự động** (`scoring.py`):

```python
def norm_name(s: str) -> str        # NFC, casefold, gộp khoảng trắng
def citation_hit(final, sources) -> bool
    # True nếu answerType == "ANSWERED" và ∃ citation: norm_name(documentName) == norm_name(src.document)
    #   và citation.page ∈ src.pages
def covers_all_documents(final, sources) -> bool   # mọi tài liệu trong sources có ≥ 1 trích dẫn (AC-009)
```

| Chỉ số | Công thức | Mục tiêu |
|---|---|---|
| Độ chính xác trích dẫn | số câu `expect: answered` có `citation_hit` / số câu `expect: answered` | ≥ 95% (AC-010) |
| Đúng "không tìm thấy" | số câu `expect: not_found` trả `NOT_FOUND` / số câu `expect: not_found` (cần ≥ 20 câu) | ≥ 95% (AC-011) |
| "Không tìm thấy" sai | số câu `answered` nhận `NOT_FOUND` / số câu `answered` | theo dõi (đánh đổi ở T-310) |
| Đủ nguồn đa tài liệu | `covers_all_documents` trên câu `tags: [multi_doc]` | theo dõi (AC-009) |
| Bất biến BRU-003 | số `ANSWERED` có `citations` rỗng | **phải = 0** (lỗi nghiêm trọng nếu > 0) |
| Thời gian phản hồi | P50, P90 của `responseTimeMs` | đối chiếu `[TBD: OQ-014]` |
| Lỗi | số câu kết thúc bằng `error`/HTTP lỗi, theo mã | theo dõi |

Câu lỗi được loại khỏi mẫu số của hai chỉ số chính nhưng được liệt kê riêng.

**Báo cáo Markdown** (`--out`):
1. Thông tin chạy: thời gian UTC, `--label`, base URL, số câu, commit (`git rev-parse --short HEAD` nếu có), cấu hình do người chạy khai báo (nhà cung cấp AI, mô hình, `prompt_version`, `RELEVANCE_THRESHOLD`) qua `--label`/`--meta key=value` `[Proposed]` — bộ đánh giá không đọc cấu hình server.
2. Bảng chỉ số + trạng thái đạt/không đạt so với ngưỡng.
3. So với baseline (nếu có): chênh lệch từng chỉ số; danh sách câu **chuyển từ đạt sang không đạt** và ngược lại.
4. Bảng chi tiết tự động: `ID | expect | answerType | trích dẫn (tên · trang) | hit | thời gian`.
5. **Bảng chấm thủ công MET-002**: `ID | Câu hỏi | Câu trả lời | Trích dẫn | Đáp án chuẩn | Đạt/Không đạt | Ghi chú` — cột chấm để trống cho người PTKD điền (chỉ câu `answered`).

JSON (`eval/results/<UTC>.json`): toàn bộ kết quả từng câu + chỉ số, làm baseline cho lần sau.

**Bảo mật dữ liệu:** báo cáo chứa câu hỏi/câu trả lời → chỉ chạy trên tài liệu mẫu không nhạy cảm (T-009); `eval/report.md` và `eval/results/` trong `.gitignore` `[Proposed]`; artifact CI giữ 30 ngày `[Proposed]`; bộ đánh giá không ghi nội dung ra stdout ngoài tóm tắt chỉ số.

## 5. Các bước thực hiện

1. Viết `scoring.py` + test đơn vị (mục 7).
2. Viết bộ đọc SSE + test với luồng mẫu (cắt giữa khung, `\r\n`).
3. Viết `client.py` (đăng nhập dev, CSRF, hội thoại mới mỗi câu, xử lý `429`).
4. Viết `report.py` (Markdown + JSON) và so sánh baseline.
5. Viết `run.py` (CLI, mã thoát), đọc + kiểm `questions.yaml` bằng `eval/validate_questions.py` của T-009 trước khi chạy.
6. Thêm job CI `eval-smoke`: dựng compose với `AI_PROVIDER=fake`, `make seed`, chạy 5 câu, chỉ kiểm mã thoát ≠ 2 và báo cáo sinh ra; thêm mẫu job hằng đêm `eval-nightly` (tắt cho tới khi T-208 xong).
7. Viết `eval/README.md` ngắn: cách chạy, cách chấm thủ công, cách so baseline.

## 6. Tiêu chí chấp nhận

- [ ] `python -m eval.run --base-url http://localhost:8080 --out eval/report.md` chạy hết bộ câu hỏi trên môi trường local (FakeLlm) và tạo báo cáo đủ 5 phần ở mục 4 + tệp JSON.
- [ ] Hai chỉ số chính tính đúng theo công thức (kiểm bằng dữ liệu kết quả giả lập đã biết đáp số).
- [ ] Có `ANSWERED` với `citations` rỗng → báo cáo đánh dấu lỗi BRU-003 và mã thoát `1`.
- [ ] `--baseline` liệt kê đúng các câu thay đổi kết quả giữa hai lần chạy.
- [ ] Dưới ngưỡng `--min-citation-accuracy`/`--min-not-found` → mã thoát `1`; không đăng nhập được → `2`.
- [ ] Mỗi câu hỏi dùng hội thoại mới (kiểm qua `GET /api/v1/conversations`: số hội thoại tăng đúng bằng số câu).
- [ ] Job `eval-smoke` chạy trong CI và lưu báo cáo làm artifact.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `citation_hit`: đúng tài liệu, đúng trang | `True` |
| Unit | Đúng tài liệu, sai trang | `False` |
| Unit | Tên khác hoa thường/dạng Unicode (NFD) | `True` |
| Unit | `answerType = NOT_FOUND` với câu `answered` | `False`, tính vào "không tìm thấy sai" |
| Unit | `covers_all_documents` 2 nguồn, chỉ trích 1 | `False` |
| Unit | Tính P50/P90 với 10 giá trị | Đúng số |
| Unit | So baseline: Q001 đạt → không đạt | Xuất hiện trong danh sách suy giảm |
| Unit | Bộ đọc SSE: khung bị cắt, sự kiện `status` trước `final` | Trả `final` đúng |
| Integration | Chạy với FakeLlm, 5 câu | Báo cáo + JSON sinh ra, mã thoát 0 hoặc 1 |
| Integration | Server trả `429` một lần | Chờ và thử lại, câu không bị tính lỗi |

## 8. Cấu hình

| Biến / tham số | Mặc định | Ghi chú |
|---|---|---|
| `EVAL_DEV_SUBJECT` | `dev-member` | `[Proposed]` tài khoản dev của T-006 |
| `EVAL_SESSION_COOKIE` | — | `[Proposed]` cho staging; lấy từ secret của CI |
| `--min-citation-accuracy`, `--min-not-found` | `0.95`, `0.95` | Theo AC-010, AC-011 |
| Mục tiêu MET-002 | — | `[TBD: OQ-007]`; BA đề xuất ≥ 85% (BRD BO-002) — chỉ hiển thị, không làm cổng tự động |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Chưa có AI thật `[TBD: OQ-006]` | Số liệu với FakeLlm không phản ánh chất lượng | Chỉ chạy kiểm khói; bật `eval-nightly` sau T-208 |
| Bộ câu hỏi chính thức chưa có `[TBD: OQ-008]`, cần ≥ 20 câu `not_found` cho AC-011 | Chưa nghiệm thu được AC-008…011 | Dùng bộ tạm của QA (T-009); báo cáo ghi rõ "bộ tạm" |
| So khớp theo tên tài liệu: đổi tên tệp khi nạp lại sẽ lệch | Hit sai | `norm_name` + kiểm tên trong `documents.yaml` (T-009) trước khi chạy |
| Báo cáo chứa nội dung tài liệu | Rò rỉ nếu dùng tài liệu nhạy cảm | Chỉ dùng tài liệu được duyệt; không commit báo cáo |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §7.1, §7.2, §7.3, §8 (launch gate)
- [SAD](../../design/SAD.md) §4.3 (đánh giá liên tục), §7 SP-04
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.6.4 (tham số cần hiệu chỉnh)
- [User_Stories](../../design/User_Stories.md) US-C1…C4
- Task liên quan: [T-009](./T-009-sample-docs-and-eval-questions.md), [T-006](./T-006-auth-session-dev-identity.md), [T-207](./T-207-messages-sse-api.md), [T-208](./T-208-real-ai-adapters-reindex.md), [T-310](./T-310-threshold-calibration.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Một báo cáo mẫu (chạy với FakeLlm) được đính kèm PR để BA/QA duyệt định dạng bảng chấm thủ công.
