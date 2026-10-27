import { expect, test } from '../evidence/fixture'
import { ask, prep, Q_PAY } from './_h'

test('Quản lý focus', async ({ ev, page }) => {
  const active = () => page.evaluate(() => document.activeElement?.getAttribute('aria-label') ?? document.activeElement?.textContent?.trim() ?? '')
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf, hỏi một câu', 'Có câu trả lời với nguồn', async () => {
    await prep(ev, 'p2', ['hop-dong-A.pdf'])
    await ask(page, Q_PAY)
  })
  await ev.step('Mở dialog xóa', 'document.activeElement = nút Hủy', async () => {
    await page.getByRole('button', { name: /^Xóa hop-dong-A/ }).click()
    await expect(page.getByRole('alertdialog')).toBeVisible()
    expect(await active()).toContain('Hủy')
  })
  await ev.step('Esc', 'Dialog đóng', async () => {
    await page.keyboard.press('Escape')
    await expect(page.getByRole('alertdialog')).toBeHidden()
  })
  await ev.step('Bấm chip nguồn', 'Focus ở nút Đóng của trình xem', async () => {
    await page.locator('article.a').first().getByRole('button', { name: /Mở nguồn 1/ }).click()
    await expect(page.getByRole('dialog')).toBeVisible()
    expect(await active()).toContain('Đóng trình xem')
    await page.waitForTimeout(1500)
  })
  await ev.step('Esc', 'Focus về đúng chip vừa bấm', async () => {
    await page.keyboard.press('Escape')
    await expect(page.getByRole('dialog')).toBeHidden()
    expect(await active()).toMatch(/Mở nguồn 1/)
  })
  await ev.step('Kiểm tra focus không lọt ra phía sau dialog khi đang mở (Tab và Shift+Tab nhiều lần)', 'Focus chỉ xoay vòng trong dialog (bẫy focus)', async () => {
    await page.getByRole('button', { name: /^Xóa hop-dong-A/ }).click()
    const where = () => page.evaluate(() => (document.activeElement?.closest('[role=alertdialog]') ? 'trong-dialog' : `ngoai:${document.activeElement?.getAttribute('aria-label') ?? document.activeElement?.tagName}`))
    const seen: string[] = []
    for (let i = 0; i < 6; i++) {
      await page.keyboard.press('Tab')
      seen.push(await where())
    }
    for (let i = 0; i < 6; i++) {
      await page.keyboard.press('Shift+Tab')
      seen.push(await where())
    }
    await page.keyboard.press('Escape')
    expect(seen.every((x) => x === 'trong-dialog'), `Focus thoát khỏi dialog: ${seen.join(', ')}`).toBe(true)
    return `12 lần Tab/Shift+Tab: ${[...new Set(seen)].join(', ')} → có bẫy focus`
  })
})
