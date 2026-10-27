import { expect, test } from '../evidence/fixture'
import { bodyOf, conversationId, prep, Q_PAY } from './_h'

test('CSRF cho mọi thao tác ghi', async ({ ev }) => {
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf và chờ Sẵn sàng', 'Dòng Sẵn sàng', async () => prep(ev, 'p2', ['hop-dong-A.pdf']))
  let id = ''
  let conv = ''
  const noToken = async (headers?: Record<string, string>) => {
    const calls: [string, string, unknown?][] = [
      ['POST', '/api/v1/upload-batches', { files: [{ name: 'a.pdf', size_bytes: 1 }] }],
      ['DELETE', `/api/v1/documents/${id}`],
      ['POST', `/api/v1/documents/${id}/reprocess`],
      ['POST', `/api/v1/conversations/${conv}/messages`, { client_request_id: crypto.randomUUID(), question: Q_PAY }],
      ['POST', '/api/v1/auth/logout'],
    ]
    for (const [m, u, j] of calls) {
      const r = await ev.api(m as 'POST', u, { json: j, csrf: false, headers })
      expect(r.status, `${m} ${u}`).toBe(403)
      expect(bodyOf(r).code).toBe('csrf_invalid')
    }
  }
  await ev.step('Gọi 5 thao tác ghi KHÔNG có X-CSRF-Token', 'Mỗi request 403 csrf_invalid', async () => {
    id = ((bodyOf(await ev.api('GET', '/api/v1/documents')).items as { id: string }[])[0]).id
    conv = await conversationId(ev)
    await noToken()
  })
  await ev.step('Gọi lại với token sai (X-CSRF-Token: abc)', '403', async () => {
    await noToken({ 'X-CSRF-Token': 'abc' })
  })
  await ev.step('Kiểm tra trạng thái', 'Tài liệu vẫn còn; không có lượt hỏi mới', async () => {
    expect(((bodyOf(await ev.api('GET', '/api/v1/documents')).items as unknown[]).length)).toBe(1)
    expect((bodyOf(await ev.api('GET', '/api/v1/conversations/current')).messages as unknown[]).length).toBe(0)
  })
})
