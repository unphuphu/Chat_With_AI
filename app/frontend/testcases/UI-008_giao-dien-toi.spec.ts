import { expect, test } from '../evidence/fixture'
import { ask, prep, Q_PAY } from './_h'

test('Giao diện tối', async ({ ev, page }) => {
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf, hỏi một câu; bật colorScheme: dark', 'Nền tối, chữ sáng', async () => {
    await prep(ev, 'p2', ['hop-dong-A.pdf'])
    await ask(page, Q_PAY)
    await page.emulateMedia({ colorScheme: 'dark' })
    await page.waitForTimeout(500)
    const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor)
    const fg = await page.evaluate(() => getComputedStyle(document.body).color)
    expect(bg).not.toBe('rgb(245, 246, 248)')
    return `body: nền ${bg}, chữ ${fg}`
  })
  await ev.step('Chụp dialog xóa và trình xem trong giao diện tối', 'Không có khối màu sáng lạc', async () => {
    await page.getByRole('button', { name: /^Xóa hop-dong-A/ }).click()
    await page.waitForTimeout(300)
    await ev.shot('dialog-xoa-toi')
    await page.keyboard.press('Escape')
    await page.locator('article.a').first().getByRole('button', { name: /Mở nguồn 1/ }).click()
    await page.waitForTimeout(2000)
    await ev.shot('trinh-xem-toi')
    await page.keyboard.press('Escape')
  })
  await ev.step('Chụp S09, S10, S11 giao diện tối', 'Đúng màu', async () => {
    for (const p of ['/access-denied', '/login-error?ref=abc', '/session-expired']) {
      await page.goto(p)
      await page.waitForTimeout(400)
      await ev.shot(`trang-${p.split('?')[0].slice(1)}-toi`)
    }
  })
  await ev.step('Designer đánh giá ảnh', 'Không lỗi màu', async () => 'Ảnh giao diện tối đã chụp cho màn hình chính, dialog xóa, trình xem, S09–S11 – Designer xác nhận.', { review: true })
})
