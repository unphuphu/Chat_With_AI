# T03-01 – Hàng đợi job và vòng lặp worker (ALG-11)

| Trường | Giá trị |
|---|---|
| Lát | VS-3 – Xử lý tài liệu (Lát 1) |
| Kích thước | M – khoảng 200–400 dòng thay đổi, 2–4 vòng lặp |
| Trạng thái | **Ready** |
| Phụ thuộc | [T00-05](T00-05_ha-tang-csdl-engine-theo-vai-tro-va-pham-vi-work.md) |
| Story | US-005 |
| Tài liệu tham chiếu | BLUEPRINT ALG-11, 3.7.1, DE-16; SAD ADR-006, 3.2 (tác vụ); schema.sql `job` |

## Mục tiêu

Worker lấy job an toàn khi nhiều bản chạy song song, có heartbeat, thử lại với backoff.

## Phạm vi file

- `backend/app/infra/jobs.py` (`enqueue`, `claim`, `heartbeat`, `complete`, `retry`, `fail`, `cancel`)
- `backend/worker/main.py` (vòng lặp, `INGEST_CONCURRENCY`, `LISTEN job_enqueued` chờ 5 s, tắt gọn)
- `backend/tests/integration/test_jobs.py`

## Các bước gợi ý

1. SQL claim đúng ALG-11; heartbeat gia hạn `locked_until` mỗi 2 phút.
2. `retry(job, backoff)` đặt `QUEUED`, `run_after`; quá `INGEST_MAX_ATTEMPTS` → `fail`.
3. Handler đăng ký theo `job.kind`; nối trace bằng `trace_parent`.

## Tiêu chí hoàn thành

- [ ] Test: 2 worker cùng lúc với 10 job → mỗi job chạy đúng 1 lần
- [ ] Test: worker chết (không heartbeat) → job được claim lại sau `locked_until`, `attempts` tăng
- [ ] Test: retry đặt `run_after` đúng backoff 30 s/120 s
- [ ] Test: SIGTERM → job đang chạy được trả về QUEUED
- [ ] Lint, typecheck, test liên quan xanh; không giảm độ bao phủ của `modules/`
- [ ] Không thêm chuỗi giao diện ngoài file i18n; không ghi nội dung người dùng vào log

## Kiểm chứng

```bash
make test-int -k jobs
```
