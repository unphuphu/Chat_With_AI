# T07-01 – API xóa tài liệu (ALG-12)

| Trường | Giá trị |
|---|---|
| Lát | VS-7 – Xóa tài liệu (Lát 2) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T03-05](T03-05_pipeline-ingest-va-ghi-chi-muc-alg-04.md), [T02-05](T02-05_api-danh-sach-tai-lieu.md) |
| Story | US-010, US-011 |
| Tài liệu tham chiếu | BLUEPRINT ALG-12; openapi.yaml `DELETE /documents/{id}`; USER_STORIES US-010, US-011 AC |

## Mục tiêu

Xóa mềm + xóa đoạn + hủy job chờ + enqueue purge trong một transaction.

## Phạm vi file

- `backend/app/modules/documents/service.py` (`soft_delete`)
- `backend/app/api/v1/documents.py` (DELETE)
- `backend/tests/integration/test_delete.py`

## Các bước gợi ý

1. Đúng ALG-12; audit `document_delete`; NOTIFY `quota.changed`.

## Tiêu chí hoàn thành

- [ ] Test: sau DELETE, truy xuất không trả đoạn của tài liệu (US-011 AC)
- [ ] Test race: ingest đang chạy tới bước 7 thì DELETE → ingest rollback, 0 đoạn, job CANCELLED (QA-14)
- [ ] Test: DELETE lần 2 → 404; tài liệu của người khác → 404
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k delete
```

## Kết quả triển khai

**Done** – Xóa mềm + xóa chunk + hủy ingest + enqueue purge; 404 + audit `access_denied`.
