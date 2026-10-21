# T-102 — Định nghĩa `FileStorePort` và viết adapter S3/MinIO ghi luồng

| Thuộc tính | Giá trị |
|---|---|
| **Sprint** | Sprint 1 |
| **Loại** | Backend |
| **User story** | US-A1 |
| **Ưu tiên** | P0 |
| **Ước lượng** | 1 ngày-người `[Estimate]` |
| **Phụ thuộc (phải xong trước)** | T-003 |
| **Mở khóa (task chờ task này)** | T-103, T-104, T-105, T-106 |
| **Người thực hiện** | _chưa giao_ |
| **Trạng thái** | To do |

## 1. Mục tiêu

Backend lưu, đọc (toàn phần hoặc theo khoảng byte) và xóa tệp PDF trong object storage S3-compatible qua một cổng `FileStorePort`, **không bao giờ nạp cả tệp vào RAM**. Ở local dùng MinIO; test đơn vị dùng adapter trong bộ nhớ.

## 2. Bối cảnh

- [SAD §2.3](../../design/SAD.md#23-tầng-hạ-tầng-dữ-liệu): bucket riêng tư, khóa `documents/{uuid}.pdf`, mã hóa phía máy chủ AES-256.
- [SAD §3.2.2](../../design/SAD.md#322-luồng-2--tải-lên-và-lập-chỉ-mục-tài-liệu-api-02) bước 3: `PutObject` (multipart nếu lớn), truyền luồng.
- [SAD §4.2](../../design/SAD.md#42-độ-tin-cậy-và-khả-năng-chịu-lỗi): timeout kho tệp 30 s.
- [SAD §4.1.4](../../design/SAD.md#414-bảo-vệ-khi-nhận-tệp-pdf): khóa đối tượng là UUID sinh phía máy chủ (chống path traversal).
- Blueprint §3.5: `FileStorePort` — `put/get/delete` theo tham chiếu.

## 3. Phạm vi

**Trong phạm vi**
- Giao diện `FileStorePort` trong `app/ports/` (nếu T-007 đã tạo khung file, hoàn thiện tại đó).
- Adapter `S3FileStore` (`app/adapters/s3/`) dùng multipart upload, `Range` GET, xóa lũy đẳng.
- Adapter `InMemoryFileStore` (`app/adapters/fake/`) cho test đơn vị.
- Hàm `document_key(document_id: UUID) -> str` trả `documents/{uuid}.pdf`.
- Tạo bucket tự động **chỉ** ở môi trường local (bước `make seed`); staging/prod bucket do hạ tầng tạo sẵn.

**Ngoài phạm vi**
- Kiểm tra `%PDF-`, đếm kích thước, băm SHA-256 (T-103 làm trên luồng trước khi đưa vào port).
- Endpoint trả tệp cho trình duyệt (T-105).
- Dọn đối tượng mồ côi (T-407) — chỉ cung cấp sẵn `list_keys()`.

## 4. Thiết kế chi tiết

**File**

| File | Nội dung |
|---|---|
| `backend/app/ports/file_store.py` | `FileStorePort` (Protocol), `ObjectInfo`, `FileStoreError`, `ObjectNotFound` |
| `backend/app/adapters/s3/file_store.py` | `S3FileStore` |
| `backend/app/adapters/fake/file_store.py` | `InMemoryFileStore` |
| `backend/app/documents/keys.py` | `document_key()` |
| `backend/tests/contract/test_file_store_contract.py` | Bộ test hợp đồng chạy cho **cả hai** adapter |

**Chữ ký**

```python
@dataclass(frozen=True)
class ObjectInfo:
    key: str
    size_bytes: int
    last_modified: datetime

class FileStorePort(Protocol):
    async def put_stream(self, key: str, chunks: AsyncIterator[bytes],
                         *, content_type: str = "application/pdf") -> ObjectInfo: ...
        # Ghi từng phần; nếu iterator ném exception → hủy multipart (AbortMultipartUpload), không để lại đối tượng
    async def open_stream(self, key: str, *, start: int | None = None,
                          end: int | None = None) -> AsyncIterator[bytes]: ...
        # end bao gồm (inclusive), giống header Range; ObjectNotFound nếu không có
    async def head(self, key: str) -> ObjectInfo: ...
    async def delete(self, key: str) -> None: ...      # lũy đẳng: không có đối tượng → không lỗi
    async def list_keys(self, prefix: str, *, older_than: datetime | None = None) -> AsyncIterator[ObjectInfo]: ...
```

**Quy tắc của `S3FileStore`**
- Thư viện: `aioboto3`/`aiobotocore` `[Proposed]` (async; nếu dùng `boto3` đồng bộ thì bắt buộc chạy trong thread pool).
- Kích thước phần multipart `8 MiB` `[Proposed]` (S3 yêu cầu ≥ 5 MiB trừ phần cuối); tệp < 8 MiB → một `PutObject`.
- Bộ đệm tối đa trong RAM = 1 phần (8 MiB) mỗi tệp đang tải.
- Mọi lời gọi có timeout: kết nối 3 s, tổng 30 s mỗi thao tác (SAD §4.2); retry tối đa 2 lần cho `head/get/delete` (lũy đẳng). `put_stream` không tự retry vì luồng nguồn không đọc lại được.
- Gửi `ServerSideEncryption=AES256` khi `S3_SSE=AES256` `[Proposed]` (MinIO local có thể cần tắt — xem mục 9).
- Ánh xạ lỗi: `NoSuchKey` → `ObjectNotFound`; lỗi khác → `FileStoreError(code)`; **không** đưa thông tin xác thực hay URL ký vào log.
- Log mỗi thao tác: `op`, `key` (chỉ UUID), `size_bytes`, `duration_ms`, `outcome`.

## 5. Các bước thực hiện

1. Viết `FileStorePort`, `ObjectInfo`, lỗi trong `app/ports/file_store.py`.
2. Viết `InMemoryFileStore` (dict `key → bytes`), hỗ trợ `start/end`.
3. Viết bộ test hợp đồng tham số hóa theo adapter (mục 7).
4. Viết `S3FileStore`: client tạo một lần ở composition root (`main.py`, `worker.py`), cấu hình endpoint/khóa từ settings.
5. Multipart: `CreateMultipartUpload` → gom chunk tới 8 MiB → `UploadPart` → `CompleteMultipartUpload`; bất kỳ exception nào → `AbortMultipartUpload` rồi ném lại.
6. `open_stream`: `GetObject` với `Range: bytes={start}-{end}`; đọc body theo khối 64 KiB.
7. Thêm lệnh tạo bucket vào `make seed`; thêm biến vào `deploy/.env.example`.
8. Chạy test hợp đồng với MinIO (Testcontainers) trong CI.

## 6. Tiêu chí chấp nhận

- [ ] Tải lên tệp 50 MB qua `put_stream` với RSS tiến trình tăng < 32 MB (đo trong test tích hợp).
- [ ] Iterator nguồn ném exception giữa chừng → không còn đối tượng nào ở `key` và không còn multipart dở dang (`ListMultipartUploads` rỗng).
- [ ] `open_stream(key, start=100, end=199)` trả đúng 100 byte trùng byte 100..199 của tệp gốc.
- [ ] `delete()` gọi 2 lần liên tiếp không lỗi.
- [ ] `open_stream`/`head` trên khóa không tồn tại → `ObjectNotFound`.
- [ ] Bộ test hợp đồng xanh cho cả `InMemoryFileStore` và `S3FileStore` (MinIO).
- [ ] `app/documents`, `app/ingestion` chỉ import `app.ports.file_store`, không import `app.adapters.s3` (import-linter).

## 7. Kiểm thử

| Loại | Trường hợp | Kỳ vọng |
|---|---|---|
| Contract (cả 2 adapter) | put 3 MB → head → open_stream toàn phần | Kích thước và nội dung khớp |
| Contract | put 20 MB (nhiều phần) | Nội dung khớp, `size_bytes` = 20.971.520 |
| Contract | Range `0-4` | Trả `%PDF-` |
| Contract | delete không tồn tại | Không lỗi |
| Integration (MinIO) | Iterator ném `ValueError` sau 10 MB | Không có đối tượng, không có multipart dở dang |
| Integration (MinIO) | Đo RSS khi put 50 MB | Tăng < 32 MB |
| Unit | `document_key(uuid)` | `documents/<uuid>.pdf`, không chứa tên tệp gốc |

## 8. Cấu hình

| Biến | Mặc định | Ghi chú |
|---|---|---|
| `S3_ENDPOINT`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` | MinIO local (plan §3.3) | Staging/prod lấy từ secret manager |
| `S3_SSE` | `AES256` `[Proposed]` | Để trống ở local nếu MinIO chưa cấu hình KMS |
| `S3_PART_SIZE_MB` | `8` `[Proposed]` | ≥ 5 |
| `S3_TIMEOUT_S` | `30` | SAD §4.2 |

## 9. Rủi ro và câu hỏi mở

| Mục | Ảnh hưởng | Cách xử lý trong lúc chờ |
|---|---|---|
| Nơi đặt kho tệp phụ thuộc OQ-006 (đám mây hay tại chỗ) | Đổi endpoint/khóa | Chỉ đổi cấu hình; cùng `FileStorePort` |
| MinIO bật SSE-S3 cần cấu hình KMS `[Verify]` | Lỗi khi `PutObject` ở local | `S3_SSE` để trống ở local; bật ở staging |
| Tệp ghi xong nhưng giao dịch CSDL lỗi (T-103) | Đối tượng mồ côi | `list_keys()` cho T-407 dọn sau 24 giờ (SAD §3.2.2) |

## 10. Tham chiếu

- [Implement_plan](../Implement_plan.md) §3.1, §3.3, §5.2 (T-102)
- [SAD](../../design/SAD.md) §2.3, §3.2.2, §4.1.4, §4.2
- [Blueprint_Design](../../design/Blueprint_Design.md) §3.5 (giao diện ra ngoài)
- [User_Stories](../../design/User_Stories.md) US-A1
- Task liên quan: [T-103](./T-103-upload-api.md), [T-104](./T-104-ingest-worker.md), [T-105](./T-105-document-read-apis.md), [T-106](./T-106-delete-document-purge.md)

## Definition of Done

- [ ] Đáp ứng toàn bộ mục 6.
- [ ] Đáp ứng Definition of Done chung ([Implement_plan §4.5](../Implement_plan.md#45-definition-of-done)).
- [ ] `.env.example` có đủ biến S3; không có bí mật thật trong repo (gitleaks xanh).
