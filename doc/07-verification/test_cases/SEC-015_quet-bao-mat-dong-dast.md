# SEC-015 – Quét bảo mật động (DAST)

| Trường | Giá trị |
|---|---|
| ID | SEC-015 |
| Loại | Security |
| Ưu tiên | High |
| Truy vết | G-04; OWASP Top 10 |
| URL ứng dụng | http://localhost:8080/ |
| Cách thực hiện | Tự động/bán tự động – kết quả chính thức cần ENV-STAGING; trên localhost chỉ để tham khảo |
| Test tự động hiện có | – |
| Trạng thái chu kỳ C1 | Bị chặn (chưa có staging) |
| Thư mục artifact | `./test_reports/SEC-015_quet-bao-mat-dong-dast/` |
| Nguồn | [TEST_PLAN.md v0.2](../TEST_PLAN.md) |

## Mục tiêu

Xác nhận OWASP ZAP baseline không phát hiện cảnh báo mức High trên ứng dụng.

## Điều kiện tiên quyết

- Ứng dụng chạy tại http://localhost:8080/ (khởi động bằng `node evidence/app.ts start` trong `app/frontend`, hoặc `run.py` trong `app/`); `GET /api/v1/readyz` trả `ready`
- Đã chạy `npm install` và `npx playwright install ffmpeg` trong `app/frontend` (ghi video)
- Có OWASP ZAP (bản Docker `zaproxy/zap-stable` hoặc bản cài đặt) – máy dev chưa có Docker

## Dữ liệu test

- Không cần dữ liệu riêng

## Các bước thực hiện

| # | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Chạy ZAP baseline với target http://localhost:8080/ (tham khảo) | Có báo cáo HTML |
| 2 | Lưu báo cáo `zap-report.html` vào `logs/` | Có file |
| 3 | 👤 Đánh giá từng cảnh báo; phân loại false positive | 0 cảnh báo High còn mở |

## Tiêu chí đạt

Mọi bước đạt kết quả mong đợi; không có lỗi Critical/High mới.

## Lệnh / công cụ

- `zap-baseline.py -t http://localhost:8080/ -r zap-report.html` (ZAP)

## Nhiệm vụ của agent (bắt buộc)

Agent thực hiện test case này **trên ứng dụng tại http://localhost:8080/** và phải tạo đủ bằng chứng sau trong thư mục **`./test_reports/SEC-015_quet-bao-mat-dong-dast/`** (tính từ thư mục gốc repo):

| Artifact | Vị trí | Yêu cầu |
|---|---|---|
| Test report | `test_reports/SEC-015_quet-bao-mat-dong-dast/report.md` (+ `result.json`) | Kết luận ĐẠT / KHÔNG ĐẠT / CẦN NGƯỜI XÁC NHẬN / BỊ CHẶN; bản build (commit); môi trường; bảng kết quả từng bước có link ảnh; link video; lỗi phát hiện |
| Ảnh chụp màn hình | `test_reports/SEC-015_quet-bao-mat-dong-dast/screenshots/NN-<bước>.png` | Ít nhất **1 ảnh cho mỗi bước** ở bảng trên, và 1 ảnh tại thời điểm lỗi nếu có |
| Video | `test_reports/SEC-015_quet-bao-mat-dong-dast/video/*.webm` | Ghi **toàn bộ quá trình test** từ bước 1 tới bước cuối, không cắt |
| Log | `test_reports/SEC-015_quet-bao-mat-dong-dast/logs/` | Output lệnh / request–response API / log ứng dụng liên quan |

**Quy trình:**

1. **Kiểm tra môi trường:** mở http://localhost:8080/ và gọi `GET http://localhost:8080/api/v1/readyz`, phải nhận `{"status":"ready"}`. Nếu không được, chạy `node evidence/app.ts start` trong `app/frontend` (lần đầu trên máy: chạy `run.py --sample` một lần để sinh PDF mẫu). Nếu vẫn không được, tạo report với kết luận **BỊ CHẶN – môi trường**, kèm ảnh/log lỗi, rồi dừng.
2. **Chạy công cụ** nêu ở mục *Lệnh / công cụ* qua bộ ghi dòng lệnh: `node evidence/record-cli.ts --tc SEC-015_quet-bao-mat-dong-dast --title "Quét bảo mật động (DAST)" -- <lệnh>`. Với k6/ZAP thì đặt `BASE_URL=http://localhost:8080/`.
3. Kết quả trên localhost chỉ để **tham khảo**. Ghi rõ trong report: *“Chạy trên ENV-DEV – không dùng cho launch gate”*. Kết quả chính thức chạy lại trên ENV-STAGING với cùng thư mục artifact.

**Không được:** lưu artifact ngoài thư mục trên; sửa dữ liệu của người dùng khác ngoài tài khoản test đã nêu; đánh dấu ĐẠT khi còn bước chưa thực hiện. Mỗi lần chạy lại, kết quả cũ tự chuyển sang `test_reports/_archive/`.

**Lỗi phát hiện:** ghi vào report theo mẫu `DEF-T-xxx` (bước tái hiện, mong đợi, thực tế, ảnh/video, mức độ, yêu cầu bị ảnh hưởng: G-04; OWASP Top 10).
