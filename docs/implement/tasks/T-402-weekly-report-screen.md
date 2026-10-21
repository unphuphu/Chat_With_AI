# T-402 — Dựng màn hình 08 Báo cáo tuần

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 4 |
| **Loại** | Frontend |
| **User story** | US-F2 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 3 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-005, T-401 |
| **Mở khóa (task chờ task này)** | T-410 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Sponsor/Admin mở `/reports/weekly`, chọn tuần bằng nút trước/sau và xem: 4 ô chỉ số, biểu đồ cột số câu hỏi theo ngày (tooltip khi hover/focus, nhãn trên cột cao nhất), hai thanh tỷ lệ có nhãn, bảng chi tiết theo ngày có dòng tổng — giống [08_weekly_report.html](../../design/html_design/08_weekly_report.html) và ảnh [report.png](../../design/images/report.png). Số trên bảng khớp số trên ô chỉ số (điều kiện đối chiếu AC-021).

## 2. Bối cảnh

- US-F2 / BR-021 / AC-021; MET-003, MET-004. Dữ liệu từ API-11 ([T-401](./T-401-weekly-report-api.md)).
- Route và vai trò: [Implement_plan §6.8](../Implement_plan.md#68-ánh-xạ-màn-hình--route-frontend) — `/reports/weekly?weekStart=2026-10-12`, chỉ SPONSOR/ADMIN; AppBar của SPONSOR: "Thư viện · Báo cáo".
- Quy ước frontend: [Implement_plan §4.2](../Implement_plan.md#42-frontend) (TanStack Query, chuỗi trong `vi.json`, truy cập được bằng bàn phím, không chỉ dùng màu).
- Giá trị mục tiêu `[TBD: OQ-007]`; mẫu số "thành viên đội" `[TBD: OQ-015]`.

## 3. Phạm vi

**Trong phạm vi**
- Trang `WeeklyReportPage` và các component con; client API `getWeeklyReport()`; chặn route theo vai trò; chuỗi i18n; trạng thái tải/lỗi/rỗng; responsive theo breakpoint của thiết kế.

**Ngoài phạm vi** (để tránh làm thừa)
- Khối "Ghi chú thiết kế" (`details.notes`) — chỉ có trong bản thiết kế, **không** đưa vào sản phẩm.
- Xuất PDF/CSV, chọn khoảng ngày tùy ý, so sánh nhiều tuần.
- Thư viện biểu đồ ngoài: vẽ bằng SVG thuần như thiết kế (không thêm phụ thuộc).

## 4. Thiết kế chi tiết

**File cần tạo/sửa**

| File | Nội dung |
|---|---|
| `frontend/src/pages/WeeklyReport/WeeklyReportPage.tsx` | Trang, đọc/ghi `weekStart` trên URL |
| `frontend/src/pages/WeeklyReport/WeekPicker.tsx` | Nhóm nút tuần trước/sau + nhãn tuần |
| `frontend/src/pages/WeeklyReport/KpiTiles.tsx` | 4 ô chỉ số |
| `frontend/src/pages/WeeklyReport/DailyBarChart.tsx` | Biểu đồ cột SVG + tooltip |
| `frontend/src/pages/WeeklyReport/RatioBar.tsx` | Thanh tỷ lệ 2 phần + chú giải |
| `frontend/src/pages/WeeklyReport/DailyTable.tsx` | Bảng chi tiết + dòng tổng |
| `frontend/src/pages/WeeklyReport/format.ts` | `formatWeekLabel()`, `pct()`, `formatInt()` |
| `frontend/src/api/reports.ts` | `getWeeklyReport(weekStart?: string): Promise<WeeklyReport>` + kiểu TS khớp schema T-401 |
| `frontend/src/app/router.tsx` | route `/reports/weekly` bọc `RequireRole roles={['SPONSOR','ADMIN']}` |
| `frontend/src/i18n/vi.json` | khóa `report.*` |
| `frontend/src/styles/tokens.css` | thêm `--series-1`, `--grid` nếu T-005 chưa có |

**Dữ liệu:** `useQuery({ queryKey: ['report','weekly', weekStart ?? 'latest'], queryFn: () => getWeeklyReport(weekStart) })`. Khi URL không có `weekStart`, gọi API không tham số rồi `navigate(?weekStart=<phản hồi.weekStart>, {replace:true})`.

**Bố cục (khớp thiết kế, max-width 1200 px, padding `24px 16px 56px`)**

1. **Page head** (`flex`, `justify-content: space-between`, xuống dòng khi hẹp):
   - Trái: `h1` "Báo cáo sử dụng hằng tuần"; `p` "Số liệu giúp đánh giá MVP trước khi quyết định đầu tư tiếp. Không chứa nội dung câu hỏi hay tài liệu."
   - Phải: `div role="group" aria-label="Chọn tuần"` gồm nút icon 44×44 `aria-label="Tuần trước"` (icon `i-back`), `<output aria-live="polite">` rộng tối thiểu 150 px, chữ đậm, ví dụ `12–18/10/2026`, khác tháng `28/09–04/10/2026`; nút `aria-label="Tuần sau"` (icon `i-next`).
   - Nút "Tuần sau" `disabled` khi `weekStart` là thứ Hai của tuần hiện tại (không cho xem tuần tương lai). Nút "Tuần trước" luôn bật `[Proposed]` (thiết kế khóa ở tuần dữ liệu đầu tiên, nhưng API không trả mốc này).
2. **Ô chỉ số** (`section aria-label="Chỉ số chính"`, lưới 4 cột, gap 12 px; ≤ 900 px: 2 cột; ≤ 480 px: 1 cột). Mỗi ô: nhãn (0,85rem, `--ink2`), giá trị (2rem, đậm), dòng phụ (0,82rem, `--muted`), tùy chọn dòng mục tiêu:

| # | Nhãn | Giá trị | Dòng phụ | Mục tiêu |
|---|---|---|---|---|
| 1 | Người dùng hoạt động | `14 / 18` (`activeUsers / teamSize`); `teamSize = null` → chỉ `14` | `78% thành viên đội · MET-003`; `teamSize = null` → `MET-003` | "Mục tiêu:" + chip `.tbd` "chờ OQ-007" |
| 2 | Câu hỏi đã đặt | `236` | `Trung bình 34 câu hỏi mỗi ngày` (`round(questionsAsked/7)`) | — |
| 3 | Đánh giá “hữu ích” | `74%` = `helpful/(helpful+notHelpful)` | `89 trên 120 lượt đánh giá · MET-004` | "Mục tiêu:" + chip "chờ OQ-007" |
| 4 | Không tìm thấy thông tin | `12%` = `notFound/questionsAsked` | `28 trên 236 câu hỏi` | — |

   Mẫu số = 0 → hiển thị `0%` (không chia cho 0). Chip mục tiêu lấy chuỗi từ `vi.json` (`report.target.pending`); khi OQ-007 chốt chỉ đổi chuỗi/cấu hình.
3. **Biểu đồ** (`section.card`, `aria-labelledby`): tiêu đề `h2` "Số câu hỏi theo ngày"; bên phải (muted) "Tổng 236 câu hỏi · Token vào ≈ 1,24 triệu, ra ≈ 0,31 triệu" (token ÷ 10⁶, 2 chữ số, dấu phẩy thập phân).
   - `svg viewBox="0 0 720 260" role="img" aria-label="Biểu đồ cột số câu hỏi theo ngày trong tuần. Chi tiết ở bảng bên dưới."`, rộng 100%.
   - Lề L40 R12 T24 B30. Trục y: đỉnh = `ceil(max/20)*20`, vạch mỗi 20 (đường `0` dùng lớp `axis`, còn lại `grid`), nhãn vạch 11 px `--muted` canh phải tại x = 32. `max = 0` → đỉnh 20 `[Proposed]`. Nếu đỉnh > 100 thì chọn bước "tròn" để có ≤ 6 vạch `[Proposed]`.
   - 7 cột (T2…CN), một chuỗi màu `--series-1`, rộng 44, căn giữa ô `iw/7`, bo góc trên 4 px, cao tối thiểu 2 px. Nhãn trục x `T2 … CN` ở y = 250.
   - **Nhãn trực tiếp** (12 px, đậm, `--ink`) chỉ trên cột có giá trị lớn nhất (mọi cột bằng max đều có nhãn), cách đỉnh 6 px.
   - Mỗi cột `tabindex="0" role="img" aria-label="T2 12/10: 38 câu hỏi"`; hover/focus: sáng hơn (`filter: brightness(1.15)`), `:focus-visible` viền 2 px `--ink`.
   - **Tooltip** (`div role="status"`, `position: fixed`, nền `--ink`, chữ `--surface`, bo 8 px): nội dung "**T2 12/10**" xuống dòng "38 câu hỏi · 9 người dùng"; đặt phía trên giữa cột, không tràn mép phải (cách 8 px). Hiện khi `mouseover`/`focusin`, ẩn khi `mouseout`/`focusout` và khi nhấn `Esc`.
4. **Hai thẻ tỷ lệ** (lưới 2 cột gap 16 px; ≤ 900 px: 1 cột):
   - "Kết quả trả lời": thanh cao 14 px bo tròn, 2 phần cách nhau 2 px — `answered` (màu `--series-1`) và `notFound` (màu `--warn`), độ rộng theo `% trên answered+notFound`; `role="img" aria-label="Có nguồn 88%, Không tìm thấy 12%"`. Chú giải: ô màu 10 px + "Có nguồn trích dẫn: **208 (88%)**", "Không tìm thấy thông tin: **28 (12%)**".
   - "Đánh giá của người dùng": tương tự với "Hữu ích: **89 (74%)**", "Không hữu ích: **31 (26%)**".
   - Tổng = 0: thanh chỉ có nền `--surface2`, nhãn `0 (0%)`.
5. **Bảng "Chi tiết theo ngày"** (`table.t` trong `.table-wrap` cuộn ngang khi hẹp): cột `Ngày | Người dùng hoạt động | Câu hỏi | Có nguồn | Không tìm thấy | Hữu ích | Không hữu ích` (`th scope="col"`, cột số canh phải, `tabular-nums`). 7 dòng `T2 12/10` … `CN 18/10`. Dòng cuối `th scope="row"` "Tổng tuần", số in đậm: `activeUsers` **của tuần** (không cộng các ngày), các cột còn lại là giá trị tuần từ API. "Có nguồn" = `answers.answered` (không tính `câu hỏi − không tìm thấy`).
6. Định dạng số `toLocaleString('vi-VN')`; phần trăm `Math.round`.

**Trạng thái giao diện**

| Trạng thái | Hiển thị |
|---|---|
| Đang tải | Khung xương (`.skel`) cho 4 ô, biểu đồ, bảng; nút tuần bị khóa |
| Lỗi mạng/5xx | `banner err` "Không tải được báo cáo." + mã yêu cầu (`requestId`) + nút "Thử lại" (`refetch`) |
| 401 / 403 | Client chung chuyển `/login` / `/error/403` (T-005, T-006); MEMBER gõ URL trực tiếp → `/error/403` |
| Tuần không có hoạt động | Mọi số 0, biểu đồ cột 2 px, thêm `banner info` "Chưa có hoạt động trong tuần này." `[Proposed]` |
| Dữ liệu | Như mục bố cục |

## 5. Các bước thực hiện

1. Viết `api/reports.ts` (kiểu `WeeklyReport`, `DailyRow`) khớp OpenAPI của T-401; mock bằng MSW với dữ liệu tuần `12–18/10/2026` của file HTML.
2. Thêm route + `RequireRole`; mục "Báo cáo" trên AppBar chỉ hiện cho SPONSOR/ADMIN (`aria-current="page"` khi đang ở trang).
3. Làm `format.ts` + test (nhãn tuần cùng tháng/khác tháng/khác năm, `pct` với mẫu 0).
4. Làm `WeekPicker` (cập nhật `?weekStart=` bằng `navigate`, ±7 ngày).
5. Làm `KpiTiles`, `RatioBar`, `DailyTable`.
6. Làm `DailyBarChart` theo thông số SVG mục 4 + tooltip hover/focus/Esc.
7. Đưa toàn bộ chuỗi vào `vi.json` (`report.title`, `report.subtitle`, `report.prevWeek`, `report.nextWeek`, `report.tiles.*`, `report.chart.*`, `report.ratio.*`, `report.table.*`, `report.target.pending`, `report.empty`, `report.error`).
8. Kiểm responsive 1280 / 900 / 480 px; dark mode bằng token; so ảnh với `report.png`.

## 6. Tiêu chí chấp nhận

- [ ] Với dữ liệu mock tuần 12–18/10/2026, màn hình hiển thị đúng: `14 / 18`, `236`, `74%`, `12%`; bảng có 8 dòng, dòng "Tổng tuần" = `14, 236, 208, 28, 89, 31`.
- [ ] Số ở dòng "Tổng tuần" trùng số trên ô chỉ số và trên chú giải thanh tỷ lệ (cùng nguồn dữ liệu API).
- [ ] Bấm "Tuần trước" đổi URL sang `weekStart` − 7 ngày, gọi lại API và `<output>` đọc nhãn tuần mới (`aria-live`); "Tuần sau" bị `disabled` ở tuần hiện tại.
- [ ] Chỉ cột có giá trị lớn nhất có nhãn số trên đỉnh; Tab đến từng cột hiện tooltip "T5 15/10 · 61 câu hỏi · 13 người dùng"; Esc/blur ẩn tooltip.
- [ ] Thanh tỷ lệ có `aria-label` chứa cả hai phần trăm; mỗi phần có nhãn chữ + số (không chỉ dựa vào màu).
- [ ] MEMBER mở `/reports/weekly` → `/error/403`; không thấy mục "Báo cáo" trên AppBar.
- [ ] `teamSize = null` → ô 1 hiển thị số tuyệt đối, không lỗi `NaN`/`Infinity` ở bất kỳ ô nào khi mọi số = 0.
- [ ] Bố cục 4/2/1 cột ở > 900 / ≤ 900 / ≤ 480 px; không cuộn ngang trang ở 360 px (bảng tự cuộn trong khung).
- [ ] Không có chuỗi tiếng Việt viết cứng trong component (kiểm bằng lint/grep).
- [ ] QA đối chiếu ảnh `report.png`: khớp bố cục, màu, thứ tự thành phần.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Unit (Vitest) | `formatWeekLabel('2026-09-28')` | `28/09–04/10/2026` |
| Unit | `pct(0, 0)`, `pct(89, 120)` | `0`, `74` |
| Component | `DailyBarChart` với `[38,52,47,61,29,6,3]` | 7 `path.bar-r`; 1 nhãn `61`; đỉnh trục 80 |
| Component | `DailyBarChart` với hai ngày cùng max | 2 nhãn trực tiếp |
| Component | Focus cột T5 | Tooltip `role=status` chứa "61 câu hỏi · 13 người dùng" |
| Component | `KpiTiles` với `teamSize=null`, mọi số 0 | `0`, `0%`, không `NaN` |
| Component | `DailyTable` | Dòng tổng dùng `activeUsers` tuần (14), không phải tổng ngày (56) |
| Component | Lỗi 500 | Banner lỗi + nút "Thử lại" gọi lại API |
| E2E (Playwright) | Đăng nhập dev vai trò SPONSOR → Báo cáo → tuần trước → tuần sau | URL và nhãn tuần đổi đúng; axe không có vi phạm mức serious |
| E2E | Vai trò MEMBER truy cập URL | Trang 403 |

## 8. Cấu hình

Không thêm biến môi trường. Phụ thuộc cấu hình backend của T-401: `REPORT_TEAM_SIZE` (`[TBD: OQ-015]`), `REPORT_TIMEZONE` `[Proposed]`. Giá trị mục tiêu hiển thị là chuỗi i18n giữ chỗ `[TBD: OQ-007]`.

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| OQ-007 chưa có giá trị mục tiêu | Ô 1 và 3 chỉ có chip "chờ OQ-007" | Giữ chip như thiết kế; đổi chuỗi khi có quyết định |
| OQ-015 chưa có số thành viên | Không có `/ 18` và % | Hiển thị số tuyệt đối |
| Thiết kế tính "Có nguồn" = câu hỏi − không tìm thấy | Lệch nếu có câu hỏi lỗi | Dùng `answers.answered` từ API |
| Ô 4 dùng mẫu số `questionsAsked`, thanh tỷ lệ dùng `answered+notFound` | Có thể chênh vài % khi có câu hỏi lỗi | Giữ theo thiết kế; nêu với PO khi UAT |
| Token trong báo cáo chưa có story (User_Stories §10) | Có thể bị bỏ | Hiển thị theo thiết kế; dễ gỡ (một dòng phụ) |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §4.2, §5.5 (T-402), §6.8
- [SAD](../../design/SAD.md) §2.1, §2.4 (API-11)
- [User_Stories](../../design/User_Stories.md) US-F2, §10
- Màn hình: [html_design/08_weekly_report.html](../../design/html_design/08_weekly_report.html) · ảnh [report.png](../../design/images/report.png) · lỗi [09_access_denied.html](../../design/html_design/09_access_denied.html)
- Task liên quan: [T-005](./T-005-frontend-skeleton.md), [T-401](./T-401-weekly-report-api.md), [T-403](./T-403-report-reconciliation.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] Ảnh chụp màn hình trên staging (dữ liệu mẫu) đính kèm PR, đặt cạnh `report.png`.
