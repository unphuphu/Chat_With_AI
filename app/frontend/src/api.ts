// Client cho /api/v1 (khớp app/contracts/openapi.yaml). Lỗi theo RFC 9457 kèm `code`.

export type DocumentStatus = 'PROCESSING' | 'READY' | 'FAILED'
export type FailureCode = 'R-01' | 'R-02' | 'R-03' | 'R-04'

export interface Limits {
  max_file_mb: number
  max_pages: number
  max_files_per_batch: number
  question_max_chars: number
}

export interface Me {
  user_id: string
  email: string
  role: string
  documents_used: number
  documents_limit: number
  session_expires_at: string
  limits: Limits
}

export interface Doc {
  id: string
  file_name: string
  status: DocumentStatus
  failure_code: FailureCode | null
  retryable: boolean
  page_count: number
  size_bytes: number
  uploaded_at: string
  ready_at: string | null
}

export interface DocList {
  items: Doc[]
  documents_used: number
  documents_limit: number
}

export interface Citation {
  ordinal: number
  document_id: string
  document_name: string
  page_number: number | null
  deleted: boolean
}

export type MessageStatus = 'PENDING' | 'ANSWERED' | 'INSUFFICIENT' | 'FAILED'

export interface Message {
  message_id: string
  client_request_id: string
  question: string
  status: MessageStatus
  answer: string | null
  citations: Citation[]
  error_code: string | null
  created_at: string
  conflict?: boolean
}

export interface Conversation {
  id: string
  messages: Message[]
}

export interface Answer {
  message_id: string
  client_request_id: string
  status: MessageStatus
  answer: string | null
  citations: Citation[]
  latency_ms: number
  conflict: boolean
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    public detail: string | null,
    public retryAfter: number | null,
    public body: Record<string, unknown>,
  ) {
    super(detail || code)
  }
}

const BASE = '/api/v1'

export function csrfToken(): string {
  const m = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/)
  return m ? decodeURIComponent(m[1]) : ''
}

type SessionListener = (code: 'unauthenticated' | 'session_expired') => void
let onSessionLost: SessionListener = () => {}
export function setSessionListener(fn: SessionListener): void {
  onSessionLost = fn
}

async function toError(res: Response): Promise<ApiError> {
  let body: Record<string, unknown> = {}
  try {
    body = await res.json()
  } catch {
    /* không phải JSON */
  }
  const ra = res.headers.get('Retry-After')
  return new ApiError(
    res.status,
    String(body.code ?? `http_${res.status}`),
    (body.detail as string) ?? null,
    ra ? Number(ra) : null,
    body,
  )
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (method !== 'GET') headers['X-CSRF-Token'] = csrfToken()
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  let res: Response
  try {
    res = await fetch(BASE + path, {
      method,
      headers,
      credentials: 'same-origin',
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError(0, 'network_error', 'Mất kết nối tới máy chủ.', null, {})
  }
  if (!res.ok) {
    const err = await toError(res)
    if (res.status === 401 && (err.code === 'unauthenticated' || err.code === 'session_expired')) {
      onSessionLost(err.code)
    }
    throw err
  }
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

export const api = {
  me: () => request<Me>('GET', '/me'),
  logout: () => request<void>('POST', '/auth/logout'),
  documents: () => request<DocList>('GET', '/documents'),
  createBatch: (files: { name: string; size_bytes: number }[]) =>
    request<{ batch_id: string; expires_at: string }>('POST', '/upload-batches', { files }),
  deleteDocument: (id: string) => request<void>('DELETE', `/documents/${id}`),
  reprocess: (id: string) => request<Doc>('POST', `/documents/${id}/reprocess`),
  conversation: () => request<Conversation>('GET', '/conversations/current'),
  ask: (conversationId: string, clientRequestId: string, question: string) =>
    request<Answer>('POST', `/conversations/${conversationId}/messages`, {
      client_request_id: clientRequestId,
      question,
    }),
}

export function loginUrl(returnTo = '/'): string {
  return `${BASE}/auth/login?return_to=${encodeURIComponent(returnTo)}`
}

export function fileUrl(docId: string, page?: number | null, fromCitation = false): string {
  const q = new URLSearchParams()
  if (fromCitation) q.set('from', 'citation')
  if (page) q.set('page', String(page))
  const qs = q.toString()
  return `${BASE}/documents/${docId}/file${qs ? `?${qs}` : ''}`
}

/** PUT file bằng XHR để có tiến độ (fetch không báo tiến độ upload). */
export function uploadFile(
  batchId: string,
  clientFileId: string,
  file: File,
  onProgress: (pct: number) => void,
): { promise: Promise<Doc>; abort: () => void } {
  const xhr = new XMLHttpRequest()
  const promise = new Promise<Doc>((resolve, reject) => {
    xhr.open('PUT', `${BASE}/upload-batches/${batchId}/files/${clientFileId}`)
    xhr.setRequestHeader('X-CSRF-Token', csrfToken())
    xhr.setRequestHeader('Accept', 'application/json')
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress(Math.min(99, Math.round((e.loaded / e.total) * 100)))
    }
    xhr.onerror = () => reject(new ApiError(0, 'network_error', 'Mất kết nối khi đang tải lên.', null, {}))
    xhr.onabort = () => reject(new ApiError(0, 'aborted', null, null, {}))
    xhr.onload = () => {
      let body: Record<string, unknown> = {}
      try {
        body = JSON.parse(xhr.responseText || '{}')
      } catch {
        /* bỏ qua */
      }
      if (xhr.status >= 200 && xhr.status < 300) {
        onProgress(100)
        resolve(body as unknown as Doc)
        return
      }
      const ra = xhr.getResponseHeader('Retry-After')
      const err = new ApiError(
        xhr.status,
        String(body.code ?? `http_${xhr.status}`),
        (body.detail as string) ?? null,
        ra ? Number(ra) : null,
        body,
      )
      if (xhr.status === 401) onSessionLost(err.code === 'session_expired' ? 'session_expired' : 'unauthenticated')
      reject(err)
    }
    const form = new FormData()
    form.append('file', file, file.name)
    xhr.send(form)
  })
  return { promise, abort: () => xhr.abort() }
}
