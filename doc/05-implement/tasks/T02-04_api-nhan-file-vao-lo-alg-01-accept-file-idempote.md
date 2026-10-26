# T02-04 – API nhận file vào lô (ALG-01 accept_file, idempotent)

| Trường | Giá trị |
|---|---|
| Lát | VS-2 – Tải lên một PDF (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T02-01](T02-01_blobport-va-adapter-s3-minio.md), [T02-02](T02-02_sandbox-va-kiem-tra-pdf-khi-nhan-alg-02.md), [T02-03](T02-03_api-tao-lo-tai-len-va-han-muc-alg-01-create-batc.md) |
| Story | US-001 |
| Tài liệu tham chiếu | BLUEPRINT ALG-01 (pha 0–4); API_DESIGN AD-06; openapi.yaml `PUT /upload-batches/{batch_id}/files/{client_file_id}` |

## Mục tiêu

Nhận một PDF, kiểm tra, lưu object, tạo tài liệu PROCESSING + job ingest; gửi lại cùng `client_file_id` không tạo trùng.

## Phạm vi file

- `backend/app/api/v1/upload_batches.py` (PUT)
- `backend/app/modules/documents/service.py` (`accept_file`)
- `backend/app/infra/jobs.py` (`enqueue` tối thiểu + `pg_notify('job_enqueued')`)
- `backend/tests/integration/test_accept_file.py`

## Các bước gợi ý

1. Pha 0 tra `(batch_id, client_file_id)` → 200 nếu có.
2. Pha 1 stream ra file tạm, dừng khi vượt `MAX_FILE_MB` → `too_large`; gọi inspector.
3. Pha 2 transaction ngắn trừ chỗ đặt (cả khi bị từ chối); pha 3 `blob.put`; pha 4 INSERT … ON CONFLICT + job + audit `document_upload`.
4. Xóa file tạm trong `finally`.

## Tiêu chí hoàn thành

- [ ] Test: PDF hợp lệ → 201 `PROCESSING`, có object trong MinIO, có job QUEUED
- [ ] Test: gửi lại cùng `client_file_id` → 200 cùng `id`, không thêm job/chỗ đặt
- [ ] Test: `.docx` → 422 `not_pdf`, không có object, `remaining_slots` giảm 1
- [ ] Test: lô hết hạn → 404 `batch_expired`; hết chỗ → 409 `batch_full`
- [ ] Test: MinIO tắt → 503 `storage_unavailable`, không có document
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k accept_file
```
