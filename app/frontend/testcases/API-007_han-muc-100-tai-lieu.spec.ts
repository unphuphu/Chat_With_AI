import { expect, test } from '../evidence/fixture'
import { bodyOf, prep, upload, waitReady } from './_h'

test('Hạn mức tài liệu mỗi người', async ({ ev, page }) => {
  try {
    await ev.step('Khởi động lại ứng dụng với MAX_DOCS_PER_WORKSPACE=3', 'Ứng dụng sẵn sàng', async () => {
      await ev.restartApp({ MAX_DOCS_PER_WORKSPACE: '3' })
    })
    await ev.step('Đăng nhập P2, tải 2 file (còn 1 chỗ)', 'GET /me → documents_used = limit − 1', async () => {
      await prep(ev, 'p2')
      await upload(page, 'hop-dong-A.pdf', 'bang-gia-Q4.pdf')
      await waitReady(page, 'hop-dong-A.pdf')
      await waitReady(page, 'bang-gia-Q4.pdf')
      const me = bodyOf(await ev.api('GET', '/api/v1/me'))
      expect(me.documents_limit).toBe(3)
      expect(me.documents_used).toBe(2)
    })
    await ev.step('POST /upload-batches xin 2 file', '422 quota_exceeded, remaining = 1', async () => {
      const r = await ev.api('POST', '/api/v1/upload-batches', {
        json: { files: [{ name: 'a.pdf', size_bytes: 10 }, { name: 'b.pdf', size_bytes: 10 }] },
      })
      expect(r.status).toBe(422)
      expect(bodyOf(r).code).toBe('quota_exceeded')
      expect(bodyOf(r).remaining).toBe(1)
      return `HTTP 422 quota_exceeded remaining=${bodyOf(r).remaining}`
    })
    await ev.step('Quan sát giao diện', 'Huy hiệu hạn mức đổi màu cảnh báo; thông báo Sắp đạt giới hạn tài liệu', async () => {
      await page.bringToFront()
      await page.reload()
      await expect(page.locator('.quota')).toHaveText('2/3 tài liệu')
      await expect(page.locator('.quota.near')).toBeVisible()
      await expect(page.getByText('Sắp đạt giới hạn tài liệu')).toBeVisible()
    })
  } finally {
    await ev.restartApp()
  }
})
