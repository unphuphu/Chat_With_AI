# T10-01 – Nhật ký kiểm toán đầy đủ

| Trường | Giá trị |
|---|---|
| Lát | VS-10 – Vận hành và đo lường (Lát 2) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T07-01](T07-01_api-xoa-tai-lieu-alg-12.md), [T04-04](T04-04_hoi-thoai-va-api-dat-cau-hoi-alg-08-co-ban.md), [T01-03](T01-03_endpoint-auth-va-me.md) |
| Story | US-C02 |
| Tài liệu tham chiếu | PRD NFR-012, NFR-023; schema.sql `audit_event`; DATABASE_DESIGN A.7 |

## Mục tiêu

Mọi hành động trong danh sách `action` được ghi đúng 1 lần, không có nội dung.

## Phạm vi file

- `backend/app/modules/audit/service.py` (bản đầy đủ, gồm `request_id`)
- `backend/tests/integration/test_audit.py`

## Các bước gợi ý

1. Rà soát mọi điểm gọi; ghi trong cùng transaction với thay đổi nghiệp vụ.
2. Kiểm tra `app_readonly_audit` đọc được, `app_api` không UPDATE/DELETE được.

## Tiêu chí hoàn thành

- [ ] Test: mỗi hành động trong 9 `action` sinh đúng 1 hàng
- [ ] Test: `app_api` UPDATE `audit_event` → permission denied
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k audit
```
