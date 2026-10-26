# T11-03 – Nêu mâu thuẫn giữa tài liệu (US-018)

| Trường | Giá trị |
|---|---|
| Lát | VS-11 – Tính năng P1 (Lát 3) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T06-02](T06-02_tong-hop-nhieu-tai-lieu-va-so-trang.md) |
| Story | US-018 |
| Tài liệu tham chiếu | USER_STORIES US-018 AC; BLUEPRINT ALG-06 (`conflict`); html_design S04 (khối mâu thuẫn) |

## Mục tiêu

Khi các nguồn khác nhau, câu trả lời liệt kê từng giá trị kèm nguồn.

## Phạm vi file

- `backend/app/modules/qa/prompt.py` (đảm bảo chỉ dẫn mâu thuẫn)
- `frontend/src/features/chat/ConflictNotice.tsx`
- `eval/datasets/sample.jsonl` (thêm cặp mâu thuẫn)

## Các bước gợi ý

1. Truyền `conflict` từ `LlmAnswer` ra `Answer` (thêm trường tùy chọn `conflict: boolean` vào openapi.yaml – thay đổi không phá vỡ).
2. Giao diện hiển thị khối cảnh báo như S04.

## Tiêu chí hoàn thành

- [ ] Cập nhật openapi.yaml + kiểm tra hợp đồng xanh
- [ ] Test với LLM giả `conflict=true` → khối hiển thị
- [ ] Bộ đánh giá có ≥ 2 câu mâu thuẫn
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k conflict
```
