# T03-06 – SSE: phát trạng thái tài liệu tới giao diện

| Trường | Giá trị |
|---|---|
| Lát | VS-3 – Xử lý tài liệu (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T03-05](T03-05_pipeline-ingest-va-ghi-chi-muc-alg-04.md), [T02-06](T02-06_spa-vung-tai-len-mot-file-va-danh-sach-tai-lieu.md) |
| Story | US-007, US-025 |
| Tài liệu tham chiếu | BLUEPRINT 3.4.2, DD-12; openapi.yaml `/events`; API_DESIGN CA-03; html_design S03 (toast) |

## Mục tiêu

Giao diện tự cập nhật trạng thái tài liệu và hiện thông báo khi Sẵn sàng/Thất bại.

## Phạm vi file

- `backend/app/modules/events/{bus.py,sse.py}`
- `backend/app/api/v1/events.py`
- `frontend/src/shared/sse/useSse.ts`
- `frontend/src/shared/ui/Toast.tsx`
- `backend/tests/integration/test_sse.py`
- `frontend/e2e/processing.spec.ts`

## Các bước gợi ý

1. EventBus: 1 kết nối `LISTEN document_status` mỗi bản API; map `ws → set[Queue]`; queue đầy 100 → đóng kết nối.
2. `/events`: `retry: 5000`, `: ping` mỗi 25 s, sự kiện `document.status_changed`, `quota.changed`.
3. SPA: `onopen` → invalidate documents; sự kiện → cập nhật cache + toast tự ẩn 5 s, vùng `aria-live`.

## Tiêu chí hoàn thành

- [ ] Test: NOTIFY cho ws A chỉ tới client của ws A
- [ ] Test: ping xuất hiện trong 26 s
- [ ] E2E: tải PDF → dòng tự chuyển 'Sẵn sàng' không tải lại trang, toast hiện rồi tự ẩn
- [ ] E2E: PDF scan → 'Thất bại' + lý do R-03 như S03
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k sse && make e2e -- processing.spec.ts
```
