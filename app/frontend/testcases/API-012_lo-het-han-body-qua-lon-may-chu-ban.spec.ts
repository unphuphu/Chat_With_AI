import { expect, test } from '../evidence/fixture'
import { bodyOf, file, prep, putFiles } from './_h'

test('Lô hết hạn, body quá lớn, máy chủ bận', async ({ ev }) => {
  test.setTimeout(420_000)
  try {
    await ev.step('Khởi động lại ứng dụng với BATCH_TTL_S=60', 'Ứng dụng sẵn sàng', async () => {
      await ev.restartApp({ BATCH_TTL_S: '60' })
    })
    await ev.step('Đăng nhập P2, xóa tài liệu cũ', 'Danh sách rỗng', async () => prep(ev, 'p2'))
    const f = file('hop-dong-A.pdf')
    await ev.step('Tạo lô, chờ 65 s rồi PUT hop-dong-A.pdf', '404 batch_expired', async () => {
      const b = await ev.api('POST', '/api/v1/upload-batches', { json: { files: [{ name: f.name, size_bytes: f.buffer.length }] } })
      const batch = bodyOf(b).batch_id as string
      await new Promise((r) => setTimeout(r, 65_000))
      const { results } = await putFiles(ev, [f], batch)
      expect(results[0].status).toBe(404)
      expect(bodyOf(results[0]).code).toBe('batch_expired')
    })
    await ev.step('PUT body 22 MB (vượt MAX_FILE_MB + 1 MB)', '413; application/problem+json', async () => {
      const big = { name: 'rat-lon.pdf', buffer: Buffer.concat([Buffer.from('%PDF-1.4\n'), Buffer.alloc(22 * 1024 * 1024, 48)]) }
      const { results } = await putFiles(ev, [big])
      expect(results[0].status).toBe(413)
      expect(results[0].headers['content-type']).toContain('application/problem+json')
    })
    ev.note('Bước tùy chọn "máy chủ bận 503 server_busy" (SANDBOX_CONCURRENCY=1) không thực hiện trong lần chạy này.')
  } finally {
    await ev.restartApp()
  }
})
