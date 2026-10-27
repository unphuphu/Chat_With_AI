import { expect, test } from '../evidence/fixture'
import { bodyOf, prep } from './_h'

test('Danh sách tài liệu', async ({ ev }) => {
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf và chờ Sẵn sàng', 'Dòng Sẵn sàng', async () => prep(ev, 'p2', ['hop-dong-A.pdf']))
  await ev.step('GET /api/v1/documents', '200; items[0] đủ trường, status=READY; documents_used=1, documents_limit=100', async () => {
    const r = await ev.api('GET', '/api/v1/documents')
    const b = bodyOf(r)
    expect(r.status).toBe(200)
    const d = (b.items as Record<string, unknown>[])[0]
    for (const k of ['id', 'file_name', 'status', 'failure_code', 'page_count', 'size_bytes', 'uploaded_at', 'ready_at']) expect(d).toHaveProperty(k)
    expect(d).toMatchObject({ status: 'READY', failure_code: null, file_name: 'hop-dong-A.pdf', page_count: 3 })
    expect(b).toMatchObject({ documents_used: 1, documents_limit: 100 })
  })
})
