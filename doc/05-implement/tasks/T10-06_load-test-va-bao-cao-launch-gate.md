# T10-06 – Load test và báo cáo launch gate

| Trường | Giá trị |
|---|---|
| Lát | VS-10 – Vận hành và đo lường (Lát 2) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Deferred** |
| Phụ thuộc | [T10-05](T10-05_dong-goi-va-cau-hinh-trien-khai-staging.md), [T06-03](T06-03_bo-danh-gia-rag-de-22-va-dinh-dang-bo-cau-hoi.md), [T08-01](T08-01_bo-test-phan-quyen-va-cach-ly-toan-he-thong.md) |
| Story | – (nền tảng / phi chức năng) |
| Tài liệu tham chiếu | PRD 5.1 (G-01…G-09), NFR-001, NFR-002, NFR-007; BLUEPRINT QA-01, QA-02 |

## Mục tiêu

Đo hiệu năng trên staging và tổng hợp trạng thái mọi điều kiện ra mắt.

## Phạm vi file

- `perf/k6/ask.js`, `perf/k6/upload.js`
- `docs/launch-gate.md`

## Các bước gợi ý

1. k6: 20 người dùng ảo hỏi liên tục 10 phút; 10 người tải file 20 MB.
2. Điền bảng G-01…G-09 với bằng chứng (link báo cáo test, eval, bảo mật).

## Tiêu chí hoàn thành

- [ ] Báo cáo p50/p90 hỏi đáp và thời gian xử lý file lớn nhất
- [ ] `docs/launch-gate.md` có trạng thái từng gate và danh sách việc còn thiếu
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
k6 run perf/k6/ask.js
```

## Kết quả triển khai

**Deferred** – Chưa chạy load test (phụ thuộc T10-05).
