# T02-01 – BlobPort và adapter S3/MinIO

| Trường | Giá trị |
|---|---|
| Lát | VS-2 – Tải lên một PDF (Lát 1) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T00-02](T00-02_docker-compose-moi-truong-dev.md), [T00-04](T00-04_khung-api-settings-loi-rfc-9457-request-id-healt.md) |
| Story | US-001 |
| Tài liệu tham chiếu | BLUEPRINT 3.2.2 (`BlobPort`), 3.5.2 (khóa object); SAD 6.2 (timeout, thử lại) |

## Mục tiêu

Lưu/đọc/xóa file PDF qua interface, có bản in-memory cho unit test.

## Phạm vi file

- `backend/app/ports/blob.py`
- `backend/app/adapters/blob_s3.py` (aioboto3 hoặc minio-py async)
- `backend/app/adapters/blob_memory.py`
- `backend/tests/integration/test_blob_s3.py`

## Các bước gợi ý

1. `put(key, stream, sha256)` với SSE (`ServerSideEncryption` khi cấu hình), kiểm tra checksum; `get_stream`; `delete` idempotent; `list(prefix, older_than)` cho ALG-10.
2. Timeout 30 s, thử lại 3 lần với lỗi mạng/5xx.
3. Khóa `ws/{workspace_id}/doc/{document_id}.pdf` sinh bằng hàm duy nhất `document_key()`.

## Tiêu chí hoàn thành

- [ ] Test với MinIO: put→get trả đúng byte; delete 2 lần không lỗi; list theo tuổi
- [ ] Unit test: adapter memory có cùng hành vi (chạy chung bộ test hợp đồng cho 2 adapter)
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k blob
```
