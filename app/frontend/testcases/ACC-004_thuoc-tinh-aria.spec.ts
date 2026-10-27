import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '../evidence/fixture'
import { ask, prep, Q_PAY, upload } from './_h'

test('Thuộc tính ARIA', async ({ ev, page }) => {
  await ev.step('Đăng nhập P2, xóa tài liệu cũ', 'Màn hình chính', async () => prep(ev, 'p2'))
  await ev.step('Chạy axe toàn trang (mọi rule)', '0 vi phạm mức serious/critical', async () => {
    const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze()
    const bad = r.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical')
    ev.note(`axe (tag wcag2a/2aa/21a/21aa): ${r.violations.length} vi phạm mọi mức, ${bad.length} mức serious/critical; ${r.passes.length} rule đạt.`)
    expect(bad.map((v) => `${v.id}: ${v.help}`)).toEqual([])
    return `${r.violations.length} vi phạm (0 serious/critical), ${r.passes.length} rule đạt`
  })
  await ev.step('Trong lúc tải: role=progressbar, aria-valuenow', 'Có và cập nhật', async () => {
    await page.route('**/upload-batches/*/files/*', async (route) => {
      await new Promise((r) => setTimeout(r, 3000))
      await route.continue()
    })
    await upload(page, 'hop-dong-A.pdf')
    const bar = page.getByRole('progressbar')
    await expect(bar).toBeVisible()
    await expect(bar).toHaveAttribute('aria-valuenow', /\d+/)
    await expect(bar).toHaveAttribute('aria-valuemin', '0')
    await expect(bar).toHaveAttribute('aria-valuemax', '100')
    await page.unroute('**/upload-batches/*/files/*')
    await expect(page.locator('li.row', { hasText: 'Sẵn sàng' })).toBeVisible({ timeout: 90_000 })
  })
  await ev.step('Trong lúc chờ câu trả lời: article[aria-busy=true]', 'Có', async () => {
    await page.route('**/messages', async (route) => {
      await new Promise((r) => setTimeout(r, 2500))
      await route.continue()
    })
    await page.locator('#q').fill(Q_PAY)
    await page.keyboard.press('Enter')
    await expect(page.locator('article[aria-busy="true"]')).toBeVisible()
    await page.unroute('**/messages')
    await expect(page.locator('article.a').first()).not.toHaveAttribute('aria-busy', 'true', { timeout: 30_000 })
  })
  await ev.step('Dialog trình xem và dialog xóa', 'dialog: aria-modal=true, aria-labelledby; xóa: role=alertdialog', async () => {
    const a = page.locator('article.a').first()
    await a.getByRole('button', { name: /Mở nguồn 1/ }).click()
    const d = page.getByRole('dialog')
    await expect(d).toHaveAttribute('aria-modal', 'true')
    await expect(d).toHaveAttribute('aria-labelledby', 'viewer-title')
    await page.keyboard.press('Escape')
    await page.getByRole('button', { name: /^Xóa hop-dong-A/ }).click()
    const ad = page.getByRole('alertdialog')
    await expect(ad).toHaveAttribute('aria-modal', 'true')
    await expect(ad).toHaveAttribute('aria-labelledby', 'dlg-t')
    await expect(ad).toHaveAttribute('aria-describedby', 'dlg-d')
    await page.keyboard.press('Escape')
  })
  void ask
})
