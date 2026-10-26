# T02-03 – API tạo lô tải lên và hạn mức (ALG-01 create_batch)

| Trường | Giá trị |
|---|---|
| Lát | VS-2 – Tải lên một PDF (Lát 1) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T01-03](T01-03_endpoint-auth-va-me.md) |
| Story | US-002 |
| Tài liệu tham chiếu | BLUEPRINT ALG-01; openapi.yaml `POST /upload-batches`, `UploadBatch`, `QuotaProblem`; DATABASE_DESIGN A.5 (`vw_workspace_quota`) |

## Mục tiêu

Đặt chỗ cho lô tải lên, chặn vượt số file/lần và hạn mức tài liệu.

## Phạm vi file

- `backend/app/modules/documents/{quota.py,service.py,repository.py}`
- `backend/app/api/v1/upload_batches.py` (POST)
- `backend/tests/integration/test_create_batch.py`

## Các bước gợi ý

1. Khóa hàng `workspace` FOR UPDATE; tính `used`; tạo `upload_batch` (TTL `BATCH_TTL_S`).
2. Lỗi: `too_many_files` (> `MAX_FILES_PER_BATCH`), `quota_exceeded` kèm `remaining`.

## Tiêu chí hoàn thành

- [ ] Test: 10 file → 201, `slots=10`; 11 file → 422 `too_many_files`, không tạo lô
- [ ] Test: đã có 95 tài liệu, xin 10 → 422 `quota_exceeded`, `remaining=5`
- [ ] Test đồng thời: 2 request song song mỗi cái 6 file khi còn 10 chỗ → đúng 1 thành công
- [ ] Phản hồi khớp schema openapi
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k create_batch
```

## Kết quả triển khai

**Done** – Tạo lô, `too_many_files`, `quota_exceeded` kèm `remaining`.
