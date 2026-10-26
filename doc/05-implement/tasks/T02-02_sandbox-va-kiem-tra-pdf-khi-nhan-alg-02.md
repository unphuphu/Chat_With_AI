# T02-02 – Sandbox và kiểm tra PDF khi nhận (ALG-02)

| Trường | Giá trị |
|---|---|
| Lát | VS-2 – Tải lên một PDF (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T00-04](T00-04_khung-api-settings-loi-rfc-9457-request-id-healt.md) |
| Story | US-003, US-004 |
| Tài liệu tham chiếu | BLUEPRINT ALG-02, 3.6.5 (sandbox), DD-02, QA-07; SAD 4.1 bước 1 |

## Mục tiêu

Kiểm tra định dạng, số trang, mật khẩu trong tiến trình con bị giới hạn, trả `InspectionResult`.

## Phạm vi file

- `backend/app/infra/sandbox.py`
- `backend/app/modules/documents/pdf_inspector.py`
- `backend/tests/fixtures/pdf/` (hợp lệ, docx đổi đuôi, mã hóa mật khẩu, mã hóa mật khẩu rỗng, 301 trang, hỏng, PDF bom nén nhỏ)
- `backend/tests/unit/test_pdf_inspector.py`

## Các bước gợi ý

1. `sandbox.run(fn, args, timeout_s, mem_mb)`: multiprocessing `spawn`, `RLIMIT_AS`, `RLIMIT_CPU`, không kế thừa socket; trả kết quả hoặc `SandboxTimeout`/`SandboxCrashed`.
2. Semaphore 2 + chờ tối đa 30 s → `SandboxBusy` (→ 503 `server_busy`).
3. Thuật toán đúng ALG-02 (byte `%PDF-`, `decrypt('')`, đếm trang).
4. Sinh fixture bằng script `tests/fixtures/pdf/make_fixtures.py` (không commit file lớn).

## Tiêu chí hoàn thành

- [ ] Mỗi fixture cho đúng kết quả (`ok`/`not_pdf`/`encrypted`/`too_many_pages`)
- [ ] PDF mật khẩu rỗng → ok
- [ ] Hàm treo giả lập → `SandboxTimeout` trong ≤ timeout + 1 s, tiến trình cha vẫn chạy
- [ ] Hàm cấp phát 2 GB → `SandboxCrashed`
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-unit -k 'sandbox or pdf_inspector'
```

## Ngoài phạm vi

- Chỉ chạy trên Linux/container (CI); trên Windows dev đánh dấu skip có lý do

## Kết quả triển khai

**Done** – Sandbox multiprocessing có timeout/giới hạn bộ nhớ (psutil trên Windows); `pdf_inspector.inspect`.
