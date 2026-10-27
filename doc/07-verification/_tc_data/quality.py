"""PERF-001…PERF-006, QLT-001…QLT-005, UAT-001…UAT-008 (TEST_PLAN 6.1.4, 6.1.6, 6.1.11)."""

from . import APP, EVIDENCE, P2

PRE = [APP, EVIDENCE]
STAGING = "Kết quả chính thức chạy trên ENV-STAGING (cấu hình theo TEST_PLAN 11.0); trên localhost (PGlite, LLM trích xuất) chỉ để tham khảo"
QSET = "Bộ câu hỏi chuẩn DEP-005 (`test-data/questions.csv`: id, loại [trong tài liệu / đa tài liệu / ngoài tài liệu / tiếp nối], câu hỏi, đáp án chuẩn, tài liệu + trang nguồn) – **chưa có, chờ PO**"
REVIEW = "👤 "


def t(id_, title, prio, trace, c1, goal, steps, pre=(), data=(), mode="staging", **kw):
    return {"id": id_, "title": title, "prio": prio, "trace": trace, "mode": mode, "c1": c1, "auto": kw.pop("auto", "–"),
            "goal": goal, "pre": [*PRE, *pre], "data": list(data), "steps": steps, **kw}


K6 = "k6 (ghim phiên bản khi cài) – script đặt tại `app/perf/<id>.js`, chạy `k6 run -e BASE_URL=http://localhost:8080 app/perf/<id>.js --summary-export logs/summary.json`"

CASES = [
    # ------------------------------------------------------------------ PERF
    t("PERF-001", "Thời gian trả lời một người dùng", "High", "NFR-001; G-03", "Bị chặn (staging)",
      "Đo p50/p90 thời gian trả lời trên 50 câu hỏi với tài khoản có 100 tài liệu Sẵn sàng.",
      [("Chuẩn bị tài khoản test có 100 tài liệu Sẵn sàng (script tải hàng loạt)", "`GET /me` → documents_used = 100"),
       ("Chạy k6: 1 VU gửi lần lượt 50 câu hỏi từ bộ câu hỏi chuẩn, đo thời gian từ gửi tới khi nhận phản hồi hoàn chỉnh", "50 phản hồi 200"),
       ("Đọc `logs/summary.json`", "p50 ≤ 8 s, p90 ≤ 15 s"),
       ("Đối chiếu với `latency_ms` trong analytics `answer_returned`", "Sai lệch < 10%")],
      pre=[QSET, STAGING], tools=[K6]),
    t("PERF-002", "Hai mươi người hỏi đồng thời", "High", "NFR-007; NFR-001; G-03", "Bị chặn (staging)",
      "Xác nhận NFR-001 vẫn đạt khi 20 người dùng hỏi đồng thời trong 15 phút.",
      [("Chuẩn bị 20 tài khoản test, mỗi tài khoản 100 tài liệu", "Sẵn sàng"),
       ("k6: 20 VU, mỗi VU hỏi liên tục (nghỉ 5–10 s giữa các câu, dưới rate limit 10 câu/phút) trong 15 phút", "Hoàn tất"),
       ("Đọc kết quả", "p90 ≤ 15 s; tỉ lệ lỗi < 1%; không có 5xx ngoài 503 do circuit breaker"),
       ("Ghi CPU/RAM của api, worker, embedding, PostgreSQL trong lúc chạy", "Không thành phần nào > 85% CPU kéo dài")],
      pre=[STAGING], tools=[K6]),
    t("PERF-003", "Xử lý file biên 20 MB / 300 trang", "High", "NFR-002; US-005; G-03", "Bị chặn (staging)",
      "Đo thời gian từ lúc tải lên tới khi tài liệu Sẵn sàng cho file ở giới hạn dung lượng và số trang.",
      [("Tạo PDF 300 trang có chữ, ~20 MB (văn bản + ảnh nhỏ để đạt dung lượng)", "File hợp lệ, không vượt giới hạn"),
       ("Tải lên trên giao diện, bấm giờ (sự kiện `document_processing_completed.duration_ms`)", "Tài liệu *Sẵn sàng*"),
       ("So sánh với ngưỡng", "≤ 3 phút"),
       ("(tham khảo localhost) Lặp lại trên ENV-DEV, ghi thời gian", "Ghi nhận")],
      pre=[STAGING, P2], mode="staging", spec=True),
    t("PERF-004", "Xử lý hàng loạt nhiều người dùng", "Medium", "NFR-002; ALG-11", "Bị chặn (staging)",
      "Xác nhận hàng đợi xử lý không kẹt khi 5 người dùng cùng tải 10 file.",
      [("5 tài khoản, mỗi tài khoản tải 10 PDF mẫu cùng lúc (k6 hoặc script)", "50 tài liệu PROCESSING"),
       ("Theo dõi số job QUEUED/RUNNING mỗi 10 s (`/metrics`)", "Giảm dần, không đứng yên > 2 phút"),
       ("Kết thúc", "50 tài liệu READY; không job nào kẹt `locked_until` quá hạn")],
      pre=[STAGING], tools=[K6]),
    t("PERF-005", "Chạy bền 2 giờ", "Medium", "NFR-015; TR-06", "Bị chặn (staging)",
      "Xác nhận không rò bộ nhớ và không rò kết nối khi 10 người dùng sử dụng liên tục 2 giờ.",
      [("k6: 10 VU, hỗn hợp hỏi 80% / tải lên 15% / xóa 5%, 2 giờ", "Hoàn tất"),
       ("Ghi RSS bộ nhớ api/worker đầu và cuối", "Tăng < 10%"),
       ("Ghi số kết nối PostgreSQL đầu và cuối", "Không tăng dần"),
       ("Tỉ lệ lỗi toàn kỳ", "< 1%")],
      pre=[STAGING], tools=[K6]),
    t("PERF-006", "Hiệu năng giao diện", "Low", "NFR-017; UX", "Chưa chạy",
      "Đo LCP và độ mượt khi danh sách có 100 tài liệu.",
      [("Đăng nhập tài khoản có 100 tài liệu; đo LCP bằng `PerformanceObserver` trong Playwright", "LCP < 2,5 s"),
       ("Cuộn danh sách tài liệu từ đầu tới cuối, ghi video", "Không giật rõ rệt; không lỗi console"),
       ("Bật CPU throttling 4× (CDP `Emulation.setCPUThrottlingRate`), lặp lại", "LCP < 4 s (ghi nhận)")],
      pre=[P2, "Tài khoản có 100 tài liệu (tạo bằng script; có thể dùng `MAX_DOCS_PER_WORKSPACE` mặc định)"], mode="ui"),
    # ------------------------------------------------------------------ QLT
    t("QLT-001", "Độ chính xác câu trả lời", "High", "NFR-003; MET-002; G-02; TR-01", "Bị chặn (DEP-005)",
      "Đo tỉ lệ câu trả lời đúng trên ≥ 50 câu hỏi có đáp án trong tài liệu.",
      [("Tải bộ tài liệu dự án thật đã được PO duyệt vào tài khoản test", "Mọi tài liệu Sẵn sàng"),
       ("Chạy script đánh giá (T06-03): gửi từng câu hỏi loại \"trong tài liệu\", lưu câu trả lời + nguồn vào `logs/answers.csv`", "≥ 50 dòng"),
       (REVIEW + "2 người dùng nghiệp vụ chấm độc lập: Đúng / Đúng một phần / Sai / Bịa", "Bảng chấm `logs/grading.csv`"),
       ("Tính tỉ lệ Đúng (bất đồng → người thứ 3 quyết định)", "≥ 80%")],
      pre=[QSET, STAGING, "Tài liệu dự án thật – lưu ngoài repo, xóa sau nghiệm thu"],
      tools=["Script đánh giá `app/backend/scripts/eval_rag.py` (cần viết – T06-03): đọc CSV, gọi API qua phiên đăng nhập như `smoke.py`, ghi kết quả"]),
    t("QLT-002", "Đúng tên tài liệu nguồn", "High", "NFR-004; MET-004; G-02", "Bị chặn (DEP-005)",
      "Đo tỉ lệ câu trả lời có căn cứ hiển thị đúng tên tài liệu nguồn.",
      [("Dùng kết quả của QLT-001", "Có `answers.csv`"),
       ("Script so sánh `citations[].document_name` với tài liệu nguồn trong đáp án chuẩn", "Bảng đối chiếu"),
       ("Tính tỉ lệ", "≥ 90%")],
      pre=[QSET, STAGING]),
    t("QLT-003", "Đúng số trang", "High", "NFR-018; G-02; TR-04", "Bị chặn (DEP-005)",
      "Đo tỉ lệ số trang hiển thị trùng với trang chứa thông tin trong PDF gốc.",
      [("Với từng nguồn của QLT-001: mở `GET /documents/{id}/file#page=N` và chụp ảnh trang", "Ảnh trang cho mỗi nguồn"),
       (REVIEW + "Người chấm xác nhận trang có chứa thông tin được trích", "Bảng chấm"),
       ("Tính tỉ lệ", "≥ 85%")],
      pre=[QSET, STAGING]),
    t("QLT-004", "Từ chối đúng câu hỏi ngoài tài liệu", "High", "NFR-005; MET-005; US-016; G-02", "Bị chặn (DEP-005)",
      "Đo tỉ lệ trả lời *Chưa đủ thông tin* trên ≥ 20 câu hỏi ngoài tài liệu.",
      [("Chạy script với các câu loại \"ngoài tài liệu\"", "≥ 20 kết quả"),
       ("Đếm `status = INSUFFICIENT`", "≥ 90%"),
       (REVIEW + "Với các câu không bị từ chối: kiểm tra có bịa thông tin không", "Ghi lại từng trường hợp")],
      pre=[QSET, STAGING]),
    t("QLT-005", "Đa tài liệu và câu hỏi tiếp nối", "Medium", "MET-003; US-017; US-015; OQ-012", "Bị chặn (DEP-005, OQ-012)",
      "Đo tỉ lệ trả lời đầy đủ cho câu hỏi đa tài liệu, và tỉ lệ hiểu đúng ngữ cảnh cho cặp câu tiếp nối (khi US-015 được triển khai).",
      [("Chạy ≥ 20 câu đa tài liệu", "Kết quả"),
       (REVIEW + "Chấm \"đầy đủ\" = nêu thông tin và nguồn từ mọi tài liệu liên quan", "≥ 80%"),
       ("(khi US-015 có) Chạy 10 cặp câu tiếp nối trong cùng hội thoại", "≥ 8/10 đúng ngữ cảnh")],
      pre=[QSET, STAGING]),
    # ------------------------------------------------------------------ UAT
    t("UAT-001", "Tải lên một PDF hợp lệ", "P0", "AC-01; US-001; US-005", "Chưa chạy (demo: đạt sơ bộ)",
      "Người dùng nghiệp vụ xác nhận tải một PDF dự án thật lên được, thấy tiến độ, và tài liệu chuyển Sẵn sàng.",
      [("Người dùng nghiệp vụ đăng nhập bằng tài khoản của mình", "Màn hình chính"),
       ("Tải 1 PDF dự án (có chữ, ≤ 20 MB)", "Thấy tiến độ, rồi *Đang xử lý*"),
       ("Chờ", "*Sẵn sàng* ≤ 3 phút, có thông báo"),
       (REVIEW + "Người dùng xác nhận đạt/không đạt và ghi ý kiến", "Ký vào report")],
      pre=["Thực hiện trên ENV-STAGING; trước đó chạy thử trên http://localhost:8080/", "Có người dùng nghiệp vụ (P1) tham gia"], mode="manual"),
    t("UAT-002", "Tải lên file không phải PDF", "P0", "AC-02; US-003", "Chưa chạy (demo: đạt sơ bộ)",
      "Người dùng xác nhận file Word/ảnh bị từ chối với thông báo dễ hiểu.",
      [("Tải 1 file .docx và 1 file ảnh .jpg", "Mỗi file *Không nhận* – \"không phải file PDF hợp lệ\""),
       (REVIEW + "Người dùng đánh giá thông báo có dễ hiểu không", "Ghi ý kiến")],
      pre=["ENV-STAGING (chạy thử trên localhost)"], mode="manual"),
    t("UAT-003", "Hỏi đáp với tài liệu đã xử lý", "P0", "AC-03; US-012; US-013", "Chưa chạy",
      "Người dùng xác nhận câu trả lời dựa trên nội dung tài liệu dự án và có nguồn.",
      [("Hỏi 5 câu nghiệp vụ thực tế có đáp án trong tài liệu", "5 câu trả lời có nguồn"),
       (REVIEW + "Người dùng đối chiếu với tài liệu gốc", "≥ 4/5 đúng"),
       ("Ghi thời gian trả lời từng câu", "Mỗi câu ≤ 15 s")],
      pre=["ENV-STAGING", "Tài liệu dự án thật đã được PO cho phép"], mode="manual"),
    t("UAT-004", "Câu hỏi cần tổng hợp nhiều file", "P0", "AC-04; US-017; US-018", "Chưa chạy",
      "Người dùng xác nhận câu trả lời tổng hợp thông tin từ nhiều tài liệu và nêu nguồn từng ý.",
      [("Hỏi 3 câu cần thông tin từ ≥ 2 tài liệu", "Câu trả lời có nguồn từ ≥ 2 tài liệu"),
       (REVIEW + "Với cặp tài liệu mâu thuẫn: câu trả lời có nêu khác biệt và nguồn từng giá trị không", "Đạt (với LLM thật)")],
      pre=["ENV-STAGING"], mode="manual"),
    t("UAT-005", "Hỏi nội dung không có trong tài liệu", "P0", "AC-05; US-016", "Chưa chạy",
      "Người dùng xác nhận hệ thống không bịa khi tài liệu không có thông tin.",
      [("Hỏi 3 câu ngoài phạm vi tài liệu (kiến thức chung, chào hỏi, dự án khác)", "*Chưa đủ thông tin*, không có nguồn"),
       (REVIEW + "Người dùng xác nhận", "Đạt")],
      pre=["ENV-STAGING"], mode="manual"),
    t("UAT-006", "Kiểm tra nguồn câu trả lời", "P0", "AC-06; US-020; US-021; US-022", "Chưa chạy",
      "Người dùng xác nhận tên tài liệu và số trang đúng, và mở được đúng trang.",
      [("Với 3 câu trả lời của UAT-003: bấm từng nguồn", "Mở đúng tài liệu, đúng trang"),
       (REVIEW + "Người dùng xác nhận trang có chứa thông tin", "Đạt")],
      pre=["ENV-STAGING"], mode="manual"),
    t("UAT-007", "Xóa tài liệu không còn được dùng", "P0", "AC-07; US-010; US-011", "Chưa chạy",
      "Người dùng xác nhận sau khi xóa tài liệu, câu trả lời không còn dùng tài liệu đó.",
      [("Hỏi câu chỉ có đáp án trong tài liệu X", "Có nguồn X"),
       ("Xóa X (xác nhận)", "X biến mất; nguồn cũ thành *(đã xóa)*"),
       ("Hỏi lại cùng câu", "Không có thông tin hoặc nguồn từ X; *Chưa đủ thông tin* nếu không tài liệu nào khác có"),
       (REVIEW + "Người dùng xác nhận", "Đạt")],
      pre=["ENV-STAGING"], mode="manual"),
    t("UAT-008", "Khả dụng với người dùng lần đầu", "P0", "NFR-008; G-05", "Chưa chạy",
      "Đo tỉ lệ người dùng lần đầu tự hoàn thành luồng tải → hỏi → xem nguồn mà không cần hỗ trợ.",
      [("Mỗi người tham gia (≥ 5) nhận nhiệm vụ bằng lời: \"Tải tài liệu này lên và tìm điều khoản thanh toán, rồi mở trang chứa nó\"", "Bắt đầu bấm giờ"),
       ("Ghi video màn hình từng phiên (Playwright headed hoặc Game Bar), không hướng dẫn", "Video từng người"),
       (REVIEW + "Ghi: hoàn thành có/không, thời gian, chỗ vướng", "Bảng `logs/usability.csv`"),
       ("Tính kết quả", "≥ 80% hoàn thành, mỗi người ≤ 5 phút")],
      pre=["≥ 5 người dùng chưa từng dùng ứng dụng", "ENV-STAGING hoặc http://localhost:8080/"], mode="manual"),
]

for _c in CASES:
    if _c["id"].startswith("UAT"):
        _c["pass"] = "Mọi bước đạt và **người dùng nghiệp vụ / PO ký xác nhận** trong report; ý kiến được ghi lại."
    if _c["id"].startswith("QLT") and not _c.get("tools"):
        _c["tools"] = ["Script đánh giá `app/backend/scripts/eval_rag.py` (viết ở QLT-001 / T06-03) và bảng chấm `logs/grading.csv`; "
                       "chạy qua `node evidence/record-cli.ts --tc <thư mục> --cwd ../backend -- .venv/Scripts/python.exe scripts/eval_rag.py …`"]
    if _c["id"].startswith(("PERF", "QLT")):
        _c["pass"] = "Đạt ngưỡng nêu ở bảng bước **trên ENV-STAGING**. Kết quả chạy trên localhost chỉ ghi nhận, không dùng cho launch gate."
