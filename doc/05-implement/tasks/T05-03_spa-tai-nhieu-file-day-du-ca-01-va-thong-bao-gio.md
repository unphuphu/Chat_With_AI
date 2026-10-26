# T05-03 – SPA: tải nhiều file đầy đủ (CA-01) và thông báo giới hạn

| Trường | Giá trị |
|---|---|
| Lát | VS-5 – Nhiều file và giới hạn (Lát 2) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T02-06](T02-06_spa-vung-tai-len-mot-file-va-danh-sach-tai-lieu.md), [T05-01](T05-01_hoan-thien-cac-duong-tu-choi-file-va-lo.md) |
| Story | US-002, US-003, US-004, US-026 |
| Tài liệu tham chiếu | API_DESIGN CA-01, 3.7.1; html_design S02, S08; USER_STORIES US-002 AC 2–3 |

## Mục tiêu

Kiểm tra trước bằng `/me.limits`, tải song song 3, thử lại an toàn, tạo lô mới khi lô hết hạn.

## Phạm vi file

- `frontend/src/features/documents/useUploadQueue.ts` (bản đầy đủ)
- `frontend/src/features/documents/UploadItem.tsx`
- `frontend/e2e/upload-multi.spec.ts`

## Các bước gợi ý

1. Đúng CA-01: file sai đuôi/quá dung lượng bị chặn ở client; > max file → báo, không tải file nào; pool 3; `Tải lại` dùng lại `client_file_id`; `batch_expired`/`batch_full` → lô mới 1 lần; `server_busy` → chờ `Retry-After` tối đa 2 lần.
2. Cảnh báo hạn mức khi còn ≤ 5 chỗ (S08).

## Tiêu chí hoàn thành

- [ ] E2E: 12 file → thông báo, 0 request PUT
- [ ] E2E: 5 file trong đó 1 `.docx` → 4 nhận, 1 báo lỗi trên dòng
- [ ] E2E: cắt mạng giữa PUT (Playwright `route.abort`) → 'Tải lại' → 1 tài liệu, không trùng
- [ ] Tối đa 3 PUT đồng thời (đếm trong test)
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make e2e -- upload-multi.spec.ts
```

## Kết quả triển khai

**Done** – Hàng đợi 3 file song song, kiểm tra trước ở client, cảnh báo hạn mức, Tải lại cùng `client_file_id`.
