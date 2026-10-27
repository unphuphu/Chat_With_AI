# Test case – AI Chat PDF

130 test case tách từ [TEST_PLAN.md v0.2](../TEST_PLAN.md), mỗi file một test case. Mọi test case chạy trên ứng dụng tại **http://localhost:8080/**. Artifact (report, ảnh chụp, video, log) của mỗi test case lưu trong `./test_reports/<tên test case>/` ở gốc repo.

Số lượng: UT 15 · INT 18 · API 31 · E2E 14 · SEC 15 · ACC 7 · UI 11 · PERF 6 · QLT 5 · UAT 8

**Kết quả thực thi chu kỳ C2:** xem [test_reports/README.md](../../../test_reports/README.md) và [TEST_PLAN Phụ lục D](../TEST_PLAN.md#phụ-lục-d--kết-quả-thực-thi-chu-kỳ-c2-27102026).

## Chuẩn bị (một lần)

```bash
cd app
backend/.venv/Scripts/python.exe run.py --sample     # chỉ lần đầu: sinh PDF mẫu (Ctrl+C sau khi thấy 'Sẵn sàng')
cd frontend && npm install && npx playwright install ffmpeg   # ffmpeg để Playwright ghi video
node evidence/app.ts start                            # ứng dụng tại http://localhost:8080/ (chạy nền)
```

Khởi động ứng dụng bằng `evidence/app.ts` (thay vì chạy `run.py` bằng tay) để các test case cần cấu hình riêng (`LLM_PROVIDER`, `SESSION_IDLE_MIN`, `MAX_DOCS_PER_WORKSPACE`…) tự khởi động lại được: `node evidence/app.ts restart KEY=VALUE`, hoặc `await ev.restartApp({...})` trong spec. Dừng: `node evidence/app.ts stop`. Log ứng dụng: `test_reports/_app/app.log`.

## Công cụ thu bằng chứng (`app/frontend/evidence/`)

| File | Dùng cho | Tạo ra |
|---|---|---|
| `fixture.ts` | Test giao diện và API (mode `ui`, `manual`) – spec ở `app/frontend/testcases/<tên test case>.spec.ts`, chạy bằng `npx playwright test -c playwright.testcases.config.ts <tên>` | Video mọi tab, ảnh sau mỗi `ev.step`, `logs/api.log`, `report.md`, `result.json` |
| `record-cli.ts` | Test chạy bằng lệnh (mode `cli`, `staging`): pytest, smoke, k6, pip-audit… – `node evidence/record-cli.ts --tc <tên> --title … -- <lệnh>` | Video trang hiển thị output, ảnh kết quả, `logs/output.log`, `report.md`, `result.json` |
| `app.ts` | Khởi động / khởi động lại / dừng ứng dụng với biến môi trường riêng, chờ `readyz` | `test_reports/_app/app.log` |
| `report.ts` | Mẫu report dùng chung; tự lưu trữ lần chạy cũ vào `test_reports/_archive/` | – |

Cấu trúc thư mục artifact:

```text
test_reports/
└── E2E-002_nguoi-ngoai-nhom-bi-tu-choi/
    ├── report.md          # test report (kết luận, môi trường, bảng bước, link ảnh/video)
    ├── result.json        # cùng nội dung, dạng máy đọc
    ├── screenshots/       # 01-<bước>.png, 02-…
    ├── video/             # <ID>-app.webm (tab ứng dụng), <ID>-page2.webm (tab API) hoặc <ID>-cli.webm
    └── logs/              # api.log hoặc output.log
```

**Mode:** `cli` = chạy lệnh · `ui` = Playwright tự động · `manual` = Playwright + người đánh giá bước 👤 · `staging` = kết quả chính thức cần ENV-STAGING, chạy trên localhost để tham khảo.

## Danh sách

| ID | Tiêu đề | Loại | Ưu tiên | Mode | Trạng thái C1 | Artifact |
|---|---|---|---|---|---|---|
| [UT-001](UT-001_chunker-thuoc-tinh-chia-doan.md) | Chunker – thuộc tính chia đoạn | Unit | High | cli | Đạt (tự động) | `test_reports/UT-001_chunker-thuoc-tinh-chia-doan/` |
| [UT-002](UT-002_chunker-doan-khong-vuot-ranh-gioi-trang.md) | Chunker – đoạn không vượt ranh giới trang | Unit | High | cli | Đạt (tự động) | `test_reports/UT-002_chunker-doan-khong-vuot-ranh-gioi-trang/` |
| [UT-003](UT-003_chuan-hoa-van-ban-trich-xuat.md) | Chuẩn hóa văn bản trích xuất | Unit | High | cli | Đạt (tự động) | `test_reports/UT-003_chuan-hoa-van-ban-trich-xuat/` |
| [UT-004](UT-004_trich-van-ban-va-kiem-tra-pdf.md) | Trích văn bản và kiểm tra PDF | Unit | High | cli | Đạt (tự động) | `test_reports/UT-004_trich-van-ban-va-kiem-tra-pdf/` |
| [UT-005](UT-005_danh-so-lai-trich-dan-va-loai-ma-nguon-la.md) | Đánh số lại trích dẫn và loại mã nguồn lạ | Unit | High | cli | Đạt (tự động) | `test_reports/UT-005_danh-so-lai-trich-dan-va-loai-ma-nguon-la/` |
| [UT-006](UT-006_chua-du-thong-tin-khi-khong-con-trich-dan-hop-le.md) | Chưa đủ thông tin khi không còn trích dẫn hợp lệ | Unit | High | cli | Đạt (tự động) | `test_reports/UT-006_chua-du-thong-tin-khi-khong-con-trich-dan-hop-le/` |
| [UT-007](UT-007_escape-noi-dung-nguon-trong-prompt.md) | Escape nội dung nguồn trong prompt | Unit | High | cli | Đạt (tự động) | `test_reports/UT-007_escape-noi-dung-nguon-trong-prompt/` |
| [UT-008](UT-008_chu-trinh-circuit-breaker.md) | Chu trình circuit breaker | Unit | Medium | cli | Đạt (tự động) | `test_reports/UT-008_chu-trinh-circuit-breaker/` |
| [UT-009](UT-009_embedding-hashing.md) | Embedding hashing | Unit | Medium | cli | Đạt (tự động) | `test_reports/UT-009_embedding-hashing/` |
| [UT-010](UT-010_bo-tra-loi-trich-xuat-chon-dung-nguon.md) | Bộ trả lời trích xuất chọn đúng nguồn | Unit | Medium | cli | Đạt (tự động) | `test_reports/UT-010_bo-tra-loi-trich-xuat-chon-dung-nguon/` |
| [UT-011](UT-011_loc-noi-dung-nhay-cam-khoi-log.md) | Lọc nội dung nhạy cảm khỏi log | Unit | High | cli | Đạt (tự động) | `test_reports/UT-011_loc-noi-dung-nhay-cam-khoi-log/` |
| [UT-012](UT-012_kiem-tra-cau-hinh-khong-an-toan.md) | Kiểm tra cấu hình không an toàn | Unit | Medium | cli | Đạt (tự động) | `test_reports/UT-012_kiem-tra-cau-hinh-khong-an-toan/` |
| [UT-013](UT-013_rate-limit-cua-so-co-dinh.md) | Rate limit cửa sổ cố định | Unit | Medium | cli | Chưa chạy | `test_reports/UT-013_rate-limit-cua-so-co-dinh/` |
| [UT-014](UT-014_anh-xa-loi-adapter-anthropic.md) | Ánh xạ lỗi adapter Anthropic | Unit | Medium | cli | Chưa chạy | `test_reports/UT-014_anh-xa-loi-adapter-anthropic/` |
| [UT-015](UT-015_xac-thuc-id-token-oidc.md) | Xác thực id_token OIDC | Unit | Critical | cli | Chưa chạy | `test_reports/UT-015_xac-thuc-id-token-oidc/` |
| [INT-001](INT-001_schema-rls-va-trigger-bat-bien.md) | Schema, RLS và trigger bất biến | Integration | Critical | cli | Đạt (tự động) | `test_reports/INT-001_schema-rls-va-trigger-bat-bien/` |
| [INT-002](INT-002_pham-vi-workspace-khong-ro-giua-transaction.md) | Phạm vi workspace không rò giữa transaction | Integration | Critical | cli | Đạt (tự động) | `test_reports/INT-002_pham-vi-workspace-khong-ro-giua-transaction/` |
| [INT-003](INT-003_ingest-dau-cuoi-va-hoi-dap-co-trich-dan.md) | Ingest đầu-cuối và hỏi đáp có trích dẫn | Integration | High | cli | Đạt (tự động) | `test_reports/INT-003_ingest-dau-cuoi-va-hoi-dap-co-trich-dan/` |
| [INT-004](INT-004_ingest-tai-lieu-lon-40-trang.md) | Ingest tài liệu lớn 40 trang | Integration | High | cli | Đạt (tự động) | `test_reports/INT-004_ingest-tai-lieu-lon-40-trang/` |
| [INT-005](INT-005_loi-tam-thoi-khi-ingest-r-04-xu-ly-lai.md) | Lỗi tạm thời khi ingest → R-04 → xử lý lại | Integration | Medium | cli | Đạt (tự động) | `test_reports/INT-005_loi-tam-thoi-khi-ingest-r-04-xu-ly-lai/` |
| [INT-006](INT-006_xoa-khi-dang-xu-ly-thi-huy-xu-ly.md) | Xóa khi đang xử lý thì hủy xử lý | Integration | High | cli | Đạt (tự động) | `test_reports/INT-006_xoa-khi-dang-xu-ly-thi-huy-xu-ly/` |
| [INT-007](INT-007_xoa-va-purge-file-goc.md) | Xóa và purge file gốc | Integration | High | cli | Đạt (tự động) | `test_reports/INT-007_xoa-va-purge-file-goc/` |
| [INT-008](INT-008_sweep-phat-hien-purge-bi-sot.md) | Sweep phát hiện purge bị sót | Integration | Medium | cli | Đạt (tự động) | `test_reports/INT-008_sweep-phat-hien-purge-bi-sot/` |
| [INT-009](INT-009_tac-vu-bao-tri-dinh-ky.md) | Tác vụ bảo trì định kỳ | Integration | Medium | cli | Đạt (tự động) | `test_reports/INT-009_tac-vu-bao-tri-dinh-ky/` |
| [INT-010](INT-010_cau-tra-loi-trich-dung-trang.md) | Câu trả lời trích đúng trang | Integration | High | cli | Đạt (tự động) | `test_reports/INT-010_cau-tra-loi-trich-dung-trang/` |
| [INT-011](INT-011_truy-xuat-da-tai-lieu-voi-nguong-dev.md) | Truy xuất đa tài liệu với ngưỡng dev | Integration | High | cli | Đạt (tự động) | `test_reports/INT-011_truy-xuat-da-tai-lieu-voi-nguong-dev/` |
| [INT-012](INT-012_cong-nguong-bo-qua-llm.md) | Cổng ngưỡng bỏ qua LLM | Integration | High | cli | Đạt (tự động) | `test_reports/INT-012_cong-nguong-bo-qua-llm/` |
| [INT-013](INT-013_circuit-breaker-o-muc-api.md) | Circuit breaker ở mức API | Integration | Medium | cli | Đạt (tự động) | `test_reports/INT-013_circuit-breaker-o-muc-api/` |
| [INT-014](INT-014_hop-dong-openapi.md) | Hợp đồng OpenAPI | Integration | High | cli | Đạt (tự động) | `test_reports/INT-014_hop-dong-openapi/` |
| [INT-015](INT-015_adapter-tich-hop-that-oidc-blob-embedding-llm.md) | Adapter tích hợp thật (OIDC, blob, embedding, LLM) | Integration | High | staging | Một phần (smoke đạt 26/10) | `test_reports/INT-015_adapter-tich-hop-that-oidc-blob-embedding-llm/` |
| [INT-016](INT-016_integration-tren-postgresql-that.md) | Integration trên PostgreSQL thật | Integration | High | cli | Chưa chạy | `test_reports/INT-016_integration-tren-postgresql-that/` |
| [INT-017](INT-017_chi-dung-tai-lieu-san-sang.md) | Chỉ dùng tài liệu Sẵn sàng | Integration | High | cli | Chưa chạy | `test_reports/INT-017_chi-dung-tai-lieu-san-sang/` |
| [INT-018](INT-018_su-kien-analytics-day-du.md) | Sự kiện analytics đầy đủ | Integration | High | cli | Chưa chạy | `test_reports/INT-018_su-kien-analytics-day-du/` |
| [API-001](API-001_dang-nhap-oidc-va-cookie-phien.md) | Đăng nhập OIDC và cookie phiên | API | Critical | ui | Đạt (tự động) | `test_reports/API-001_dang-nhap-oidc-va-cookie-phien/` |
| [API-002](API-002_callback-tu-choi-nguoi-ngoai-nhom-va-open-redirect.md) | Callback từ chối người ngoài nhóm và open redirect | API | Critical | ui | Đạt (tự động) | `test_reports/API-002_callback-tu-choi-nguoi-ngoai-nhom-va-open-redirect/` |
| [API-003](API-003_callback-voi-state-sai-hoac-het-han.md) | Callback với state sai hoặc hết hạn | API | High | ui | Chưa chạy | `test_reports/API-003_callback-voi-state-sai-hoac-het-han/` |
| [API-004](API-004_dang-xuat-can-csrf.md) | Đăng xuất cần CSRF | API | Critical | ui | Đạt (tự động) | `test_reports/API-004_dang-xuat-can-csrf/` |
| [API-005](API-005_thong-tin-nguoi-dung-me.md) | Thông tin người dùng /me | API | High | ui | Đạt (tự động) | `test_reports/API-005_thong-tin-nguoi-dung-me/` |
| [API-006](API-006_lo-tai-len-qua-10-file.md) | Lô tải lên quá 10 file | API | High | ui | Đạt (tự động) | `test_reports/API-006_lo-tai-len-qua-10-file/` |
| [API-007](API-007_han-muc-100-tai-lieu.md) | Hạn mức 100 tài liệu | API | High | ui | Đạt (tự động) | `test_reports/API-007_han-muc-100-tai-lieu/` |
| [API-008](API-008_tai-len-mot-pdf-hop-le.md) | Tải lên một PDF hợp lệ | API | High | ui | Đạt (tự động) | `test_reports/API-008_tai-len-mot-pdf-hop-le/` |
| [API-009](API-009_tai-len-idempotent-va-lo-het-cho.md) | Tải lên idempotent và lô hết chỗ | API | High | ui | Đạt (tự động) | `test_reports/API-009_tai-len-idempotent-va-lo-het-cho/` |
| [API-010](API-010_tu-choi-file-khong-hop-le.md) | Từ chối file không hợp lệ | API | High | ui | Đạt (tự động) | `test_reports/API-010_tu-choi-file-khong-hop-le/` |
| [API-011](API-011_bien-dung-luong-va-pdf-khoa-in.md) | Biên dung lượng và PDF khóa in | API | High | ui | Đạt (tự động) | `test_reports/API-011_bien-dung-luong-va-pdf-khoa-in/` |
| [API-012](API-012_lo-het-han-body-qua-lon-may-chu-ban.md) | Lô hết hạn, body quá lớn, máy chủ bận | API | Medium | ui | Chưa chạy | `test_reports/API-012_lo-het-han-body-qua-lon-may-chu-ban/` |
| [API-013](API-013_rate-limit-tai-file.md) | Rate limit tải file | API | Medium | ui | Chưa chạy | `test_reports/API-013_rate-limit-tai-file/` |
| [API-014](API-014_danh-sach-tai-lieu.md) | Danh sách tài liệu | API | High | ui | Đạt (tự động) | `test_reports/API-014_danh-sach-tai-lieu/` |
| [API-015](API-015_xoa-tai-lieu.md) | Xóa tài liệu | API | High | ui | Đạt (tự động) | `test_reports/API-015_xoa-tai-lieu/` |
| [API-016](API-016_xu-ly-lai-chi-voi-r-04.md) | Xử lý lại chỉ với R-04 | API | Medium | ui | Đạt (tự động) | `test_reports/API-016_xu-ly-lai-chi-voi-r-04/` |
| [API-017](API-017_tai-file-goc-de-xem.md) | Tải file gốc để xem | API | Medium | ui | Đạt (tự động) | `test_reports/API-017_tai-file-goc-de-xem/` |
| [API-018](API-018_file-cua-tai-lieu-da-xoa-hoac-cua-nguoi-khac.md) | File của tài liệu đã xóa hoặc của người khác | API | Critical | ui | Đạt (tự động) | `test_reports/API-018_file-cua-tai-lieu-da-xoa-hoac-cua-nguoi-khac/` |
| [API-019](API-019_hoi-thoai-hien-tai.md) | Hội thoại hiện tại | API | Medium | ui | Đạt (tự động) | `test_reports/API-019_hoi-thoai-hien-tai/` |
| [API-020](API-020_dat-cau-hoi-co-trich-dan.md) | Đặt câu hỏi có trích dẫn | API | High | ui | Đạt (tự động) | `test_reports/API-020_dat-cau-hoi-co-trich-dan/` |
| [API-021](API-021_hoi-khi-chua-co-tai-lieu-san-sang.md) | Hỏi khi chưa có tài liệu Sẵn sàng | API | High | ui | Đạt (tự động) | `test_reports/API-021_hoi-khi-chua-co-tai-lieu-san-sang/` |
| [API-022](API-022_dat-cau-hoi-idempotent.md) | Đặt câu hỏi idempotent | API | High | ui | Đạt (tự động) | `test_reports/API-022_dat-cau-hoi-idempotent/` |
| [API-023](API-023_kiem-tra-cau-hoi-khong-hop-le.md) | Kiểm tra câu hỏi không hợp lệ | API | High | ui | Đạt (tự động; spec bằng chứng đạt 26/10) | `test_reports/API-023_kiem-tra-cau-hoi-khong-hop-le/` |
| [API-024](API-024_loi-dich-vu-ai-va-qua-thoi-gian.md) | Lỗi dịch vụ AI và quá thời gian | API | High | ui | Đạt (tự động) | `test_reports/API-024_loi-dich-vu-ai-va-qua-thoi-gian/` |
| [API-025](API-025_gui-lai-cau-hoi-bi-loi.md) | Gửi lại câu hỏi bị lỗi | API | Medium | ui | Đạt (tự động) | `test_reports/API-025_gui-lai-cau-hoi-bi-loi/` |
| [API-026](API-026_rate-limit-cau-hoi.md) | Rate limit câu hỏi | API | Medium | ui | Đạt (tự động) | `test_reports/API-026_rate-limit-cau-hoi/` |
| [API-027](API-027_request-trung-dang-chay.md) | Request trùng đang chạy | API | Medium | ui | Chưa chạy | `test_reports/API-027_request-trung-dang-chay/` |
| [API-028](API-028_luong-su-kien-sse.md) | Luồng sự kiện SSE | API | Medium | ui | Chưa chạy | `test_reports/API-028_luong-su-kien-sse/` |
| [API-029](API-029_kiem-tra-suc-khoe.md) | Kiểm tra sức khỏe | API | Low | ui | Đạt một phần | `test_reports/API-029_kiem-tra-suc-khoe/` |
| [API-030](API-030_hop-dong-api-so-voi-openapi-yaml.md) | Hợp đồng API so với openapi.yaml | API | High | ui | Đạt (tự động) | `test_reports/API-030_hop-dong-api-so-voi-openapi-yaml/` |
| [API-031](API-031_mo-nguon-khong-co-so-trang.md) | Mở nguồn không có số trang | API | Medium | ui | Chưa chạy | `test_reports/API-031_mo-nguon-khong-co-so-trang/` |
| [E2E-001](E2E-001_dang-nhap-tai-pdf-hoi-xem-nguon-xoa.md) | Đăng nhập, tải PDF, hỏi, xem nguồn, xóa | System (E2E) | P0 | ui | Đạt (tự động) | `test_reports/E2E-001_dang-nhap-tai-pdf-hoi-xem-nguon-xoa/` |
| [E2E-002](E2E-002_nguoi-ngoai-nhom-bi-tu-choi.md) | Người ngoài nhóm bị từ chối | System (E2E) | P0 | ui | Đạt (tự động; spec bằng chứng đạt 26/10) | `test_reports/E2E-002_nguoi-ngoai-nhom-bi-tu-choi/` |
| [E2E-003](E2E-003_smoke-dau-cuoi-qua-proxy.md) | Smoke đầu-cuối qua proxy | System (E2E) | P0 | cli | Đạt (thủ công, 26/10) | `test_reports/E2E-003_smoke-dau-cuoi-qua-proxy/` |
| [E2E-004](E2E-004_tai-10-file-song-song.md) | Tải 10 file song song | System (E2E) | P0 | ui | Chưa chạy | `test_reports/E2E-004_tai-10-file-song-song/` |
| [E2E-005](E2E-005_mat-mang-khi-tai-len-va-tai-lai.md) | Mất mạng khi tải lên và tải lại | System (E2E) | P0 | ui | Chưa chạy | `test_reports/E2E-005_mat-mang-khi-tai-len-va-tai-lai/` |
| [E2E-006](E2E-006_rate-limit-cau-hoi-va-dem-nguoc.md) | Rate limit câu hỏi và đếm ngược | System (E2E) | P1 | ui | Chưa chạy | `test_reports/E2E-006_rate-limit-cau-hoi-va-dem-nguoc/` |
| [E2E-007](E2E-007_loi-ai-va-gui-lai.md) | Lỗi AI và Gửi lại | System (E2E) | P0 | ui | Chưa chạy | `test_reports/E2E-007_loi-ai-va-gui-lai/` |
| [E2E-008](E2E-008_het-phien-khi-dang-soan-cau-hoi.md) | Hết phiên khi đang soạn câu hỏi | System (E2E) | P0 | ui | Chưa chạy | `test_reports/E2E-008_het-phien-khi-dang-soan-cau-hoi/` |
| [E2E-009](E2E-009_tai-lai-trang-giua-phien.md) | Tải lại trang giữa phiên | System (E2E) | P0 | ui | Chưa chạy | `test_reports/E2E-009_tai-lai-trang-giua-phien/` |
| [E2E-010](E2E-010_xu-ly-lai-tai-lieu-loi-tam-thoi.md) | Xử lý lại tài liệu lỗi tạm thời | System (E2E) | P1 | ui | Chưa chạy | `test_reports/E2E-010_xu-ly-lai-tai-lieu-loi-tam-thoi/` |
| [E2E-011](E2E-011_vuot-gioi-han-so-file-va-han-muc.md) | Vượt giới hạn số file và hạn mức | System (E2E) | P0 | ui | Đạt (thủ công) | `test_reports/E2E-011_vuot-gioi-han-so-file-va-han-muc/` |
| [E2E-012](E2E-012_pdf-co-mot-phan-la-anh-scan.md) | PDF có một phần là ảnh scan | System (E2E) | P0 | ui | Chưa chạy | `test_reports/E2E-012_pdf-co-mot-phan-la-anh-scan/` |
| [E2E-013](E2E-013_trung-ten-file.md) | Trùng tên file | System (E2E) | P0 | ui | Chưa chạy | `test_reports/E2E-013_trung-ten-file/` |
| [E2E-014](E2E-014_nam-cau-hoi-lien-tiep.md) | Năm câu hỏi liên tiếp | System (E2E) | P0 | ui | Chưa chạy | `test_reports/E2E-014_nam-cau-hoi-lien-tiep/` |
| [SEC-001](SEC-001_truy-cap-khong-co-phien.md) | Truy cập không có phiên | Security | Critical | ui | Đạt (tự động) | `test_reports/SEC-001_truy-cap-khong-co-phien/` |
| [SEC-002](SEC-002_tu-choi-theo-nhom-idp-va-ghi-audit.md) | Từ chối theo nhóm IdP và ghi audit | Security | Critical | ui | Đạt (tự động) | `test_reports/SEC-002_tu-choi-theo-nhom-idp-va-ghi-audit/` |
| [SEC-003](SEC-003_chan-open-redirect.md) | Chặn open redirect | Security | High | ui | Đạt (tự động) | `test_reports/SEC-003_chan-open-redirect/` |
| [SEC-004](SEC-004_csrf-cho-moi-thao-tac-ghi.md) | CSRF cho mọi thao tác ghi | Security | Critical | ui | Đạt (tự động) | `test_reports/SEC-004_csrf-cho-moi-thao-tac-ghi/` |
| [SEC-005](SEC-005_cach-ly-tai-lieu-giua-nguoi-dung-idor.md) | Cách ly tài liệu giữa người dùng (IDOR) | Security | Critical | ui | Đạt (tự động) | `test_reports/SEC-005_cach-ly-tai-lieu-giua-nguoi-dung-idor/` |
| [SEC-006](SEC-006_rls-o-muc-co-so-du-lieu.md) | RLS ở mức cơ sở dữ liệu | Security | Critical | cli | Đạt (tự động) | `test_reports/SEC-006_rls-o-muc-co-so-du-lieu/` |
| [SEC-007](SEC-007_du-lieu-gui-toi-nha-cung-cap-ai.md) | Dữ liệu gửi tới nhà cung cấp AI | Security | High | cli | Đạt (tự động) | `test_reports/SEC-007_du-lieu-gui-toi-nha-cung-cap-ai/` |
| [SEC-008](SEC-008_khong-lo-noi-dung-trong-analytics-audit-log.md) | Không lộ nội dung trong analytics, audit, log | Security | High | cli | Đạt (tự động) | `test_reports/SEC-008_khong-lo-noi-dung-trong-analytics-audit-log/` |
| [SEC-009](SEC-009_kiem-tra-file-tai-len-an-toan.md) | Kiểm tra file tải lên an toàn | Security | High | ui | Đạt (tự động) | `test_reports/SEC-009_kiem-tra-file-tai-len-an-toan/` |
| [SEC-010](SEC-010_prompt-injection-qua-tai-lieu.md) | Prompt injection qua tài liệu | Security | High | ui | Đạt một phần (tự động) | `test_reports/SEC-010_prompt-injection-qua-tai-lieu/` |
| [SEC-011](SEC-011_header-bao-mat-va-cookie.md) | Header bảo mật và cookie | Security | High | ui | Đạt một phần | `test_reports/SEC-011_header-bao-mat-va-cookie/` |
| [SEC-012](SEC-012_ma-hoa-khi-truyen-va-khi-luu.md) | Mã hóa khi truyền và khi lưu | Security | High | manual | Bị chặn (chưa có staging) | `test_reports/SEC-012_ma-hoa-khi-truyen-va-khi-luu/` |
| [SEC-013](SEC-013_rate-limit-chong-lam-dung.md) | Rate limit chống lạm dụng | Security | Medium | ui | Đạt (tự động, phần câu hỏi) | `test_reports/SEC-013_rate-limit-chong-lam-dung/` |
| [SEC-014](SEC-014_quet-lo-hong-thu-vien-phu-thuoc.md) | Quét lỗ hổng thư viện phụ thuộc | Security | High | cli | Chưa chạy | `test_reports/SEC-014_quet-lo-hong-thu-vien-phu-thuoc/` |
| [SEC-015](SEC-015_quet-bao-mat-dong-dast.md) | Quét bảo mật động (DAST) | Security | High | staging | Bị chặn (chưa có staging) | `test_reports/SEC-015_quet-bao-mat-dong-dast/` |
| [ACC-001](ACC-001_dung-toan-bo-luong-chinh-bang-ban-phim.md) | Dùng toàn bộ luồng chính bằng bàn phím | Accessibility | High | manual | Chưa chạy | `test_reports/ACC-001_dung-toan-bo-luong-chinh-bang-ban-phim/` |
| [ACC-002](ACC-002_trinh-doc-man-hinh-nvda.md) | Trình đọc màn hình NVDA | Accessibility | High | manual | Chưa chạy | `test_reports/ACC-002_trinh-doc-man-hinh-nvda/` |
| [ACC-003](ACC-003_do-tuong-phan-mau.md) | Độ tương phản màu | Accessibility | High | ui | Chưa chạy | `test_reports/ACC-003_do-tuong-phan-mau/` |
| [ACC-004](ACC-004_thuoc-tinh-aria.md) | Thuộc tính ARIA | Accessibility | Medium | ui | Đạt một phần | `test_reports/ACC-004_thuoc-tinh-aria/` |
| [ACC-005](ACC-005_quan-ly-focus.md) | Quản lý focus | Accessibility | Medium | manual | Chưa chạy | `test_reports/ACC-005_quan-ly-focus/` |
| [ACC-006](ACC-006_trang-thai-khong-chi-dua-vao-mau.md) | Trạng thái không chỉ dựa vào màu | Accessibility | Medium | manual | Đạt (thủ công) | `test_reports/ACC-006_trang-thai-khong-chi-dua-vao-mau/` |
| [ACC-007](ACC-007_giam-chuyen-dong.md) | Giảm chuyển động | Accessibility | Low | ui | Chưa chạy | `test_reports/ACC-007_giam-chuyen-dong/` |
| [UI-001](UI-001_so-sanh-giao-dien-voi-thiet-ke.md) | So sánh giao diện với thiết kế | UI/UX | Medium | manual | Đạt sơ bộ (thủ công) | `test_reports/UI-001_so-sanh-giao-dien-voi-thiet-ke/` |
| [UI-002](UI-002_do-rong-man-hinh.md) | Độ rộng màn hình | UI/UX | Medium | ui | Chưa chạy | `test_reports/UI-002_do-rong-man-hinh/` |
| [UI-003](UI-003_trang-thai-thanh-phan.md) | Trạng thái thành phần | UI/UX | Medium | ui | Đạt một phần | `test_reports/UI-003_trang-thai-thanh-phan/` |
| [UI-004](UI-004_trang-thai-trong-va-loi.md) | Trạng thái trống và lỗi | UI/UX | Medium | manual | Đạt một phần (E-03 chưa kiểm) | `test_reports/UI-004_trang-thai-trong-va-loi/` |
| [UI-005](UI-005_trang-thai-cho.md) | Trạng thái chờ | UI/UX | Medium | ui | Đạt | `test_reports/UI-005_trang-thai-cho/` |
| [UI-006](UI-006_thong-bao-tu-an.md) | Thông báo tự ẩn | UI/UX | Low | ui | Đạt sơ bộ (thủ công) | `test_reports/UI-006_thong-bao-tu-an/` |
| [UI-007](UI-007_bo-dem-va-gioi-han-ky-tu.md) | Bộ đếm và giới hạn ký tự | UI/UX | Medium | ui | Đạt một phần | `test_reports/UI-007_bo-dem-va-gioi-han-ky-tu/` |
| [UI-008](UI-008_giao-dien-toi.md) | Giao diện tối | UI/UX | Low | manual | Chưa chạy | `test_reports/UI-008_giao-dien-toi/` |
| [UI-009](UI-009_tuong-thich-chrome-va-edge.md) | Tương thích Chrome và Edge | UI/UX | Medium | ui | Đạt một phần (Edge) | `test_reports/UI-009_tuong-thich-chrome-va-edge/` |
| [UI-010](UI-010_ngon-ngu-giao-dien-va-cau-tra-loi.md) | Ngôn ngữ giao diện và câu trả lời | UI/UX | Medium | manual | Chưa chạy | `test_reports/UI-010_ngon-ngu-giao-dien-va-cau-tra-loi/` |
| [UI-011](UI-011_nguon-khong-co-so-trang.md) | Nguồn không có số trang | UI/UX | Medium | ui | Chưa chạy | `test_reports/UI-011_nguon-khong-co-so-trang/` |
| [PERF-001](PERF-001_thoi-gian-tra-loi-mot-nguoi-dung.md) | Thời gian trả lời một người dùng | Performance | High | staging | Bị chặn (staging) | `test_reports/PERF-001_thoi-gian-tra-loi-mot-nguoi-dung/` |
| [PERF-002](PERF-002_hai-muoi-nguoi-hoi-dong-thoi.md) | Hai mươi người hỏi đồng thời | Performance | High | staging | Bị chặn (staging) | `test_reports/PERF-002_hai-muoi-nguoi-hoi-dong-thoi/` |
| [PERF-003](PERF-003_xu-ly-file-bien-20-mb-300-trang.md) | Xử lý file biên 20 MB / 300 trang | Performance | High | staging | Bị chặn (staging) | `test_reports/PERF-003_xu-ly-file-bien-20-mb-300-trang/` |
| [PERF-004](PERF-004_xu-ly-hang-loat-nhieu-nguoi-dung.md) | Xử lý hàng loạt nhiều người dùng | Performance | Medium | staging | Bị chặn (staging) | `test_reports/PERF-004_xu-ly-hang-loat-nhieu-nguoi-dung/` |
| [PERF-005](PERF-005_chay-ben-2-gio.md) | Chạy bền 2 giờ | Performance | Medium | staging | Bị chặn (staging) | `test_reports/PERF-005_chay-ben-2-gio/` |
| [PERF-006](PERF-006_hieu-nang-giao-dien.md) | Hiệu năng giao diện | Performance | Low | ui | Chưa chạy | `test_reports/PERF-006_hieu-nang-giao-dien/` |
| [QLT-001](QLT-001_do-chinh-xac-cau-tra-loi.md) | Độ chính xác câu trả lời | Chất lượng câu trả lời | High | staging | Bị chặn (DEP-005) | `test_reports/QLT-001_do-chinh-xac-cau-tra-loi/` |
| [QLT-002](QLT-002_dung-ten-tai-lieu-nguon.md) | Đúng tên tài liệu nguồn | Chất lượng câu trả lời | High | staging | Bị chặn (DEP-005) | `test_reports/QLT-002_dung-ten-tai-lieu-nguon/` |
| [QLT-003](QLT-003_dung-so-trang.md) | Đúng số trang | Chất lượng câu trả lời | High | staging | Bị chặn (DEP-005) | `test_reports/QLT-003_dung-so-trang/` |
| [QLT-004](QLT-004_tu-choi-dung-cau-hoi-ngoai-tai-lieu.md) | Từ chối đúng câu hỏi ngoài tài liệu | Chất lượng câu trả lời | High | staging | Bị chặn (DEP-005) | `test_reports/QLT-004_tu-choi-dung-cau-hoi-ngoai-tai-lieu/` |
| [QLT-005](QLT-005_da-tai-lieu-va-cau-hoi-tiep-noi.md) | Đa tài liệu và câu hỏi tiếp nối | Chất lượng câu trả lời | Medium | staging | Bị chặn (DEP-005, OQ-012) | `test_reports/QLT-005_da-tai-lieu-va-cau-hoi-tiep-noi/` |
| [UAT-001](UAT-001_tai-len-mot-pdf-hop-le.md) | Tải lên một PDF hợp lệ | Acceptance | P0 | manual | Chưa chạy (demo: đạt sơ bộ) | `test_reports/UAT-001_tai-len-mot-pdf-hop-le/` |
| [UAT-002](UAT-002_tai-len-file-khong-phai-pdf.md) | Tải lên file không phải PDF | Acceptance | P0 | manual | Chưa chạy (demo: đạt sơ bộ) | `test_reports/UAT-002_tai-len-file-khong-phai-pdf/` |
| [UAT-003](UAT-003_hoi-dap-voi-tai-lieu-da-xu-ly.md) | Hỏi đáp với tài liệu đã xử lý | Acceptance | P0 | manual | Chưa chạy | `test_reports/UAT-003_hoi-dap-voi-tai-lieu-da-xu-ly/` |
| [UAT-004](UAT-004_cau-hoi-can-tong-hop-nhieu-file.md) | Câu hỏi cần tổng hợp nhiều file | Acceptance | P0 | manual | Chưa chạy | `test_reports/UAT-004_cau-hoi-can-tong-hop-nhieu-file/` |
| [UAT-005](UAT-005_hoi-noi-dung-khong-co-trong-tai-lieu.md) | Hỏi nội dung không có trong tài liệu | Acceptance | P0 | manual | Chưa chạy | `test_reports/UAT-005_hoi-noi-dung-khong-co-trong-tai-lieu/` |
| [UAT-006](UAT-006_kiem-tra-nguon-cau-tra-loi.md) | Kiểm tra nguồn câu trả lời | Acceptance | P0 | manual | Chưa chạy | `test_reports/UAT-006_kiem-tra-nguon-cau-tra-loi/` |
| [UAT-007](UAT-007_xoa-tai-lieu-khong-con-duoc-dung.md) | Xóa tài liệu không còn được dùng | Acceptance | P0 | manual | Chưa chạy | `test_reports/UAT-007_xoa-tai-lieu-khong-con-duoc-dung/` |
| [UAT-008](UAT-008_kha-dung-voi-nguoi-dung-lan-dau.md) | Khả dụng với người dùng lần đầu | Acceptance | P0 | manual | Chưa chạy | `test_reports/UAT-008_kha-dung-voi-nguoi-dung-lan-dau/` |

_File được sinh bằng `doc/07-verification/_build_test_cases.py` – sửa dữ liệu trong `_tc_data/` rồi chạy lại script._
