# T-401 — Xây API báo cáo tuần (API-11)

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 4 |
| **Loại** | Backend |
| **User story** | US-F2 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 2 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-110, T-212, T-303 |
| **Mở khóa (task chờ task này)** | T-402, T-403 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Sponsor/Admin gọi `GET /api/v1/reports/weekly?weekStart=YYYY-MM-DD` và nhận số liệu sử dụng của một tuần (thứ Hai → Chủ nhật): số người dùng hoạt động, số câu hỏi, số câu trả lời có nguồn / "không tìm thấy", số đánh giá hữu ích / không hữu ích, token vào/ra — tính **chỉ từ `usage_event`**, kèm phân rã theo ngày cho màn 08. Mỗi lần tạo báo cáo ghi sự kiện `weekly_usage_report_generated`.

## 2. Bối cảnh

- BR-021 / AC-021: báo cáo tuần phải thể hiện số người dùng hoạt động và số câu hỏi **khớp nhật ký sử dụng** của tuần đó. Nhật ký = bảng `usage_event` (SAD §3.1 "Dữ liệu phân tích tách khỏi nội dung", §4.3 "Sự kiện sản phẩm").
- MET-003 (BRD): "Số người dùng hoạt động trong tuần / tổng thành viên đội" — người dùng hoạt động = người **đặt ít nhất 1 câu hỏi** trong tuần. MET-004: "Số đánh giá hữu ích / tổng số đánh giá".
- Hợp đồng API-11: SAD §2.4. Quyền: chỉ `SPONSOR`, `ADMIN` (SAD §4.1.1). Xem báo cáo phải ghi `audit_log` (SAD §4.1.6).
- Các sự kiện nguồn do T-110 (`access_denied`), T-212 (`question_asked`, `answer_returned`), T-303 (`answer_feedback_submitted`) ghi. Task này là nơi ghi `weekly_usage_report_generated` ([Implement_plan §10.2](../Implement_plan.md#102-sự-kiện-telemetry-prd-52)).

## 3. Phạm vi

**Trong phạm vi**
- Router, service, repository, schema Pydantic cho API-11 trong `backend/app/analytics/`.
- Tính tổng tuần + phân rã 7 ngày; quy tắc khử trùng đánh giá (ghi đè/bỏ chọn).
- Kiểm quyền ở service bằng `require_role()`; `audit_log` hành động xem báo cáo; sự kiện `weekly_usage_report_generated`.
- Chỉ mục hỗ trợ truy vấn trên `usage_event` nếu T-004 chưa tạo.

**Ngoài phạm vi** (để tránh làm thừa)
- Giao diện màn 08 (T-402); script đối soát AC-021 (T-403).
- Gửi báo cáo qua email/lịch tự động, xuất file (BRD §5.3 — không có trong MVP).
- Lưu sẵn (materialize) báo cáo; cache — tính trực tiếp mỗi lần gọi (lưu lượng rất thấp, SAD AD-06).

## 4. Thiết kế chi tiết

**File cần tạo/sửa** (theo [Implement_plan §3.1](../Implement_plan.md#31-cấu-trúc-repository-monorepo)):

| File | Nội dung |
|---|---|
| `backend/app/analytics/report_router.py` | `router = APIRouter(prefix="/api/v1/reports")`, `GET /weekly` |
| `backend/app/analytics/report_service.py` | `WeeklyReportService` |
| `backend/app/analytics/report_repository.py` | SQL tổng hợp (chỉ đọc `usage_event`) |
| `backend/app/analytics/report_schemas.py` | `WeeklyReportResponse`, `DailyRow`, `AnswerCounts`, `FeedbackCounts`, `TokenCounts` |
| `backend/app/analytics/week.py` | `resolve_week_start()`, `week_bounds()` (thuần, không I/O) |
| `backend/app/main.py` | gắn `report_router` |
| `backend/migrations/versions/xxxx_usage_event_report_idx.py` | chỉ mục (nếu chưa có) |
| `backend/tests/unit/analytics/test_week.py`, `backend/tests/integration/analytics/test_weekly_report_api.py` | test |

**Chữ ký**

```python
# week.py
def resolve_week_start(raw: str | None, today_local: date) -> date: ...
    # None → thứ Hai của tuần ĐÃ KẾT THÚC gần nhất; raw không phải thứ Hai hoặc > thứ Hai tuần hiện tại → AppError 422
def week_bounds(week_start: date, tz: ZoneInfo) -> tuple[datetime, datetime]: ...
    # [thứ Hai 00:00, thứ Hai kế tiếp 00:00) theo giờ địa phương, trả về timestamptz UTC

# report_service.py
class WeeklyReportService:
    async def get_weekly(self, user: CurrentUser, week_start_raw: str | None) -> WeeklyReport: ...
```

**Hợp đồng API-11** — trường gốc theo SAD §2.4; các trường đánh dấu `*` là bổ sung **tương thích ngược** cần cho màn 08 `[Proposed]`:

```http
GET /api/v1/reports/weekly?weekStart=2026-10-12
Cookie: session=…
```

```json
{
  "weekStart": "2026-10-12",
  "weekEnd": "2026-10-18",
  "timezone": "Asia/Ho_Chi_Minh",
  "teamSize": 18,
  "activeUsers": 14,
  "questionsAsked": 236,
  "answers": { "answered": 208, "notFound": 28 },
  "feedback": { "helpful": 89, "notHelpful": 31 },
  "tokens": { "in": 1239000, "out": 309160 },
  "days": [
    { "date": "2026-10-12", "activeUsers": 9, "questionsAsked": 38,
      "answers": { "answered": 34, "notFound": 4 }, "feedback": { "helpful": 14, "notHelpful": 5 } }
  ],
  "generatedAt": "2026-10-19T02:00:00Z"
}
```

`*` = `weekEnd`, `timezone`, `teamSize` (null nếu chưa cấu hình — `[TBD: OQ-015]`), `days` (luôn đủ 7 phần tử, ngày không có sự kiện trả 0), `generatedAt`.

| Tình huống | HTTP | `error.code` |
|---|---|---|
| Không có phiên | 401 | `UNAUTHENTICATED` |
| Vai trò `MEMBER` | 403 | `FORBIDDEN` (+ `access_denied` qua cơ chế T-110) |
| `weekStart` sai định dạng, không phải thứ Hai, hoặc là tuần tương lai | 422 | mã lỗi kiểm tra đầu vào chung của T-003 (ví dụ `VALIDATION_ERROR` `[Proposed]`) |

**Định nghĩa chỉ số (quy tắc nghiệp vụ phải giữ)**

| Trường | Định nghĩa trên `usage_event` trong `[start, end)` |
|---|---|
| `activeUsers` | `count(DISTINCT user_id)` của `question_asked` (MET-003). Cột tổng ≠ tổng 7 ngày |
| `questionsAsked` | `count(*)` của `question_asked` |
| `answers.answered` / `notFound` | `count(*)` của `answer_returned` theo `properties->>'answer_type'` = `answered` / `not_found` |
| `feedback.*` | Với mỗi `properties->>'message_id'`, lấy sự kiện `answer_feedback_submitted` **mới nhất** trong tuần; đếm theo `rating` `helpful` / `not_helpful`; sự kiện mới nhất là bỏ chọn (`rating` null — theo T-303) thì không đếm |
| `tokens.in` / `out` | `sum` của `properties->>'tokens_in'` / `'tokens_out'` trong `answer_returned`. Nếu T-212 chưa ghi hai thuộc tính này, bổ sung vào emitter của T-212 trong task này `[Proposed]` |

**SQL** (repository; tham số `:start`, `:end`, `:tz`):

```sql
-- Tổng tuần + theo ngày (một lượt quét, GROUPING SETS)
SELECT (occurred_at AT TIME ZONE :tz)::date                                     AS day,
       count(DISTINCT user_id) FILTER (WHERE event_name = 'question_asked')       AS active_users,
       count(*) FILTER (WHERE event_name = 'question_asked')                      AS questions_asked,
       count(*) FILTER (WHERE event_name = 'answer_returned'
                          AND properties->>'answer_type' = 'answered')            AS answered,
       count(*) FILTER (WHERE event_name = 'answer_returned'
                          AND properties->>'answer_type' = 'not_found')           AS not_found,
       coalesce(sum((properties->>'tokens_in')::bigint)
                FILTER (WHERE event_name = 'answer_returned'), 0)                 AS tokens_in,
       coalesce(sum((properties->>'tokens_out')::bigint)
                FILTER (WHERE event_name = 'answer_returned'), 0)                 AS tokens_out
FROM usage_event
WHERE occurred_at >= :start AND occurred_at < :end
  AND event_name IN ('question_asked', 'answer_returned')
GROUP BY GROUPING SETS ((occurred_at AT TIME ZONE :tz)::date, ());   -- day IS NULL = tổng tuần

-- Đánh giá: bản mới nhất mỗi message_id
SELECT day, rating, count(*) AS n
FROM (
  SELECT DISTINCT ON (properties->>'message_id')
         properties->>'rating' AS rating, (occurred_at AT TIME ZONE :tz)::date AS day
  FROM usage_event
  WHERE event_name = 'answer_feedback_submitted'
    AND occurred_at >= :start AND occurred_at < :end
  ORDER BY properties->>'message_id', occurred_at DESC
) latest
WHERE rating IN ('helpful', 'not_helpful')
GROUP BY GROUPING SETS ((day, rating), (rating));
```

```sql
-- Chỉ mục (tạo trên bảng cha phân vùng; PostgreSQL 16 tự tạo trên từng phân vùng)
CREATE INDEX IF NOT EXISTS usage_event_name_time_idx ON usage_event (event_name, occurred_at);
```

**Sự kiện và kiểm toán** (cùng giao dịch, sau khi tính xong):
- `emit("weekly_usage_report_generated", user_id=user.id, properties={"week_start_date": "2026-10-12", "active_user_count": 14, "question_count": 236})` (PRD §5.2). Sự kiện này **không** thuộc nhóm được đếm, nên không làm thay đổi báo cáo.
- `audit_log(action="report_view" [Proposed], target="weekly:2026-10-12", result="success")`.

## 5. Các bước thực hiện

1. Viết `week.py` + test đơn vị (thứ Hai, Chủ nhật, đổi tháng/năm, tuần tương lai, mặc định = tuần đã kết thúc gần nhất theo `REPORT_TIMEZONE`).
2. Thêm `REPORT_TIMEZONE`, `REPORT_TEAM_SIZE` vào settings và `deploy/.env.example`.
3. Viết `report_repository.py` với hai truy vấn trên; thêm migration chỉ mục nếu T-004 chưa có (`\d usage_event` để kiểm).
4. Kiểm tra emitter T-212: `answer_returned.properties` có `tokens_in`, `tokens_out` (số nguyên); nếu chưa, bổ sung + test.
5. Viết `WeeklyReportService.get_weekly()`: `require_role(user, "SPONSOR", "ADMIN")` → tính khoảng → gọi repository → điền đủ 7 ngày → ghi sự kiện + audit → trả DTO.
6. Viết router + schema Pydantic (camelCase alias, `extra="forbid"` cho query), gắn vào `main.py`; xác nhận OpenAPI có API-11.
7. Viết test tích hợp (Testcontainers PostgreSQL) theo mục 7; chạy T-109 để chắc route mới nằm trong danh sách được bảo vệ.

## 6. Tiêu chí chấp nhận

- [ ] `GET /api/v1/reports/weekly?weekStart=2026-10-12` với SPONSOR hoặc ADMIN trả `200` đúng schema mục 4; `days` có đúng 7 phần tử từ `2026-10-12` đến `2026-10-18`.
- [ ] MEMBER → `403 FORBIDDEN`; không phiên → `401 UNAUTHENTICATED`; `weekStart=2026-10-14` (thứ Tư) → `422`.
- [ ] Không có `weekStart` → trả tuần đã kết thúc gần nhất (`weekStart` trong phản hồi là thứ Hai đó).
- [ ] Với dữ liệu mẫu cố định, mọi trường khớp số đếm trực tiếp trên `usage_event` (cùng định nghĩa mục 4); tổng 7 ngày của `questionsAsked`, `answers.*`, `feedback.*` bằng giá trị tuần.
- [ ] Sự kiện lúc Chủ nhật 23:59:59 giờ địa phương thuộc tuần đó; lúc thứ Hai 00:00:00 thuộc tuần sau.
- [ ] Một tin nhắn được đánh giá `helpful` rồi đổi sang `not_helpful` trong tuần chỉ được đếm 1 lần ở `notHelpful`.
- [ ] Mỗi lời gọi thành công ghi đúng 1 `weekly_usage_report_generated` và 1 `audit_log`; không trường nào chứa nội dung câu hỏi/câu trả lời.
- [ ] P95 thời gian phản hồi < 1 s với 100.000 sự kiện trong tuần (đo trong test tích hợp, `[Proposed]`).
- [ ] AC-021 (một phần): số người dùng hoạt động và số câu hỏi khớp nhật ký — xác nhận chính thức ở T-403.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit | `resolve_week_start(None, today=2026-10-21 thứ Tư)` | `2026-10-12` |
| Unit | `resolve_week_start("2026-10-19", today=2026-10-21)` (tuần hiện tại) | `2026-10-19` (cho phép, tuần đang diễn ra) |
| Unit | `"2026-10-26"` (tương lai), `"2026-10-14"`, `"abc"` | `AppError` 422 |
| Unit | `week_bounds(2026-10-12, Asia/Ho_Chi_Minh)` | `2026-10-11T17:00Z` → `2026-10-18T17:00Z` |
| Integration | 3 người hỏi 5/3/0 câu (người thứ 3 chỉ đánh giá) | `activeUsers=2`, `questionsAsked=8` |
| Integration | `answer_returned` 6 `answered` + 2 `not_found` | `answers = {6, 2}` |
| Integration | Đánh giá đổi ý, bỏ chọn, đánh giá ở tuần trước | Đếm theo bản mới nhất trong tuần; bỏ chọn không đếm |
| Integration | Người dùng hỏi T2 và T3 | `days[0].activeUsers=1`, `days[1].activeUsers=1`, tổng tuần `activeUsers=1` |
| Integration | Tuần không có sự kiện | Mọi số = 0, `days` đủ 7 phần tử |
| Integration | MEMBER gọi API | 403, có `access_denied` trong `usage_event` |
| Integration | Gọi 2 lần | 2 sự kiện `weekly_usage_report_generated`, số liệu báo cáo không đổi |
| Contract | Phản hồi so với OpenAPI | Hợp lệ |

## 8. Cấu hình

| Biến | Giá trị | Ghi chú |
|---|---|---|
| `REPORT_TIMEZONE` `[Proposed]` | `Asia/Ho_Chi_Minh` `[Default]` | Ranh giới tuần/ngày. Docs chỉ nói "tuần bắt đầu thứ Hai", chưa nêu múi giờ |
| `REPORT_TEAM_SIZE` `[Proposed]` | trống → `teamSize: null` | Mẫu số MET-003 `[TBD: OQ-015]` ([Implement_plan §9.1](../Implement_plan.md#91-quyết-định-cần-có-và-ảnh-hưởng-tới-lập-trình): "mẫu số lấy từ cấu hình") |
| `DATABASE_URL` | như §3.3 | |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| SAD §2.4 không có phân rã theo ngày nhưng màn 08 cần | Thiếu dữ liệu cho biểu đồ/bảng | Thêm trường `days` tương thích ngược `[Proposed]`; Tech Lead xác nhận |
| `question_asked` có được ghi cho câu hỏi lỗi AI không (SAD §3.2.1 bước 13 ghi cùng giao dịch với câu trả lời) | `questionsAsked` có thể = `answered + notFound` hoặc lớn hơn | Báo cáo dùng nguyên số đếm `question_asked`; không suy diễn `answered = questions − notFound` |
| OQ-015 (số thành viên đội) | Không tính được % MET-003 | `teamSize: null`; giao diện hiển thị số tuyệt đối |
| OQ-007 (giá trị mục tiêu) | Không ảnh hưởng API | API không trả mục tiêu |
| Múi giờ chưa được docs chốt | Lệch ngày ở ranh giới | Cấu hình `REPORT_TIMEZONE`; PO xác nhận |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §4.1, §5.5 (T-401), §6.1 (`usage_event`), §10.1 (API-11), §10.2
- [SAD](../../design/SAD.md) §2.4 (API-11), §3.1, §4.1.1, §4.1.6, §4.3
- [User_Stories](../../design/User_Stories.md) US-F2
- [PRD](../../requirements/PRD.md) §5.2 · [BRD](../../requirements/BRD.md) BR-021, AC-021, MET-003, MET-004
- Màn hình: [html_design/08_weekly_report.html](../../design/html_design/08_weekly_report.html)
- Task liên quan: [T-110](./T-110-telemetry-documents-access.md), [T-212](./T-212-telemetry-qa.md), [T-303](./T-303-answer-feedback.md), [T-402](./T-402-weekly-report-screen.md), [T-403](./T-403-report-reconciliation.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] `.env.example` có `REPORT_TIMEZONE`, `REPORT_TEAM_SIZE`; OpenAPI hiển thị API-11 với ví dụ phản hồi.
