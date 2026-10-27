import { expect, test } from '../evidence/fixture'
import { ask, prep, Q_PAY } from './_h'

test('Hết phiên khi đang soạn câu hỏi', async ({ ev, page }) => {
  test.setTimeout(420_000)
  const draft = 'Hợp đồng có hiệu lực bao lâu?'
  try {
    await ev.step('Khởi động lại với SESSION_IDLE_MIN=1', 'Ứng dụng sẵn sàng', async () => {
      await ev.restartApp({ SESSION_IDLE_MIN: '1' })
    })
    await ev.step('Đăng nhập P2, tải hop-dong-A.pdf, hỏi một câu và gõ dở câu thứ hai (không gửi)', 'Câu hỏi nằm trong ô', async () => {
      await prep(ev, 'p2', ['hop-dong-A.pdf'])
      await ask(page, Q_PAY)
      await page.locator('#q').fill(draft)
    })
    await ev.step('Không thao tác 75 s, sau đó bấm Gửi', 'Trang "Phiên làm việc đã hết hạn" với đếm ngược và nút Đăng nhập ngay', async () => {
      await page.waitForTimeout(75_000)
      await page.getByRole('button', { name: 'Gửi' }).click()
      await expect(page.getByRole('heading', { name: 'Phiên làm việc đã hết hạn' })).toBeVisible({ timeout: 15_000 })
      await expect(page.getByRole('link', { name: 'Đăng nhập ngay' })).toBeVisible()
    })
    await ev.step('Bấm Đăng nhập ngay, chọn P2', 'Màn hình chính; ô hỏi chứa sẵn câu đang soạn; hội thoại mới (không còn câu trước)', async () => {
      await page.getByRole('link', { name: 'Đăng nhập ngay' }).click()
      await page.getByRole('button', { name: /Trần Minh/ }).click()
      await page.locator('.docs li.row').first().waitFor()
      await expect(page.locator('#q')).toHaveValue(draft)
      await expect(page.locator('article.a')).toHaveCount(0)
    })
  } finally {
    await ev.restartApp()
  }
})
