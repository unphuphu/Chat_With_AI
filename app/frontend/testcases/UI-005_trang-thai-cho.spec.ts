import { expect, test } from '../evidence/fixture'
import { prep, Q_PAY, upload, waitReady } from './_h'

test('Trạng thái chờ', async ({ ev, page }) => {
  await ev.step('Đăng nhập P2; tải file (làm chậm request 3 s)', 'Đang tải lên x% + thanh tiến độ', async () => {
    await prep(ev, 'p2')
    await page.route('**/upload-batches/*/files/*', async (r) => {
      await new Promise((x) => setTimeout(x, 3000))
      await r.continue()
    })
    await upload(page, 'hop-dong-A.pdf')
    await expect(page.getByText(/Đang tải lên \d+%/)).toBeVisible()
    await expect(page.getByRole('progressbar')).toBeVisible()
    await page.unroute('**/upload-batches/*/files/*')
  })
  await ev.step('Chụp khi đang xử lý', 'Đang xử lý có biểu tượng xoay', async () => {
    await expect(page.locator('.status.st-processing .spin').first()).toBeVisible({ timeout: 30_000 })
  })
  await ev.step('Gửi câu hỏi, chụp ngay', 'Thẻ Trợ lý tài liệu có ba chấm và "Đang tìm trong tài liệu và soạn câu trả lời…"', async () => {
    await waitReady(page, 'hop-dong-A.pdf')
    await page.route('**/messages', async (r) => {
      await new Promise((x) => setTimeout(x, 3000))
      await r.continue()
    })
    await page.locator('#q').fill(Q_PAY)
    await page.keyboard.press('Enter')
    await expect(page.locator('.dots')).toBeVisible()
    await expect(page.getByText('Đang tìm trong tài liệu và soạn câu trả lời')).toBeVisible()
    await page.unroute('**/messages')
    await expect(page.locator('article.a').first()).not.toHaveAttribute('aria-busy', 'true', { timeout: 30_000 })
  })
})
