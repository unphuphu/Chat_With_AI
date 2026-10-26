# T06-02 – Tổng hợp nhiều tài liệu và số trang

| Trường | Giá trị |
|---|---|
| Lát | VS-6 – Chất lượng câu trả lời (Lát 2) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T04-04](T04-04_hoi-thoai-va-api-dat-cau-hoi-alg-08-co-ban.md) |
| Story | US-017, US-021 |
| Tài liệu tham chiếu | USER_STORIES US-017, US-021 AC; BLUEPRINT ALG-06, DD-11; DATABASE_DESIGN `citation` |

## Mục tiêu

Câu trả lời trích nhiều tài liệu; số trang đúng hoặc null, không bao giờ đoán.

## Phạm vi file

- `backend/tests/integration/test_multi_doc.py`
- `frontend/src/features/chat/CitationChip.tsx` (trường hợp không có trang)

## Các bước gợi ý

1. Fixture 2 PDF có thông tin bổ sung nhau; LLM giả trích cả hai.
2. Đoạn có `page_number` → chip 'tr.X'; trích dẫn không có trang → chỉ tên file.

## Tiêu chí hoàn thành

- [ ] Test: citations chứa 2 `document_id` khác nhau, đúng trang của đoạn đã truy xuất
- [ ] Test: tài liệu bị đổi tên/xóa sau khi trả lời → `document_name_snapshot` giữ tên cũ
- [ ] Unit test chip không trang
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k multi_doc
```
