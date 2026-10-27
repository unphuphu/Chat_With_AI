import { expect, test } from '../evidence/fixture'
import { bodyOf, file, prep, putFiles } from './_h'

test('Rate limit tải file', async ({ ev }) => {
  test.setTimeout(300_000)
  try {
    await ev.step('Khởi động lại ứng dụng với RATE_FILES_PER_HOUR=3', 'Ứng dụng sẵn sàng', async () => {
      await ev.restartApp({ RATE_FILES_PER_HOUR: '3' })
    })
    await ev.step('Đăng nhập tài khoản Quản trị viên (bộ đếm giờ còn sạch), xóa tài liệu cũ', 'Danh sách rỗng', async () => prep(ev, 'admin'))
    const f = file('gia-mao.pdf')
    const results: Awaited<ReturnType<typeof putFiles>>['results'] = []
    await ev.step('Tạo lô 4 file; PUT lần lượt 4 file gia-mao.pdf', '3 lần đầu 422 not_pdf; lần 4 → 429 rate_limited', async () => {
      const b = await ev.api('POST', '/api/v1/upload-batches', {
        json: { files: Array.from({ length: 4 }, (_, i) => ({ name: `g${i}.pdf`, size_bytes: f.buffer.length })) },
      })
      const batch = bodyOf(b).batch_id as string
      for (let i = 0; i < 4; i++) results.push(...(await putFiles(ev, [f], batch)).results)
      expect(results.map((r) => r.status)).toEqual([422, 422, 422, 429])
      expect(bodyOf(results[3]).code).toBe('rate_limited')
    })
    await ev.step('Kiểm tra header của phản hồi 429', 'Retry-After > 0; RateLimit-Limit: 3; RateLimit-Remaining: 0', async () => {
      const h = results[3].headers
      expect(Number(h['retry-after'])).toBeGreaterThan(0)
      expect(h['ratelimit-limit']).toBe('3')
      expect(h['ratelimit-remaining']).toBe('0')
      return `Retry-After=${h['retry-after']}, RateLimit-Limit=${h['ratelimit-limit']}, Remaining=${h['ratelimit-remaining']}`
    })
  } finally {
    await ev.restartApp()
  }
})
