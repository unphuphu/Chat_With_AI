# T04-06 – Demo lát 1: E2E luồng xuyên suốt

| Trường | Giá trị |
|---|---|
| Lát | VS-4 – Hỏi đáp có trích dẫn (Lát 1) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T04-05](T04-05_spa-khung-chat-cau-tra-loi-va-nhan-nguon.md), [T01-05](T01-05_spa-phien-header-nguoi-dung-trang-loi-dang-nhap.md) |
| Story | US-001, US-005, US-006, US-012, US-013, US-020, US-023 |
| Tài liệu tham chiếu | USER_STORIES mục 3 (lát 1); PRD 2.2 (hành trình) |

## Mục tiêu

Một test E2E chứng minh luồng Đăng nhập → Tải PDF → Sẵn sàng → Hỏi → Trả lời có nguồn chạy được trên docker-compose.

## Phạm vi file

- `frontend/e2e/slice1-journey.spec.ts`
- `docs/demo/slice1.md` (kịch bản demo, ảnh chụp)

## Các bước gợi ý

1. Chạy toàn bộ stack (embedding thật nếu máy đủ, LLM giả hoặc thật nếu có key).
2. Ghi thời gian từng bước.

## Tiêu chí hoàn thành

- [ ] E2E xanh trên CI với LLM giả + embedding giả
- [ ] Chạy thủ công 1 lần với embedding thật, ghi kết quả vào `docs/demo/slice1.md`
- [ ] PO xem demo (ghi ngày vào file)
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make e2e -- slice1-journey.spec.ts
```
