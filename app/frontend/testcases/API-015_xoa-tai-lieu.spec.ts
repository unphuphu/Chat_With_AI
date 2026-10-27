import { expect, test } from '../evidence/fixture'
import { bodyOf, prep } from './_h'

test('Xóa tài liệu', async ({ ev }) => {
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf và chờ Sẵn sàng', 'Dòng Sẵn sàng', async () => prep(ev, 'p2', ['hop-dong-A.pdf']))
  let id = ''
  await ev.step('DELETE /documents/{id}', '204', async () => {
    id = ((bodyOf(await ev.api('GET', '/api/v1/documents')).items as { id: string }[])[0]).id
    expect((await ev.api('DELETE', `/api/v1/documents/${id}`)).status).toBe(204)
  })
  await ev.step('GET /documents', 'Không còn tài liệu; documents_used=0', async () => {
    const b = bodyOf(await ev.api('GET', '/api/v1/documents'))
    expect(b.items).toEqual([])
    expect(b.documents_used).toBe(0)
  })
  await ev.step('DELETE lần 2', '404 not_found', async () => {
    const r = await ev.api('DELETE', `/api/v1/documents/${id}`)
    expect(r.status).toBe(404)
    expect(bodyOf(r).code).toBe('not_found')
  })
})
