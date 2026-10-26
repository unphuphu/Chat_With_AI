# T08-01 – Bộ test phân quyền và cách ly toàn hệ thống

| Trường | Giá trị |
|---|---|
| Lát | VS-8 – Cách ly và bảo mật (Lát 2) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T07-01](T07-01_api-xoa-tai-lieu-alg-12.md), [T04-04](T04-04_hoi-thoai-va-api-dat-cau-hoi-alg-08-co-ban.md) |
| Story | US-024 |
| Tài liệu tham chiếu | USER_STORIES US-024 AC; PRD NFR-010, G-04; BLUEPRINT QA-06; API_DESIGN AD-11 |

## Mục tiêu

Chứng minh không endpoint nào cho phép truy cập dữ liệu của workspace khác.

## Phạm vi file

- `backend/tests/security/test_isolation.py`
- `backend/tests/security/test_rls_direct.py`

## Các bước gợi ý

1. Sinh tự động danh sách route từ OpenAPI; với mọi route có tham số ID: dùng ID của workspace A khi đăng nhập B → 404, không lộ dữ liệu.
2. Test RLS trực tiếp bằng SQL cho cả `app_api` và `app_worker` (không scope → 0 hàng).
3. Test view `vw_document_list` không lộ dữ liệu (security_invoker).
4. Test analytics: không có khóa nội dung (CHECK).

## Tiêu chí hoàn thành

- [ ] Mọi route trong OpenAPI được phủ (test fail nếu có route mới chưa khai báo)
- [ ] 0 rò rỉ; mỗi lần bị từ chối có `audit_event access_denied`
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k security
```
