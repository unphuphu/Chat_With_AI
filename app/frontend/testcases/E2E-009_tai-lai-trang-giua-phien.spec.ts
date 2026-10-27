import { expect, test } from '../evidence/fixture'
import { ask, prep, Q_PAY, row } from './_h'

test('Tải lại trang giữa phiên', async ({ ev, page }) => {
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf và chờ Sẵn sàng', 'Dòng Sẵn sàng', async () => prep(ev, 'p2', ['hop-dong-A.pdf']))
  await ev.step('Hỏi 2 câu', '2 lượt hỏi–đáp', async () => {
    await ask(page, Q_PAY)
    await ask(page, 'Lãi chậm trả là bao nhiêu?')
    await expect(page.locator('article.a')).toHaveCount(2)
  })
  await ev.step('Nhấn F5 (reload)', 'Danh sách vẫn có hop-dong-A.pdf Sẵn sàng; hội thoại đủ 2 lượt kèm nguồn', async () => {
    await page.reload()
    await expect(row(page, 'hop-dong-A.pdf').getByText('Sẵn sàng')).toBeVisible()
    await expect(page.locator('article.a')).toHaveCount(2)
    await expect(page.locator('article.a').first().locator('.chip')).toHaveCount(1)
  })
  await ev.step('Đăng xuất rồi đăng nhập lại P2', 'Tài liệu còn; hội thoại mới trống (NFR-024)', async () => {
    await page.getByRole('button', { name: 'Đăng xuất' }).click()
    await page.getByRole('button', { name: /Trần Minh/ }).click()
    await expect(row(page, 'hop-dong-A.pdf').getByText('Sẵn sàng')).toBeVisible()
    await expect(page.locator('article.a')).toHaveCount(0)
  })
})
