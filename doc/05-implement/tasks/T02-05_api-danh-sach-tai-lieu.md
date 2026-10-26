# T02-05 – API danh sách tài liệu

| Trường | Giá trị |
|---|---|
| Lát | VS-2 – Tải lên một PDF (Lát 1) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T02-04](T02-04_api-nhan-file-vao-lo-alg-01-accept-file-idempote.md) |
| Story | US-006 |
| Tài liệu tham chiếu | openapi.yaml `GET /documents`, `DocumentList`; DATABASE_DESIGN A.5 (`vw_document_list`) |

## Mục tiêu

Trả tài liệu chưa xóa của workspace, mới nhất trước, kèm hạn mức.

## Phạm vi file

- `backend/app/api/v1/documents.py` (GET list)
- `backend/tests/integration/test_list_documents.py`

## Các bước gợi ý

1. Đọc `vw_document_list` trong `workspace_scope`, sắp `uploaded_at DESC`; `retryable` từ view.
2. Không trả `storage_key`, `sha256`, `workspace_id`, `batch_id`.

## Tiêu chí hoàn thành

- [ ] Test: 3 trạng thái hiện đúng; tài liệu đã xóa không hiện
- [ ] Test: phản hồi không chứa trường cấm (kiểm tra khóa JSON)
- [ ] Test: user P2 không thấy tài liệu P1
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k list_documents
```
