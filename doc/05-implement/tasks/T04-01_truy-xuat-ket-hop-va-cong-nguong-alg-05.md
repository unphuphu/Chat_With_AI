# T04-01 – Truy xuất kết hợp và cổng ngưỡng (ALG-05)

| Trường | Giá trị |
|---|---|
| Lát | VS-4 – Hỏi đáp có trích dẫn (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T03-05](T03-05_pipeline-ingest-va-ghi-chi-muc-alg-04.md) |
| Story | US-013, US-017 |
| Tài liệu tham chiếu | BLUEPRINT ALG-05; DATABASE_DESIGN B.4, B.5; SAD ADR-009 |

## Mục tiêu

Từ câu hỏi trả top-8 đoạn trong workspace (vector + full-text, RRF) và cờ `below_gate`.

## Phạm vi file

- `backend/app/modules/retrieval/{service.py,hybrid_sql.py,domain.py}`
- `backend/tests/integration/test_retrieval.py`

## Các bước gợi ý

1. Câu SQL đúng ALG-05 (lọc `workspace_id`, `embedding_model`), `SET LOCAL hnsw.ef_search`, `hnsw.iterative_scan`.
2. Embed câu hỏi (timeout 2 s); trả `RetrievalResult`.

## Tiêu chí hoàn thành

- [ ] Test (fake embedding, nội dung có từ khóa): câu hỏi chứa mã hợp đồng tìm đúng đoạn qua nhánh full-text
- [ ] Test: không bao giờ trả đoạn của workspace khác (2 workspace có cùng nội dung)
- [ ] Test: không có đoạn liên quan → `below_gate=True`
- [ ] `EXPLAIN` trên 10.000 đoạn giả dùng `idx_chunk_embedding_hnsw` và `idx_chunk_tsv_gin` (ghi plan vào PR)
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k retrieval
```
