# T11-01 – Xử lý lại tài liệu lỗi tạm thời (US-009)

| Trường | Giá trị |
|---|---|
| Lát | VS-11 – Tính năng P1 (Lát 3) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T03-05](T03-05_pipeline-ingest-va-ghi-chi-muc-alg-04.md), [T02-06](T02-06_spa-vung-tai-len-mot-file-va-danh-sach-tai-lieu.md) |
| Story | US-009 |
| Tài liệu tham chiếu | USER_STORIES US-009 AC; openapi.yaml `POST /documents/{id}/reprocess`; html_design S03 |

## Mục tiêu

Tài liệu Thất bại R-04 xử lý lại được; mã khác không có nút.

## Phạm vi file

- `backend/app/api/v1/documents.py` (reprocess)
- `frontend/src/features/documents/DocumentRow.tsx` (nút Xử lý lại)
- `backend/tests/integration/test_reprocess.py`

## Các bước gợi ý

1. FAILED R-04 → PROCESSING (xóa `failure_code`), enqueue job, audit `document_reprocess`; khác → 409 `not_retryable`.

## Tiêu chí hoàn thành

- [ ] Test: R-04 → 202 và job mới; R-03 → 409; gọi 2 lần → lần 2 409
- [ ] E2E: nút chỉ hiện với R-04
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k reprocess
```

## Kết quả triển khai

**Done** – Chỉ R-04 được xử lý lại; test 202/409.
