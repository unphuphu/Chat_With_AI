import { expect, test } from '../evidence/fixture'
import { bodyOf, file, prep, putFiles } from './_h'

test('Tải lên idempotent và lô hết chỗ', async ({ ev }) => {
  await ev.step('Đăng nhập P2, xóa tài liệu cũ', 'Danh sách rỗng', async () => prep(ev, 'p2'))
  const a = file('hop-dong-A.pdf')
  const cid = crypto.randomUUID()
  let batch = ''
  let id = ''
  await ev.step('Tạo lô 1 file; PUT hop-dong-A.pdf với client_file_id = X', '201, id = D', async () => {
    const b = await ev.api('POST', '/api/v1/upload-batches', { json: { files: [{ name: a.name, size_bytes: a.buffer.length }] } })
    batch = bodyOf(b).batch_id as string
    const { results } = await putFiles(ev, [{ ...a, cid }], batch)
    expect(results[0].status).toBe(201)
    id = bodyOf(results[0]).id as string
  })
  await ev.step('PUT lại đúng file với cùng client_file_id', '200, cùng id D', async () => {
    const { results } = await putFiles(ev, [{ ...a, cid }], batch)
    expect(results[0].status).toBe(200)
    expect(bodyOf(results[0]).id).toBe(id)
  })
  await ev.step('PUT chinh-sach-ban-hang-2026.pdf với client_file_id khác vào cùng lô', '409 batch_full', async () => {
    const { results } = await putFiles(ev, [file('chinh-sach-ban-hang-2026.pdf')], batch)
    expect(results[0].status).toBe(409)
    expect(bodyOf(results[0]).code).toBe('batch_full')
  })
  await ev.step('GET /documents', 'Chỉ 1 tài liệu, documents_used = 1', async () => {
    const r = await ev.api('GET', '/api/v1/documents')
    expect((bodyOf(r).items as unknown[]).length).toBe(1)
    expect(bodyOf(r).documents_used).toBe(1)
  })
})
