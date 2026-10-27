import { expect, test } from '../evidence/fixture'
import { bodyOf, prep } from './_h'

test('File của tài liệu đã xóa hoặc của người khác', async ({ ev }) => {
  let id = ''
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf, ghi lại id', 'Có id tài liệu của P2', async () => {
    await prep(ev, 'p2', ['hop-dong-A.pdf'])
    id = ((bodyOf(await ev.api('GET', '/api/v1/documents')).items as { id: string }[])[0]).id
  })
  await ev.step('Đăng xuất; đăng nhập P1; GET file của tài liệu P2', '404 not_found (không lộ sự tồn tại)', async () => {
    await ev.api('POST', '/api/v1/auth/logout')
    await ev.login('p1')
    const r = await ev.api('GET', `/api/v1/documents/${id}/file`)
    expect(r.status).toBe(404)
    expect(bodyOf(r).code).toBe('not_found')
  })
  await ev.step('Đăng nhập lại P2; xóa tài liệu; GET file', '410 deleted', async () => {
    await ev.api('POST', '/api/v1/auth/logout')
    await ev.login('p2')
    expect((await ev.api('DELETE', `/api/v1/documents/${id}`)).status).toBe(204)
    const r = await ev.api('GET', `/api/v1/documents/${id}/file`)
    expect(r.status).toBe(410)
    expect(bodyOf(r).code).toBe('deleted')
  })
})
