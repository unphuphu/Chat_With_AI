import { expect, test } from '../evidence/fixture'
import { bodyOf, prep, upload, waitReady } from './_h'

type Doc = { id: string; file_name: string; status: string; failure_code: string | null; retryable: boolean }

test('Xử lý lại chỉ với R-04', async ({ ev, page }) => {
  test.setTimeout(540_000)
  const docs = async () => (bodyOf(await ev.api('GET', '/api/v1/documents')).items as Doc[])
  const find = async (name: string) => (await docs()).find((d) => d.file_name === name)
  let restored = false
  try {
    await ev.step('Đăng nhập P2, tải hop-dong-A.pdf, chờ Sẵn sàng', 'Dòng Sẵn sàng', async () => prep(ev, 'p2', ['hop-dong-A.pdf']))
    await ev.step('POST /reprocess với tài liệu READY', '409 not_retryable', async () => {
      const r = await ev.api('POST', `/api/v1/documents/${(await find('hop-dong-A.pdf'))!.id}/reprocess`)
      expect(r.status).toBe(409)
      expect(bodyOf(r).code).toBe('not_retryable')
    })
    await ev.step('Tải ho-so-scan-2019.pdf (→ R-03); POST /reprocess', '409 not_retryable', async () => {
      await page.bringToFront()
      await upload(page, 'ho-so-scan-2019.pdf')
      await expect(page.locator('li.row', { hasText: 'ho-so-scan-2019.pdf' }).getByText('Thất bại')).toBeVisible({ timeout: 60_000 })
      const d = (await find('ho-so-scan-2019.pdf'))!
      expect(d.failure_code).toBe('R-03')
      const r = await ev.api('POST', `/api/v1/documents/${d.id}/reprocess`)
      expect(r.status).toBe(409)
    })
    await ev.step('Khởi động lại với dịch vụ embedding không tồn tại; tải bang-gia-Q4.pdf', 'Tài liệu thất bại R-04 sau 3 lần thử (≈ 3 phút)', async () => {
      await ev.restartApp({ EMBEDDING_PROVIDER: 'http', EMBEDDING_URL: 'http://127.0.0.1:9' })
      await page.bringToFront()
      await upload(page, 'bang-gia-Q4.pdf')
      await expect
        .poll(async () => (await find('bang-gia-Q4.pdf'))?.failure_code, { timeout: 330_000, intervals: [5000] })
        .toBe('R-04')
      expect((await find('bang-gia-Q4.pdf'))!.retryable).toBe(true)
    })
    await ev.step('Khôi phục cấu hình mặc định (embedding hoạt động)', 'Ứng dụng sẵn sàng; tài liệu vẫn FAILED R-04, retryable', async () => {
      await ev.restartApp()
      restored = true
      expect((await find('bang-gia-Q4.pdf'))!.failure_code).toBe('R-04')
    })
    await ev.step('POST /reprocess tài liệu R-04', '202, status=PROCESSING', async () => {
      const r = await ev.api('POST', `/api/v1/documents/${(await find('bang-gia-Q4.pdf'))!.id}/reprocess`)
      expect(r.status).toBe(202)
      expect(bodyOf(r).status).toBe('PROCESSING')
    })
  } finally {
    // Phòng khi test lỗi giữa chừng: trả cấu hình mặc định (không khởi động lại lần nữa khi đã khôi phục – tránh ngắt job đang chạy)
    if (!restored) await ev.restartApp()
  }
  await ev.step('Sau khi khôi phục cấu hình mặc định', 'bang-gia-Q4.pdf được xử lý lại và Sẵn sàng', async () => {
    await page.bringToFront()
    await page.reload()
    await waitReady(page, 'bang-gia-Q4.pdf', 120_000)
  })
})
