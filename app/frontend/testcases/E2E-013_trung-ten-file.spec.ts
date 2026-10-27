import { expect, test } from '../evidence/fixture'
import { ask, prep, Q_PAY, upload, waitReady } from './_h'

test('Trùng tên file', async ({ ev, page }) => {
  test.setTimeout(300_000)
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf, chờ Sẵn sàng', '1 dòng', async () => prep(ev, 'p2', ['hop-dong-A.pdf']))
  await ev.step('Chờ ≥ 61 s rồi tải lại hop-dong-A.pdf', '2 dòng cùng tên, thời điểm tải lên khác nhau', async () => {
    await page.waitForTimeout(61_000)
    await upload(page, 'hop-dong-A.pdf')
    await expect(page.locator('.docs li.row', { hasText: 'hop-dong-A.pdf' })).toHaveCount(2, { timeout: 30_000 })
    await expect(page.locator('.docs li.row', { hasText: 'Sẵn sàng' })).toHaveCount(2, { timeout: 90_000 })
    const metas = await page.locator('.docs li.row .meta').allInnerTexts()
    const times = metas.map((m) => m.split('·').pop()!.trim())
    expect(new Set(times).size).toBe(2)
    return `Thời điểm tải lên: ${times.join(' | ')}`
  })
  await ev.step('Xóa dòng mới hơn', 'Còn 1 dòng (bản cũ), vẫn Sẵn sàng', async () => {
    const newest = page.locator('.docs li.row').first() // danh sách xếp mới nhất lên đầu hoặc cuối → xóa dòng cuối rồi kiểm tra còn 1
    await newest.getByRole('button', { name: /^Xóa / }).click()
    await page.getByRole('button', { name: 'Xóa tài liệu' }).click()
    await expect(page.locator('.docs li.row')).toHaveCount(1)
    await waitReady(page, 'hop-dong-A.pdf')
  })
  await ev.step(`Hỏi "${Q_PAY}"`, 'Câu trả lời có nguồn hop-dong-A.pdf', async () => {
    const a = await ask(page, Q_PAY)
    await expect(a).toContainText('30 ngày')
    await expect(a.getByRole('button', { name: /hop-dong-A\.pdf/ })).toBeVisible()
  })
})
