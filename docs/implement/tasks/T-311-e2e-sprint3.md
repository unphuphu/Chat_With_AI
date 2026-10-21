# T-311 — Viết E2E Sprint 3 cho AC-012, AC-013, AC-014, AC-015, AC-017, AC-019

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 3 |
| **Loại** | QA |
| **User story** | US-C5, US-C6, US-C7, US-C8, US-D2, US-F1 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 2 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-301, T-302, T-303, T-304, T-307, T-308 |
| **Mở khóa (task chờ task này)** | — |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Mỗi AC của Sprint 3 có ít nhất một kịch bản kiểm thử tự động chạy trên mỗi merge vào `main` (Playwright với `FakeLlm` có kịch bản), cộng một script đo thời gian phản hồi cho AC-012 chạy được với AI thật. Đây là bằng chứng cho dòng "100% AC-001…AC-021 có kịch bản kiểm thử" của launch gate.

## 2. Bối cảnh

- [Implement_plan §7.2](../Implement_plan.md#72-ac--loại-kiểm-thử): AC-012 → test hiệu năng; AC-013, 014, 015, 017, 019 → E2E. §7.1: E2E chạy mỗi merge `main`; hiệu năng cuối Sprint 3 và trước phát hành.
- AC (BRD; [User_Stories](../../design/User_Stories.md)):
  - **AC-012**: ≥ 90% câu trả lời trong ngưỡng `[TBD: OQ-014]` trên bộ câu hỏi kiểm thử.
  - **AC-013**: hỏi nối tiếp "Còn … thì sao?" → trả lời đúng đối tượng mới, cùng chủ đề.
  - **AC-014**: chọn chỉ tài liệu Y → chỉ trích dẫn Y dù X cũng liên quan.
  - **AC-015**: câu hỏi bằng ngôn ngữ được duyệt `[TBD: OQ-009]` → trả lời cùng ngôn ngữ.
  - **AC-017**: mở lại hội thoại cũ thấy đủ hỏi/đáp; người khác không xem được.
  - **AC-019**: đánh giá được ghi nhận và có trong số liệu MET-004.
- Hạ tầng E2E, fixture PDF (`tests/fixtures`) và cơ chế kịch bản `FakeLlm` đã có từ T-111/T-213; bộ câu hỏi `eval/questions.yaml` từ T-009/T-211.

## 3. Phạm vi

**Trong phạm vi**
- 6 file spec Playwright (§4.2) + dữ liệu kịch bản FakeLlm cho chúng.
- Script đo AC-012 `python -m eval.latency` `[Proposed]` (dùng lại client SSE của T-211).
- Kiểm tra phụ trợ ở tầng API/CSDL trong E2E (đọc `usage_event`, `feedback` qua fixture test).
- Đưa các spec vào job CI E2E hiện có.

**Ngoài phạm vi** (để tránh làm thừa)
- Chất lượng nội dung với AI thật (CMP-17, T-211/T-310); kiểm thử tải đầy đủ (T-309).
- Kiểm thử từng trạng thái màn 05 ở mức component (T-307 đã có); ở đây chỉ một kịch bản hồi quy.
- Ký nghiệm thu chính thức (T-410).

## 4. Thiết kế chi tiết

### 4.1 Môi trường

- `docker-compose` với `AI_PROVIDER=fake`, `AUTH_MODE=dev`; `make seed` nạp PDF mẫu; 2 người dùng dev `member_a`, `member_b` (MEMBER) + `sponsor` (SPONSOR).
- Fixture tài liệu: "Hợp đồng khung đối tác A.pdf" (trang 12: điều kiện thanh toán) và "Báo giá dự án Beta Q3-2026.pdf" (trang 5: thanh toán) — **cả hai** chứa từ khóa "thanh toán" (điều kiện của AC-014).
- Biến riêng cho E2E: `RATE_LIMIT_QUESTIONS_PER_MIN=30` (tránh 429 ngẫu nhiên), trừ spec hồi quy 429.
- Thư mục: cùng thư mục E2E của T-111/T-213 (vd. `frontend/e2e/sprint3/`) `[Proposed]`.

### 4.2 Kịch bản

| Spec | AC | Các bước | Khẳng định |
|---|---|---|---|
| `ac013-follow-up.spec.ts` | AC-013 | `member_a` tạo hội thoại mới → hỏi "Điều kiện thanh toán trong hợp đồng khung với đối tác A là gì?" → chờ `final` → hỏi "Còn báo giá dự án Beta thì thanh toán thế nào?" | Câu trả lời 2 có chip trích dẫn "Báo giá dự án Beta Q3-2026.pdf · trang 5"; không có `event: error`. Biến thể: kịch bản FakeLlm `rewrite=timeout` → vẫn có `final` (fallback, T-301) |
| `ac014-scope.spec.ts` | AC-014 | Mở bộ chọn "Phạm vi" → bỏ chọn "Hợp đồng khung đối tác A.pdf" → "Xong" → nhãn "Phạm vi: K tài liệu", chip "Đang hỏi trên: …" → hỏi "Điều kiện thanh toán là gì?" | **Mọi** chip trích dẫn thuộc tài liệu Beta; request có `documentIds`. Phụ: gọi API-09 với id `DELETED` → 422 `INVALID_SCOPE` |
| `ac015-language.spec.ts` | AC-015 | Hỏi câu tiếng Việt có dấu | Giao diện và chữ trạng thái là tiếng Việt (từ `vi.json`); sự kiện `question_asked.language = "vi"`; prompt gửi tới FakeLlm có chỉ thị ngôn ngữ (FakeLlm ghi lại cờ, không ghi nội dung). Ngôn ngữ khác: `[TBD: OQ-009]` — thêm biến thể khi chốt |
| `ac017-history.spec.ts` | AC-017 | `member_a` tạo 2 hội thoại (3 lượt + 1 lượt) → mở `/history` → tìm "thanh toan" → mở hội thoại | Thấy đủ 3 cặp hỏi/đáp với trích dẫn như lúc tạo; có dòng "Chỉ bạn nhìn thấy các hội thoại này."; 1 sự kiện `conversation_resumed`. Đăng nhập `member_b` → `/history` không có hội thoại của A; mở URL `/chat/<id của A>` → trang lỗi; `GET /api/v1/conversations/<id>` → 404 |
| `ac019-feedback.spec.ts` | AC-019 | Hỏi 1 câu → bấm "Hữu ích" → tải lại trang → bấm "Không hữu ích" → bấm lại "Không hữu ích" | Sau bước 2: `aria-pressed="true"`, bảng `feedback` có `helpful`, có 1 `answer_feedback_submitted`; sau tải lại vẫn được nhấn; sau bước 4: rating `not_helpful`; sau bước 5: cả 2 nút `aria-pressed="false"`, không còn dòng `feedback` |
| `chat-states-regression.spec.ts` | (hồi quy T-307) | (a) `context.setOffline(true)` khi đang chờ; (b) FakeLlm `generate=timeout`; (c) `RATE_LIMIT_QUESTIONS_PER_MIN=2`, gửi 3 câu | (a) không có nội dung trả lời dở dang, banner mất mạng, văn bản ô nhập giữ nguyên; (b) banner "Chưa nhận được câu trả lời" + "Gửi lại" thành công; (c) banner "Bạn đang hỏi hơi nhanh" |

Thêm vào mỗi spec: chỉ báo tiến trình xuất hiện ≤ 300 ms sau khi bấm Gửi (đo `performance.now()` trong trang).

### 4.3 AC-012 — đo thời gian phản hồi `[Proposed]`

```bash
python -m eval.latency --base-url https://staging… --questions eval/questions.yaml \
       --threshold-s ${AC012_THRESHOLD_S} --concurrency 1 --out eval/reports/ac012-<ngày>.md
```

- Gửi mọi câu hỏi của bộ kiểm thử qua API-09 (SSE), đo từ lúc gửi tới khi nhận `final` (phía client) và ghi `responseTimeMs`.
- Kết quả: P50, P90, % câu ≤ ngưỡng, danh sách câu vượt (chỉ id). **Đạt** khi ≥ 90% ≤ `AC012_THRESHOLD_S`.
- `AC012_THRESHOLD_S` = giá trị OQ-014; tới khi chốt dùng `15` `[Default]` (mục tiêu nội bộ P90 ≤ 15 s, QAS-01).
- Chạy với AI thật (cần T-208); với FakeLlm chỉ để kiểm script chạy được (không có giá trị nghiệm thu). Lỗi `error`/429 tính là **không đạt** cho câu đó.

### 4.4 Tiện ích test

- `e2e/helpers/db.ts`: truy vấn chỉ đọc `usage_event`, `feedback` (kết nối CSDL test) `[Proposed]`.
- `e2e/helpers/fakeLlm.ts`: đặt kịch bản FakeLlm cho test (dùng cơ chế của T-213).
- `e2e/helpers/login.ts`: đăng nhập dev theo vai trò (T-006/T-111).

## 5. Các bước thực hiện

1. Rà fixture: 2 PDF có cùng từ khóa "thanh toán" ở các trang đã biết; cập nhật `make seed` nếu thiếu.
2. Viết helper §4.4.
3. Viết lần lượt 5 spec AC theo §4.2 (chạy được độc lập, dọn dữ liệu bằng người dùng/hội thoại riêng mỗi spec).
4. Viết spec hồi quy trạng thái.
5. Viết `eval/latency.py`, chạy thử với FakeLlm trên local.
6. Thêm spec vào job E2E của CI; đảm bảo tổng thời gian job tăng ≤ 5 phút.
7. Khi có T-208 + staging: chạy AC-012 và đính kèm báo cáo vào T-410.
8. Cập nhật bảng truy vết AC → kịch bản (README E2E).

## 6. Tiêu chí chấp nhận

- [ ] 6 spec ở §4.2 pass liên tiếp 3 lần trên CI (không flaky).
- [ ] Mỗi AC-013, 014, 015, 017, 019 có ít nhất 1 spec pass, ghi mã AC trong tên test.
- [ ] Spec AC-014 thất bại nếu bỏ bộ lọc phạm vi ở backend (kiểm bằng cách tạm vô hiệu điều kiện `scope` — chứng minh test có tác dụng).
- [ ] Spec AC-017 thất bại nếu bỏ lọc `owner_id` (cùng cách chứng minh).
- [ ] `eval.latency` xuất báo cáo có P50/P90 và % ≤ ngưỡng; chạy được bằng 1 lệnh.
- [ ] Kết quả AC-012 trên staging với AI thật được đính vào T-410 (hoặc ghi ⛔ nếu chưa có T-208/OQ-014).
- [ ] Test không ghi nội dung câu hỏi/câu trả lời vào log CI ngoài văn bản cố định của fixture.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| E2E | `ac013-follow-up` (thường + rewrite timeout) | Trích dẫn Beta trang 5; không lỗi |
| E2E | `ac014-scope` | Chỉ trích dẫn Beta; 422 với id `DELETED` |
| E2E | `ac015-language` | Tiếng Việt; `language="vi"` |
| E2E | `ac017-history` (2 người dùng) | A thấy đủ; B bị từ chối |
| E2E | `ac019-feedback` | Bật/đổi/bỏ đánh giá; dữ liệu đúng |
| E2E | `chat-states-regression` | Banner đúng, không có câu trả lời dở dang |
| Hiệu năng | `eval.latency` trên staging | ≥ 90% ≤ `AC012_THRESHOLD_S` |

## 8. Cấu hình

| Biến | Giá trị | Ghi chú |
|---|---|---|
| `AI_PROVIDER` | `fake` (E2E), thật (AC-012 staging) | |
| `RATE_LIMIT_QUESTIONS_PER_MIN` | `30` cho E2E; `2` cho spec 429 | Ghi đè trong compose test |
| `AC012_THRESHOLD_S` | `15` `[Default]` | **Thay bằng giá trị OQ-014**; tên biến `[Proposed]` (chỉ dùng trong script đo) |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| AC-012 phụ thuộc OQ-014 và AI thật (OQ-006) | Chưa nghiệm thu được | Script sẵn sàng; chạy khi có T-208 |
| AC-015: danh sách ngôn ngữ `[TBD: OQ-009]` | Chỉ kiểm tiếng Việt | Thêm biến thể khi chốt |
| AC-013/AC-015 với FakeLlm chỉ kiểm luồng, không kiểm hiểu ngữ nghĩa | Có thể pass dù AI thật kém | Bổ sung câu hỏi nối tiếp và đa ngôn ngữ vào CMP-17 |
| Tìm kiếm lịch sử có thể bị PO cắt (T-304) | Bước "tìm" trong `ac017` | Bỏ bước tìm, giữ phần còn lại |
| Đếm MET-004 khi đổi/bỏ đánh giá chưa định nghĩa (T-303) | Khẳng định "xuất hiện trong MET-004" | Kiểm dữ liệu nguồn ở đây; đối soát báo cáo ở T-401/T-403 |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §5.4, §7.1, §7.2, §7.3, §8
- [SAD](../../design/SAD.md) §3.2.1 (ngân sách độ trễ), §3.1 (cách ly hội thoại)
- [Blueprint_Design](../../design/Blueprint_Design.md) QAS-01, QAS-13, §3.7
- [User_Stories](../../design/User_Stories.md) US-C5, US-C6, US-C7, US-C8, US-D2, US-F1, §9
- Màn hình: [04_chat.html](../../design/html_design/04_chat.html), [05_chat_states.html](../../design/html_design/05_chat_states.html), [07_history.html](../../design/html_design/07_history.html)
- Task liên quan: [T-301](./T-301-follow-up-rewrite.md), [T-302](./T-302-document-scope.md), [T-303](./T-303-answer-feedback.md), [T-304](./T-304-history-screen.md), [T-307](./T-307-chat-states.md), [T-308](./T-308-i18n.md), [T-213](./T-213-e2e-sprint2.md), [T-410](./T-410-launch-gate-uat.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Bảng truy vết AC → spec được cập nhật trong README E2E.
