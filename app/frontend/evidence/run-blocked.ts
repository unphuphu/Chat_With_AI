// Ghi report BỊ CHẶN (ảnh + video + report.md) cho các test case không thực thi được ở môi trường hiện tại.
//   node evidence/run-blocked.ts
import { spawnSync } from 'node:child_process'

const NO_STAGING = 'Chưa có môi trường staging (HTTPS, PostgreSQL thật, S3, embedding bge-m3, LLM được duyệt) – T10-05 chưa triển khai.'
const NO_K6 = 'Máy dev chưa có k6 và chưa có staging; kết quả trên PGlite (một kết nối) không đại diện cho hiệu năng thật.'
const NO_QSET = 'Chưa có bộ câu hỏi chuẩn + đáp án (DEP-005 / T06-03) và tài liệu dự án thật do PO cung cấp; chưa có LLM thật.'
const NO_HUMAN = 'Cần người dùng nghiệp vụ/PO thực hiện và ký xác nhận trên môi trường nghiệm thu – agent không thể thay thế.'

const cases: [string, string, string, string][] = [
  ['INT-016_integration-tren-postgresql-that', 'Integration trên PostgreSQL thật', 'Máy dev chưa có PostgreSQL 16+ có extension pgvector và chưa có Docker; CI (GitHub Actions) chưa chạy.', 'Có PostgreSQL pgvector (đặt TEST_DATABASE_URL) hoặc chạy CI app/.github/workflows/ci.yml ở gốc repo.'],
  ['SEC-012_ma-hoa-khi-truyen-va-khi-luu', 'Mã hóa khi truyền và khi lưu', 'Ứng dụng dev chạy HTTP trên localhost; chưa có TLS và chưa có hạ tầng lưu trữ mã hóa. ' + NO_STAGING, 'Staging có HTTPS (COOKIE_SECURE=true), cấu hình mã hóa ổ đĩa CSDL/object storage, người đánh giá IT/Security.'],
  ['SEC-015_quet-bao-mat-dong-dast', 'Quét bảo mật động (DAST)', 'Chưa có OWASP ZAP (cần Docker hoặc bản cài đặt) và chưa có staging. ' + NO_STAGING, 'Cài ZAP, chạy zap-baseline.py trên staging, IT/Security phân loại cảnh báo.'],
  ['PERF-001_thoi-gian-tra-loi-mot-nguoi-dung', 'Thời gian trả lời một người dùng', NO_K6 + ' Bộ trả lời trích xuất (offline) không phản ánh độ trễ của LLM thật; ngoài ra giới hạn 10 câu/phút khiến 50 câu cần ≥ 5 phút.', 'Staging + LLM thật + tài khoản có 100 tài liệu Sẵn sàng + k6.'],
  ['PERF-002_hai-muoi-nguoi-hoi-dong-thoi', 'Hai mươi người hỏi đồng thời', NO_K6 + ' CSDL dev chỉ nhận một kết nối nên không thể kiểm tải đồng thời.', 'Staging với DB_MODE=pool + 20 tài khoản test + k6.'],
  ['PERF-004_xu-ly-hang-loat-nhieu-nguoi-dung', 'Xử lý hàng loạt nhiều người dùng', NO_K6 + ' Chế độ một tiến trình/một kết nối không đại diện cho worker thật.', 'Staging với worker riêng + 5 tài khoản test + k6.'],
  ['PERF-005_chay-ben-2-gio', 'Chạy bền 2 giờ', NO_K6, 'Staging + k6 + giám sát bộ nhớ/kết nối trong 2 giờ.'],
  ['QLT-001_do-chinh-xac-cau-tra-loi', 'Độ chính xác câu trả lời', NO_QSET, 'Bộ câu hỏi chuẩn DEP-005 (≥ 50 câu trong tài liệu), script đánh giá app/backend/scripts/eval_rag.py, 2 người chấm nghiệp vụ.'],
  ['QLT-002_dung-ten-tai-lieu-nguon', 'Đúng tên tài liệu nguồn', NO_QSET, 'Kết quả QLT-001 và đáp án chuẩn có tài liệu nguồn.'],
  ['QLT-003_dung-so-trang', 'Đúng số trang', NO_QSET, 'Kết quả QLT-001, PDF gốc để đối chiếu từng trang, người chấm.'],
  ['QLT-004_tu-choi-dung-cau-hoi-ngoai-tai-lieu', 'Từ chối đúng câu hỏi ngoài tài liệu', NO_QSET, '≥ 20 câu hỏi ngoài tài liệu trong bộ câu hỏi chuẩn.'],
  ['QLT-005_da-tai-lieu-va-cau-hoi-tiep-noi', 'Đa tài liệu và câu hỏi tiếp nối', NO_QSET + ' US-015 (câu hỏi tiếp nối) chưa triển khai (OQ-012).', '≥ 20 câu đa tài liệu + 10 cặp tiếp nối; triển khai US-015.'],
  ['UAT-001_tai-len-mot-pdf-hop-le', 'Tải lên một PDF hợp lệ', NO_HUMAN, 'Người dùng nghiệp vụ, tài liệu dự án thật, staging. (Luồng tương ứng đã đạt ở E2E-001/E2E-003 trên bản demo.)'],
  ['UAT-002_tai-len-file-khong-phai-pdf', 'Tải lên file không phải PDF', NO_HUMAN, 'Người dùng nghiệp vụ trên staging. (Tương ứng E2E-001, API-010 đã đạt trên bản demo.)'],
  ['UAT-003_hoi-dap-voi-tai-lieu-da-xu-ly', 'Hỏi đáp với tài liệu đã xử lý', NO_HUMAN, 'Người dùng nghiệp vụ, tài liệu dự án thật, LLM thật.'],
  ['UAT-004_cau-hoi-can-tong-hop-nhieu-file', 'Câu hỏi cần tổng hợp nhiều file', NO_HUMAN, 'Người dùng nghiệp vụ; LLM thật để nêu mâu thuẫn.'],
  ['UAT-005_hoi-noi-dung-khong-co-trong-tai-lieu', 'Hỏi nội dung không có trong tài liệu', NO_HUMAN, 'Người dùng nghiệp vụ trên staging.'],
  ['UAT-006_kiem-tra-nguon-cau-tra-loi', 'Kiểm tra nguồn câu trả lời', NO_HUMAN, 'Người dùng nghiệp vụ đối chiếu trang với tài liệu thật.'],
  ['UAT-007_xoa-tai-lieu-khong-con-duoc-dung', 'Xóa tài liệu không còn được dùng', NO_HUMAN, 'Người dùng nghiệp vụ trên staging.'],
  ['UAT-008_kha-dung-voi-nguoi-dung-lan-dau', 'Khả dụng với người dùng lần đầu', NO_HUMAN + ' Cần ≥ 5 người chưa từng dùng ứng dụng.', '≥ 5 người tham gia, kịch bản nhiệm vụ, ghi video màn hình từng người.'],
  ['ACC-002_trinh-doc-man-hinh-nvda', 'Trình đọc màn hình NVDA', 'Cần NVDA (trình đọc màn hình) trên máy Windows và người nghe/đánh giá đầu ra giọng đọc; Playwright không điều khiển được NVDA.', 'Cài NVDA + Speech Viewer, người thực hiện, quay toàn màn hình.'],
]

for (const [tc, title, reason, need] of cases) {
  const r = spawnSync(process.execPath, ['evidence/blocked.ts', '--tc', tc, '--title', title, '--reason', reason, '--need', need], { encoding: 'utf8' })
  console.log((r.stdout.match(/\[evidence\] .*/g) ?? [`LỖI ${tc}: ${r.stderr.slice(-200)}`]).pop())
}
