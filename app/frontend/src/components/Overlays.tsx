// S06 trình xem PDF, S07 xác nhận xóa, thông báo góc dưới trái.
import { useEffect, useRef, type RefObject } from 'react'
import { fileUrl, type Citation, type Doc } from '../api'
import { Icon, type IconName } from '../ui'


const FOCUSABLE = 'button:not([disabled]), a[href], input:not([disabled]), select, textarea, iframe, [tabindex]:not([tabindex="-1"])'

/** Bẫy focus trong hộp thoại modal: Tab/Shift+Tab chỉ xoay vòng giữa các phần tử trong hộp (WCAG 2.4.3, ARIA modal). */
function useFocusTrap(ref: RefObject<HTMLElement>) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab' || !ref.current) return
      const items = Array.from(ref.current.querySelectorAll<HTMLElement>(FOCUSABLE))
      if (items.length === 0) {
        e.preventDefault()
        return
      }
      const first = items[0]
      const last = items[items.length - 1]
      const active = document.activeElement as HTMLElement | null
      if (!active || !ref.current.contains(active)) {
        e.preventDefault()
        first.focus()
      } else if (e.shiftKey && active === first) {
        e.preventDefault()
        last.focus()
      } else if (!e.shiftKey && active === last) {
        e.preventDefault()
        first.focus()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [ref])
}

export function PdfViewer({ citation, onClose }: { citation: Citation; onClose: () => void }) {
  const closeRef = useRef<HTMLButtonElement>(null)
  const boxRef = useRef<HTMLDivElement>(null)
  useFocusTrap(boxRef)
  useEffect(() => {
    closeRef.current?.focus()
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  const page = citation.page_number ?? 1
  // Trình xem PDF có sẵn của trình duyệt; #page=N mở đúng trang được trích dẫn
  const src = `${fileUrl(citation.document_id, citation.page_number, true)}#page=${page}`
  return (
    <>
      <div className="overlay" style={{ background: 'rgba(16,22,30,.35)' }} onClick={onClose} />
      <div ref={boxRef} className="viewer" role="dialog" aria-modal="true" aria-labelledby="viewer-title">
        <div className="viewer-bar">
          <Icon name="file" size={18} />
          <span className="title" id="viewer-title">
            {citation.document_name}
          </span>
          <span className="badge" style={{ background: 'var(--cite-soft)', color: 'var(--cite)' }}>
            Mở từ nguồn [{citation.ordinal}] · trang {page}
          </span>
          <span style={{ marginLeft: 'auto' }} />
          <button ref={closeRef} className="btn" type="button" aria-label="Đóng trình xem (Esc)" onClick={onClose}>
            <Icon name="close" /> Đóng
          </button>
        </div>
        <iframe title={`${citation.document_name} – trang ${page}`} src={src} />
      </div>
    </>
  )
}

export function DeleteDialog({
  doc,
  busy,
  onCancel,
  onConfirm,
}: {
  doc: Doc
  busy: boolean
  onCancel: () => void
  onConfirm: () => void
}) {
  const cancelRef = useRef<HTMLButtonElement>(null)
  const boxRef = useRef<HTMLDivElement>(null)
  useFocusTrap(boxRef)
  useEffect(() => {
    cancelRef.current?.focus()
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onCancel()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onCancel])
  return (
    <div className="overlay">
      <div ref={boxRef} className="dialog" role="alertdialog" aria-modal="true" aria-labelledby="dlg-t" aria-describedby="dlg-d">
        <h2 id="dlg-t">Xóa tài liệu?</h2>
        <p id="dlg-d">
          <strong style={{ color: 'var(--text)' }}>{doc.file_name}</strong> sẽ bị xóa khỏi danh sách và{' '}
          <strong style={{ color: 'var(--text)' }}>không còn được dùng để trả lời câu hỏi</strong> từ bây giờ.
          {doc.status === 'PROCESSING' && ' Việc xử lý tài liệu sẽ bị hủy.'}
        </p>
        <div className="alert alert-info">
          <Icon name="info" />
          <div className="body">
            File gốc sẽ được xóa hoàn toàn khỏi hệ thống trong vòng 24 giờ. Thao tác này không thể hoàn tác.
          </div>
        </div>
        <div className="foot">
          <button ref={cancelRef} className="btn" type="button" onClick={onCancel} disabled={busy}>
            Hủy
          </button>
          <button className="btn btn-danger" type="button" onClick={onConfirm} disabled={busy}>
            <Icon name="trash" /> {busy ? 'Đang xóa…' : 'Xóa tài liệu'}
          </button>
        </div>
      </div>
    </div>
  )
}

export interface ToastItem {
  id: string
  kind: 'ok' | 'warn' | 'danger'
  title: string
  body: string
  sticky?: boolean
}

const TOAST_ICON: Record<ToastItem['kind'], IconName> = { ok: 'check', warn: 'clock', danger: 'alert' }

export function Toasts({ items, onClose }: { items: ToastItem[]; onClose: (id: string) => void }) {
  return (
    <div className="toasts" aria-live="polite">
      {items.map((t) => (
        <ToastView key={t.id} t={t} onClose={() => onClose(t.id)} />
      ))}
    </div>
  )
}

function ToastView({ t, onClose }: { t: ToastItem; onClose: () => void }) {
  const closeRef = useRef(onClose)
  closeRef.current = onClose
  useEffect(() => {
    if (t.sticky) return
    const h = setTimeout(() => closeRef.current(), 5000)
    return () => clearTimeout(h)
  }, [t.sticky])
  return (
    <div className={`toast ${t.kind}`} role="status">
      <span className="lead">
        <Icon name={TOAST_ICON[t.kind]} size={18} />
      </span>
      <div style={{ flex: 1 }}>
        <div className="t">{t.title}</div>
        <div>{t.body}</div>
        {!t.sticky && (
          <div className="timer" aria-hidden="true">
            <span />
          </div>
        )}
      </div>
      <button className="icon-btn" type="button" aria-label="Đóng thông báo" onClick={onClose}>
        <Icon name="close" size={14} />
      </button>
    </div>
  )
}
