# T-403 — Viết script đối soát báo cáo tuần (AC-021)

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 4 |
| **Loại** | QA |
| **User story** | US-F2 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 1 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-401 |
| **Mở khóa (task chờ task này)** | T-410 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Có một script tự động chứng minh AC-021: các số trên báo cáo tuần (API-11) **khớp** với số đếm thô trên nhật ký `usage_event` của cùng tuần. Script chạy trong CI integration trên mỗi PR, và chạy được trên staging cho một tuần thật để làm bằng chứng launch gate.

## 2. Bối cảnh

- AC-021: "Báo cáo tuần thể hiện số người dùng hoạt động và số câu hỏi khớp với nhật ký sử dụng của tuần đó." Phương pháp kiểm chứng: Inspection ([BRD](../../requirements/BRD.md) BR-021). [Implement_plan §7.2](../Implement_plan.md#72-ac--loại-kiểm-thử): AC-021 → "Script đối soát T-403".
- Launch gate (PRD §5.1 "Đo lường"): báo cáo tuần chạy thử tối thiểu 1 chu kỳ và số liệu khớp với nhật ký thô.
- Script phải là **cài đặt độc lập** với repository của T-401 (viết SQL riêng, đơn giản nhất có thể) — nếu dùng lại code T-401 thì chỉ chứng minh code bằng chính nó.

## 3. Phạm vi

**Trong phạm vi**
- Module CLI `backend/app/analytics/reconcile.py` (so sánh API-11 với truy vấn thô).
- Bộ dữ liệu sinh xác định (deterministic) gồm cả trường hợp biên; test tích hợp trong CI.
- Chế độ "luồng thật": sinh sự kiện bằng cách gọi API thật với `FakeLlm` (hỏi, nhận `not_found`, đánh giá).
- Xuất báo cáo đối soát (Markdown + JSON) làm bằng chứng.

**Ngoài phạm vi** (để tránh làm thừa)
- Kiểm tra giao diện màn 08 (T-402 có test component; E2E trong T-410).
- Đối soát chi phí token với hóa đơn nhà cung cấp AI.

## 4. Thiết kế chi tiết

**File cần tạo**

| File | Nội dung |
|---|---|
| `backend/app/analytics/reconcile.py` | CLI: `python -m app.analytics.reconcile --base-url URL --week-start YYYY-MM-DD --out reconcile.md [--json reconcile.json]` |
| `backend/tests/integration/analytics/fixtures_usage.py` | `seed_week(db, week_start, tz) -> ExpectedTotals` — sinh sự kiện xác định |
| `backend/tests/integration/analytics/test_report_reconciliation.py` | Test CI |
| `.github/workflows/ci.yml` | Bước integration đã chạy `pytest tests/integration` — xác nhận test mới nằm trong đó, không cần job riêng |

**Chữ ký**

```python
@dataclass(frozen=True)
class FieldResult:
    field: str            # "activeUsers", "days[2].questionsAsked", ...
    report: int
    raw: int
    ok: bool

async def raw_counts(conn, start: datetime, end: datetime, tz: str) -> dict[str, int | list]: ...
async def fetch_report(base_url: str, week_start: str, session_cookie: str) -> dict: ...
def compare(report: dict, raw: dict) -> list[FieldResult]: ...
def render_markdown(results: list[FieldResult], meta: dict) -> str: ...
def main(argv: list[str] | None = None) -> int: ...   # 0 = khớp hoàn toàn, 1 = lệch, 2 = lỗi chạy
```

**Truy vấn thô** (cố ý viết theo cách khác T-401: từng con số một truy vấn, không `FILTER`, không `GROUPING SETS`):

```sql
-- người dùng hoạt động
SELECT count(*) FROM (SELECT DISTINCT user_id FROM usage_event
  WHERE event_name = 'question_asked' AND occurred_at >= :start AND occurred_at < :end) u;
-- câu hỏi
SELECT count(*) FROM usage_event
  WHERE event_name = 'question_asked' AND occurred_at >= :start AND occurred_at < :end;
-- answered / not_found
SELECT properties->>'answer_type', count(*) FROM usage_event
  WHERE event_name = 'answer_returned' AND occurred_at >= :start AND occurred_at < :end
  GROUP BY 1;
-- feedback: bản mới nhất mỗi message_id (window function thay vì DISTINCT ON)
SELECT rating, count(*) FROM (
  SELECT properties->>'rating' AS rating,
         row_number() OVER (PARTITION BY properties->>'message_id' ORDER BY occurred_at DESC) AS rn
  FROM usage_event
  WHERE event_name = 'answer_feedback_submitted' AND occurred_at >= :start AND occurred_at < :end) t
WHERE rn = 1 AND rating IN ('helpful','not_helpful') GROUP BY rating;
-- tokens
SELECT coalesce(sum((properties->>'tokens_in')::bigint),0), coalesce(sum((properties->>'tokens_out')::bigint),0)
FROM usage_event WHERE event_name = 'answer_returned' AND occurred_at >= :start AND occurred_at < :end;
```

Theo ngày: lặp 7 lần với `[start + i ngày, start + i+1 ngày)` (tính ranh giới ngày theo `REPORT_TIMEZONE` trong Python, không dùng `AT TIME ZONE` trong SQL).

**Trường được so sánh (phải bằng nhau tuyệt đối):** `activeUsers`, `questionsAsked`, `answers.answered`, `answers.notFound`, `feedback.helpful`, `feedback.notHelpful`, `tokens.in`, `tokens.out`, và cùng các trường cho từng phần tử `days[i]` (trừ token). Thêm 2 kiểm tra nhất quán nội bộ: `Σ days[i].questionsAsked == questionsAsked`; `max(days[i].activeUsers) ≤ activeUsers ≤ Σ days[i].activeUsers`.

**Kiểm tra chéo thông tin (không làm fail):** số tin nhắn `role='user'` trong bảng `message` trong tuần so với `questionsAsked`; in ra chênh lệch để PO hiểu khác biệt (câu hỏi lỗi AI / ngắt kết nối).

**Bộ dữ liệu `seed_week`** (tuần `2026-10-12`, `Asia/Ho_Chi_Minh`):

| Nhóm | Nội dung |
|---|---|
| Thường | 5 người dùng, 40 `question_asked` rải 7 ngày, 40 `answer_returned` (32 `answered`, 8 `not_found`), token ngẫu nhiên có seed cố định |
| Biên thời gian | 1 sự kiện CN 23:59:59.999 (thuộc tuần), 1 sự kiện T2 tuần sau 00:00:00 (không thuộc), 1 sự kiện T2 tuần này 00:00:00 (thuộc) |
| Đánh giá | 1 tin nhắn đổi ý helpful → not_helpful; 1 tin nhắn bỏ chọn; 1 tin nhắn đánh giá lần đầu ở tuần trước, đổi trong tuần này |
| Nhiễu | `document_upload_succeeded`, `access_denied`, `weekly_usage_report_generated` (không được ảnh hưởng số liệu) |
| Người dùng không hỏi | 1 người chỉ đánh giá/tải tài liệu → không tính vào `activeUsers` |

**Báo cáo đầu ra** (`reconcile.md`): tuần, múi giờ, thời điểm chạy, commit/phiên bản, bảng `Trường | Báo cáo | Nhật ký | Kết quả`, dòng tổng kết `KHỚP` / `LỆCH (n trường)`, phần "Kiểm tra chéo" chỉ mang tính thông tin.

## 5. Các bước thực hiện

1. Viết `fixtures_usage.py` sinh sự kiện bằng `INSERT` trực tiếp vào `usage_event` (dùng `random.Random(42)`), trả `ExpectedTotals` tính bằng Python.
2. Viết `raw_counts()` với các truy vấn trên, `compare()`, `render_markdown()`.
3. Viết `main()` (CLI argparse; cookie phiên SPONSOR qua biến `RECONCILE_SESSION_COOKIE` hoặc đăng nhập dev khi `AUTH_MODE=dev`).
4. Test CI kịch bản A — dữ liệu sinh: `seed_week` → gọi API-11 qua `httpx.AsyncClient(app=...)` → `compare` → mọi `ok == True`; đồng thời so với `ExpectedTotals` (3 nguồn khớp nhau).
5. Test CI kịch bản B — luồng thật: tạo 3 người dùng dev, tải 1 PDF mẫu, hỏi 6 câu qua API-09 với `FakeLlm` có kịch bản (4 `answered`, 2 `not_found`), đánh giá 3 câu → chạy đối soát cho tuần hiện tại → khớp.
6. Test âm: sửa tay 1 sự kiện sau khi lấy báo cáo (hoặc mock báo cáo lệch 1) → `main()` trả `1` và báo đúng trường lệch.
7. Viết hướng dẫn chạy trên staging trong docstring module (dùng ở T-410): chạy cho tuần đã kết thúc gần nhất, lưu `reconcile.md` vào bằng chứng launch gate.

## 6. Tiêu chí chấp nhận

- [ ] `pytest tests/integration/analytics/test_report_reconciliation.py` chạy trong CI integration trên mỗi PR và pass.
- [ ] Kịch bản A: 100% trường (tuần + 7 ngày) khớp giữa API-11, truy vấn thô và `ExpectedTotals`.
- [ ] Kịch bản B: báo cáo phản ánh đúng 3 người dùng, 6 câu hỏi, 4/2 answered/not found, 3 đánh giá.
- [ ] Sự kiện T2 00:00:00 tuần sau không được đếm; CN 23:59:59.999 được đếm.
- [ ] Khi có lệch, CLI thoát mã `1` và `reconcile.md` nêu đúng tên trường, giá trị báo cáo, giá trị nhật ký.
- [ ] Script không import `app.analytics.report_repository` / `report_service` (kiểm bằng test import hoặc review).
- [ ] Đã chạy CLI trên staging cho ít nhất 1 tuần đã kết thúc; `reconcile.md` kết quả `KHỚP` được lưu làm bằng chứng cho T-410 (điều kiện launch gate "Đo lường").

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `compare()` với báo cáo = thô | Mọi `ok=True` |
| Unit | `compare()` lệch `activeUsers` 1 | 1 `FieldResult` `ok=False` |
| Unit | Kiểm tra nhất quán: `Σ days.questionsAsked ≠ questionsAsked` | Báo lỗi |
| Integration | Kịch bản A (dữ liệu sinh, biên thời gian, đổi ý đánh giá, nhiễu) | Khớp |
| Integration | Kịch bản B (luồng thật qua API với FakeLlm) | Khớp |
| Integration | Tuần rỗng | Mọi số 0, khớp |
| Integration | Test âm (dữ liệu bị sửa) | CLI trả 1 |
| Thủ công (staging) | Tuần đã kết thúc gần nhất | `reconcile.md` = `KHỚP` |

## 8. Cấu hình

| Biến | Giá trị | Ghi chú |
|---|---|---|
| `DATABASE_URL` | như [Implement_plan §3.3](../Implement_plan.md#33-biến-môi-trường) | Trên staging dùng tài khoản **chỉ đọc** `[Proposed]` |
| `REPORT_TIMEZONE` | như T-401 | Phải trùng với API |
| `RECONCILE_SESSION_COOKIE` `[Proposed]` | — | Chỉ cho lần chạy staging; không commit, không log |
| `AUTH_MODE` | `dev` trong CI | |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Định nghĩa "người dùng hoạt động" (MET-003 = có ≥ 1 câu hỏi) chưa được Sponsor xác nhận lại | Đối soát đúng code nhưng sai kỳ vọng | Ghi định nghĩa trong `reconcile.md`; xác nhận ở UAT (T-410) |
| Sự kiện ghi trễ/cuối tuần đang chạy | Lệch khi chạy cho tuần chưa kết thúc | Trên staging chỉ chạy cho tuần **đã kết thúc** |
| Truy vấn thô và T-401 cùng sai một quy tắc (ví dụ khử trùng đánh giá) | Không phát hiện | `ExpectedTotals` tính bằng Python là nguồn thứ ba độc lập |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §5.5 (T-403), §7.1, §7.2, §8
- [SAD](../../design/SAD.md) §2.4 (API-11), §4.3 (sự kiện sản phẩm)
- [User_Stories](../../design/User_Stories.md) US-F2
- [PRD](../../requirements/PRD.md) §5.1, §5.2 · [BRD](../../requirements/BRD.md) AC-021
- Task liên quan: [T-401](./T-401-weekly-report-api.md), [T-410](./T-410-launch-gate-uat.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] `reconcile.md` của lần chạy staging được đính kèm vào hồ sơ launch gate.
