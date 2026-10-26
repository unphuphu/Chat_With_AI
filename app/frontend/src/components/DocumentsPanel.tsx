// Khu vực Tài liệu (S01–S03, S08): kéo thả, hàng đợi tải lên (tối đa 3 song song), danh sách trạng thái.
import { useCallback, useEffect, useRef, useState } from 'react'
import { api, ApiError, uploadFile, type Doc, type Me } from '../api'
import { FAILURE_TEXT, Icon, formatBytes, formatDateTime, uuid } from '../ui'

const PARALLEL = 3

type UploadState = 'queued' | 'uploading' | 'rejected' | 'failed'

interface UploadItem {
  key: string
  file: File
  batchId: string | null
  clientFileId: string
  state: UploadState
  progress: number
  reason?: string
}

interface Props {
  me: Me
  docs: Doc[]
  used: number
  limit: number
  onUploaded: () => void
  onDelete: (doc: Doc) => void
  onReprocess: (doc: Doc) => void
}

export function DocumentsPanel({ me, docs, used, limit, onUploaded, onDelete, onReprocess }: Props) {
  const [items, setItems] = useState<UploadItem[]>([])
  const [batchError, setBatchError] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const running = useRef(new Set<string>())
  const { limits } = me
  const remaining = Math.max(0, limit - used)

  const patch = useCallback((key: string, p: Partial<UploadItem>) => {
    setItems((xs) => xs.map((x) => (x.key === key ? { ...x, ...p } : x)))
  }, [])

  const start = useCallback(
    async (item: UploadItem) => {
      running.current.add(item.key)
      patch(item.key, { state: 'uploading', progress: 0, reason: undefined })
      try {
        let batchId = item.batchId
        if (!batchId) {
          batchId = (await api.createBatch([{ name: item.file.name, size_bytes: item.file.size }])).batch_id
          patch(item.key, { batchId })
        }
        const { promise } = uploadFile(batchId, item.clientFileId, item.file, (pct) =>
          patch(item.key, { progress: pct }),
        )
        await promise
        setItems((xs) => xs.filter((x) => x.key !== item.key))
        onUploaded()
      } catch (e) {
        const err = e as ApiError
        if (err.status === 422) {
          patch(item.key, { state: 'rejected', reason: err.detail ?? 'File không hợp lệ.' })
        } else if (err.code === 'batch_expired') {
          // Lô quá hạn: lần thử sau tạo lô mới, client_file_id mới
          patch(item.key, {
            state: 'failed',
            batchId: null,
            clientFileId: uuid(),
            reason: 'Phiên tải lên đã hết hạn. Bấm Tải lại để thử lần nữa.',
          })
        } else if (err.status === 429 || err.status === 503) {
          const wait = err.retryAfter ? ` sau ${err.retryAfter} giây` : ''
          patch(item.key, { state: 'failed', reason: `Hệ thống đang bận, vui lòng thử lại${wait}.` })
        } else if (err.status === 401) {
          patch(item.key, { state: 'failed', reason: 'Phiên đăng nhập đã hết hạn.' })
        } else {
          patch(item.key, {
            state: 'failed',
            reason: 'Mất kết nối khi đang tải lên. Bấm Tải lại – file sẽ không bị trùng.',
          })
        }
      } finally {
        running.current.delete(item.key)
      }
    },
    [onUploaded, patch],
  )

  // Bơm hàng đợi: luôn chạy tối đa PARALLEL file
  useEffect(() => {
    const free = PARALLEL - running.current.size
    if (free <= 0) return
    items
      .filter((x) => x.state === 'queued' && !running.current.has(x.key))
      .slice(0, free)
      .forEach((x) => void start(x))
  }, [items, start])

  async function addFiles(list: FileList | File[]) {
    const files = Array.from(list)
    setBatchError(null)
    if (files.length === 0) return
    if (files.length > limits.max_files_per_batch) {
      setBatchError(
        `Mỗi lần chỉ tải tối đa ${limits.max_files_per_batch} file – bạn đã chọn ${files.length} file. ` +
          `Hãy chọn lại tối đa ${limits.max_files_per_batch} file.`,
      )
      return
    }
    if (files.length > remaining) {
      setBatchError(
        `Bạn chỉ còn có thể thêm ${remaining} tài liệu (${used}/${limit}). Xóa tài liệu không còn dùng để có thêm chỗ.`,
      )
      return
    }
    const maxBytes = limits.max_file_mb * 1024 * 1024
    const newItems: UploadItem[] = files.map((f) => {
      const base = { key: uuid(), file: f, batchId: null, clientFileId: uuid(), progress: 0 }
      if (!/\.pdf$/i.test(f.name)) {
        return { ...base, state: 'rejected', reason: `"${f.name}" không phải file PDF hợp lệ.` }
      }
      if (f.size > maxBytes) {
        return { ...base, state: 'rejected', reason: `"${f.name}" vượt quá ${limits.max_file_mb} MB.` }
      }
      return { ...base, state: 'queued' }
    })
    const valid = newItems.filter((x) => x.state === 'queued')
    if (valid.length > 0) {
      try {
        const batch = await api.createBatch(valid.map((x) => ({ name: x.file.name, size_bytes: x.file.size })))
        valid.forEach((x) => (x.batchId = batch.batch_id))
      } catch (e) {
        const err = e as ApiError
        if (err.status === 422) {
          setBatchError(err.detail ?? 'Không thể tải lên các file này.')
          setItems((xs) => [...xs, ...newItems.filter((x) => x.state === 'rejected')])
          return
        }
        // Lỗi khác: để từng file tự tạo lô khi chạy
      }
    }
    setItems((xs) => [...xs, ...newItems])
  }

  const active = items.filter((x) => x.state === 'queued' || x.state === 'uploading').length
  const nearQuota = remaining <= 5

  return (
    <section className="docs" aria-labelledby="docs-title">
      <div className="panel-head">
        <h2 id="docs-title">Tài liệu</h2>
        <span className={`quota${nearQuota ? ' near' : ''}`} title="Số tài liệu đang dùng / giới hạn">
          {used}/{limit} tài liệu
        </span>
      </div>
      <div
        className={`drop${dragging ? ' active' : ''}`}
        aria-label="Vùng tải tài liệu"
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragging(false)
          void addFiles(e.dataTransfer.files)
        }}
      >
        <div className="drop-title">
          <Icon name="upload" size={18} /> Kéo thả file PDF vào đây
        </div>
        <p>hoặc</p>
        <button
          className="btn btn-primary"
          type="button"
          disabled={remaining === 0}
          onClick={() => inputRef.current?.click()}
        >
          <Icon name="upload" /> Chọn file PDF
        </button>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          multiple
          onChange={(e) => {
            if (e.target.files) void addFiles(e.target.files)
            e.target.value = ''
          }}
        />
        <p>
          Tối đa {limits.max_files_per_batch} file mỗi lần · mỗi file ≤ {limits.max_file_mb} MB và ≤ {limits.max_pages}{' '}
          trang · chỉ PDF có chữ (chưa hỗ trợ PDF scan)
        </p>
      </div>
      <div className="scroll" aria-live="polite">
        {batchError && (
          <div className="alert alert-danger" role="alert" style={{ marginTop: 4 }}>
            <Icon name="alert" />
            <div className="body">
              <span className="t">Chưa có file nào được tải lên.</span>
              <br />
              {batchError}
            </div>
          </div>
        )}
        {nearQuota && remaining > 0 && (
          <div className="alert alert-warn" role="status" style={{ marginTop: 8 }}>
            <Icon name="alert" />
            <div className="body">
              <span className="t">Sắp đạt giới hạn tài liệu.</span>
              <br />
              Bạn còn có thể thêm <strong>{remaining} tài liệu</strong> ({used}/{limit}). Xóa tài liệu không còn dùng
              để có thêm chỗ.
            </div>
          </div>
        )}
        {items.length > 0 && (
          <>
            <div className="section-label">
              Đang tải lên ({active}/{items.length})
            </div>
            <ul className="list">
              {items.map((x) => (
                <UploadRow
                  key={x.key}
                  item={x}
                  onRetry={() => patch(x.key, { state: 'queued' })}
                  onDismiss={() => setItems((xs) => xs.filter((y) => y.key !== x.key))}
                />
              ))}
            </ul>
            <div className="section-label">Tài liệu của bạn</div>
          </>
        )}
        {docs.length === 0 ? (
          items.length === 0 ? (
            <div className="empty">
              <span className="ill">
                <Icon name="file" size={26} />
              </span>
              <h3>Chưa có tài liệu nào</h3>
              <p>Tải lên các file PDF của dự án để bắt đầu hỏi đáp.</p>
            </div>
          ) : (
            <div className="empty" style={{ padding: '16px 0' }}>
              <p>Tài liệu sẽ xuất hiện ở đây khi tải lên xong.</p>
            </div>
          )
        ) : (
          <ul className="list">
            {docs.map((d) => (
              <DocRow key={d.id} doc={d} onDelete={() => onDelete(d)} onReprocess={() => onReprocess(d)} />
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}

function UploadRow({ item, onRetry, onDismiss }: { item: UploadItem; onRetry: () => void; onDismiss: () => void }) {
  const failed = item.state === 'rejected' || item.state === 'failed'
  return (
    <li className={`row${failed ? ' is-failed' : ''}`}>
      <span className="file-ic">
        <Icon name="file" size={18} />
      </span>
      <div>
        <div className="name">{item.file.name}</div>
        <div className="meta">{formatBytes(item.file.size)}</div>
        {item.state === 'uploading' && (
          <>
            <span className="status st-uploading">
              <span className="spin" aria-hidden="true" /> Đang tải lên {item.progress}%
            </span>
            <div
              className="progress"
              role="progressbar"
              aria-label={`Tiến độ tải ${item.file.name}`}
              aria-valuenow={item.progress}
              aria-valuemin={0}
              aria-valuemax={100}
            >
              <span style={{ width: `${item.progress}%` }} />
            </div>
          </>
        )}
        {item.state === 'queued' && (
          <span className="status st-uploading">
            <Icon name="clock" size={12} /> Đang chờ tải lên
          </span>
        )}
        {item.state === 'rejected' && (
          <>
            <span className="status st-failed">
              <Icon name="x" size={12} /> Không nhận
            </span>
            <div className="reason">{item.reason}</div>
          </>
        )}
        {item.state === 'failed' && (
          <>
            <span className="status st-failed">
              <Icon name="wifi-off" size={12} /> Tải lên thất bại
            </span>
            <div className="reason">{item.reason}</div>
            <div style={{ marginTop: 8 }}>
              <button className="btn" type="button" onClick={onRetry}>
                <Icon name="refresh" size={14} /> Tải lại
              </button>
            </div>
          </>
        )}
      </div>
      <div className="actions">
        {failed && (
          <button
            className="icon-btn"
            type="button"
            aria-label={`Đóng thông báo về ${item.file.name}`}
            onClick={onDismiss}
          >
            <Icon name="close" />
          </button>
        )}
      </div>
    </li>
  )
}

function DocRow({ doc, onDelete, onReprocess }: { doc: Doc; onDelete: () => void; onReprocess: () => void }) {
  const meta = `${doc.page_count} trang · ${formatBytes(doc.size_bytes)} · ${formatDateTime(doc.uploaded_at)}`
  return (
    <li className={`row${doc.status === 'FAILED' ? ' is-failed' : ''}`}>
      <span className="file-ic">
        <Icon name="file" size={18} />
      </span>
      <div>
        <div className="name">{doc.file_name}</div>
        <div className="meta">{meta}</div>
        {doc.status === 'PROCESSING' && (
          <span className="status st-processing">
            <span className="spin" aria-hidden="true" /> Đang xử lý
          </span>
        )}
        {doc.status === 'READY' && (
          <span className="status st-ready">
            <Icon name="check" size={12} /> Sẵn sàng
          </span>
        )}
        {doc.status === 'FAILED' && (
          <>
            <span className="status st-failed">
              <Icon name="x" size={12} /> Thất bại
            </span>
            <div className="reason">{FAILURE_TEXT[doc.failure_code ?? 'R-01']}</div>
            {doc.retryable && (
              <div style={{ marginTop: 8 }}>
                <button className="btn" type="button" onClick={onReprocess}>
                  <Icon name="refresh" size={14} /> Xử lý lại
                </button>
              </div>
            )}
          </>
        )}
      </div>
      <div className="actions">
        <button className="icon-btn" type="button" aria-label={`Xóa ${doc.file_name}`} onClick={onDelete}>
          <Icon name="trash" />
        </button>
      </div>
    </li>
  )
}
