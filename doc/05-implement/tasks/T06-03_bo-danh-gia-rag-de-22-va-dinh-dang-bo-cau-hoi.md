# T06-03 – Bộ đánh giá RAG (DE-22) và định dạng bộ câu hỏi

| Trường | Giá trị |
|---|---|
| Lát | VS-6 – Chất lượng câu trả lời (Lát 2) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T04-04](T04-04_hoi-thoai-va-api-dat-cau-hoi-alg-08-co-ban.md) |
| Story | US-013, US-016, US-017, US-021 |
| Tài liệu tham chiếu | BLUEPRINT DE-22, QA-11; PRD 5.1 G-02, NFR-003…005, NFR-018; BRD DEP-005 |

## Mục tiêu

Công cụ chạy bộ câu hỏi qua API staging và tính MET-002…005, NFR-018; chạy hằng đêm.

## Phạm vi file

- `eval/` (package riêng: `run.py`, `metrics.py`, `schema.json` cho bộ câu hỏi)
- `eval/datasets/sample.jsonl` (10 câu minh họa trên PDF tự tạo)
- workflow CI hằng đêm

## Các bước gợi ý

1. Định dạng câu hỏi: `{id, question, type: in_doc|multi_doc|out_of_doc|followup, expected_docs, expected_pages, reference_answer}`.
2. Chấm tự động: tài liệu/trang trích dẫn; tỷ lệ INSUFFICIENT với out_of_doc. Chấm 'đúng nội dung' xuất file CSV để người dùng nghiệp vụ chấm (không dùng LLM tự chấm làm số liệu chính thức).
3. So sánh với lần chạy trước, cảnh báo khi giảm > 3 điểm %.

## Tiêu chí hoàn thành

- [ ] Chạy trên `sample.jsonl` sinh báo cáo JSON + Markdown có đủ chỉ số
- [ ] README hướng dẫn BA soạn DEP-005 theo schema
- [ ] Job hằng đêm chạy được trên staging (hoặc docker-compose)
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
python -m eval.run --suite sample --out eval/reports/sample.json
```
