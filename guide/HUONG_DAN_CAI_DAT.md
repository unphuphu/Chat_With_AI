# Hướng dẫn cài đặt AI Chat PDF (bản demo)

Tài liệu này dành cho người cài đặt và vận hành bản demo trên một máy tính cá nhân. Người dùng cuối xem
[Hướng dẫn sử dụng](HUONG_DAN_SU_DUNG.md).

Bản demo chạy hoàn toàn trên một máy và **không cần Docker, PostgreSQL hay API key**. Cơ sở dữ liệu, máy chủ đăng
nhập và bộ trả lời đều có sẵn bản chạy tại chỗ. Khi cần, có thể chuyển sang dùng mô hình Claude thật (mục 5).

---

## 1. Yêu cầu

| Thành phần | Phiên bản | Ghi chú |
|---|---|---|
| Hệ điều hành | Windows 10/11 | Đã kiểm thử trên Windows 10. Linux/macOS dùng cùng các bước nhưng chưa kiểm thử |
| Python | 3.12 trở lên | Đã kiểm thử với 3.14. Khi cài nhớ chọn *Add python.exe to PATH* |
| Node.js | 20 trở lên | Đã kiểm thử với 24 (kèm npm) |
| Trình duyệt | Microsoft Edge hoặc Google Chrome | Cần trình xem PDF có sẵn của trình duyệt |
| Ổ đĩa trống | khoảng 1 GB | Thư viện Python + Node và dữ liệu demo |
| Cổng mạng | 8080, 8000, 8090, 54329 | Chỉ mở trên `127.0.0.1`, không lộ ra mạng ngoài |

Kiểm tra nhanh trong cửa sổ lệnh (Git Bash, PowerShell hoặc Command Prompt):

```bash
python --version     # Python 3.12.x trở lên
node --version       # v20.x trở lên
npm --version
```

## 2. Cài đặt

Mở cửa sổ lệnh tại thư mục dự án (thư mục chứa `app/`, `doc/`, `guide/`), rồi chạy lần lượt:

```bash
cd app

# 2.1 Tạo môi trường Python riêng và cài thư viện backend (mất vài phút)
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt

# 2.2 Cài thư viện Node cho cơ sở dữ liệu dev và giao diện web
cd devdb && npm install && cd ..
cd frontend && npm install && cd ..
```

> **Linux/macOS:** thay `backend/.venv/Scripts/python.exe` bằng `backend/.venv/bin/python` ở mọi lệnh trong tài liệu này.

Bước 2.2 là tùy chọn: lần chạy đầu, `run.py` sẽ tự chạy `npm install` nếu thấy thiếu thư mục `node_modules`.

Nếu npm in cảnh báo `install-scripts ... esbuild`, có thể bỏ qua: gói esbuild cho Windows đã được cài sẵn,
nên giao diện web vẫn build và chạy được.

## 3. Chạy ứng dụng

```bash
cd app
backend/.venv/Scripts/python.exe run.py --sample
```

- `--sample` sinh bộ PDF mẫu vào `app/sample-pdfs/`. Chỉ cần ở lần đầu; các lần sau chạy `run.py` không kèm tham số.
- Lần đầu chạy, `run.py` tự tạo file cấu hình `app/.env` từ `app/.env.example`.

`run.py` khởi động lần lượt 4 dịch vụ và in log của từng dịch vụ với tiền tố riêng:

| Tiền tố | Dịch vụ | Cổng | Vai trò |
|---|---|---|---|
| `devdb` | PostgreSQL 17 + pgvector (PGlite) | 54329 | Lưu tài liệu, đoạn văn bản, vector, hội thoại |
| `devidp` | Máy chủ đăng nhập OIDC giả lập | 8090 | Thay cho hệ thống đăng nhập của công ty |
| `api` | API + worker xử lý tài liệu | 8000 | Tự tạo bảng CSDL ở lần chạy đầu |
| `web` | Giao diện web (Vite) | 8080 | Địa chỉ người dùng truy cập |

Khi thấy dòng sau là ứng dụng đã sẵn sàng:

```
[run] Sẵn sàng → http://localhost:8080  (đăng nhập: chọn người dùng mẫu p1). Ctrl+C để dừng.
```

Mở trình duyệt tới **<http://localhost:8080>**. Trang đăng nhập của máy chủ giả lập sẽ hiện ra:

![Trang chọn tài khoản của máy chủ đăng nhập giả lập](images/01-dang-nhap.png)

Chọn **Nguyễn Lan (P1)** để vào ứng dụng. Cách dùng tiếp theo xem trong [Hướng dẫn sử dụng](HUONG_DAN_SU_DUNG.md).

**Dừng ứng dụng:** nhấn `Ctrl+C` trong cửa sổ đang chạy `run.py`. Cả 4 dịch vụ sẽ dừng theo.

### Tài khoản mẫu

| Tài khoản | Email | Nhóm | Kết quả khi đăng nhập |
|---|---|---|---|
| Nguyễn Lan (P1) | lan.nguyen@congty.vn | `aichat-users` | Dùng được ứng dụng |
| Trần Minh (P2) | minh.tran@congty.vn | `aichat-users` | Dùng được, có kho tài liệu riêng (không thấy tài liệu của P1) |
| Quản trị viên | admin@congty.vn | `aichat-admins` | Dùng được |
| Người ngoài nhóm | khach@congty.vn | (không có) | Bị chặn ở trang *Bạn chưa được cấp quyền* |

## 4. Kiểm tra sau cài đặt

Để `run.py` tiếp tục chạy, mở **một cửa sổ lệnh khác** rồi chạy:

```bash
cd app/backend
.venv/Scripts/python.exe scripts/smoke.py
```

Kết quả mong đợi (rút gọn):

```
login ok: lan.nguyen@congty.vn
upload hop-dong-A.pdf 201
...
documents: [('bang-gia-Q4.pdf', 'READY'), ('chinh-sach-ban-hang-2026.pdf', 'READY'), ('hop-dong-A.pdf', 'READY')]

Q: Bên B thanh toán trong vòng bao nhiêu ngày?
  ANSWERED (2.2s): ... trong vòng 30 ngày ... [1]
  nguồn: [('hop-dong-A.pdf', 2)]
...
Q: Đối thủ cạnh tranh tại thị trường Nhật Bản là ai?
  INSUFFICIENT (2.1s): None
```

Script này đăng nhập bằng tài khoản P1, rồi tải 3 PDF mẫu lên kho của P1.

Bộ kiểm thử tự động (không cần `run.py` đang chạy, nhưng cổng 54329 phải trống hoặc dùng cổng ngẫu nhiên do test tự chọn):

```bash
cd app/backend
.venv/Scripts/python.exe -m pytest -q          # khoảng 1 phút, 48 test
```

Kiểm thử giao diện bằng Microsoft Edge (cần `run.py` đang chạy):

```bash
cd app/frontend
npx playwright test e2e/demo.spec.ts
```

## 5. Cấu hình

Mọi cấu hình nằm trong `app/.env`. Sửa xong thì dừng rồi chạy lại `run.py` để áp dụng.

### 5.1 Dùng mô hình Claude thay cho bộ trả lời có sẵn

Mặc định `LLM_PROVIDER=extractive`: hệ thống chọn nguyên văn các câu trong tài liệu khớp với câu hỏi. Cách này
chạy offline nhưng không diễn giải và không tự nhận ra hai tài liệu mâu thuẫn nhau. Để có câu trả lời tự nhiên hơn:

```ini
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-...           # API key từ console.anthropic.com
LLM_MODEL=claude-opus-5-5
# Mô hình có suy luận thường cần hơn 10 giây; nới thời gian chờ nếu hay gặp lỗi "phản hồi quá lâu"
LLM_TIMEOUT_S=25
ANSWER_BUDGET_S=30
```

Khi dùng Claude, chỉ nội dung các đoạn văn bản liên quan và câu hỏi được gửi đi. Tên file, mã tài liệu và
email người dùng không được gửi.

### 5.2 Các giới hạn thường chỉnh

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `MAX_FILE_MB` | 20 | Dung lượng tối đa mỗi file PDF |
| `MAX_PAGES` | 300 | Số trang tối đa mỗi file |
| `MAX_FILES_PER_BATCH` | 10 | Số file tối đa mỗi lần tải lên |
| `MAX_DOCS_PER_WORKSPACE` | 100 | Số tài liệu tối đa mỗi người dùng |
| `QUESTION_MAX_CHARS` | 2000 | Độ dài tối đa một câu hỏi |
| `RATE_QUESTIONS_PER_MIN` | 10 | Số câu hỏi tối đa mỗi phút mỗi người |
| `RATE_FILES_PER_HOUR` | 30 | Số file tải lên tối đa mỗi giờ mỗi người |
| `SESSION_IDLE_MIN` | 120 | Phiên hết hạn sau bao nhiêu phút không thao tác |
| `RETRIEVAL_MIN_SIMILARITY` | 0.45 | Ngưỡng liên quan; giảm nếu hệ thống hay trả "Chưa đủ thông tin" dù tài liệu có thông tin |

Danh sách đầy đủ: `app/backend/app/infra/settings.py` (tên biến môi trường = tên trường viết hoa).

### 5.3 Dữ liệu được lưu ở đâu

| Đường dẫn | Nội dung |
|---|---|
| `app/.data/pgdata/` | Cơ sở dữ liệu (tài liệu, đoạn văn bản, vector, hội thoại, nhật ký) |
| `app/.data/blobs/` | File PDF gốc người dùng tải lên |
| `app/.data/devidp_key.pem` | Khóa ký của máy chủ đăng nhập giả lập |

**Xóa toàn bộ dữ liệu demo:** dừng `run.py`, xóa thư mục `app/.data`, rồi chạy lại `run.py`.

## 6. Xử lý sự cố

| Hiện tượng | Nguyên nhân và cách xử lý |
|---|---|
| `[run] cổng 8080 đang được dùng …` | Một bản `run.py` cũ hoặc chương trình khác đang chiếm cổng. Tìm tiến trình bằng `netstat -ano \| findstr :8080`, đóng nó (Task Manager → *End task* theo PID) rồi chạy lại |
| `[run] devdb đã dừng …` | Thường do `npm install` trong `app/devdb` chưa chạy xong. Chạy lại `cd app/devdb && npm install`. Nếu dữ liệu hỏng, xóa `app/.data/pgdata` |
| Trình duyệt báo *This site can't be reached* | Chưa thấy dòng `[run] Sẵn sàng`. Đợi thêm, hoặc xem log có dòng lỗi màu đỏ |
| Chọn tài khoản xong lại hiện trang *Không thể đăng nhập* | Đang mở bằng `127.0.0.1:8080` trong khi cấu hình là `localhost:8080` (`PUBLIC_BASE_URL`), nên cookie đăng nhập không khớp. Dùng đúng `http://localhost:8080` |
| Tài liệu đứng mãi ở *Đang xử lý* | Xem log `api` có dòng `job_failed`. File quá lớn có thể cần hơn 2 phút. Nếu thất bại với lý do tạm thời, người dùng bấm *Xử lý lại* |
| Câu trả lời hay là "Chưa đủ thông tin" | Bộ trả lời có sẵn chỉ khớp theo từ ngữ. Hãy hỏi bằng từ ngữ có trong tài liệu, giảm `RETRIEVAL_MIN_SIMILARITY`, hoặc dùng Claude (mục 5.1) |
| Lỗi tiếng Việt kiểu `UnicodeEncodeError: 'charmap'` khi chạy script | Đặt biến môi trường `PYTHONIOENCODING=utf-8` trước khi chạy |
| `pytest` báo không tìm thấy `node` | Node.js chưa có trong PATH. Mở lại cửa sổ lệnh sau khi cài Node |

## 7. Giới hạn của bản demo

Bản demo phục vụ trình diễn và thử nghiệm, chưa dùng cho dữ liệu thật của công ty:

- Đăng nhập dùng máy chủ giả lập: ai mở được máy cũng chọn được tài khoản. Khi triển khai thật cần kết nối
  IdP của công ty (`OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`) và bật HTTPS (`COOKIE_SECURE=true`).
- Cơ sở dữ liệu PGlite chỉ nhận một kết nối, nên phù hợp cho vài người dùng thử cùng lúc. Bản thật dùng
  PostgreSQL 16+ có pgvector với `DB_MODE=pool`.
- Embedding dạng hashing chỉ khớp theo từ ngữ, chưa hiểu từ đồng nghĩa.
- Chưa hỗ trợ PDF scan (ảnh chụp), chưa có câu hỏi tiếp nối theo ngữ cảnh.

Chi tiết kỹ thuật và khác biệt so với kế hoạch: [app/README.md](../app/README.md).
