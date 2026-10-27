# Kết quả thực thi test case

Tạo lúc 2026-10-27T16:43:31.096Z bằng `app/frontend/evidence/summary.ts`. Mỗi test case có thư mục riêng `test_reports/<tên test case>/` gồm `report.md`, `result.json`, `screenshots/`, `video/`, `logs/`. Ứng dụng được kiểm thử tại **http://localhost:8080/**.

## Tổng hợp

| Kết luận | Số test case |
|---|---|
| ĐẠT | 103 |
| BỊ CHẶN | 21 |
| CẦN NGƯỜI XÁC NHẬN | 6 |
| **Tổng** | **130** |

## Chi tiết

| ID | Tiêu đề | Kết luận | Bước (đạt/tổng) | Ảnh | Video (MB) | Report |
|---|---|---|---|---|---|---|
| UT-001 | Chunker – thuộc tính chia đoạn | ĐẠT | 1/1 | 2 | 0.4 | [report](UT-001_chunker-thuoc-tinh-chia-doan/report.md) |
| UT-002 | Chunker – đoạn không vượt ranh giới trang | ĐẠT | 1/1 | 2 | 0.3 | [report](UT-002_chunker-doan-khong-vuot-ranh-gioi-trang/report.md) |
| UT-003 | Chuẩn hóa văn bản trích xuất | ĐẠT | 1/1 | 2 | 0.4 | [report](UT-003_chuan-hoa-van-ban-trich-xuat/report.md) |
| UT-004 | Trích văn bản và kiểm tra PDF | ĐẠT | 1/1 | 2 | 0.3 | [report](UT-004_trich-van-ban-va-kiem-tra-pdf/report.md) |
| UT-005 | Đánh số lại trích dẫn và loại mã nguồn lạ | ĐẠT | 1/1 | 2 | 0.4 | [report](UT-005_danh-so-lai-trich-dan-va-loai-ma-nguon-la/report.md) |
| UT-006 | Chưa đủ thông tin khi không còn trích dẫn hợp lệ | ĐẠT | 1/1 | 2 | 0.6 | [report](UT-006_chua-du-thong-tin-khi-khong-con-trich-dan-hop-le/report.md) |
| UT-007 | Escape nội dung nguồn trong prompt | ĐẠT | 1/1 | 2 | 0.5 | [report](UT-007_escape-noi-dung-nguon-trong-prompt/report.md) |
| UT-008 | Chu trình circuit breaker | ĐẠT | 1/1 | 2 | 0.6 | [report](UT-008_chu-trinh-circuit-breaker/report.md) |
| UT-009 | Embedding hashing | ĐẠT | 1/1 | 2 | 0.6 | [report](UT-009_embedding-hashing/report.md) |
| UT-010 | Bộ trả lời trích xuất chọn đúng nguồn | ĐẠT | 1/1 | 2 | 0.3 | [report](UT-010_bo-tra-loi-trich-xuat-chon-dung-nguon/report.md) |
| UT-011 | Lọc nội dung nhạy cảm khỏi log | ĐẠT | 1/1 | 2 | 0.3 | [report](UT-011_loc-noi-dung-nhay-cam-khoi-log/report.md) |
| UT-012 | Kiểm tra cấu hình không an toàn | ĐẠT | 1/1 | 2 | 0.4 | [report](UT-012_kiem-tra-cau-hinh-khong-an-toan/report.md) |
| UT-013 | Rate limit cửa sổ cố định | ĐẠT | 1/1 | 2 | 0.7 | [report](UT-013_rate-limit-cua-so-co-dinh/report.md) |
| UT-014 | Ánh xạ lỗi adapter Anthropic | ĐẠT | 1/1 | 2 | 1.4 | [report](UT-014_anh-xa-loi-adapter-anthropic/report.md) |
| UT-015 | Xác thực id_token OIDC | ĐẠT | 1/1 | 2 | 0.7 | [report](UT-015_xac-thuc-id-token-oidc/report.md) |
| INT-001 | Schema, RLS và trigger bất biến | ĐẠT | 1/1 | 2 | 1.0 | [report](INT-001_schema-rls-va-trigger-bat-bien/report.md) |
| INT-002 | Phạm vi workspace không rò giữa transaction | ĐẠT | 1/1 | 2 | 0.4 | [report](INT-002_pham-vi-workspace-khong-ro-giua-transaction/report.md) |
| INT-003 | Ingest đầu-cuối và hỏi đáp có trích dẫn | ĐẠT | 1/1 | 2 | 0.7 | [report](INT-003_ingest-dau-cuoi-va-hoi-dap-co-trich-dan/report.md) |
| INT-004 | Ingest tài liệu lớn 40 trang | ĐẠT | 1/1 | 2 | 1.5 | [report](INT-004_ingest-tai-lieu-lon-40-trang/report.md) |
| INT-005 | Lỗi tạm thời khi ingest → R-04 → xử lý lại | ĐẠT | 1/1 | 2 | 0.7 | [report](INT-005_loi-tam-thoi-khi-ingest-r-04-xu-ly-lai/report.md) |
| INT-006 | Xóa khi đang xử lý thì hủy xử lý | ĐẠT | 1/1 | 2 | 0.7 | [report](INT-006_xoa-khi-dang-xu-ly-thi-huy-xu-ly/report.md) |
| INT-007 | Xóa và purge file gốc | ĐẠT | 1/1 | 2 | 0.6 | [report](INT-007_xoa-va-purge-file-goc/report.md) |
| INT-008 | Sweep phát hiện purge bị sót | ĐẠT | 1/1 | 2 | 1.0 | [report](INT-008_sweep-phat-hien-purge-bi-sot/report.md) |
| INT-009 | Tác vụ bảo trì định kỳ | ĐẠT | 1/1 | 2 | 1.9 | [report](INT-009_tac-vu-bao-tri-dinh-ky/report.md) |
| INT-010 | Câu trả lời trích đúng trang | ĐẠT | 1/1 | 2 | 2.0 | [report](INT-010_cau-tra-loi-trich-dung-trang/report.md) |
| INT-011 | Truy xuất đa tài liệu với ngưỡng dev | ĐẠT | 1/1 | 2 | 1.9 | [report](INT-011_truy-xuat-da-tai-lieu-voi-nguong-dev/report.md) |
| INT-012 | Cổng ngưỡng bỏ qua LLM | ĐẠT | 1/1 | 2 | 1.8 | [report](INT-012_cong-nguong-bo-qua-llm/report.md) |
| INT-013 | Circuit breaker ở mức API | ĐẠT | 1/1 | 2 | 2.1 | [report](INT-013_circuit-breaker-o-muc-api/report.md) |
| INT-014 | Hợp đồng OpenAPI | ĐẠT | 1/1 | 2 | 0.9 | [report](INT-014_hop-dong-openapi/report.md) |
| INT-015 | Adapter tích hợp thật (OIDC, blob, embedding, LLM) | ĐẠT | 1/1 | 2 | 0.8 | [report](INT-015_adapter-tich-hop-that-oidc-blob-embedding-llm/report.md) |
| INT-016 | Integration trên PostgreSQL thật | BỊ CHẶN | 0/1 | 1 | 0.2 | [report](INT-016_integration-tren-postgresql-that/report.md) |
| INT-017 | Chỉ dùng tài liệu Sẵn sàng | ĐẠT | 1/1 | 2 | 3.7 | [report](INT-017_chi-dung-tai-lieu-san-sang/report.md) |
| INT-018 | Sự kiện analytics đầy đủ | ĐẠT | 1/1 | 2 | 0.6 | [report](INT-018_su-kien-analytics-day-du/report.md) |
| API-001 | Đăng nhập OIDC và cookie phiên | ĐẠT | 5/5 | 5 | 0.5 + 0.5 | [report](API-001_dang-nhap-oidc-va-cookie-phien/report.md) |
| API-002 | Callback từ chối người ngoài nhóm và open redirect | ĐẠT | 3/3 | 3 | 0.2 + 0.1 | [report](API-002_callback-tu-choi-nguoi-ngoai-nhom-va-open-redirect/report.md) |
| API-003 | Callback với state sai hoặc hết hạn | ĐẠT | 4/4 | 4 | 0.2 + 0.2 | [report](API-003_callback-voi-state-sai-hoac-het-han/report.md) |
| API-004 | Đăng xuất cần CSRF | ĐẠT | 4/4 | 4 | 0.3 + 0.2 | [report](API-004_dang-xuat-can-csrf/report.md) |
| API-005 | Thông tin người dùng /me | ĐẠT | 3/3 | 3 | 0.2 + 0.1 | [report](API-005_thong-tin-nguoi-dung-me/report.md) |
| API-006 | Lô tải lên quá 10 file | ĐẠT | 3/3 | 3 | 0.4 + 0.2 | [report](API-006_lo-tai-len-qua-10-file/report.md) |
| API-007 | Hạn mức tài liệu mỗi người | ĐẠT | 4/4 | 4 | 1.9 + 2.4 | [report](API-007_han-muc-100-tai-lieu/report.md) |
| API-008 | Tải lên một PDF hợp lệ | ĐẠT | 4/4 | 4 | 1.3 + 1.1 | [report](API-008_tai-len-mot-pdf-hop-le/report.md) |
| API-009 | Tải lên idempotent và lô hết chỗ | ĐẠT | 5/5 | 5 | 0.8 + 0.7 | [report](API-009_tai-len-idempotent-va-lo-het-cho/report.md) |
| API-010 | Từ chối file không hợp lệ | ĐẠT | 6/6 | 6 | 1.7 + 2.2 | [report](API-010_tu-choi-file-khong-hop-le/report.md) |
| API-011 | Biên dung lượng và PDF khóa in | ĐẠT | 4/4 | 4 | 1.4 + 1.6 | [report](API-011_bien-dung-luong-va-pdf-khoa-in/report.md) |
| API-012 | Lô hết hạn, body quá lớn, máy chủ bận | ĐẠT | 4/4 | 4 | 4.1 + 5.6 | [report](API-012_lo-het-han-body-qua-lon-may-chu-ban/report.md) |
| API-013 | Rate limit tải file | ĐẠT | 4/4 | 4 | 2.3 + 4.1 | [report](API-013_rate-limit-tai-file/report.md) |
| API-014 | Danh sách tài liệu | ĐẠT | 2/2 | 2 | 0.6 + 0.1 | [report](API-014_danh-sach-tai-lieu/report.md) |
| API-015 | Xóa tài liệu | ĐẠT | 4/4 | 4 | 0.8 + 0.2 | [report](API-015_xoa-tai-lieu/report.md) |
| API-016 | Xử lý lại chỉ với R-04 | ĐẠT | 7/7 | 7 | 15.0 + 13.2 | [report](API-016_xu-ly-lai-chi-voi-r-04/report.md) |
| API-017 | Tải file gốc để xem | ĐẠT | 4/4 | 4 | 1.8 + 0.3 | [report](API-017_tai-file-goc-de-xem/report.md) |
| API-018 | File của tài liệu đã xóa hoặc của người khác | ĐẠT | 3/3 | 3 | 1.3 + 0.6 | [report](API-018_file-cua-tai-lieu-da-xoa-hoac-cua-nguoi-khac/report.md) |
| API-019 | Hội thoại hiện tại | ĐẠT | 4/4 | 4 | 0.8 + 0.2 | [report](API-019_hoi-thoai-hien-tai/report.md) |
| API-020 | Đặt câu hỏi có trích dẫn | ĐẠT | 4/4 | 4 | 0.6 + 0.1 | [report](API-020_dat-cau-hoi-co-trich-dan/report.md) |
| API-021 | Hỏi khi chưa có tài liệu Sẵn sàng | ĐẠT | 2/2 | 2 | 0.5 + 0.4 | [report](API-021_hoi-khi-chua-co-tai-lieu-san-sang/report.md) |
| API-022 | Đặt câu hỏi idempotent | ĐẠT | 5/5 | 5 | 0.9 + 0.5 | [report](API-022_dat-cau-hoi-idempotent/report.md) |
| API-023 | Kiểm tra câu hỏi không hợp lệ | ĐẠT | 6/6 | 6 | 0.4 + 0.4 | [report](API-023_kiem-tra-cau-hoi-khong-hop-le/report.md) |
| API-024 | Lỗi dịch vụ AI và quá thời gian | ĐẠT | 5/5 | 5 | 2.6 + 3.1 | [report](API-024_loi-dich-vu-ai-va-qua-thoi-gian/report.md) |
| API-025 | Gửi lại câu hỏi bị lỗi | ĐẠT | 4/4 | 4 | 2.1 + 2.0 | [report](API-025_gui-lai-cau-hoi-bi-loi/report.md) |
| API-026 | Rate limit câu hỏi | ĐẠT | 4/4 | 4 | 7.2 + 8.5 | [report](API-026_rate-limit-cau-hoi/report.md) |
| API-027 | Request trùng đang chạy | ĐẠT | 2/2 | 2 | 1.1 + 0.1 | [report](API-027_request-trung-dang-chay/report.md) |
| API-028 | Luồng sự kiện SSE | ĐẠT | 5/5 | 5 | 2.9 + 3.1 | [report](API-028_luong-su-kien-sse/report.md) |
| API-029 | Kiểm tra sức khỏe | ĐẠT | 3/3 | 3 | 0.0 + 0.2 | [report](API-029_kiem-tra-suc-khoe/report.md) |
| API-030 | Hợp đồng API so với openapi.yaml | ĐẠT | 2/2 | 2 | 0.0 + 0.1 | [report](API-030_hop-dong-api-so-voi-openapi-yaml/report.md) |
| API-031 | Mở nguồn không có số trang | ĐẠT | 3/3 | 3 | 2.0 + 0.6 | [report](API-031_mo-nguon-khong-co-so-trang/report.md) |
| E2E-001 | Đăng nhập, tải PDF, hỏi, xem nguồn, xóa | ĐẠT | 9/9 | 9 | 1.6 | [report](E2E-001_dang-nhap-tai-pdf-hoi-xem-nguon-xoa/report.md) |
| E2E-002 | Người ngoài nhóm bị từ chối truy cập | ĐẠT | 4/4 | 4 | 0.1 + 0.1 | [report](E2E-002_nguoi-ngoai-nhom-bi-tu-choi/report.md) |
| E2E-003 | Smoke đầu-cuối qua proxy | ĐẠT | 1/1 | 2 | 0.8 | [report](E2E-003_smoke-dau-cuoi-qua-proxy/report.md) |
| E2E-004 | Tải 10 file song song | ĐẠT | 4/4 | 4 | 3.3 | [report](E2E-004_tai-10-file-song-song/report.md) |
| E2E-005 | Mất mạng khi tải lên và tải lại | ĐẠT | 5/5 | 5 | 0.5 | [report](E2E-005_mat-mang-khi-tai-len-va-tai-lai/report.md) |
| E2E-006 | Rate limit câu hỏi và đếm ngược | ĐẠT | 5/5 | 5 | 7.2 | [report](E2E-006_rate-limit-cau-hoi-va-dem-nguoc/report.md) |
| E2E-007 | Lỗi AI và Gửi lại | ĐẠT | 6/6 | 6 | 4.1 | [report](E2E-007_loi-ai-va-gui-lai/report.md) |
| E2E-008 | Hết phiên khi đang soạn câu hỏi | ĐẠT | 4/4 | 4 | 7.0 | [report](E2E-008_het-phien-khi-dang-soan-cau-hoi/report.md) |
| E2E-009 | Tải lại trang giữa phiên | ĐẠT | 4/4 | 4 | 1.0 | [report](E2E-009_tai-lai-trang-giua-phien/report.md) |
| E2E-010 | Xử lý lại tài liệu lỗi tạm thời | ĐẠT | 6/6 | 6 | 12.2 | [report](E2E-010_xu-ly-lai-tai-lieu-loi-tam-thoi/report.md) |
| E2E-011 | Vượt giới hạn số file và hạn mức | ĐẠT | 3/3 | 3 | 2.7 | [report](E2E-011_vuot-gioi-han-so-file-va-han-muc/report.md) |
| E2E-012 | PDF có một phần là ảnh scan | ĐẠT | 4/4 | 4 | 0.7 | [report](E2E-012_pdf-co-mot-phan-la-anh-scan/report.md) |
| E2E-013 | Trùng tên file | ĐẠT | 4/4 | 4 | 4.7 | [report](E2E-013_trung-ten-file/report.md) |
| E2E-014 | Năm câu hỏi liên tiếp | ĐẠT | 4/4 | 4 | 1.1 | [report](E2E-014_nam-cau-hoi-lien-tiep/report.md) |
| SEC-001 | Truy cập không có phiên | ĐẠT | 4/4 | 4 | 0.3 + 0.6 | [report](SEC-001_truy-cap-khong-co-phien/report.md) |
| SEC-002 | Từ chối theo nhóm IdP và ghi audit | ĐẠT | 3/3 | 3 | 0.3 | [report](SEC-002_tu-choi-theo-nhom-idp-va-ghi-audit/report.md) |
| SEC-003 | Chặn open redirect | ĐẠT | 5/5 | 5 | 0.8 + 0.3 | [report](SEC-003_chan-open-redirect/report.md) |
| SEC-004 | CSRF cho mọi thao tác ghi | ĐẠT | 4/4 | 4 | 1.4 + 1.2 | [report](SEC-004_csrf-cho-moi-thao-tac-ghi/report.md) |
| SEC-005 | Cách ly tài liệu giữa người dùng (IDOR) | ĐẠT | 7/7 | 7 | 1.6 + 1.2 | [report](SEC-005_cach-ly-tai-lieu-giua-nguoi-dung-idor/report.md) |
| SEC-006 | RLS ở mức cơ sở dữ liệu | ĐẠT | 1/1 | 2 | 0.6 | [report](SEC-006_rls-o-muc-co-so-du-lieu/report.md) |
| SEC-007 | Dữ liệu gửi tới nhà cung cấp AI | ĐẠT | 1/1 | 2 | 0.6 | [report](SEC-007_du-lieu-gui-toi-nha-cung-cap-ai/report.md) |
| SEC-008 | Không lộ nội dung trong analytics, audit, log | ĐẠT | 1/1 | 2 | 0.9 | [report](SEC-008_khong-lo-noi-dung-trong-analytics-audit-log/report.md) |
| SEC-009 | Kiểm tra file tải lên an toàn | ĐẠT | 4/4 | 4 | 0.7 + 1.1 | [report](SEC-009_kiem-tra-file-tai-len-an-toan/report.md) |
| SEC-010 | Prompt injection qua tài liệu | ĐẠT | 4/4 | 4 | 1.0 | [report](SEC-010_prompt-injection-qua-tai-lieu/report.md) |
| SEC-011 | Header bảo mật và cookie | ĐẠT | 5/5 | 5 | 0.8 + 0.3 | [report](SEC-011_header-bao-mat-va-cookie/report.md) |
| SEC-012 | Mã hóa khi truyền và khi lưu | BỊ CHẶN | 0/1 | 1 | 0.2 | [report](SEC-012_ma-hoa-khi-truyen-va-khi-luu/report.md) |
| SEC-013 | Rate limit chống lạm dụng | ĐẠT | 4/4 | 4 | 1.6 + 1.5 | [report](SEC-013_rate-limit-chong-lam-dung/report.md) |
| SEC-014 | Quét lỗ hổng thư viện phụ thuộc | ĐẠT | 1/1 | 2 | 1.8 | [report](SEC-014_quet-lo-hong-thu-vien-phu-thuoc/report.md) |
| SEC-015 | Quét bảo mật động (DAST) | BỊ CHẶN | 0/1 | 1 | 0.1 | [report](SEC-015_quet-bao-mat-dong-dast/report.md) |
| ACC-001 | Dùng toàn bộ luồng chính bằng bàn phím | CẦN NGƯỜI XÁC NHẬN | 7/8 | 8 | 1.6 | [report](ACC-001_dung-toan-bo-luong-chinh-bang-ban-phim/report.md) |
| ACC-002 | Trình đọc màn hình NVDA | BỊ CHẶN | 0/1 | 1 | 0.1 | [report](ACC-002_trinh-doc-man-hinh-nvda/report.md) |
| ACC-003 | Độ tương phản màu | ĐẠT | 3/3 | 3 | 2.3 | [report](ACC-003_do-tuong-phan-mau/report.md) |
| ACC-004 | Thuộc tính ARIA | ĐẠT | 5/5 | 5 | 1.2 | [report](ACC-004_thuoc-tinh-aria/report.md) |
| ACC-005 | Quản lý focus | ĐẠT | 6/6 | 6 | 1.4 | [report](ACC-005_quan-ly-focus/report.md) |
| ACC-006 | Trạng thái không chỉ dựa vào màu | CẦN NGƯỜI XÁC NHẬN | 2/3 | 3 | 1.4 | [report](ACC-006_trang-thai-khong-chi-dua-vao-mau/report.md) |
| ACC-007 | Giảm chuyển động | ĐẠT | 3/3 | 3 | 0.7 | [report](ACC-007_giam-chuyen-dong/report.md) |
| UI-001 | So sánh giao diện với thiết kế | CẦN NGƯỜI XÁC NHẬN | 0/10 | 20 | 4.2 | [report](UI-001_so-sanh-giao-dien-voi-thiet-ke/report.md) |
| UI-002 | Độ rộng màn hình | ĐẠT | 4/4 | 4 | 1.1 | [report](UI-002_do-rong-man-hinh/report.md) |
| UI-003 | Trạng thái thành phần | ĐẠT | 5/5 | 5 | 1.0 | [report](UI-003_trang-thai-thanh-phan/report.md) |
| UI-004 | Trạng thái trống và lỗi | CẦN NGƯỜI XÁC NHẬN | 3/4 | 4 | 1.4 | [report](UI-004_trang-thai-trong-va-loi/report.md) |
| UI-005 | Trạng thái chờ | ĐẠT | 3/3 | 3 | 0.7 | [report](UI-005_trang-thai-cho/report.md) |
| UI-006 | Thông báo tự ẩn | ĐẠT | 3/3 | 3 | 1.0 | [report](UI-006_thong-bao-tu-an/report.md) |
| UI-007 | Bộ đếm và giới hạn ký tự | ĐẠT | 3/3 | 3 | 0.6 | [report](UI-007_bo-dem-va-gioi-han-ky-tu/report.md) |
| UI-008 | Giao diện tối | CẦN NGƯỜI XÁC NHẬN | 3/4 | 9 | 1.5 | [report](UI-008_giao-dien-toi/report.md) |
| UI-009 | Tương thích Chrome và Edge | ĐẠT | 2/2 | 4 | 0.1 | [report](UI-009_tuong-thich-chrome-va-edge/report.md) |
| UI-010 | Ngôn ngữ giao diện và câu trả lời | CẦN NGƯỜI XÁC NHẬN | 2/3 | 3 | 0.8 | [report](UI-010_ngon-ngu-giao-dien-va-cau-tra-loi/report.md) |
| UI-011 | Nguồn không có số trang | ĐẠT | 3/3 | 3 | 1.2 | [report](UI-011_nguon-khong-co-so-trang/report.md) |
| PERF-001 | Thời gian trả lời một người dùng | BỊ CHẶN | 0/1 | 1 | 0.2 | [report](PERF-001_thoi-gian-tra-loi-mot-nguoi-dung/report.md) |
| PERF-002 | Hai mươi người hỏi đồng thời | BỊ CHẶN | 0/1 | 1 | 0.2 | [report](PERF-002_hai-muoi-nguoi-hoi-dong-thoi/report.md) |
| PERF-003 | Xử lý file biên 20 MB / 300 trang | ĐẠT | 3/3 | 3 | 1.2 + 0.1 | [report](PERF-003_xu-ly-file-bien-20-mb-300-trang/report.md) |
| PERF-004 | Xử lý hàng loạt nhiều người dùng | BỊ CHẶN | 0/1 | 1 | 0.1 | [report](PERF-004_xu-ly-hang-loat-nhieu-nguoi-dung/report.md) |
| PERF-005 | Chạy bền 2 giờ | BỊ CHẶN | 0/1 | 1 | 0.1 | [report](PERF-005_chay-ben-2-gio/report.md) |
| PERF-006 | Hiệu năng giao diện | ĐẠT | 5/5 | 5 | 19.4 + 30.5 | [report](PERF-006_hieu-nang-giao-dien/report.md) |
| QLT-001 | Độ chính xác câu trả lời | BỊ CHẶN | 0/1 | 1 | 0.2 | [report](QLT-001_do-chinh-xac-cau-tra-loi/report.md) |
| QLT-002 | Đúng tên tài liệu nguồn | BỊ CHẶN | 0/1 | 1 | 0.2 | [report](QLT-002_dung-ten-tai-lieu-nguon/report.md) |
| QLT-003 | Đúng số trang | BỊ CHẶN | 0/1 | 1 | 0.2 | [report](QLT-003_dung-so-trang/report.md) |
| QLT-004 | Từ chối đúng câu hỏi ngoài tài liệu | BỊ CHẶN | 0/1 | 1 | 0.1 | [report](QLT-004_tu-choi-dung-cau-hoi-ngoai-tai-lieu/report.md) |
| QLT-005 | Đa tài liệu và câu hỏi tiếp nối | BỊ CHẶN | 0/1 | 1 | 0.2 | [report](QLT-005_da-tai-lieu-va-cau-hoi-tiep-noi/report.md) |
| UAT-001 | Tải lên một PDF hợp lệ | BỊ CHẶN | 0/1 | 1 | 0.2 | [report](UAT-001_tai-len-mot-pdf-hop-le/report.md) |
| UAT-002 | Tải lên file không phải PDF | BỊ CHẶN | 0/1 | 1 | 0.2 | [report](UAT-002_tai-len-file-khong-phai-pdf/report.md) |
| UAT-003 | Hỏi đáp với tài liệu đã xử lý | BỊ CHẶN | 0/1 | 1 | 0.1 | [report](UAT-003_hoi-dap-voi-tai-lieu-da-xu-ly/report.md) |
| UAT-004 | Câu hỏi cần tổng hợp nhiều file | BỊ CHẶN | 0/1 | 1 | 0.2 | [report](UAT-004_cau-hoi-can-tong-hop-nhieu-file/report.md) |
| UAT-005 | Hỏi nội dung không có trong tài liệu | BỊ CHẶN | 0/1 | 1 | 0.2 | [report](UAT-005_hoi-noi-dung-khong-co-trong-tai-lieu/report.md) |
| UAT-006 | Kiểm tra nguồn câu trả lời | BỊ CHẶN | 0/1 | 1 | 0.2 | [report](UAT-006_kiem-tra-nguon-cau-tra-loi/report.md) |
| UAT-007 | Xóa tài liệu không còn được dùng | BỊ CHẶN | 0/1 | 1 | 0.2 | [report](UAT-007_xoa-tai-lieu-khong-con-duoc-dung/report.md) |
| UAT-008 | Khả dụng với người dùng lần đầu | BỊ CHẶN | 0/1 | 1 | 0.2 | [report](UAT-008_kha-dung-voi-nguoi-dung-lan-dau/report.md) |
