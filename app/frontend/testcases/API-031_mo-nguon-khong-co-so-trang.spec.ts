import { expect, test } from '../evidence/fixture'
import { ask, bodyOf, prep, Q_PAY } from './_h'

test('Mở nguồn không có số trang', async ({ ev, page }) => {
  let id = ''
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf và chờ Sẵn sàng', 'Dòng Sẵn sàng', async () => prep(ev, 'p2', ['hop-dong-A.pdf']))
  await ev.step('GET /documents/{id}/file?from=citation (không có page)', '200 PDF', async () => {
    id = ((bodyOf(await ev.api('GET', '/api/v1/documents')).items as { id: string }[])[0]).id
    const r = await ev.api('GET', `/api/v1/documents/${id}/file?from=citation`)
    expect(r.status).toBe(200)
    expect(r.headers['content-type']).toBe('application/pdf')
  })
  await ev.step('Hỏi, giả lập page_number = null (page.route), tải lại trang, bấm chip nguồn', 'Chip không có "tr."; trình xem mở trang 1, iframe có #page=1', async () => {
    await page.bringToFront()
    await ask(page, Q_PAY)
    await page.route('**/api/v1/conversations/current', async (route) => {
      const resp = await route.fetch()
      const body = await resp.json()
      for (const m of body.messages) for (const c of m.citations) c.page_number = null
      await route.fulfill({ response: resp, json: body })
    })
    await page.reload()
    const chip = page.locator('article.a').first().getByRole('button', { name: /Mở nguồn 1/ })
    await expect(chip).toBeVisible()
    expect(await chip.innerText()).not.toContain('tr.')
    await chip.click()
    await expect(page.getByRole('dialog')).toContainText('trang 1')
    expect(await page.locator('.viewer iframe').getAttribute('src')).toContain('#page=1')
    await page.waitForTimeout(2000)
  })
})
