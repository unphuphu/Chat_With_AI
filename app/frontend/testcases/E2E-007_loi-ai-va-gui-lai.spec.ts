import { expect, test } from '../evidence/fixture'
import { ask, prep, Q_PAY } from './_h'

test('Lỗi AI và Gửi lại', async ({ ev, page }) => {
  test.setTimeout(420_000)
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf và chờ Sẵn sàng', 'Dòng Sẵn sàng', async () => prep(ev, 'p2', ['hop-dong-A.pdf']))
  await ev.step('(Mất mạng – E-05) Chặn POST /messages, gửi câu hỏi thanh toán', 'Thẻ "Chưa trả lời được – Mất kết nối tới máy chủ", câu hỏi gốc vẫn hiện, có nút Gửi lại', async () => {
    await page.route('**/messages', (r) => r.abort('internetdisconnected'))
    await page.locator('#q').fill(Q_PAY)
    await page.keyboard.press('Enter')
    const card = page.locator('article.a.failed')
    await expect(card).toContainText('Mất kết nối tới máy chủ')
    await expect(page.locator('.q')).toContainText(Q_PAY)
    await expect(card.getByRole('button', { name: 'Gửi lại' })).toBeVisible()
  })
  await ev.step('Bỏ chặn, bấm Gửi lại', 'Câu trả lời có "30 ngày" thay thẻ lỗi tại cùng vị trí; không tạo lượt mới', async () => {
    await page.unroute('**/messages')
    await page.getByRole('button', { name: 'Gửi lại' }).click()
    await expect(page.locator('article.a').first()).toContainText('30 ngày', { timeout: 30_000 })
    await expect(page.locator('article.a')).toHaveCount(1)
  })
  try {
    await ev.step('(Dịch vụ AI lỗi – E-06) Khởi động lại với LLM không hợp lệ; hỏi câu mới', 'Thẻ "Không thể tạo câu trả lời lúc này, vui lòng thử lại"; không có câu trả lời dở dang', async () => {
      await ev.restartApp({ LLM_PROVIDER: 'anthropic', LLM_API_KEY: 'sk-ant-invalid' })
      await page.locator('#q').fill('Lãi chậm trả là bao nhiêu?')
      await page.keyboard.press('Enter')
      const card = page.locator('article.a.failed')
      await expect(card).toContainText('Không thể tạo câu trả lời lúc này, vui lòng thử lại', { timeout: 60_000 })
      await expect(card.getByRole('button', { name: 'Gửi lại' })).toBeVisible()
    })
    await ev.step('Bấm Gửi lại lần nữa (vẫn lỗi)', 'Thẻ lỗi hiện lại, vẫn có nút Gửi lại', async () => {
      await page.getByRole('button', { name: 'Gửi lại' }).click()
      await expect(page.locator('article.a.failed')).toContainText('Không thể tạo câu trả lời lúc này', { timeout: 60_000 })
      await expect(page.getByRole('button', { name: 'Gửi lại' })).toBeVisible()
    })
  } finally {
    await ev.restartApp()
  }
  await ev.step('Khôi phục LLM mặc định; tải lại trang; bấm Gửi lại trên thẻ lỗi', 'Có câu trả lời', async () => {
    await page.reload()
    await page.getByRole('button', { name: 'Gửi lại' }).click()
    await expect(page.locator('article.a.failed')).toHaveCount(0, { timeout: 30_000 })
    await expect(page.locator('article.a').nth(1)).toContainText('0,05%', { timeout: 30_000 })
  })
  void ask
})
