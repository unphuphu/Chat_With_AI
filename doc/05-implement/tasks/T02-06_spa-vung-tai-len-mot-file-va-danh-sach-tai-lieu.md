# T02-06 – SPA: vùng tải lên một file và danh sách tài liệu

| Trường | Giá trị |
|---|---|
| Lát | VS-2 – Tải lên một PDF (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T01-05](T01-05_spa-phien-header-nguoi-dung-trang-loi-dang-nhap.md), [T02-05](T02-05_api-danh-sach-tai-lieu.md) |
| Story | US-001, US-006 |
| Tài liệu tham chiếu | html_design S01, S02, S03; API_DESIGN CA-01 (phần 1 file), 3.7.1, 3.7.3; USER_STORIES US-001, US-006 AC |

## Mục tiêu

Kéo thả/chọn 1 PDF, thấy tiến độ, thấy dòng tài liệu với trạng thái.

## Phạm vi file

- `frontend/src/features/documents/{UploadDropzone,DocumentList,DocumentRow,QuotaBadge}.tsx`
- `frontend/src/features/documents/useUploadQueue.ts` (bản 1 file)
- `frontend/src/shared/api/upload.ts` (XHR có `onprogress`)
- `frontend/e2e/upload-single.spec.ts`

## Các bước gợi ý

1. Tạo lô 1 file → PUT với `client_file_id = crypto.randomUUID()` → invalidate `['documents']`, `['me']`.
2. DocumentRow: biểu tượng + chữ trạng thái, meta (trang · dung lượng · thời gian `vi-VN`), nút xóa (chưa hoạt động – VS-7).
3. Trạng thái trống E-01 như S01.

## Tiêu chí hoàn thành

- [ ] E2E: chọn 1 PDF → thanh tiến độ xuất hiện ≤ 300 ms → dòng 'Đang xử lý'
- [ ] Unit test DocumentRow cho 3 trạng thái (snapshot + có chữ trạng thái)
- [ ] axe-core không có lỗi serious
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
pnpm -C frontend test && make e2e -- upload-single.spec.ts
```
