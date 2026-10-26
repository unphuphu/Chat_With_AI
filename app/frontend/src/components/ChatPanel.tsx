// Khu vực Hỏi đáp (S03–S05): luồng hội thoại, gửi lại cùng client_request_id, đếm ngược khi bị giới hạn.
import { Fragment, useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { api, ApiError, type Citation, type Conversation, type Message } from '../api'
import { ERROR_TEXT, Icon, formatInt, formatTime, uuid } from '../ui'

export const DRAFT_KEY = 'aichat-draft'

interface Props {
  conversation: Conversation | null
  readyCount: number
  processingCount: number
  maxChars: number
  onOpenCitation: (c: Citation, el: HTMLElement) => void
}

export function ChatPanel({ conversation, readyCount, processingCount, maxChars, onOpenCitation }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [text, setText] = useState(() => {
    try {
      const d = sessionStorage.getItem(DRAFT_KEY)
      if (d) sessionStorage.removeItem(DRAFT_KEY)
      return d ?? ''
    } catch {
      return ''
    }
  })
  const [sending, setSending] = useState(false)
  const [rateUntil, setRateUntil] = useState<number | null>(null)
  const [now, setNow] = useState(Date.now())
  const [notice, setNotice] = useState<string | null>(null)
  const threadRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (conversation) setMessages(conversation.messages)
  }, [conversation])

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight })
  }, [messages])

  // Lưu nháp để khôi phục khi phiên hết hạn (S11)
  useEffect(() => {
    try {
      if (text) sessionStorage.setItem(`${DRAFT_KEY}-live`, text)
      else sessionStorage.removeItem(`${DRAFT_KEY}-live`)
    } catch {
      /* bỏ qua */
    }
  }, [text])

  useEffect(() => {
    if (!rateUntil) return
    const t = setInterval(() => {
      setNow(Date.now())
      if (Date.now() >= rateUntil) setRateUntil(null)
    }, 500)
    return () => clearInterval(t)
  }, [rateUntil])

  const rateLeft = rateUntil ? Math.max(0, Math.ceil((rateUntil - now) / 1000)) : 0
  const noDocs = readyCount === 0
  const locked = noDocs || sending || rateLeft > 0 || !conversation

  async function send(question: string, crid: string) {
    if (!conversation) return
    setSending(true)
    setNotice(null)
    const optimistic: Message = {
      message_id: `pending-${crid}`,
      client_request_id: crid,
      question,
      status: 'PENDING',
      answer: null,
      citations: [],
      error_code: null,
      created_at: new Date().toISOString(),
    }
    setMessages((ms) => [...ms.filter((m) => m.client_request_id !== crid), optimistic])
    const replace = (m: Partial<Message> | null) =>
      setMessages((ms) =>
        m === null
          ? ms.filter((x) => x.client_request_id !== crid)
          : ms.map((x) => (x.client_request_id === crid ? { ...x, ...m } : x)),
      )
    try {
      const a = await api.ask(conversation.id, crid, question)
      replace({
        message_id: a.message_id,
        status: a.status,
        answer: a.answer,
        citations: a.citations,
        conflict: a.conflict,
        error_code: null,
      })
    } catch (e) {
      const err = e as ApiError
      if (err.status === 429) {
        replace(null)
        setText(question)
        setRateUntil(Date.now() + (err.retryAfter ?? 30) * 1000)
      } else if (err.status === 409 && err.code === 'request_in_progress') {
        replace({ status: 'PENDING' })
      } else if (err.status === 409 || err.status === 422) {
        replace(null)
        setText(question)
        setNotice(err.detail ?? 'Không gửi được câu hỏi.')
      } else if (err.status === 401) {
        replace(null)
      } else {
        replace({ status: 'FAILED', error_code: ERROR_TEXT[err.code] ? err.code : 'internal_error' })
      }
    } finally {
      setSending(false)
    }
  }

  function submit() {
    const q = text.trim()
    if (!q || locked || q.length > maxChars) return
    setText('')
    void send(q, uuid())
  }

  function onKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      submit()
    }
  }

  const reason = noDocs
    ? processingCount > 0
      ? 'Đang xử lý tài liệu, bạn có thể hỏi khi có ít nhất một tài liệu Sẵn sàng.'
      : 'Cần ít nhất một tài liệu Sẵn sàng để bắt đầu hỏi.'
    : null

  return (
    <section className="chat" aria-labelledby="chat-title">
      <div className="panel-head">
        <div>
          <h2 id="chat-title" style={{ margin: 0, fontSize: 'var(--fs-lg)' }}>
            Hỏi đáp
          </h2>
          <p>Hỏi bằng tiếng Việt hoặc tiếng Anh. Mỗi câu trả lời kèm tên tài liệu và số trang để bạn kiểm chứng.</p>
        </div>
      </div>
      <div className="thread" id="thread" ref={threadRef} aria-live="polite" aria-label="Hội thoại">
        <div className="thread-inner">
          {messages.length === 0 ? (
            <EmptyChat readyCount={readyCount} />
          ) : (
            messages.map((m) => (
              <Fragment key={m.client_request_id}>
                <div className="q">
                  <span className="sr-only">Bạn hỏi: </span>
                  {m.question}
                  <span className="time">{formatTime(m.created_at)}</span>
                </div>
                <AnswerView
                  m={m}
                  onOpen={onOpenCitation}
                  onResend={() => void send(m.question, m.client_request_id)}
                  canResend={!sending && rateLeft === 0}
                />
              </Fragment>
            ))
          )}
        </div>
      </div>
      <div className="composer">
        <div className="composer-inner">
          {rateLeft > 0 && (
            <div className="alert alert-warn" role="status" style={{ marginBottom: 8 }}>
              <Icon name="clock" />
              <div className="body">
                <span className="t">Bạn thao tác quá nhanh.</span> Vui lòng thử lại sau{' '}
                <strong>{rateLeft} giây</strong>.
              </div>
            </div>
          )}
          {notice && (
            <div className="alert alert-danger" role="alert" style={{ marginBottom: 8 }}>
              <Icon name="alert" />
              <div className="body">{notice}</div>
            </div>
          )}
          {reason && (
            <div className="locked-reason">
              <Icon name="lock" size={14} /> {reason}
            </div>
          )}
          <form
            className={`box${locked ? ' locked' : ''}`}
            aria-label="Đặt câu hỏi"
            onSubmit={(e) => {
              e.preventDefault()
              submit()
            }}
          >
            <label className="sr-only" htmlFor="q">
              Câu hỏi về tài liệu
            </label>
            <textarea
              id="q"
              rows={2}
              maxLength={maxChars}
              placeholder="Hỏi về nội dung tài liệu, ví dụ: Điều khoản thanh toán trong hợp đồng A là gì?"
              value={text}
              disabled={noDocs || !conversation}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={onKey}
            />
            <button className="btn btn-primary" type="submit" disabled={locked || !text.trim()}>
              <Icon name="send" /> {sending ? 'Đang gửi…' : 'Gửi'}
            </button>
          </form>
          <div className="composer-foot">
            <span>
              Enter để gửi · Shift + Enter để xuống dòng · Câu trả lời chỉ dựa trên tài liệu Sẵn sàng của bạn
            </span>
            <span className={`counter${text.length >= maxChars ? ' over' : ''}`}>
              {formatInt(text.length)}/{formatInt(maxChars)}
            </span>
          </div>
        </div>
      </div>
    </section>
  )
}

function EmptyChat({ readyCount }: { readyCount: number }) {
  if (readyCount > 0) {
    return (
      <div className="empty" style={{ paddingTop: 64 }}>
        <span className="ill">
          <Icon name="chat" size={26} />
        </span>
        <h3>Bạn có thể bắt đầu hỏi</h3>
        <p>
          {readyCount} tài liệu đã Sẵn sàng.{' '}
          {readyCount > 1
            ? 'Câu trả lời có thể tổng hợp từ nhiều tài liệu.'
            : 'Các tài liệu đang xử lý sẽ tự được dùng khi sẵn sàng.'}
        </p>
      </div>
    )
  }
  return (
    <div className="empty" style={{ paddingTop: 64 }}>
      <span className="ill">
        <Icon name="chat" size={26} />
      </span>
      <h3>Hỏi đáp với tài liệu của bạn</h3>
      <p>Chỉ cần ba bước:</p>
      <ol className="steps">
        <li>
          <b>1</b>
          <span>
            Tải lên một hoặc nhiều file PDF ở khu vực <strong>Tài liệu</strong> bên trái.
          </span>
        </li>
        <li>
          <b>2</b>
          <span>
            Chờ tài liệu chuyển sang <strong>Sẵn sàng</strong> (thường dưới 3 phút).
          </span>
        </li>
        <li>
          <b>3</b>
          <span>Đặt câu hỏi – câu trả lời luôn kèm tên tài liệu và số trang để bạn kiểm chứng.</span>
        </li>
      </ol>
    </div>
  )
}

function AnswerView({
  m,
  onOpen,
  onResend,
  canResend,
}: {
  m: Message
  onOpen: (c: Citation, el: HTMLElement) => void
  onResend: () => void
  canResend: boolean
}) {
  if (m.status === 'PENDING') {
    return (
      <article className="a" aria-label="Đang soạn câu trả lời" aria-busy="true">
        <div className="a-head">
          <Icon name="chat" size={14} /> Trợ lý tài liệu
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-muted)' }}>
          <span className="dots" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>{' '}
          Đang tìm trong tài liệu và soạn câu trả lời… (thường dưới 15 giây)
        </div>
      </article>
    )
  }
  if (m.status === 'FAILED') {
    const t = ERROR_TEXT[m.error_code ?? ''] ?? ERROR_TEXT.internal_error
    return (
      <article className="a failed" aria-label="Lỗi khi tạo câu trả lời" role="alert">
        <div className="a-head">
          <span className="badge badge-failed">
            <Icon name="alert" size={12} /> Chưa trả lời được
          </span>
        </div>
        <p>
          <strong>{t.title}</strong>
        </p>
        <p style={{ color: 'var(--text-muted)', fontSize: 'var(--fs-sm)' }}>{t.detail}</p>
        <button className="btn" type="button" onClick={onResend} disabled={!canResend}>
          <Icon name="refresh" size={14} /> Gửi lại
        </button>
      </article>
    )
  }
  if (m.status === 'INSUFFICIENT') {
    return (
      <article className="a insufficient" aria-label="Câu trả lời: chưa đủ thông tin">
        <div className="a-head">
          <span className="badge badge-insufficient">
            <Icon name="info" size={12} /> Chưa đủ thông tin
          </span>
        </div>
        <p>
          Các tài liệu Sẵn sàng của bạn chưa có thông tin để trả lời câu hỏi này. Hệ thống không suy đoán ngoài tài
          liệu.
        </p>
        <p style={{ color: 'var(--text-muted)', fontSize: 'var(--fs-sm)', margin: 0 }}>
          Gợi ý: tải thêm tài liệu có chứa thông tin này, hoặc diễn đạt lại câu hỏi cụ thể hơn.
        </p>
      </article>
    )
  }
  const byOrdinal = new Map(m.citations.map((c) => [c.ordinal, c]))
  // Tách "[n]" thành nút – không dựng HTML từ câu trả lời (CA-04)
  const parts = (m.answer ?? '').split(/(\[\d+\])/g)
  return (
    <article className="a" aria-label="Câu trả lời">
      <div className="a-head">
        <Icon name="chat" size={14} /> Trợ lý tài liệu
      </div>
      <p className="answer-text">
        {parts.map((p, i) => {
          const mm = p.match(/^\[(\d+)\]$/)
          const c = mm ? byOrdinal.get(Number(mm[1])) : undefined
          if (!mm || !c) return <Fragment key={i}>{p}</Fragment>
          return (
            <button
              key={i}
              className="ref"
              type="button"
              aria-label={`Xem nguồn ${c.ordinal}`}
              disabled={c.deleted}
              onClick={(e) => onOpen(c, e.currentTarget)}
            >
              {c.ordinal}
            </button>
          )
        })}
      </p>
      {m.conflict && (
        <div className="conflict">
          <span className="badge badge-conflict">
            <Icon name="scale" size={12} /> Các tài liệu không thống nhất
          </span>
          <div style={{ marginTop: 4, fontSize: 'var(--fs-sm)' }}>
            Hãy kiểm tra tài liệu nào mới hơn trước khi sử dụng thông tin.
          </div>
        </div>
      )}
      <div className="sources">
        <h4>Nguồn tham chiếu</h4>
        <div className="chips">
          {m.citations.map((c) => {
            const label = `${c.document_name}${c.page_number ? ` · tr.${c.page_number}` : ''}`
            return c.deleted ? (
              <span key={c.ordinal} className="chip deleted" aria-disabled="true" title="Tài liệu đã bị xóa">
                <span className="n">[{c.ordinal}]</span> {label} (đã xóa)
              </span>
            ) : (
              <button
                key={c.ordinal}
                className="chip"
                type="button"
                aria-label={`Mở nguồn ${c.ordinal}: ${label}`}
                onClick={(e) => onOpen(c, e.currentTarget)}
              >
                <span className="n">[{c.ordinal}]</span> <Icon name="file" size={14} /> {label}
              </button>
            )
          })}
        </div>
      </div>
    </article>
  )
}
