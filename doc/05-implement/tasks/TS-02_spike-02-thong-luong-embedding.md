# TS-02 – SPIKE-02: thông lượng embedding

| Trường | Giá trị |
|---|---|
| Lát | SPIKE – Thử nghiệm kỹ thuật (Song song) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T03-04](T03-04_embedding-service-va-embeddingport.md), [T03-03](T03-03_chia-doan-trong-trang-alg-03-chunk.md) |
| Story | US-005 |
| Tài liệu tham chiếu | SAD 12 (SPIKE-02, TR-02), 9.2; PRD NFR-002 |

## Mục tiêu

Xác định CPU 4 vCPU có xử lý file 300 trang ≤ 3 phút không, hay cần GPU.

## Phạm vi file

- `eval/reports/spike-02.md`
- `eval/bench_embedding.py`

## Các bước gợi ý

1. Đo đoạn/giây với lô 8/16/32 trên 4 vCPU; ước tính file 300 trang (~600 đoạn).
2. Nếu có GPU: đo lại.

## Tiêu chí hoàn thành

- [ ] Báo cáo có số liệu và khuyến nghị cấu hình (CPU/GPU, số bản) cập nhật SAD 9.2
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
python eval/bench_embedding.py --texts 600 --batch 32
```
