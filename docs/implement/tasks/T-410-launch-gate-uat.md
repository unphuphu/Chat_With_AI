# T-410 — Chạy launch gate và UAT với người dùng PTKD

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 4 |
| **Loại** | QA |
| **User story** | Tất cả (16 P0 + 4 P1 + 1 P2) |
| **Ưu tiên** | P0 |
| **Ước lượng** | 2 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-309, T-310, T-402, T-403, T-405, T-406, T-408, T-409 |
| **Mở khóa (task chờ task này)** | — |
| **Người thực hiện** | _chưa giao_ (QA chủ trì; Tech Lead, BA hỗ trợ) |
| **Trạng thái** | To do |

## 1. Mục tiêu

Kiểm toàn bộ điều kiện launch gate trên staging với bằng chứng cho từng mục, chạy UAT với 3–5 nhân viên PTKD theo kịch bản cho từng story, và lập biên bản quyết định go/no-go có chữ ký để Sponsor quyết định đưa MVP lên production.

## 2. Bối cảnh

- [Implement_plan §8](../Implement_plan.md#8-launch-gate-điều-kiện-lên-production) và PRD §5.1: MVP **không được** lên production nếu bất kỳ điều kiện nào chưa đạt. PRD §5.1 nêu trạng thái hiện tại: gate chưa thể đóng vì OQ-006, OQ-008, OQ-013, OQ-014, OQ-009, OQ-007 còn mở.
- [Implement_plan §7.2](../Implement_plan.md#72-ac--loại-kiểm-thử): AC → loại kiểm thử; các E2E đã có ở T-111, T-213, T-311.
- Persona: nhân viên PTKD (người dùng chính), Sponsor, IT/Bảo mật ([User_Stories §1.1](../../design/User_Stories.md)). RSK-005 (mức sử dụng thấp): UAT cũng thu phản hồi về độ tin cậy và tính dễ dùng.

## 3. Phạm vi

**Trong phạm vi**
- Bảng kiểm launch gate (mục 4.1) với bằng chứng, người chịu trách nhiệm.
- Chuẩn bị và chạy UAT: tài khoản, dữ liệu, kịch bản (mục 4.2), ghi nhận lỗi, phân loại mức độ.
- Họp go/no-go và biên bản (mục 4.3).

**Ngoài phạm vi** (để tránh làm thừa)
- Sửa lỗi phát hiện (tạo ticket, đưa vào kế hoạch sửa); triển khai production.
- Thử nghiệm 4 tuần đo MET-003/MET-004 sau ra mắt (BRD BO-003, `[TBD: OQ-005]`).

## 4. Thiết kế chi tiết

**Sản phẩm bàn giao** `[Proposed]` đường dẫn: `docs/implement/launch/launch_gate_checklist.md`, `docs/implement/launch/uat_scripts.md`, `docs/implement/launch/uat_results.md` (bảng lỗi), `docs/implement/launch/go_no_go_record.md`.

### 4.1 Bảng kiểm launch gate (staging, một git SHA cố định)

| # | Điều kiện (PRD §5.1 / Plan §8) | Bằng chứng bắt buộc | Nguồn | Người chịu trách nhiệm |
|---|---|---|---|---|
| G1 | 100% story P0 (16 story) đạt AC | Kết quả E2E (T-111, T-213, T-311) trên SHA đã chốt + UAT mục 4.2 | Plan §7.2 | QA |
| G2 | CMP-17 đạt MET-002 đã phê duyệt `[TBD: OQ-007]`; AC-010 ≥ 95%; AC-011 ≥ 95% trên ≥ 20 câu; AC-009 | `eval/report.md` chạy với **AI thật** trên bộ câu hỏi OQ-008, ngưỡng đã chốt ở T-310 | T-211, T-310 | QA + Business Owner |
| G3 | ≥ 90% câu trả lời trong ngưỡng `[TBD: OQ-014]` (AC-012) | Báo cáo tải/độ trễ (SP-01 T-309 + chạy lại trên staging) | T-309 | Tech Lead |
| G4 | 100% route nghiệp vụ từ chối khi chưa xác thực/không được cấp quyền (AC-018) | Kết quả T-109 + ma trận vai trò T-405 trên SHA đã chốt | T-109, T-405 | QA |
| G5 | IT/Bảo mật ký hồ sơ tuân thủ (AC-020) | `AC-020_signoff.md` + bản ký, đúng SHA | T-406 (**phụ thuộc OQ-006**) | Tech Lead |
| G6 | OQ-009, OQ-013, OQ-014 đã thay các `[Default]` trong cấu hình | Bảng "biến → giá trị → OQ → ngày chốt" so với cấu hình staging | Plan §3.3, §9.1 | Tech Lead + Business Owner |
| G7 | Báo cáo tuần chạy ≥ 1 chu kỳ, đối soát khớp (AC-021) | `reconcile.md` = `KHỚP` cho 1 tuần đã kết thúc trên staging | T-403 | QA |
| G8 | 100% AC-001…AC-021 có kịch bản kiểm thử và đã pass | Ma trận AC → test → kết quả (mục 4.2 + E2E + CMP-17 + review) | Plan §7.2 | QA |
| G9 | Diễn tập khôi phục thành công; cảnh báo hoạt động; rollback đã thử | Biên bản T-408; bằng chứng nhận cảnh báo T-404/T-409; biên bản rollback T-409 | T-404, T-408, T-409 | DevOps |

Mỗi dòng ghi: **Đạt / Không đạt / Chặn bởi OQ-xxx**, ngày kiểm, liên kết bằng chứng. Gate chỉ "Đạt" khi 9/9 dòng Đạt.

### 4.2 UAT

**Người tham gia:** 3–5 nhân viên PTKD (người dùng chính) do Business Owner chỉ định; 1 Sponsor cho US-F2; quan sát viên: QA (ghi chép), BA. **Dữ liệu:** bộ PDF mẫu DEP-001 trên staging; chỉ dùng tài liệu thật nếu OQ-006 đã cho phép và T-406 đã ký. **Thời lượng:** 60–90 phút/người, người dùng tự thao tác, nói to suy nghĩ (think-aloud); QA không hướng dẫn trừ khi bị kẹt > 3 phút.

**Kịch bản theo story** (mỗi dòng → Đạt/Không đạt + ghi chú; câu hỏi mẫu lấy từ bộ OQ-008, ví dụ dưới là minh họa theo Plan §5):

| # | Story (ưu tiên) | Kịch bản cho người dùng | Kỳ vọng (AC) |
|---|---|---|---|
| U1 | US-E1 (P0) | Mở link ứng dụng ở cửa sổ ẩn danh; đăng nhập | Chưa đăng nhập không thấy thư viện; đăng nhập vào được (AC-018) |
| U2 | US-A1 (P0) | Kéo thả cùng lúc 3 PDF hợp lệ | Cả 3 xuất hiện trong thư viện (AC-001) |
| U3 | US-A2 (P0) | Tải 1 tệp .docx, .jpg, .xlsx | Mỗi tệp bị từ chối, thông báo "chỉ chấp nhận PDF" (AC-002) |
| U4 | US-A3 (P0) | Theo dõi trạng thái tới "Sẵn sàng", hỏi một câu chỉ có trong tệp đó | Trả lời đúng ngay khi sẵn sàng (AC-003) |
| U5 | US-A4 (P0) | Tải 1 PDF scan | Thông báo không thể truy vấn; không bị trích dẫn (AC-004) |
| U6 | US-A5 (P1) | Đọc giới hạn trên màn; tải tệp vượt giới hạn | Bị từ chối kèm giới hạn `[TBD: OQ-013]` (AC-005) |
| U7 | US-B1 (P0) | Xem danh sách thư viện | Đủ tên, người tải, ngày tải, trạng thái (AC-006) |
| U8 | US-B2 (P0) | Xóa tài liệu X; hỏi câu chỉ có trong X | X biến mất; trả "không tìm thấy" (AC-007) |
| U9 | US-D1 (P0) | Tạo hội thoại mới | Hội thoại trống, không mang ngữ cảnh cũ (AC-016) |
| U10 | US-C1 (P0) | Hỏi 3 câu công việc thật theo cách tự nhiên | Câu trả lời đúng theo đánh giá của người dùng (AC-008; chính thức bằng CMP-17) |
| U11 | US-C2 (P0) | Hỏi câu có đáp án ở 2 tài liệu | Đủ thông tin, trích dẫn ≥ 2 tài liệu (AC-009) |
| U12 | US-C3 (P0) | Bấm từng trích dẫn | Mở đúng tài liệu và trang chứa thông tin (AC-010) |
| U13 | US-C4 (P0) | Hỏi câu không có trong thư viện | Khung "Không tìm thấy thông tin", không bịa (AC-011) |
| U14 | US-C5 (P0) | Ghi thời gian chờ mỗi câu hỏi ở U10–U13 | Trong ngưỡng `[TBD: OQ-014]`; thấy trạng thái tiến trình (AC-012) |
| U15 | US-C6 (P1) | Hỏi "Giá gói A?" rồi "Còn gói B thì sao?" | Câu thứ hai nói về gói B (AC-013) |
| U16 | US-C7 (P1) | Chọn phạm vi chỉ tài liệu Y rồi hỏi | Chỉ trích dẫn Y (AC-014) |
| U17 | US-C8 (P0) | Hỏi bằng mỗi ngôn ngữ được duyệt `[TBD: OQ-009]` | Trả lời cùng ngôn ngữ (AC-015) |
| U18 | US-D2 (P2) | Mở Lịch sử, tìm và mở lại hội thoại ở U10 | Thấy đủ câu hỏi/trả lời; người khác không xem được (AC-017) |
| U19 | US-F1 (P1) | Đánh giá 2 câu "Hữu ích", 1 câu "Không hữu ích", bỏ chọn 1 | Ghi nhận; xuất hiện trong báo cáo (AC-019) |
| U20 | US-F2 (P0) — Sponsor | Mở Báo cáo, xem tuần UAT, chuyển tuần | Số khớp với đối soát T-403 (AC-021) |
| U21 | US-E2 (P0) | Không có thao tác UI | Xác nhận bằng G5 (AC-020) |
| U22 | Trạng thái lỗi (PRD §4.2) | QA giả lập AI lỗi, mất mạng, chưa có tài liệu, hỏi quá nhanh | Đúng các trạng thái màn 05; câu hỏi được giữ |

**Phân loại lỗi:** *Critical* (sai dữ liệu, lộ dữ liệu, bịa thông tin có trích dẫn sai, chặn luồng chính) · *High* (story P0 không đạt AC, có cách vòng) · *Medium* (P1/P2 không đạt, khó dùng rõ rệt) · *Low* (thẩm mỹ, câu chữ). Mỗi lỗi: id, kịch bản, bước tái hiện, ảnh chụp, mức độ, người phát hiện.

**Tiêu chí thoát UAT:** 0 lỗi Critical/High mở trên story P0; mọi lỗi Medium có kế hoạch; ≥ 80% người tham gia hoàn thành U2–U14 không cần trợ giúp `[Proposed]`.

**Câu hỏi phản hồi sau phiên** (thang 1–5 + ý kiến): mức tin tưởng câu trả lời; tìm thông tin nhanh hơn cách cũ không (gợi ý cho MET-001, không thay đo chính thức); điều cản trở dùng hằng tuần (RSK-005).

### 4.3 Họp go/no-go và biên bản

**Thành phần:** Sponsor (quyết định), Business Owner, IT/Bảo mật, Tech Lead, QA, BA. **Đầu vào:** bảng kiểm 4.1, kết quả UAT, danh sách lỗi mở, các OQ còn mở. **Biên bản `go_no_go_record.md` bắt buộc có:** ngày; git SHA và phiên bản cấu hình được đánh giá; trạng thái G1–G9; tóm tắt UAT (số người, tỷ lệ đạt, lỗi theo mức độ); quyết định **GO / NO-GO / GO có điều kiện** (điều kiện phải là việc đo được, có hạn, có người chịu trách nhiệm — không được miễn G5 khi OQ-006 chưa có kết quả); chữ ký Sponsor, Business Owner, IT/Bảo mật, Tech Lead.

## 5. Các bước thực hiện

1. Chốt SHA ứng viên phát hành trên staging (T-409); đóng băng thay đổi trừ sửa lỗi.
2. Thu bằng chứng G1–G9; với dòng bị chặn bởi OQ ghi rõ OQ và người cần quyết định.
3. Chuẩn bị UAT: tài khoản MEMBER cho 3–5 người, SPONSOR cho Sponsor; nạp dữ liệu mẫu; in/chia sẻ kịch bản; lịch phiên.
4. Chạy phiên UAT; ghi lỗi vào `uat_results.md`; phân loại mức độ cùng BA/Tech Lead trong ngày.
5. Sửa lỗi Critical/High (ticket riêng), triển khai lại, chạy lại kịch bản liên quan + E2E; cập nhật bằng chứng.
6. Chạy lại đối soát T-403 cho tuần có UAT (U20) khi tuần kết thúc.
7. Tổ chức họp go/no-go; lập và thu chữ ký biên bản.

## 6. Tiêu chí chấp nhận

- [ ] `launch_gate_checklist.md` có đủ G1–G9, mỗi dòng có trạng thái, ngày, liên kết bằng chứng và người chịu trách nhiệm.
- [ ] UAT hoàn tất với ≥ 3 người dùng PTKD + 1 Sponsor; mỗi kịch bản U1–U22 có kết quả ghi nhận.
- [ ] Ma trận AC-001…AC-021 → test → kết quả: 21/21 dòng có kết quả (Đạt hoặc Chặn bởi OQ nêu rõ).
- [ ] 0 lỗi Critical/High mở trên story P0 tại thời điểm họp (hoặc quyết định NO-GO được ghi).
- [ ] Biên bản go/no-go có quyết định và đủ chữ ký các vai trò ở mục 4.3.

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| E2E | Chạy lại toàn bộ Playwright (T-111, T-213, T-311) trên SHA ứng viên | 100% pass |
| Chất lượng | CMP-17 với AI thật, bộ OQ-008 | Đạt G2 |
| Hiệu năng | Script tải trên staging | Đạt G3 |
| Bảo mật | T-109 + ma trận vai trò T-405 | Đạt G4 |
| Đối soát | T-403 trên tuần đã kết thúc | `KHỚP` |
| UAT | U1–U22 | Theo tiêu chí thoát |

## 8. Cấu hình

Không thêm biến. Ghi lại giá trị thực tế trên staging của mọi biến phụ thuộc OQ ([Implement_plan §3.3](../Implement_plan.md#33-biến-môi-trường)): `MAX_UPLOAD_MB`, `MAX_PAGES` (`[TBD: OQ-013]`), `RELEVANCE_THRESHOLD`, `RETRIEVAL_K` (OQ-008/T-310), `ANSWER_TIMEOUT_S` và ngưỡng cảnh báo độ trễ (`[TBD: OQ-014]`), danh sách ngôn ngữ (`[TBD: OQ-009]`), `AI_PROVIDER`/`LLM_MODEL`/`EMBEDDING_MODEL` (OQ-006), `REPORT_TEAM_SIZE` (`[TBD: OQ-015]`), `AUTH_MODE` (OQ-018).

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| OQ-006 chưa có → G5 không đạt, G2/G3 không đo được với AI thật | NO-GO bắt buộc | Chạy UAT với `FakeLlm` chỉ để kiểm luồng/giao diện; ghi rõ G2, G3, G5 "Chặn bởi OQ-006" |
| OQ-007, OQ-008 chưa có → không có mục tiêu MET-002 | G2 không kết luận được | Trình số đo cho Business Owner; ghi "Chặn bởi OQ-007/OQ-008" |
| OQ-009, OQ-013, OQ-014 chưa chốt | G6 không đạt | Nhắc Business Owner trước họp ≥ 1 tuần |
| OQ-018 chưa có IdP | Staging dùng `DevIdentity`; G4 chỉ kiểm cơ chế phiên | Ghi điều kiện: kiểm lại G4 khi bật OIDC |
| Người dùng UAT không đại diện (OQ-003 chưa phỏng vấn) | Phản hồi lệch | Business Owner chọn người từ nhiều vai trò trong đội PTKD |
| Tuần UAT chưa kết thúc khi họp | U20/G7 chưa có số thật | Dùng tuần đã kết thúc trước đó cho G7; bổ sung tuần UAT sau |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §7.1, §7.2, §7.3, §8, §9.1
- [SAD](../../design/SAD.md) §4.1, §4.2, §4.3
- [User_Stories](../../design/User_Stories.md) §1.2 (21 story), §9 (trạng thái lỗi), §11 (OQ)
- [PRD](../../requirements/PRD.md) §5.1, §5.2 · [BRD](../../requirements/BRD.md) AC-001…AC-021
- Màn hình: [html_design/index.html](../../design/html_design/index.html) (01–09)
- Task liên quan: [T-109](./T-109-route-auth-guard-test.md), [T-111](./T-111-e2e-sprint1.md), [T-211](./T-211-eval-harness-v1.md), [T-213](./T-213-e2e-sprint2.md), [T-309](./T-309-spike-sp01-latency.md), [T-310](./T-310-threshold-calibration.md), [T-311](./T-311-e2e-sprint3.md), [T-402](./T-402-weekly-report-screen.md), [T-403](./T-403-report-reconciliation.md), [T-405](./T-405-security-hardening.md), [T-406](./T-406-compliance-package.md), [T-408](./T-408-backup-restore-drill.md), [T-409](./T-409-staging-deployment.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)) ở phần áp dụng được.
- [ ] Biên bản go/no-go được lưu và gửi tới Sponsor; lỗi còn mở có ticket và người chịu trách nhiệm.
