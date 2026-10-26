# T09-01 – Circuit breaker LLM và ánh xạ 503/504 (ALG-07)

| Trường | Giá trị |
|---|---|
| Lát | VS-9 – Lỗi, giới hạn và phiên (Lát 2) |
| Kích thước | S – khoảng ≤ 200 dòng thay đổi, 1–2 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T04-03](T04-03_sinh-cau-tra-loi-va-kiem-tra-trich-dan-alg-06.md) |
| Story | US-026 |
| Tài liệu tham chiếu | BLUEPRINT ALG-07, 3.7.5; SAD 6.2; PRD E-06 |

## Mục tiêu

Khi LLM lỗi liên tục, trả lỗi ngay thay vì chờ; tự phục hồi.

## Phạm vi file

- `backend/app/infra/circuit.py`
- `backend/tests/unit/test_circuit.py`
- `backend/tests/integration/test_ask_failures.py`

## Các bước gợi ý

1. Đúng ALG-07; `LlmInvalidOutput` không tính; metric `circuit_breaker_state`.
2. Message chuyển FAILED với `error_code`; analytics `answer_failed`.

## Tiêu chí hoàn thành

- [ ] Test: 5 lỗi trong 60 s → OPEN, request tiếp trả 503 < 100 ms với `Retry-After`
- [ ] Test: sau 30 s chỉ 1 request đi qua (HALF_OPEN)
- [ ] Test: LLM giả timeout → 504 `ai_timeout`, message FAILED
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-unit -k circuit && make test-int -k ask_failures
```

## Kết quả triển khai

**Done** – Circuit breaker CLOSED/OPEN/HALF_OPEN, 503 kèm Retry-After / 504.
