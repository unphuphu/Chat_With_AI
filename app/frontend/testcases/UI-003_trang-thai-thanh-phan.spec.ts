import { expect, test } from '../evidence/fixture'
import { prep, Q_PAY, upload, waitReady } from './_h'

test('Trạng thái thành phần', async ({ ev, page }) => {
  await ev.step('Đăng nhập P2 (chưa có tài liệu): ô hỏi', 'Khóa, nền xám, dòng lý do có biểu tượng ổ khóa', async () => {
    await prep(ev, 'p2')
    await expect(page.locator('#q')).toBeDisabled()
    await expect(page.locator('.box.locked')).toBeVisible()
    await expect(page.locator('.locked-reason')).toContainText('Cần ít nhất một tài liệu Sẵn sàng')
    await expect(page.locator('.locked-reason svg')).toHaveCount(1)
  })
  await ev.step('Tải file, Sẵn sàng; hover nút Chọn file PDF', 'Màu hover khác màu thường', async () => {
    await upload(page, 'hop-dong-A.pdf')
    await waitReady(page, 'hop-dong-A.pdf')
    const btn = page.getByRole('button', { name: 'Chọn file PDF' })
    const normal = await btn.evaluate((el) => getComputedStyle(el).backgroundColor)
    await btn.hover()
    await page.waitForTimeout(200)
    const hover = await btn.evaluate((el) => getComputedStyle(el).backgroundColor)
    expect(hover).not.toBe(normal)
    return `Nền thường ${normal} → hover ${hover}`
  })
  await ev.step('Ô hỏi trống', 'Nút Gửi vô hiệu', async () => {
    await expect(page.getByRole('button', { name: 'Gửi' })).toBeDisabled()
    await page.locator('#q').fill('abc')
    await expect(page.getByRole('button', { name: 'Gửi' })).toBeEnabled()
    await page.locator('#q').fill('')
  })
  await ev.step('Focus vào ô hỏi', 'Có viền/đổ bóng focus', async () => {
    await page.locator('#q').focus()
    const shadow = await page.locator('.box').evaluate((el) => `${getComputedStyle(el).borderColor} | ${getComputedStyle(el).boxShadow}`)
    expect(shadow).not.toContain('none')
    return shadow
  })
  await ev.step('Gửi câu hỏi (làm chậm 2,5 s)', 'Nút đổi thành "Đang gửi…", ô hỏi khóa tới khi có kết quả', async () => {
    await page.route('**/messages', async (r) => {
      await new Promise((x) => setTimeout(x, 2500))
      await r.continue()
    })
    await page.locator('#q').fill(Q_PAY)
    await page.keyboard.press('Enter')
    await expect(page.getByRole('button', { name: 'Đang gửi…' })).toBeVisible()
    await expect(page.locator('.box.locked')).toBeVisible()
    await page.unroute('**/messages')
    await expect(page.locator('article.a').first()).not.toHaveAttribute('aria-busy', 'true', { timeout: 30_000 })
  })
})
