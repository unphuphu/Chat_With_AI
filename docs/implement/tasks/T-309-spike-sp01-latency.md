# T-309 — Spike SP-01: đo độ trễ luồng hỏi và chọn cách lọc phạm vi

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 3 |
| **Loại** | Spike |
| **User story** | US-C5 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 2 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-203, T-205 (ưu tiên có T-208) |
| **Mở khóa (task chờ task này)** | T-410 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Có số đo thực P50/P90 của từng bước luồng hỏi ở quy mô ~10⁵ chunk, và quyết định có căn cứ về cách truy xuất khi lọc phạm vi (quét lặp HNSW hay quét chính xác). Kết quả ghi trong `docs/implement/spikes/SP-01.md`, dùng để Business Owner chốt **OQ-014** và để chỉnh `k`/ngưỡng.

## 2. Bối cảnh

- SP-01 ([SAD §7](../../design/SAD.md)): "Độ trễ thực của luồng hỏi (từng bước) và chất lượng truy xuất ở ~10⁵ chunk có lọc phạm vi; chọn quét lặp hay quét chính xác". Chặn: OQ-014, AD-05, giá trị `k`, ngưỡng.
- Ngân sách `[Estimate]` [SAD §3.2.1](../../design/SAD.md): tổng ≈ 4–13 s, mục tiêu nội bộ P90 ≤ 15 s (QAS-01) — "nằm sát biên".
- Lọc phạm vi: HNSW có thể trả < `kv` dòng → `SET LOCAL hnsw.ef_search = 100`; nếu thiếu → quét lặp (`hnsw.iterative_scan`, pgvector ≥ 0.8 `[Verify]`) hoặc quét chính xác khi phạm vi hẹp ([Implement_plan §6.5](../Implement_plan.md#65-truy-xuất-lai)).
- AD-05 điều kiện xem lại: truy xuất P95 > 500 ms ở quy mô thật.
- Không có T-208 (OQ-006 chưa chốt) → đo phần CSDL bằng `FakeEmbedding` và **giả lập** độ trễ AI; số đo AI thật bổ sung khi có T-208.

## 3. Phạm vi

**Trong phạm vi**
- Script nạp dữ liệu tổng hợp ~10⁵ chunk.
- Đo từng bước: `rewrite`, `embed`, `retrieve_vector`, `retrieve_text`, `rrf+neighbors`, `generate`, `validate`, `persist`, tổng (đầu-cuối từ phía client).
- Thí nghiệm lọc phạm vi: 3 chế độ × 4 độ rộng phạm vi; đo độ trễ **và** recall.
- Đo dưới tải 1 và 10 người dùng đồng thời.
- Báo cáo `SP-01.md` với khuyến nghị và đòn bẩy nếu P90 > 15 s.

**Ngoài phạm vi** (để tránh làm thừa)
- Tối ưu code sản phẩm (chỉ đề xuất; thay đổi làm trong task riêng).
- Chọn nhà cung cấp/mô hình AI (SP-04, OQ-006).
- Kiểm thử AC-012 chính thức (T-311, T-410).

## 4. Thiết kế chi tiết

### 4.1 Sản phẩm bàn giao

| Sản phẩm | Đường dẫn |
|---|---|
| Báo cáo | `docs/implement/spikes/SP-01.md` |
| Script nạp dữ liệu | `eval/perf/seed_chunks.py` `[Proposed]` |
| Script đo truy xuất | `eval/perf/bench_retrieval.py` `[Proposed]` |
| Kịch bản tải đầu-cuối | `eval/perf/ask_load.js` (k6) hoặc `locustfile.py` `[Proposed]` |
| Dữ liệu thô | `eval/perf/results/SP-01-<ngày>.csv` (không chứa nội dung tài liệu thật) |

### 4.2 Dữ liệu thử

- **Quy mô:** 500 tài liệu × ~200 chunk ≈ 100.000 chunk (SAD §0.1: ≤ ~500 tài liệu, ≤ ~100 trang).
- **Văn bản:** lấy chunk thật từ bộ PDF mẫu (DEP-001, T-009), nhân bản có xáo trộn câu + thay số/tên để tạo 500 tài liệu giả; trạng thái `READY`; thêm 5% chunk thuộc tài liệu `DELETED` để kiểm lọc.
- **Vector:** cùng `EMBEDDING_DIM` với mô hình dự kiến. Có T-208 → embed thật (theo lô); không có → `FakeEmbedding` **cộng nhiễu nhỏ quanh vector của chunk gốc** để giữ cấu trúc cụm (vector ngẫu nhiên đều cho kết quả HNSW lạc quan sai).
- Chỉ mục HNSW `m=16`, `ef_construction=64` (SAD §2.3); ghi lại thời gian dựng chỉ mục và dung lượng.
- Bộ câu hỏi: ≥ 50 câu từ `eval/questions.yaml` (T-009) + câu nối tiếp để kích hoạt `rewrite`.

### 4.3 Phương pháp đo độ trễ

1. Bật span OTel/metric `answer_pipeline_duration_seconds{stage}` và `upstream_request_duration_seconds` (T-305); nếu T-404 chưa có, ghi `time.perf_counter()` theo bước vào log debug **không chứa nội dung**.
2. Đầu-cuối: client đo từ lúc gửi `POST` tới khi nhận `final` (so với `responseTimeMs` trong `final`).
3. Mỗi cấu hình chạy ≥ 200 lượt hỏi; bỏ 10 lượt khởi động; báo P50, P90, P95, max.
4. Tải: 1 người dùng tuần tự; 10 người dùng đồng thời (`MAX_CONCURRENT_AI_REQUESTS` ≥ 10, nâng giới hạn tốc độ trong môi trường đo).
5. Không có AI thật: thay `rewrite`/`generate` bằng `FakeLlm` có độ trễ giả lập phân bố log-normal quanh trung vị 1 s / 6 s `[Proposed]` (khớp ngân sách SAD) — ghi rõ trong báo cáo là **ước lượng**.
6. Môi trường: ghi cấu hình máy (CPU, RAM, phiên bản PostgreSQL/pgvector, `shared_buffers`, `work_mem`).

### 4.4 Thí nghiệm lọc phạm vi

Độ rộng phạm vi: **1 tài liệu**, **3 tài liệu**, **10% thư viện (50)**, **không lọc**.

| Chế độ | Cài đặt |
|---|---|
| (a) HNSW thường | `SET LOCAL hnsw.ef_search = 100` |
| (b) Quét lặp | (a) + `SET LOCAL hnsw.iterative_scan = relaxed_order` (thử cả `strict_order`), `hnsw.max_scan_tuples` mặc định `[Verify]` |
| (c) Quét chính xác | Lọc trước theo `document_id = ANY(:scope)` rồi sắp theo khoảng cách không dùng chỉ mục HNSW (vd. CTE `MATERIALIZED` hoặc `SET LOCAL enable_indexscan = off` trong giao dịch) |

Mỗi ô đo: độ trễ P50/P90 của truy vấn (a) vector, **tỉ lệ truy vấn trả < `kv`**, **recall@kv** so với (c) làm chuẩn. Truy vấn full-text (GIN) đo riêng cho cùng phạm vi.

### 4.5 Quy tắc quyết định `[Proposed]`

- Chọn chế độ mặc định có recall@kv ≥ 0,95 và P90 truy xuất ≤ 300 ms (ngân sách SAD bước 8) ở mọi độ rộng.
- Nếu (c) đạt ngân sách khi phạm vi ≤ X chunk mà (a)/(b) không đạt recall → đề xuất quy tắc lai: `số chunk trong phạm vi ≤ X` → quét chính xác, ngược lại → quét lặp. Ghi giá trị X đề xuất và cấu hình `[Proposed]` để T-203 áp dụng.
- AD-05 cần xem lại nếu P95 truy xuất > 500 ms ở 10⁵ chunk.

### 4.6 Mẫu báo cáo `SP-01.md`

```markdown
# SP-01 — Độ trễ luồng hỏi & lọc phạm vi
## Tóm tắt (≤ 5 dòng): P90 đầu-cuối = … s (AI thật | giả lập); đề xuất OQ-014 = …; chế độ lọc = …
## Môi trường & dữ liệu
## Bảng 1 — Độ trễ theo bước (ms): stage | P50 | P90 | P95 | % tổng
## Bảng 2 — Lọc phạm vi: chế độ | phạm vi | P50 | P90 | % trả < kv | recall@kv
## Bảng 3 — Tải đồng thời: người dùng | P50 | P90 | lỗi | 429
## Quyết định & cấu hình đề xuất (k, ef_search, chế độ lọc, X)
## Đòn bẩy nếu P90 > 15 s (đã thử / ước tính tác động)
## Giới hạn của phép đo; việc cần đo lại khi có T-208
```

### 4.7 Đòn bẩy nếu P90 > 15 s (thứ tự SAD §3.2.1)

1. Mô hình nhỏ cho `rewrite` (`LLM_REWRITE_MODEL`).
2. Giảm `RETRIEVAL_K` (8 → 6 → 4) — đo ảnh hưởng chất lượng bằng CMP-17 (T-310).
3. Rút ngắn ngữ cảnh: bỏ đoạn kề, giảm `MAX_CHUNKS_PER_DOC`.
4. Mô hình sinh nhanh hơn.

Với mỗi đòn bẩy đã thử: ghi độ trễ trước/sau; với đòn bẩy chưa thử: ước tính tác động từ bảng 1.

## 5. Các bước thực hiện

1. Dựng môi trường đo riêng (không dùng dữ liệu nhạy cảm); ghi cấu hình máy.
2. Viết `seed_chunks.py`, nạp ~10⁵ chunk, dựng chỉ mục, ghi thời gian/dung lượng.
3. Viết `bench_retrieval.py`, chạy ma trận §4.4, xuất CSV.
4. Chạy tải đầu-cuối 1 và 10 người dùng qua API-09 (SSE), xuất CSV.
5. Nếu có T-208: lặp bước 4 với AI thật trên ≥ 2 mô hình (SAD §7 "thử 2–3 mô hình").
6. Viết `SP-01.md` theo §4.6; review với Tech Lead.
7. Trình bày cho Business Owner: phân phối thời gian thực để chốt OQ-014; tạo ticket cho thay đổi cấu hình/code được đề xuất.

## 6. Tiêu chí chấp nhận

- [ ] `SP-01.md` có đủ 3 bảng §4.6, nêu rõ số nào đo với AI thật, số nào giả lập.
- [ ] Dữ liệu thử ≥ 95.000 chunk `READY`, có chunk `DELETED` và không chunk `DELETED` nào xuất hiện trong kết quả.
- [ ] Có P50/P90 cho mỗi bước trong 8 bước §3 và cho tổng đầu-cuối, ở 1 và 10 người dùng đồng thời.
- [ ] Ma trận lọc phạm vi đủ 3 chế độ × 4 độ rộng, có recall@kv so với quét chính xác.
- [ ] Có một khuyến nghị duy nhất về chế độ lọc (kèm X nếu lai) và giá trị `k`, `hnsw.ef_search` đề xuất.
- [ ] Có đề xuất giá trị cho OQ-014 kèm phân phối (vd. "90% ≤ 11 s"), và danh sách đòn bẩy nếu P90 > 15 s.
- [ ] Script nằm trong repo, chạy lại được bằng một lệnh ghi trong `SP-01.md`.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Kiểm tra dữ liệu | Đếm `chunk` theo trạng thái tài liệu sau seed | ≈ 95% `READY`, 5% `DELETED` |
| Kiểm tra truy xuất | 50 truy vấn có phạm vi = 1 tài liệu | Mọi kết quả thuộc tài liệu đó |
| Kiểm tra đo | So `responseTimeMs` với thời gian client | Chênh ≤ vài trăm ms (chi phí mạng/SSE) |
| Lặp lại | Chạy lại ma trận §4.4 lần 2 | P90 lệch ≤ 15% so với lần 1 |

## 8. Cấu hình

Thử các giá trị: `RETRIEVAL_KV`, `RETRIEVAL_KT` (`20`), `RETRIEVAL_K` (`8`, `6`, `4`), `MAX_CHUNKS_PER_DOC` (`3`, `2`), `EMBEDDING_DIM` theo mô hình; tham số phiên `hnsw.ef_search` (80, 100, 200), `hnsw.iterative_scan`. Môi trường đo nâng `RATE_LIMIT_QUESTIONS_PER_MIN` và `MAX_CONCURRENT_AI_REQUESTS` để không bị 429. Không thay cấu hình staging/prod trong spike.

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Chưa có AI thật (OQ-006) | Phần lớn độ trễ (bước 10) chỉ là giả lập | Báo cáo tách rõ; đo lại khi có T-208 trước T-410 |
| Ngưỡng thời gian `[TBD: OQ-014]` | Không kết luận đạt/không đạt AC-012 | Đưa phân phối số đo cho Business Owner chọn |
| Dữ liệu tổng hợp khác dữ liệu thật | Recall/độ trễ sai lệch | Dùng văn bản thật nhân bản + vector có cấu trúc; ghi giới hạn |
| Phiên bản pgvector trên dịch vụ quản lý có thể < 0.8 `[Verify]` | Không có quét lặp | Khi đó chỉ so (a) và (c) |
| Số người dùng `[TBD: OQ-015]` | Mức tải đồng thời | Dùng 10 (SAD §0.1) |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §5.4, §6.5, §7.1 (hiệu năng), §9.2
- [SAD](../../design/SAD.md) §0.1, §2.3 (lọc phạm vi, HNSW), §3.2.1 (ngân sách), §4.3 (metric), §5 AD-05, §7 SP-01
- [Blueprint_Design](../../design/Blueprint_Design.md) QAS-01, QAS-11
- [User_Stories](../../design/User_Stories.md) US-C5
- Task liên quan: [T-203](./T-203-hybrid-retrieval.md), [T-205](./T-205-answer-service.md), [T-208](./T-208-real-ai-adapters-reindex.md), [T-302](./T-302-document-scope.md), [T-305](./T-305-upstream-resilience.md), [T-310](./T-310-threshold-calibration.md), [T-410](./T-410-launch-gate-uat.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)) ở phần áp dụng được cho spike (script được review, không log nội dung).
- [ ] Business Owner đã nhận báo cáo; quyết định OQ-014 (hoặc hạn quyết định) ghi vào `SP-01.md`.
