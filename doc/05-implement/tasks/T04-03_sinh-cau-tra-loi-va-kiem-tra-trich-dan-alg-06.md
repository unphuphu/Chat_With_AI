# T04-03 – Sinh câu trả lời và kiểm tra trích dẫn (ALG-06)

| Trường | Giá trị |
|---|---|
| Lát | VS-4 – Hỏi đáp có trích dẫn (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T04-01](T04-01_truy-xuat-ket-hop-va-cong-nguong-alg-05.md), [T04-02](T04-02_llmport-adapter-gia-va-adapter-nha-cung-cap.md) |
| Story | US-013, US-016, US-020 |
| Tài liệu tham chiếu | BLUEPRINT ALG-06, DD-11; SAD ADR-010, 4.3, 7.4; USER_STORIES US-013, US-016, US-020 AC |

## Mục tiêu

Dựng prompt, gọi LLM trong ngân sách thời gian, chỉ chấp nhận trích dẫn hợp lệ, đánh số [n].

## Phạm vi file

- `backend/app/modules/qa/{prompt.py,answerer.py,validator.py}`
- `backend/tests/unit/test_answerer.py`

## Các bước gợi ý

1. `PROMPT_SYSTEM` phiên bản 1 (đúng nội dung ALG-06), hằng `PROMPT_VERSION`.
2. Kiểm tra: mã S# hợp lệ, xóa mã lạ, không còn trích dẫn → INSUFFICIENT, đổi S# → [n] theo thứ tự xuất hiện.
3. Ngân sách: timeout lần đầu `LLM_TIMEOUT_S`; thử lại chỉ khi lỗi trong `LLM_RETRY_WINDOW_S` và còn ≥ 2 s; sửa JSON 1 lần nếu còn ngân sách.

## Tiêu chí hoàn thành

- [ ] Test: LLM trích S9 (không tồn tại) → bị loại; chỉ còn mã lạ → INSUFFICIENT
- [ ] Test: `[S3] … [S1]` → `[1] … [2]` và citations đúng thứ tự
- [ ] Test (đồng hồ giả): lỗi 429 ở 1 s → thử lại với timeout = 15 − 1 − 1,5; lỗi ở 4 s → không thử lại
- [ ] Test: đường xấu nhất ≤ 15 s
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-unit -k answerer
```

## Kết quả triển khai

**Done** – Kiểm tra trích dẫn S#→[n], sửa/loại mã lạ, ngân sách thời gian; unit test.
