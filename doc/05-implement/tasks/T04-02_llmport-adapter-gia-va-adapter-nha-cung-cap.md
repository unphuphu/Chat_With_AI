# T04-02 – LlmPort, adapter giả và adapter nhà cung cấp

| Trường | Giá trị |
|---|---|
| Lát | VS-4 – Hỏi đáp có trích dẫn (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Ready (giả định)** |
| Phụ thuộc | [T00-04](T00-04_khung-api-settings-loi-rfc-9457-request-id-healt.md) |
| Story | US-012 |
| Tài liệu tham chiếu | BLUEPRINT 3.2.2 (`LlmPort`), DE-13, DD-07; SAD ADR-007, 6.2; PRD NFR-011 |

## Mục tiêu

Gọi LLM qua interface trả JSON đúng schema; mặc định dùng adapter giả để phát triển và test.

## Phạm vi file

- `backend/app/ports/llm.py` (lỗi chuẩn hóa)
- `backend/app/adapters/llm_fake.py` (kịch bản: answered/insufficient/invalid/timeout/5xx)
- `backend/app/adapters/llm_anthropic.py` (`LLM_MODEL=claude-sonnet-5-5`, structured output theo schema `LlmAnswer`)
- `backend/tests/unit/test_llm_contract.py`

## Các bước gợi ý

1. `complete_json(system, user, schema, max_output_tokens, timeout_s)`; ánh xạ 429/5xx/timeout/JSON sai sang lỗi chuẩn.
2. Adapter thật chỉ bật khi có `LLM_API_KEY`; không ghi prompt/phản hồi vào log.
3. Contract test: payload gửi đi chỉ chứa prompt hệ thống, câu hỏi và nội dung đoạn có nhãn S1…S8 – không có `document_id`, tên file, số trang, email.

## Tiêu chí hoàn thành

- [ ] Unit test adapter giả cho 5 kịch bản
- [ ] Contract test NFR-011 xanh cho cả 2 adapter (adapter thật dùng HTTP mock)
- [ ] Adapter thật chạy được với key thử nghiệm (thủ công, ghi kết quả vào PR) – bỏ qua nếu chưa có quyền (OQ-005)
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-unit -k llm
```

## Ngoài phạm vi

- Chọn nhà cung cấp chính thức chờ OQ-005 – chỉ thêm adapter khác nếu được yêu cầu
