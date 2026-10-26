# T11-04 – Trình xem PDF tại trang (US-022)

| Trường | Giá trị |
|---|---|
| Lát | VS-11 – Tính năng P1 (Lát 3) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T04-05](T04-05_spa-khung-chat-cau-tra-loi-va-nhan-nguon.md) |
| Story | US-022 |
| Tài liệu tham chiếu | USER_STORIES US-022 AC; openapi.yaml `GET /documents/{id}/file`; html_design S06; API_DESIGN AD-12 |

> **Chặn bởi:** OQ-014 (mở trong ứng dụng hay không)

## Mục tiêu

Bấm nhãn nguồn mở PDF gốc đúng trang trong lớp phủ.

## Phạm vi file

- `backend/app/api/v1/documents.py` (file stream, 410, EVT-09)
- `frontend/src/features/viewer/PdfViewerOverlay.tsx` (pdf.js tải lười)

## Các bước gợi ý

1. Stream qua API (`Cache-Control: private, no-store`, `Content-Disposition` inline).
2. Overlay `aria-modal`, Esc đóng, trả focus; mở trang X hoặc trang 1.

## Tiêu chí hoàn thành

- [ ] E2E: bấm [1] → mở đúng trang
- [ ] Tài liệu đã xóa → thông báo 'Tài liệu đã bị xóa'
- [ ] Bundle chính không tăng (pdf.js ở chunk riêng)
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make e2e -- viewer.spec.ts
```

## Kết quả triển khai

**Done** – Trình xem PDF có sẵn của trình duyệt trong dialog, mở đúng trang (`#page=N`), ghi EVT-09; chưa tô sáng đoạn.
