# T03-05 – Pipeline ingest và ghi chỉ mục (ALG-04)

| Trường | Giá trị |
|---|---|
| Lát | VS-3 – Xử lý tài liệu (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T03-01](T03-01_hang-doi-job-va-vong-lap-worker-alg-11.md), [T03-03](T03-03_chia-doan-trong-trang-alg-03-chunk.md), [T03-04](T03-04_embedding-service-va-embeddingport.md), [T02-01](T02-01_blobport-va-adapter-s3-minio.md) |
| Story | US-005, US-008 |
| Tài liệu tham chiếu | BLUEPRINT ALG-04, 3.4.3; DATABASE_DESIGN A.7 (trigger bất biến) |

## Mục tiêu

Job `ingest_document` biến tài liệu PROCESSING thành READY (có đoạn + vector) hoặc FAILED với mã lý do.

## Phạm vi file

- `backend/app/modules/ingestion/pipeline.py`
- `backend/worker/handlers/ingest.py`
- `backend/tests/integration/test_ingest.py`

## Các bước gợi ý

1. Đúng ALG-04: scope workspace, tải file, extract, chunk, embed theo lô 32, transaction cuối khóa hàng + kiểm tra `deleted_at`, `COPY` đoạn, READY, `pg_notify('document_status')`.
2. Lỗi phân loại → `mark_failed(R-0x)`; lỗi tạm thời → retry; hết lượt → R-04.

## Tiêu chí hoàn thành

- [ ] Test (fake embedding): PDF mẫu → READY, số đoạn > 0, mọi đoạn có `embedding_model='bge-m3@v1'`
- [ ] PDF scan → FAILED R-03, không có đoạn
- [ ] Embedding lỗi 3 lần → FAILED R-04
- [ ] Chạy lại job đã READY một phần (giả lập worker chết trước COMMIT) → kết quả giống chạy 1 lần
- [ ] Có thông báo NOTIFY khi đổi trạng thái
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k ingest
```

## Kết quả triển khai

**Done** – Pipeline ingest an toàn với xóa; ghi `chunk` bằng INSERT theo lô (COPY không dùng được với RLS).
