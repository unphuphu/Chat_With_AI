# T05-01 – Hoàn thiện các đường từ chối file và lô

| Trường | Giá trị |
|---|---|
| Lát | VS-5 – Nhiều file và giới hạn (Lát 2) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T02-04](T02-04_api-nhan-file-vao-lo-alg-01-accept-file-idempote.md) |
| Story | US-002, US-003, US-004 |
| Tài liệu tham chiếu | USER_STORIES US-002, US-003, US-004 AC, I-01; PRD E-07, E-08; openapi.yaml (413/422/404/409) |

## Mục tiêu

Mọi đường lỗi tải lên trả đúng mã, đúng thông điệp, không để rác.

## Phạm vi file

- `backend/tests/integration/test_upload_rejections.py`
- `deploy/nginx/api.conf` (`client_max_body_size MAX_FILE_MB+1m`)

## Các bước gợi ý

1. Bảng test cho: không phải PDF, đuôi .pdf giả, quá dung lượng (dừng sớm khi stream), > 300 trang, mật khẩu, lô hết hạn, hết chỗ, vượt hạn mức.
2. Proxy trả 413 dạng Problem (`too_large`).

## Tiêu chí hoàn thành

- [ ] Mọi dòng trong bảng test xanh; sau mỗi lỗi: không có object mồ côi, không có document, `remaining_slots` đúng
- [ ] Upload 25 MB bị dừng trước khi đọc hết body (đo byte đã đọc)
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k upload_rejections
```

## Kết quả triển khai

**Done** – Đủ các đường từ chối (scan R-03, quá trang, mật khẩu, hỏng, docx, giả PDF, quá dung lượng); test tham số hóa.
