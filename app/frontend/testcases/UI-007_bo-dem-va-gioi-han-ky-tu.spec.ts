import { expect, test } from '../evidence/fixture'
import { prep } from './_h'

test('Bộ đếm và giới hạn ký tự', async ({ ev, page }) => {
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf; xem bộ đếm khi ô trống', '0/2.000', async () => {
    await prep(ev, 'p2', ['hop-dong-A.pdf'])
    await expect(page.locator('.counter')).toHaveText('0/2.000')
  })
  await ev.step('Gõ 10 ký tự', '10/2.000', async () => {
    await page.locator('#q').fill('abcdefghij')
    await expect(page.locator('.counter')).toHaveText('10/2.000')
  })
  await ev.step('Dán 2.100 ký tự', 'Ô chỉ nhận 2.000 ký tự; bộ đếm 2.000/2.000 màu cảnh báo', async () => {
    await page.locator('#q').fill('x'.repeat(2100))
    expect((await page.locator('#q').inputValue()).length).toBe(2000)
    await expect(page.locator('.counter')).toHaveText('2.000/2.000')
    await expect(page.locator('.counter.over')).toBeVisible()
  })
})
