import { expect, test } from '../evidence/fixture'
import { bodyOf, prep } from './_h'

test('Lô tải lên quá 10 file', async ({ ev }) => {
  await ev.step('Đăng nhập P2, xóa tài liệu cũ', 'Danh sách rỗng', async () => prep(ev, 'p2'))
  await ev.step('POST /upload-batches với 11 mục', '422 too_many_files; application/problem+json', async () => {
    const files = Array.from({ length: 11 }, (_, i) => ({ name: `${i + 1}.pdf`, size_bytes: 1 }))
    const r = await ev.api('POST', '/api/v1/upload-batches', { json: { files } })
    expect(r.status).toBe(422)
    expect(bodyOf(r).code).toBe('too_many_files')
    expect(r.headers['content-type']).toContain('application/problem+json')
  })
  await ev.step('GET /documents', 'Danh sách vẫn rỗng', async () => {
    const r = await ev.api('GET', '/api/v1/documents')
    expect(bodyOf(r).items).toEqual([])
  })
})
