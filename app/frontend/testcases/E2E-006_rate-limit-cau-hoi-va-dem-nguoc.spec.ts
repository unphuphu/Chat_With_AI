import { expect, test } from '../evidence/fixture'
import { ask, prep } from './_h'

test('Rate limit câu hỏi và đếm ngược', async ({ ev, page }) => {
  test.setTimeout(300_000)
  await ev.step('Đăng nhập Quản trị viên, tải hop-dong-A.pdf và chờ Sẵn sàng', 'Dòng Sẵn sàng', async () => prep(ev, 'admin', ['hop-dong-A.pdf']))
  await ev.step('Chờ đầu phút kế tiếp rồi gửi liên tiếp 10 câu hỏi ngắn', '10 câu trả lời', async () => {
    const ms = 60_000 - (Date.now() % 60_000)
    if (ms < 56_000) await page.waitForTimeout(ms + 600)
    for (let i = 1; i <= 10; i++) await ask(page, `Câu ${i}: Bên B thanh toán trong bao nhiêu ngày?`)
    await expect(page.locator('article.a')).toHaveCount(10)
  })
  let first = 0
  await ev.step('Gõ câu thứ 11 và gửi', 'Cảnh báo "Bạn thao tác quá nhanh… N giây"; nội dung câu hỏi còn trong ô; nút Gửi khóa', async () => {
    await page.locator('#q').fill('Câu 11: có được chuyển nhượng không?')
    await page.keyboard.press('Enter')
    const warn = page.locator('.alert-warn', { hasText: 'Bạn thao tác quá nhanh' })
    await expect(warn).toBeVisible()
    first = Number((await warn.locator('strong').innerText()).match(/\d+/)![0])
    await expect(page.locator('#q')).toHaveValue('Câu 11: có được chuyển nhượng không?')
    await expect(page.getByRole('button', { name: 'Gửi' })).toBeDisabled()
    return `Đếm ngược ban đầu: ${first} giây`
  })
  await ev.step('Chụp ảnh sau 5 s', 'Số giây đếm ngược giảm', async () => {
    await page.waitForTimeout(5000)
    const now = Number((await page.locator('.alert-warn strong').innerText()).match(/\d+/)![0])
    expect(now).toBeLessThan(first)
    return `Còn ${now} giây (trước đó ${first})`
  })
  await ev.step('Chờ hết đếm ngược', 'Cảnh báo biến mất; gửi được câu hỏi', async () => {
    await expect(page.locator('.alert-warn', { hasText: 'Bạn thao tác quá nhanh' })).toBeHidden({ timeout: 90_000 })
    await expect(page.locator('#q')).toHaveValue('Câu 11: có được chuyển nhượng không?')
    await page.keyboard.press('Control+End')
    await page.getByRole('button', { name: 'Gửi' }).click()
    await expect(page.locator('article.a')).toHaveCount(11, { timeout: 30_000 })
  })
})
