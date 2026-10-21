# T-008 — Chạy spike SP-03: chất lượng trích văn bản PDF và ngưỡng NOT_EXTRACTABLE

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 0 |
| **Loại** | Spike |
| **User story** | US-A3, US-A4 (đầu vào kỹ thuật) |
| **Ưu tiên** | P0 |
| **Ước lượng** | 1,5 ngày-người `[Estimate]` (timebox, không kéo dài) |
| **Phụ thuộc (phải xong trước)** | T-000 |
| **Mở khóa (task chờ task này)** | T-104 |
| **Người thực hiện** | _chưa giao_ (BE) |
| **Trạng thái** | To do |

## 1. Mục tiêu

Trả lời bằng số đo câu hỏi của SP-03 ([SAD §7](../../design/SAD.md#7-spike-cần-chạy-trước-khi-chốt-rủi-ro-kỹ-thuật-chưa-kiểm-chứng)): thư viện trích văn bản nào (`pypdfium2` hay `pdfminer.six`) đủ tốt cho PDF thật (tiếng Việt có dấu, bảng, nhiều cột), quy tắc chuẩn hóa văn bản nào cần, và **ngưỡng cụ thể** để `has_meaningful_text()` gán `NOT_EXTRACTABLE`. Kết quả ghi trong `docs/implement/spikes/SP-03.md` để T-104 cài đặt không phải đoán.

## 2. Bối cảnh

- Rủi ro RSK-003/DR-05: bảng biểu/PDF phức tạp mất cấu trúc ([Blueprint §6.3](../../design/Blueprint_Design.md#63-rủi-ro-thiết-kế)); OCR ngoài phạm vi MVP.
- SAD §2.2 bước 3 đề xuất ngưỡng `NOT_EXTRACTABLE`: tổng ký tự có nghĩa < 50/tài liệu **hoặc** < 10% số trang có văn bản `[Proposed]`; bước 4–5: chuẩn hóa NFC, chunk trong trang ~300–500 token, chồng lấp ~50.
- Implement_plan §1.2 chọn `pypdfium2`; **không** PyMuPDF (AGPL) trừ khi Pháp chế duyệt. Phương án dự phòng là `pdfminer.six` ([Implement_plan §9.2](../Implement_plan.md#92-rủi-ro-kỹ-thuật)).
- AC-004: PDF chỉ chứa ảnh scan → báo "không thể truy vấn" và không bao giờ được trích dẫn.
- OQ-010 (tỷ lệ PDF scan/bảng biểu) chưa có; spike cung cấp dữ liệu quan sát cho BA.

## 3. Phạm vi

**Trong phạm vi**
- Bộ mẫu 20–30 PDF, phân loại theo bảng mục 4.
- So sánh `pypdfium2` và `pdfminer.six` trên cùng bộ mẫu.
- Đo: đúng dấu tiếng Việt, tỷ lệ lỗi ký tự, thứ tự đọc nhiều cột, giữ nội dung bảng, thời gian/bộ nhớ, lỗi/crash.
- Phân bố số ký tự có nghĩa mỗi trang → đề xuất ngưỡng.
- Chạy thử chia chunk trong trang (400 token, chồng 50) và quan sát.
- Báo cáo `SP-03.md` + script spike.

**Ngoài phạm vi**
- OCR; xử lý bảng thành cấu trúc; code sản xuất của `ingest_document` ([T-104](./T-104-ingest-worker.md)).
- Đánh giá PyMuPDF (chỉ ghi lý do loại trừ).
- Chọn mô hình embedding (SP-04).

## 4. Thiết kế chi tiết

**Sản phẩm**
- `docs/implement/spikes/SP-03.md` — báo cáo.
- `backend/scripts/spikes/sp03_extract.py` `[Proposed]` — script đo, không import vào `app/`; đầu ra `sp03_results.csv` (không commit nếu chứa trích đoạn tài liệu nhạy cảm).
- Bản chép tay đối chiếu (ground truth) chỉ cho các đoạn mẫu, lưu cùng nơi lưu bộ mẫu (không đưa nội dung nhạy cảm vào repo).

**Bộ mẫu** (ưu tiên lấy từ DEP-001 do [T-009](./T-009-sample-docs-and-eval-questions.md) thu thập; nếu chưa có, dùng PDF công khai/không nhạy cảm cùng loại — dữ liệu thật **không** dùng ở dev):

| Nhóm | Số tệp tối thiểu | Mục đích |
|---|---|---|
| A. Văn bản tiếng Việt một cột (hợp đồng, báo giá) | 6 | Dấu, NFC, ngắt dòng |
| B. Có bảng (báo giá, phụ lục giá) | 5 | Nội dung ô bảng có còn đọc được |
| C. Hai cột / bố cục phức tạp | 3 | Thứ tự đọc |
| D. Scan thuần ảnh | 3 | Phải ra `NOT_EXTRACTABLE` |
| E. Hỗn hợp (một số trang scan) | 2 | Quy tắc theo tỉ lệ trang |
| F. Tiếng Anh / song ngữ | 2 | Phụ thuộc OQ-009 |
| G. Lớn (≥ 300 trang) | 1 | Thời gian, bộ nhớ, timeout 120 s |
| H. Bất thường: hỏng, có mật khẩu, PDF tạo bằng font nhúng lạ | 2 | Hành vi lỗi (`FAILED` hay `NOT_EXTRACTABLE`) |

**Phương pháp**
1. Với mỗi tệp × mỗi thư viện: trích theo trang trong tiến trình con có timeout 120 s (như SAD AD-09); ghi thời gian, bộ nhớ đỉnh (`resource.getrusage`), ngoại lệ.
2. Chuẩn hóa ứng viên: NFC, bỏ ký tự điều khiển (trừ `\n`), gộp dòng bị ngắt giữa câu, bỏ gạch nối cuối dòng; đo trước/sau.
3. Chọn 2 trang/tệp nhóm A–C, chép tay đoạn ~300 ký tự làm chuẩn; tính **CER** (character error rate, Levenshtein/độ dài) và **tỷ lệ lỗi dấu** (ký tự có dấu sai hoặc tách tổ hợp NFD).
4. Nhóm B: chấm thủ công thang 1–3 (1 = mất ô/lẫn cột, 2 = đủ chữ nhưng lẫn thứ tự, 3 = đọc được theo hàng).
5. Nhóm C: thứ tự đọc đúng/sai mỗi trang.
6. Mọi trang: đếm `meaningful_chars` = số ký tự chữ/số sau chuẩn hóa (bỏ khoảng trắng, dấu câu). Vẽ phân bố cho trang scan và trang văn bản → chọn ngưỡng tách hai nhóm.
7. Chia chunk thử: `split_within_page(text, page_no, target_tokens=400, overlap=50)` với bộ đếm token xấp xỉ `[Proposed: số từ × 1,3]`; ghi số chunk/trang, chunk rỗng, chunk quá ngắn.

**Chỉ số và ngưỡng đạt** `[Proposed]` — chốt trong báo cáo:

| Chỉ số | Mục tiêu đề xuất để chọn thư viện |
|---|---|
| CER nhóm A | ≤ 2% |
| Tỷ lệ lỗi dấu nhóm A | ≤ 1% ký tự có dấu |
| Bảng nhóm B | điểm trung bình ≥ 2 |
| Nhóm D phát hiện đúng | 100% |
| Crash/treo | 0 (timeout xử lý được) |
| Thời gian | P90 ≤ 0,5 s/trang `[Estimate]` |

**Quyết định đầu ra bắt buộc trong `SP-03.md`**

```markdown
# SP-03 — Kết quả trích văn bản PDF
## 1. Bộ mẫu (bảng nhóm A–H, số tệp, số trang, nguồn — không ghi nội dung nhạy cảm)
## 2. Kết quả theo thư viện (bảng chỉ số × pypdfium2 / pdfminer.six)
## 3. Quyết định
- D1 Thư viện: pypdfium2 | pdfminer.six (+ lý do, giấy phép, phiên bản ghim)
- D2 Quy tắc has_meaningful_text: MIN_CHARS_PER_PAGE = <n>; tài liệu NOT_EXTRACTABLE khi
       tổng meaningful_chars < <n1> HOẶC tỉ lệ trang có văn bản < <p>%
- D3 Danh sách bước normalize() theo thứ tự
- D4 Tham số chunk khởi đầu (target_tokens, overlap) và bộ đếm token tạm
- D5 Ánh xạ lỗi: PDF hỏng/mật khẩu → FAILED hay NOT_EXTRACTABLE (đề xuất, PO xác nhận)
- D6 Giới hạn tài nguyên tiến trình con (timeout, bộ nhớ)
## 4. Hạn chế đã biết cần báo PO (ví dụ bảng phức tạp) và dữ liệu cho OQ-010
## 5. Việc cho T-104
```

## 5. Các bước thực hiện

1. Nhận bộ mẫu từ T-009 (hoặc tự tạo bộ công khai); lập bảng phân nhóm.
2. Viết `sp03_extract.py` (CLI: `--lib pypdfium2|pdfminer --in <dir> --out <csv>`), chạy trong tiến trình con có timeout.
3. Chạy cả hai thư viện; thu CSV.
4. Chép tay đoạn chuẩn, tính CER/lỗi dấu; chấm bảng, thứ tự đọc.
5. Vẽ/tổng hợp phân bố `meaningful_chars`; chọn ngưỡng; kiểm lại trên nhóm D, E.
6. Chạy thử chunk; ghi quan sát.
7. Viết `SP-03.md` theo mẫu, review với Tech Lead; chuyển D1–D6 cho T-104.

## 6. Tiêu chí chấp nhận

- [ ] `SP-03.md` tồn tại, đủ 5 mục và quyết định D1–D6, mỗi quyết định có số liệu dẫn chứng.
- [ ] Bộ mẫu ≥ 20 tệp, có ít nhất 1 tệp cho mỗi nhóm A–H.
- [ ] Bảng kết quả có đủ 6 chỉ số cho cả hai thư viện.
- [ ] Ngưỡng D2 phân loại đúng 100% tệp nhóm D và không gán nhầm `NOT_EXTRACTABLE` cho tệp nhóm A–C nào.
- [ ] Không có nội dung tài liệu nhạy cảm trong repo (gitleaks xanh, review thủ công).
- [ ] Tech Lead approve báo cáo.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Thực nghiệm | Tệp scan (nhóm D) với ngưỡng đề xuất | Phân loại `NOT_EXTRACTABLE` |
| Thực nghiệm | Tệp nhóm E (vài trang scan) | Không `NOT_EXTRACTABLE` nếu tỉ lệ trang có chữ ≥ ngưỡng; trang scan chỉ không có chunk |
| Thực nghiệm | Tệp ≥ 300 trang | Hoàn tất < 120 s hoặc timeout được bắt, không treo worker |
| Thực nghiệm | Tệp có mật khẩu/hỏng | Ngoại lệ được bắt, ghi phân loại lỗi |
| Review | So chuỗi NFC trước/sau chuẩn hóa | Không còn ký tự tổ hợp NFD |

## 8. Cấu hình

Không thêm biến vào ứng dụng ở task này. Báo cáo đề xuất tên biến cho T-104 `[Proposed]`: `EXTRACT_MIN_CHARS_PER_PAGE`, `EXTRACT_MIN_DOC_CHARS` (khởi điểm 50 theo SAD), `EXTRACT_MIN_PAGE_RATIO` (khởi điểm 0,10), `PDF_EXTRACT_TIMEOUT_S` (120). Liên quan `MAX_PAGES=500` `[Default]` (**OQ-013**).

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Chưa có PDF thật (DEP-001, OQ-008) | Kết luận kém đại diện | Dùng PDF công khai cùng loại; chạy lại script khi có bộ thật |
| Hạn SP-03 trong SAD là 2026-11-13, nhưng T-104 (Sprint 1) cần sớm hơn | T-104 phải đoán ngưỡng | Timebox 1,5 ngày trong Sprint 0; T-104 dùng ngưỡng SAD `[Proposed]` nếu báo cáo trễ |
| Cả hai thư viện kém với bảng | Câu trả lời về giá sai | Báo PO, ghi hạn chế; cảnh báo tài liệu chất lượng thấp là đề xuất cần PO duyệt (không tự thêm) |
| Tỷ lệ PDF scan cao `[TBD: OQ-010]` | Nhiều tài liệu không dùng được | Cung cấp số đo cho BA để quyết định OCR giai đoạn sau |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §1.2, §5.1, §6.4, §9.2
- [SAD](../../design/SAD.md) §2.2 (quy trình ingest), §4.1.4, §6, §7 (SP-03), AD-09
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.4 (DD-04), §6.3 (DR-05)
- [User_Stories](../../design/User_Stories.md) US-A3, US-A4
- [BRD](../../requirements/BRD.md) AC-004, OQ-010, DEP-001

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)) ở phần áp dụng được cho spike (merge báo cáo, review).
- [ ] Các quyết định D1–D6 được chép vào mục "Thiết kế chi tiết" của [T-104](./T-104-ingest-worker.md) trước khi T-104 bắt đầu.
