// Gốc SPA: định tuyến theo pathname, nạp /me + /documents + hội thoại, nhận SSE /events.
import { useCallback, useEffect, useRef, useState } from 'react'
import { api, ApiError, loginUrl, setSessionListener, type Citation, type Conversation, type Doc, type Me } from './api'
import { ChatPanel, DRAFT_KEY } from './components/ChatPanel'
import { DocumentsPanel } from './components/DocumentsPanel'
import { DeleteDialog, PdfViewer, Toasts, type ToastItem } from './components/Overlays'
import { AccessDeniedPage, LoginErrorPage, SessionExpiredPage } from './components/StandalonePages'
import { Icon, uuid } from './ui'

export function App() {
  const path = window.location.pathname
  if (path === '/access-denied') return <AccessDeniedPage />
  if (path === '/login-error') return <LoginErrorPage />
  if (path === '/session-expired') return <SessionExpiredPage />
  return <MainApp />
}

function MainApp() {
  const [me, setMe] = useState<Me | null>(null)
  const [docs, setDocs] = useState<Doc[]>([])
  const [quota, setQuota] = useState({ used: 0, limit: 100 })
  const [conversation, setConversation] = useState<Conversation | null>(null)
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const [viewer, setViewer] = useState<Citation | null>(null)
  const [toDelete, setToDelete] = useState<Doc | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const viewerOpener = useRef<HTMLElement | null>(null)
  const prevStatus = useRef(new Map<string, string>())

  const toast = useCallback((t: Omit<ToastItem, 'id'>) => setToasts((xs) => [...xs.slice(-2), { ...t, id: uuid() }]), [])

  useEffect(() => {
    setSessionListener((code) => {
      if (code === 'session_expired') {
        try {
          const live = sessionStorage.getItem(`${DRAFT_KEY}-live`)
          if (live) sessionStorage.setItem(DRAFT_KEY, live)
        } catch {
          /* bỏ qua */
        }
        window.location.assign('/session-expired')
      } else {
        window.location.assign(loginUrl(window.location.pathname))
      }
    })
  }, [])

  const refreshDocs = useCallback(async () => {
    try {
      const list = await api.documents()
      // Thông báo khi tài liệu chuyển sang Sẵn sàng / Thất bại
      for (const d of list.items) {
        const before = prevStatus.current.get(d.id)
        if (before === 'PROCESSING' && d.status === 'READY') {
          toast({ kind: 'ok', title: 'Tài liệu đã Sẵn sàng', body: `${d.file_name} đã có thể dùng để hỏi đáp.` })
        } else if (before === 'PROCESSING' && d.status === 'FAILED') {
          toast({ kind: 'danger', title: 'Xử lý tài liệu thất bại', body: d.file_name })
        }
      }
      prevStatus.current = new Map(list.items.map((d) => [d.id, d.status]))
      setDocs(list.items)
      setQuota({ used: list.documents_used, limit: list.documents_limit })
    } catch (e) {
      if ((e as ApiError).status !== 401) setLoadError('Không tải được danh sách tài liệu.')
    }
  }, [toast])

  useEffect(() => {
    void (async () => {
      try {
        const m = await api.me()
        setMe(m)
        await refreshDocs()
        setConversation(await api.conversation())
      } catch (e) {
        if ((e as ApiError).status !== 401) setLoadError('Không kết nối được máy chủ. Hãy tải lại trang.')
      }
    })()
  }, [refreshDocs])

  // SSE: trạng thái tài liệu, hạn mức, phiên sắp hết hạn
  useEffect(() => {
    if (!me) return
    const es = new EventSource('/api/v1/events')
    es.addEventListener('document.status_changed', () => void refreshDocs())
    es.addEventListener('quota.changed', () => void refreshDocs())
    es.addEventListener('session.expiring', () =>
      toast({
        kind: 'warn',
        title: 'Phiên sắp hết hạn',
        body: 'Phiên làm việc sẽ hết hạn sau ít phút. Câu hỏi đang soạn sẽ được giữ lại khi bạn đăng nhập lại.',
        sticky: true,
      }),
    )
    // Dự phòng khi SSE bị chặn: thăm dò khi còn tài liệu đang xử lý
    const poll = setInterval(() => {
      if ([...prevStatus.current.values()].includes('PROCESSING')) void refreshDocs()
    }, 5000)
    return () => {
      es.close()
      clearInterval(poll)
    }
  }, [me, refreshDocs, toast])

  async function confirmDelete() {
    if (!toDelete) return
    const doc = toDelete
    setDeleting(true)
    setDocs((ds) => ds.filter((d) => d.id !== doc.id)) // lạc quan
    try {
      await api.deleteDocument(doc.id)
    } catch (e) {
      if ((e as ApiError).status !== 404) {
        toast({ kind: 'danger', title: 'Chưa xóa được tài liệu', body: 'Vui lòng thử lại.' })
      }
    } finally {
      setDeleting(false)
      setToDelete(null)
      await refreshDocs()
      setConversation(await api.conversation().catch(() => conversation))
    }
  }

  async function reprocess(doc: Doc) {
    try {
      await api.reprocess(doc.id)
      prevStatus.current.set(doc.id, 'PROCESSING')
    } catch {
      toast({ kind: 'danger', title: 'Không xử lý lại được', body: doc.file_name })
    }
    await refreshDocs()
  }

  const closeViewer = useCallback(() => {
    setViewer(null)
    viewerOpener.current?.focus()
  }, [])

  if (loadError) {
    return (
      <main className="center" id="main">
        <div className="card">
          <span className="ill" style={{ background: 'var(--danger-soft)', color: 'var(--danger)' }}>
            <Icon name="wifi-off" size={30} />
          </span>
          <h1>Có lỗi khi tải ứng dụng</h1>
          <p>{loadError}</p>
          <div className="actions">
            <button className="btn btn-primary" type="button" onClick={() => window.location.reload()}>
              Tải lại trang
            </button>
          </div>
        </div>
      </main>
    )
  }
  if (!me) {
    return (
      <div className="loading-page">
        <span>
          <span className="spin" aria-hidden="true" /> Đang tải…
        </span>
      </div>
    )
  }

  const ready = docs.filter((d) => d.status === 'READY').length
  const processing = docs.filter((d) => d.status === 'PROCESSING').length
  const initials = me.email
    .split('@')[0]
    .split(/[._-]/)
    .map((s) => s[0]?.toUpperCase() ?? '')
    .join('')
    .slice(0, 2)

  return (
    <>
      <a className="skip" href="#main">
        Bỏ qua tới nội dung chính
      </a>
      <div className="app">
        <header className="topbar">
          <div className="brand">
            <span className="brand-mark">
              <Icon name="chat" />
            </span>
            AI Chat PDF
          </div>
          <div className="spacer" />
          <div className="user">
            <span className="avatar" aria-hidden="true">
              {initials}
            </span>
            <span>{me.email}</span>
            <button
              className="btn btn-ghost"
              type="button"
              onClick={async () => {
                await api.logout().catch(() => undefined)
                window.location.assign(loginUrl('/'))
              }}
            >
              <Icon name="logout" /> Đăng xuất
            </button>
          </div>
        </header>
        <main className="main" id="main">
          <DocumentsPanel
            me={me}
            docs={docs}
            used={quota.used}
            limit={quota.limit}
            onUploaded={() => void refreshDocs()}
            onDelete={setToDelete}
            onReprocess={(d) => void reprocess(d)}
          />
          <ChatPanel
            conversation={conversation}
            readyCount={ready}
            processingCount={processing}
            maxChars={me.limits.question_max_chars}
            onOpenCitation={(c, el) => {
              viewerOpener.current = el
              setViewer(c)
            }}
          />
        </main>
      </div>
      <Toasts items={toasts} onClose={(id) => setToasts((xs) => xs.filter((t) => t.id !== id))} />
      {viewer && <PdfViewer citation={viewer} onClose={closeViewer} />}
      {toDelete && (
        <DeleteDialog
          doc={toDelete}
          busy={deleting}
          onCancel={() => setToDelete(null)}
          onConfirm={() => void confirmDelete()}
        />
      )}
    </>
  )
}
