import { expect, test } from '../evidence/fixture'
import { bodyOf, file, prep, putFiles, waitReady } from './_h'

test('Tải lên một PDF hợp lệ', async ({ ev, page }) => {
  await ev.step('Đăng nhập P2, xóa tài liệu cũ', 'Danh sách rỗng', async () => prep(ev, 'p2'))
  const f = file('hop-dong-A.pdf')
  let batch = ''
  await ev.step('POST /upload-batches với 1 file', '201, có batch_id, expires_at', async () => {
    const r = await ev.api('POST', '/api/v1/upload-batches', { json: { files: [{ name: f.name, size_bytes: f.buffer.length }] } })
    expect(r.status).toBe(201)
    batch = bodyOf(r).batch_id as string
    expect(bodyOf(r).expires_at).toBeTruthy()
  })
  await ev.step('PUT /upload-batches/{batch}/files/{uuid} multipart', '201; PROCESSING, page_count=3, retryable=false, file_name=hop-dong-A.pdf', async () => {
    const { results } = await putFiles(ev, [f], batch)
    const d = bodyOf(results[0])
    expect(results[0].status).toBe(201)
    expect(d).toMatchObject({ status: 'PROCESSING', page_count: 3, retryable: false, file_name: 'hop-dong-A.pdf' })
    return `status=${d.status}, page_count=${d.page_count}`
  })
  await ev.step('Tải lại trang, xem khu vực Tài liệu', 'hop-dong-A.pdf chuyển Sẵn sàng ≤ 60 s', async () => {
    await page.bringToFront()
    await page.reload()
    await waitReady(page, 'hop-dong-A.pdf', 60_000)
  })
})
