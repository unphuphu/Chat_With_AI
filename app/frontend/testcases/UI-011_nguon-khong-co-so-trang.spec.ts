import { expect, test } from '../evidence/fixture'
import { ask, prep, Q_PAY } from './_h'

test('Nguồn không có số trang', async ({ ev, page }) => {
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf, hỏi 1 câu', 'Chip "[1] hop-dong-A.pdf · tr.2"', async () => {
    await prep(ev, 'p2', ['hop-dong-A.pdf'])
    const a = await ask(page, Q_PAY)
    await expect(a.getByRole('button', { name: /hop-dong-A\.pdf · tr\.2/ })).toBeVisible()
  })
  await ev.step('Sửa phản hồi /conversations/current: page_number = null (page.route); tải lại trang', 'Chip chỉ còn "[1] hop-dong-A.pdf", không có "tr."', async () => {
    await page.route('**/api/v1/conversations/current', async (route) => {
      const resp = await route.fetch()
      const body = await resp.json()
      for (const m of body.messages) for (const c of m.citations) c.page_number = null
      await route.fulfill({ response: resp, json: body })
    })
    await page.reload()
    const chip = page.locator('article.a').first().locator('.chip')
    await expect(chip).toBeVisible()
    const t = await chip.innerText()
    expect(t).toContain('hop-dong-A.pdf')
    expect(t).not.toContain('tr.')
    return `Nhãn nguồn: "${t.replace(/\s+/g, ' ')}"`
  })
  await ev.step('Bấm chip', 'Trình xem mở trang 1', async () => {
    await page.locator('article.a').first().locator('.chip').click()
    await expect(page.getByRole('dialog')).toContainText('trang 1')
    await page.waitForTimeout(1500)
  })
})
