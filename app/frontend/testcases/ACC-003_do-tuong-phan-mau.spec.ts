import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '../evidence/fixture'
import { prep, row } from './_h'

test('Độ tương phản màu', async ({ ev, page }) => {
  const contrast = async (label: string) => {
    const r = await new AxeBuilder({ page }).withRules(['color-contrast']).analyze()
    const v = r.violations.flatMap((x) => x.nodes.map((n) => `${n.target.join(' ')}: ${n.any[0]?.message ?? ''}`))
    if (v.length) throw new Error(`Vi phạm tương phản (${label}): ${v.join(' || ').replace(/\s+/g, ' ')}`)
    return `${label}: ${r.passes.length ? 'đạt' : ''}, ${v.length} vi phạm`
  }
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf và scan; chạy axe color-contrast (giao diện sáng)', '0 vi phạm', async () => {
    await prep(ev, 'p2', ['hop-dong-A.pdf'])
    await page.locator('input[type=file]').setInputFiles('../sample-pdfs/ho-so-scan-2019.pdf')
    await expect(row(page, 'ho-so-scan-2019.pdf').getByText('Thất bại')).toBeVisible({ timeout: 60_000 })
    await page.waitForTimeout(5500)
    return contrast('màn hình chính (sáng)')
  })
  await ev.step('Giao diện tối (colorScheme: dark), chạy lại', '0 vi phạm', async () => {
    await page.emulateMedia({ colorScheme: 'dark' })
    await page.waitForTimeout(500)
    return contrast('màn hình chính (tối)')
  })
  await ev.step('Lặp lại trên S09, S10, S11 và dialog xóa (sáng và tối)', '0 vi phạm', async () => {
    const res: string[] = []
    for (const scheme of ['light', 'dark'] as const) {
      await page.emulateMedia({ colorScheme: scheme })
      for (const p of ['/access-denied', '/login-error?ref=abc', '/session-expired']) {
        await page.goto(p)
        res.push(await contrast(`${p} (${scheme})`))
      }
      await page.goto('/')
      await row(page, 'hop-dong-A.pdf').getByRole('button', { name: /^Xóa / }).click()
      res.push(await contrast(`dialog xóa (${scheme})`))
      await page.keyboard.press('Escape')
    }
    return res.join('; ')
  })
})
