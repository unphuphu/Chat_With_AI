# T03-04 – Embedding service và EmbeddingPort

| Trường | Giá trị |
|---|---|
| Lát | VS-3 – Xử lý tài liệu (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Done** |
| Phụ thuộc | [T00-01](T00-01_khoi-tao-monorepo-va-cong-cu.md) |
| Story | US-005 |
| Tài liệu tham chiếu | BLUEPRINT 3.6.5 (`POST /embed`), DE-14; SAD ADR-007; DATABASE_DESIGN B.2, B.7 |

## Mục tiêu

Service tạo vector `bge-m3` 1024 chiều và adapter gọi nó; adapter giả xác định cho test.

## Phạm vi file

- `embedding-service/app.py` (FastAPI, nạp mô hình khi khởi động, token `EMBEDDING_TOKEN`)
- `embedding-service/Dockerfile` (tải mô hình lúc build)
- `backend/app/ports/embedding.py`
- `backend/app/adapters/{embedding_http.py,embedding_fake.py}`
- `deploy/docker-compose.dev.yml` (service `embedding`, tùy chọn profile `full`)

## Các bước gợi ý

1. `/embed`: 1–32 văn bản, trả vector chuẩn hóa L2; 413 khi > 32; `/healthz`.
2. Adapter HTTP: timeout 30 s (passage) / 2 s (query), thử lại lỗi 5xx.
3. Fake: vector từ hash nội dung (xác định, chuẩn hóa) để test truy xuất không cần mô hình.
4. `EMBEDDING_MODEL_ID=bge-m3@v1`.

## Tiêu chí hoàn thành

- [ ] Test service (đánh dấu `slow`, chạy trên CI hằng đêm): 2 câu đồng nghĩa có cosine > 2 câu không liên quan
- [ ] Unit test adapter fake: cùng input → cùng vector, chuẩn L2 = 1
- [ ] Thiếu/sai token → 401
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-unit -k embedding
docker compose --profile full up embedding && curl -X POST …/embed
```

## Ngoài phạm vi

- Đo thông lượng là việc của SPIKE-02 (TS-02)

## Kết quả triển khai

**Done** – EmbeddingPort + `hashing-ngram@v1` (offline) + adapter HTTP; bge-m3 chưa triển khai.
