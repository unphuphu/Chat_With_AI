# T11-05 – Câu hỏi tiếp nối hiểu ngữ cảnh (US-015)

| Trường | Giá trị |
|---|---|
| Lát | VS-11 – Tính năng P1 (Lát 3) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Deferred** |
| Phụ thuộc | [T04-04](T04-04_hoi-thoai-va-api-dat-cau-hoi-alg-08-co-ban.md), [T06-03](T06-03_bo-danh-gia-rag-de-22-va-dinh-dang-bo-cau-hoi.md) |
| Story | US-015 |
| Tài liệu tham chiếu | USER_STORIES US-015 AC; BLUEPRINT ALG-06 (câu hỏi tiếp nối, `FEATURE_FOLLOWUP`) |

> **Chặn bởi:** OQ-012

## Mục tiêu

Viết lại câu hỏi tiếp nối thành câu độc lập trước khi truy xuất.

## Phạm vi file

- `backend/app/modules/qa/rewriter.py`
- `eval/datasets/sample.jsonl` (10 cặp followup)

## Các bước gợi ý

1. Gọi LLM (100 token, 2 s) với 3 lượt gần nhất; tính vào ngân sách 15 s; bật bằng cờ.

## Tiêu chí hoàn thành

- [ ] ≥ 8/10 cặp đúng ngữ cảnh trên bộ đánh giá
- [ ] Tắt cờ → hành vi như cũ
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
python -m eval.run --suite followup
```

## Kết quả triển khai

**Deferred** – Blocked theo kế hoạch (câu hỏi mở + cần LLM thật).
