// S09 – chưa được cấp quyền, S10 – lỗi đăng nhập, S11 – phiên hết hạn.
import { useEffect, useState, type ReactNode } from 'react'
import { loginUrl } from '../api'
import { Icon, type IconName } from '../ui'

function Card(props: {
  bg: string
  fg: string
  icon: IconName
  title: string
  children: ReactNode
  actions: ReactNode
  foot?: ReactNode
}) {
  return (
    <main className="center" id="main">
      <div className="card">
        <span className="ill" style={{ background: props.bg, color: props.fg }}>
          <Icon name={props.icon} size={30} />
        </span>
        <h1>{props.title}</h1>
        {props.children}
        <div className="actions">{props.actions}</div>
        {props.foot}
      </div>
    </main>
  )
}

export function AccessDeniedPage() {
  return (
    <Card
      bg="var(--warn-soft)"
      fg="var(--warn)"
      icon="shield"
      title="Bạn chưa được cấp quyền dùng ứng dụng"
      actions={
        <a className="btn btn-primary" href={loginUrl('/')}>
          Đăng nhập lại
        </a>
      }
    >
      <p>
        Tài khoản của bạn đã đăng nhập thành công nhưng chưa thuộc nhóm người dùng của{' '}
        <strong style={{ color: 'var(--text)' }}>AI Chat PDF</strong>.
      </p>
      <p>
        Hãy liên hệ quản trị viên để được thêm vào nhóm <span className="ref-code">aichat-users</span>, sau đó đăng
        nhập lại.
      </p>
    </Card>
  )
}

export function LoginErrorPage() {
  const ref = new URLSearchParams(window.location.search).get('ref')
  return (
    <Card
      bg="var(--danger-soft)"
      fg="var(--danger)"
      icon="alert"
      title="Không thể đăng nhập"
      actions={
        <a className="btn btn-primary" href={loginUrl('/')}>
          Thử đăng nhập lại
        </a>
      }
      foot={
        ref ? (
          <p style={{ marginTop: 20, fontSize: 'var(--fs-xs)' }}>
            Nếu lỗi lặp lại, gửi mã tham chiếu này cho bộ phận hỗ trợ: <span className="ref-code">{ref}</span>
          </p>
        ) : null
      }
    >
      <p>
        Phiên đăng nhập đã hết hạn hoặc không hợp lệ. Điều này có thể xảy ra nếu bạn mở trang đăng nhập quá lâu hoặc ở
        nhiều tab.
      </p>
    </Card>
  )
}

export function SessionExpiredPage() {
  const [n, setN] = useState(5)
  useEffect(() => {
    const t = setInterval(() => setN((x) => Math.max(0, x - 1)), 1000)
    return () => clearInterval(t)
  }, [])
  useEffect(() => {
    if (n === 0) window.location.assign(loginUrl('/'))
  }, [n])
  return (
    <Card
      bg="var(--info-soft)"
      fg="var(--info)"
      icon="clock"
      title="Phiên làm việc đã hết hạn"
      actions={
        <a className="btn btn-primary" href={loginUrl('/')}>
          Đăng nhập ngay
        </a>
      }
    >
      <p>Để bảo vệ tài liệu, bạn cần đăng nhập lại. Đang chuyển tới trang đăng nhập…</p>
      <div className="alert alert-info" style={{ textAlign: 'left', marginTop: 12 }}>
        <Icon name="info" />
        <div className="body">
          Câu hỏi bạn đang soạn đã được lưu và sẽ hiện lại sau khi đăng nhập. Lịch sử hội thoại của phiên trước không
          được giữ lại.
        </div>
      </div>
      <p style={{ marginTop: 16 }}>
        <span className="spin" style={{ color: 'var(--primary)' }} aria-hidden="true" /> Tự chuyển sau{' '}
        <strong>{n}</strong> giây
      </p>
    </Card>
  )
}
