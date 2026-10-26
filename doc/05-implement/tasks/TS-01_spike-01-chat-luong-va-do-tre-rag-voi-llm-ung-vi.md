# TS-01 – SPIKE-01: chất lượng và độ trễ RAG với LLM ứng viên

| Trường | Giá trị |
|---|---|
| Lát | SPIKE – Thử nghiệm kỹ thuật (Song song) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Deferred** |
| Phụ thuộc | [T04-04](T04-04_hoi-thoai-va-api-dat-cau-hoi-alg-08-co-ban.md), [T06-03](T06-03_bo-danh-gia-rag-de-22-va-dinh-dang-bo-cau-hoi.md) |
| Story | US-013, US-016 |
| Tài liệu tham chiếu | SAD 12 (SPIKE-01, TR-01, TR-04); PRD NFR-001, NFR-003…005 |

> **Chặn bởi:** DEP-003, DEP-005 (bộ PDF, bộ câu hỏi), OQ-005 (quyền dùng LLM)

## Mục tiêu

Đo MET-002/004/005 và p90 độ trễ trên bộ câu hỏi thật với LLM ứng viên để quyết định ADR-007.

## Phạm vi file

- `eval/reports/spike-01.md`

## Các bước gợi ý

1. Nạp bộ PDF mẫu (DEP-003), chạy bộ câu hỏi (DEP-005) qua bộ đánh giá T06-03.
2. Load 20 người dùng đồng thời (k6 script của T10-06 bản rút gọn).
3. So sánh top-k 6/8, ef_search 80/120.

## Tiêu chí hoàn thành

- [ ] Báo cáo có bảng MET-002, MET-004, MET-005, NFR-018, p50/p90 và đề xuất giữ/đổi ADR-007, ADR-009
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
python -m eval.run --suite dep005 --out eval/reports/spike-01.json
```

## Kết quả triển khai

**Deferred** – Cần API key LLM thật và bộ câu hỏi chuẩn (T06-03) – chưa chạy.
