# TS-04 – SPIKE-04: hiệu chỉnh ngưỡng τ và top-k

| Trường | Giá trị |
|---|---|
| Lát | SPIKE – Thử nghiệm kỹ thuật (Song song) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Blocked** |
| Phụ thuộc | [T04-01](T04-01_truy-xuat-ket-hop-va-cong-nguong-alg-05.md), [T06-03](T06-03_bo-danh-gia-rag-de-22-va-dinh-dang-bo-cau-hoi.md) |
| Story | US-016 |
| Tài liệu tham chiếu | SAD 12 (SPIKE-04); DATABASE_DESIGN B.6 (đo recall) |

> **Chặn bởi:** DEP-005

## Mục tiêu

Chọn `RETRIEVAL_MIN_SIMILARITY` và `RETRIEVAL_TOP_K` tối đa MET-005 mà MET-002 ≥ 80%; đo recall@30 HNSW.

## Phạm vi file

- `eval/reports/spike-04.md`

## Các bước gợi ý

1. Quét τ 0,30…0,60 bước 0,05; top-k 6/8/10.
2. Đo recall@30 theo B.6.

## Tiêu chí hoàn thành

- [ ] Bảng kết quả và giá trị đề xuất cập nhật `.env.example` + BLUEPRINT 3.6.6
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
python -m eval.sweep --param tau --from 0.30 --to 0.60 --step 0.05
```
