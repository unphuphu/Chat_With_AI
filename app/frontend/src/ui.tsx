// Biểu tượng SVG và hàm định dạng dùng chung (khớp bộ thiết kế html_design).
import type { ReactNode } from 'react'

const PATHS: Record<string, ReactNode> = {
  check: <path d="M20 6 9 17l-5-5" />,
  x: <path d="M18 6 6 18M6 6l12 12" />,
  alert: (
    <>
      <path d="M12 9v4M12 17h.01" />
      <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
    </>
  ),
  info: (
    <>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 16v-4M12 8h.01" />
    </>
  ),
  file: (
    <>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
      <path d="M14 2v6h6" />
    </>
  ),
  upload: (
    <>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <path d="m17 8-5-5-5 5M12 3v12" />
    </>
  ),
  trash: <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" />,
  refresh: (
    <>
      <path d="M21 12a9 9 0 1 1-3-6.7L21 8" />
      <path d="M21 3v5h-5" />
    </>
  ),
  send: (
    <>
      <path d="m22 2-7 20-4-9-9-4Z" />
      <path d="M22 2 11 13" />
    </>
  ),
  logout: <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />,
  close: <path d="M18 6 6 18M6 6l12 12" />,
  lock: (
    <>
      <rect x="3" y="11" width="18" height="11" rx="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 6v6l4 2" />
    </>
  ),
  scale: <path d="M12 3v18M5 8h14M5 8l-3 7a4 4 0 0 0 6 0Zm14 0-3 7a4 4 0 0 0 6 0Z" />,
  chat: <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2Z" />,
  shield: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />,
  'wifi-off': (
    <path d="M2 2l20 20M8.5 16.5a5 5 0 0 1 7 0M2 8.8a15 15 0 0 1 4.2-2.6M10.7 5.1A15 15 0 0 1 22 8.8M5 12.9a10 10 0 0 1 5.2-2.8M19 12.9a10 10 0 0 0-1.9-1.4M12 20h.01" />
  ),
}

export type IconName = keyof typeof PATHS

export function Icon({ name, size = 16, label }: { name: IconName; size?: number; label?: string }) {
  return (
    <svg
      className="i"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...(label ? { role: 'img', 'aria-label': label } : { 'aria-hidden': true })}
    >
      {PATHS[name]}
    </svg>
  )
}

export function formatBytes(n: number): string {
  if (n < 1024 * 1024) return `${Math.max(1, Math.round(n / 1024))} KB`
  return `${(n / 1024 / 1024).toLocaleString('vi-VN', { maximumFractionDigits: 1, minimumFractionDigits: 1 })} MB`
}

export function formatDateTime(iso: string): string {
  const d = new Date(iso)
  const p = (x: number) => String(x).padStart(2, '0')
  return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()} ${p(d.getHours())}:${p(d.getMinutes())}`
}

export function formatTime(iso?: string): string {
  const d = iso ? new Date(iso) : new Date()
  return d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
}

export const FAILURE_TEXT: Record<string, string> = {
  'R-01': 'Không đọc được nội dung file (file hỏng hoặc định dạng không hỗ trợ).',
  'R-02': 'File được bảo vệ bằng mật khẩu. Hãy gỡ mật khẩu rồi tải lại.',
  'R-03': 'File không chứa văn bản trích xuất được (PDF scan chưa được hỗ trợ). Hãy tải bản PDF có chữ.',
  'R-04': 'Lỗi xử lý tạm thời. Bạn có thể xử lý lại mà không cần tải lại file.',
}

export const ERROR_TEXT: Record<string, { title: string; detail: string }> = {
  ai_unavailable: {
    title: 'Không thể tạo câu trả lời lúc này, vui lòng thử lại.',
    detail: 'Câu hỏi của bạn vẫn được giữ nguyên. Bấm Gửi lại để thử lần nữa.',
  },
  ai_timeout: {
    title: 'Hệ thống phản hồi quá lâu.',
    detail: 'Câu hỏi của bạn vẫn được giữ nguyên. Bấm Gửi lại để thử lần nữa.',
  },
  network_error: {
    title: 'Mất kết nối tới máy chủ.',
    detail: 'Kiểm tra kết nối mạng rồi bấm Gửi lại – câu hỏi sẽ không bị trùng.',
  },
  internal_error: {
    title: 'Đã có lỗi xảy ra.',
    detail: 'Bấm Gửi lại để thử lần nữa.',
  },
}

export function uuid(): string {
  return crypto.randomUUID()
}

/** 2000 → "2.000" (không phụ thuộc dữ liệu ICU của trình duyệt). */
export function formatInt(n: number): string {
  return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.')
}
