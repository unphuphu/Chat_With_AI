# T-310 — Hiệu chỉnh `RELEVANCE_THRESHOLD` và `k` bằng bộ đánh giá CMP-17

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 3 |
| **Loại** | QA |
| **User story** | US-C1, US-C4 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 1,5 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-009, T-211, OQ-008 |
| **Mở khóa (task chờ task này)** | T-410 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do ⛔ (chờ OQ-008) |

## 1. Mục tiêu

Chọn giá trị `RELEVANCE_THRESHOLD`, `RETRIEVAL_K` (và `MAX_CHUNKS_PER_DOC` nếu cần) dựa trên số đo trên bộ câu hỏi kiểm thử thật, thay cho `[Default]` 0,30 / 8 / 3. Kết quả trình bày dưới dạng bảng đánh đổi "bịa ↔ không tìm thấy sai" để **Business Owner chọn** điểm cân bằng; Tech Lead áp dụng vào cấu hình staging.

## 2. Bối cảnh

- Lớp 1 `NotFoundPolicy`: trả `NOT_FOUND` không gọi LLM nếu điểm vector tốt nhất < `relevance_threshold` **và** không có khớp từ khóa ([SAD §3.2.1](../../design/SAD.md) bước 9; [Implement_plan §6.6](../Implement_plan.md#66-điều-phối-trả-lời)).
- [Blueprint §3.6.4](../../design/Blueprint_Design.md): `relevance_threshold`, `k`, giới hạn mỗi tài liệu **phải hiệu chỉnh bằng bộ câu hỏi kiểm thử** (`[TBD: OQ-008]`) qua CMP-17; "tăng ngưỡng giảm bịa (AC-011) nhưng có thể tăng 'không tìm thấy' sai (giảm MET-002); đây là đánh đổi chính… cần Business Owner chọn". DR-02.
- Mục tiêu: AC-010 ≥ 95% trích dẫn đúng; AC-011 ≥ 95% trên ≥ 20 câu không có đáp án; MET-002 `[TBD: OQ-007]` (BA đề xuất ≥ 85%) — [Implement_plan §8](../Implement_plan.md#8-launch-gate-điều-kiện-lên-production).
- Bộ đánh giá `eval/` (T-211), định dạng `eval/questions.yaml` [Implement_plan §7.3](../Implement_plan.md#73-bộ-đánh-giá-cmp-17).
- **OQ-008** (ai soạn bộ câu hỏi, bao nhiêu câu) chặn việc hiệu chỉnh chính thức; khi chưa có chỉ chạy thử trên bộ tạm của QA ([Implement_plan §9.1](../Implement_plan.md#91-quyết-định-cần-có-và-ảnh-hưởng-tới-lập-trình)).

## 3. Phạm vi

**Trong phạm vi**
- Chế độ "quét tham số" cho CMP-17: đo lớp 1 offline nhanh, rồi chạy đầy đủ cho vài cấu hình ứng viên.
- Bảng kết quả + biểu đồ đánh đổi + khuyến nghị; buổi trình bày với Business Owner; ghi quyết định.
- Cập nhật giá trị cấu hình staging theo quyết định (qua Tech Lead).

**Ngoài phạm vi** (để tránh làm thừa)
- Soạn bộ câu hỏi (T-009/đội PTKD).
- Đổi prompt, mô hình, cách chia chunk (task riêng; nếu đổi phải chạy lại task này).
- Chấm thủ công MET-002 cho mọi cấu hình (chỉ chấm cấu hình ứng viên cuối).

## 4. Thiết kế chi tiết

### 4.1 Điều kiện tiên quyết

| Điều kiện | Lý do |
|---|---|
| Bộ câu hỏi theo OQ-008: ≥ 30 câu `answered` có `sources`, ≥ 20 câu `not_found` | AC-010, AC-011 |
| **Embedding thật** (T-208) cho cả thư viện và câu hỏi | Ngưỡng phụ thuộc phân bố điểm của mô hình; với `FakeEmbedding` con số vô nghĩa |
| LLM thật cho bước chạy đầy đủ (§4.3) | Lớp 2 và nội dung |
| Thư viện thử = bộ PDF mẫu (DEP-001) ở trạng thái `READY` | Khớp `sources` |

Nếu thiếu T-208: chỉ chạy thử quy trình (dry-run) với adapter giả để kiểm script, **không** đưa ra khuyến nghị.

### 4.2 Bước A — quét lớp 1 offline (nhanh, không gọi LLM)

Script `python -m eval.calibrate --base-url … --out eval/calibration/` `[Proposed]`:

1. Với mỗi câu hỏi: gọi truy xuất (endpoint/hàm nội bộ chỉ bật ở môi trường đánh giá `[Proposed]`, hoặc import trực tiếp `RetrievalService` trong tiến trình) với `kv` lớn (50) → ghi `best_vector_score`, `has_text_match`, danh sách `(document, page, score, rank)`. Không ghi văn bản chunk.
2. Với mỗi ngưỡng `t ∈ {0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50}` `[Proposed]` (thang điểm cosine `1 - distance`; điều chỉnh dải theo phân bố quan sát được):
   - `refuse(q) = best_vector_score < t and not has_text_match`.
   - **Chặn đúng** = % câu `not_found` bị lớp 1 từ chối.
   - **Chặn sai** = % câu `answered` bị lớp 1 từ chối.
3. Với mỗi `k ∈ {4, 6, 8, 10}` và `MAX_CHUNKS_PER_DOC ∈ {2, 3}`: **recall nguồn@k** = % câu `answered` có ≥ 1 chunk trùng `sources` (tài liệu + trang) trong top-k sau RRF.
4. Xuất histogram `best_vector_score` tách theo `answered` / `not_found` — cơ sở trực quan cho Business Owner.

### 4.3 Bước B — chạy đầy đủ CMP-17 cho 3–4 cấu hình ứng viên

Chọn từ bước A: (1) ngưỡng thấp nhất đạt chặn đúng ≥ 95%, (2) ngưỡng có chặn sai thấp nhất mà vẫn để lớp 2 xử lý, (3) mặc định hiện tại 0,30/8/3, (4) tùy chọn. Mỗi cấu hình: khởi động lại API với biến môi trường tương ứng, chạy `python -m eval.run` (T-211), ghi:

| Chỉ số | Định nghĩa | Mục tiêu |
|---|---|---|
| Đúng "không tìm thấy" (AC-011) | % câu `not_found` trả `NOT_FOUND` (lớp 1 **hoặc** lớp 2) | ≥ 95% |
| Không tìm thấy sai | % câu `answered` trả `NOT_FOUND` | Càng thấp càng tốt — Business Owner chọn mức chấp nhận |
| Độ chính xác trích dẫn (AC-010) | % câu `answered` có ≥ 1 trích dẫn trùng `sources` | ≥ 95% |
| MET-002 (chấm thủ công, chỉ cấu hình cuối) | % câu đúng nội dung **và** trích dẫn đúng | `[TBD: OQ-007]` |
| Tỉ lệ gọi LLM | % câu vượt lớp 1 | Chi phí/độ trễ |
| P90 `responseTimeMs` | | Tham khảo T-309 / `[TBD: OQ-014]` |

### 4.4 Bảng kết quả bàn giao

`eval/calibration/report-<YYYYMMDD>.md`:

```markdown
| Cấu hình | threshold | k | max/doc | AC-011 | Không tìm thấy sai | AC-010 | Gọi LLM | P90 (s) | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|
| C1 | 0.35 | 8 | 3 | 97% | 12% | 96% | 71% | 9.8 | ít bịa nhất |
| C2 | 0.25 | 8 | 3 | 95% | 5% | 96% | 83% | 10.4 | cân bằng |
```

(Số trong ví dụ là minh họa.) Kèm: histogram điểm, danh sách id câu hỏi bị "không tìm thấy sai" và id câu "bịa" (trả `ANSWERED` cho câu `not_found`) để đội PTKD xem lại — chỉ id và đường dẫn câu hỏi trong `questions.yaml`, không chép câu trả lời vào log.

### 4.5 Quyết định

- **Người quyết định: Business Owner** (theo Blueprint §3.6.4, SAD §8.3 điều kiện 4). QA + Tech Lead trình bày; khuyến nghị kỹ thuật được ghi rõ là khuyến nghị.
- Ghi quyết định (cấu hình chọn, lý do, ngày, người duyệt) ở đầu `report-<ngày>.md` và cập nhật giá trị vào cấu hình staging; giá trị mặc định trong `.env.example` giữ nhãn `[Default]` tới khi launch gate.
- Mọi thay đổi prompt/mô hình/chunking sau đó → chạy lại bước A + B (so sánh với lần trước, Implement_plan §7.3).

## 5. Các bước thực hiện

1. Kiểm điều kiện tiên quyết §4.1; nếu thiếu OQ-008/T-208 thì chỉ dry-run và ghi trạng thái ⛔.
2. Viết `eval/calibrate.py` (bước A) dùng lại client/định dạng của T-211.
3. Chạy bước A, xuất bảng + histogram; chọn 3–4 ứng viên.
4. Chạy bước B cho từng ứng viên; đội PTKD chấm MET-002 cho ứng viên dẫn đầu.
5. Viết `report-<ngày>.md`; họp với Business Owner; ghi quyết định.
6. Tech Lead cập nhật cấu hình staging; chạy lại CMP-17 một lần trên staging để xác nhận.

## 6. Tiêu chí chấp nhận

- [ ] `eval/calibrate.py` chạy được bằng một lệnh và xuất bảng bước A cho ≥ 8 ngưỡng × 4 giá trị `k`.
- [ ] Bảng bước B có ≥ 3 cấu hình với đủ các cột §4.4, chạy trên embedding + LLM thật.
- [ ] Cấu hình được chọn đạt AC-011 ≥ 95% (≥ 20 câu `not_found`) và AC-010 ≥ 95% trên bộ OQ-008 — hoặc báo cáo nêu rõ không cấu hình nào đạt và đề xuất bước tiếp theo.
- [ ] Quyết định của Business Owner được ghi (tên, ngày, cấu hình) trong báo cáo.
- [ ] Giá trị mới được áp dụng ở staging và một lần chạy CMP-17 xác nhận cho kết quả trong ±2 điểm % so với bước B.
- [ ] Báo cáo và log không chứa văn bản chunk hoặc câu trả lời.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | Hàm `refuse(score, has_text, t)` khớp `NotFoundPolicy.should_refuse` | Kết quả giống hệt trên 100 bộ ngẫu nhiên (dùng chính lớp domain, không viết lại) |
| Unit | Tính chặn đúng/chặn sai trên bộ 4 câu giả | Đúng tỉ lệ |
| Integration | Bước A dry-run với FakeEmbedding trên 5 câu | Xuất file đúng định dạng |
| Hồi quy | Chạy lại bước B với cùng cấu hình | Chênh ≤ 2 điểm % (độ ổn định LLM) |

## 8. Cấu hình

| Biến | `[Default]` hiện tại | Dải thử |
|---|---|---|
| `RELEVANCE_THRESHOLD` | `0.30` | 0,15–0,50 bước 0,05 `[Proposed]` |
| `RETRIEVAL_K` | `8` | 4, 6, 8, 10 |
| `MAX_CHUNKS_PER_DOC` | `3` | 2, 3 |
| `RETRIEVAL_KV`, `RETRIEVAL_KT` | `20`, `20` | Giữ nguyên (bước A dùng 50 để quan sát) |

Giá trị thật quyết định bởi Business Owner dựa trên báo cáo này (OQ-008 cho dữ liệu, OQ-007 cho mục tiêu MET-002).

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| OQ-008 chưa chốt | Không hiệu chỉnh chính thức | Dry-run trên bộ tạm của QA; không đổi cấu hình |
| Chưa có embedding/LLM thật (OQ-006, T-208) | Ngưỡng không có ý nghĩa | Đánh dấu ⛔; lên lịch ngay khi T-208 xong |
| Bộ câu hỏi nhỏ (30 + 20) | Sai số lớn (1 câu = 2–5 điểm %) | Báo khoảng tin cậy; khuyến nghị bổ sung câu hỏi |
| Mục tiêu MET-002 `[TBD: OQ-007]` | Không kết luận "đạt" | Báo số đo; Sponsor chốt mục tiêu |
| Lớp 1 dùng cả khớp từ khóa → ngưỡng ít tác dụng khi câu hỏi chứa từ phổ biến | AC-011 phụ thuộc lớp 2 | Báo riêng tỉ lệ chặn của lớp 1 và lớp 2 |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §3.3, §5.4, §6.6, §7.3, §8, §9.1
- [SAD](../../design/SAD.md) §3.2.1 bước 8–11, §4.3 (đánh giá liên tục), §8.3
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.6.4, DR-02
- [User_Stories](../../design/User_Stories.md) US-C1, US-C4
- Task liên quan: [T-009](./T-009-sample-docs-and-eval-questions.md), [T-204](./T-204-notfound-policy-citation-validator.md), [T-208](./T-208-real-ai-adapters-reindex.md), [T-211](./T-211-eval-harness-v1.md), [T-309](./T-309-spike-sp01-latency.md), [T-410](./T-410-launch-gate-uat.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)) ở phần áp dụng được (script được review và merge).
- [ ] Quyết định của Business Owner được lưu cùng báo cáo trong repo.
