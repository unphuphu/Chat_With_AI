import { expect, test } from '../evidence/fixture'
import { prep, upload } from './_h'

test('Thông báo tự ẩn', async ({ ev, page }) => {
  await ev.step('Đăng nhập P2; tải 1 PDF có chữ và 1 PDF scan', 'Lần lượt xuất hiện "Tài liệu đã Sẵn sàng" và "Xử lý tài liệu thất bại"', async () => {
    await prep(ev, 'p2')
    await upload(page, 'hop-dong-A.pdf', 'ho-so-scan-2019.pdf')
    await expect(page.locator('.toast', { hasText: 'Tài liệu đã Sẵn sàng' })).toBeVisible({ timeout: 60_000 })
    await expect(page.locator('.toast', { hasText: 'Xử lý tài liệu thất bại' })).toBeVisible({ timeout: 60_000 })
  })
  await ev.step('Kiểm tra vị trí', 'Thông báo nằm góc dưới trái, không che ô hỏi', async () => {
    const t = (await page.locator('.toasts').boundingBox())!
    const q = (await page.locator('.composer').boundingBox())!
    const view = page.viewportSize()!
    expect(t.x).toBeLessThan(view.width / 2)
    expect(t.x + t.width).toBeLessThan(q.x + 1) // toast không chồng lên cột hỏi đáp
    return `Toast: x=${Math.round(t.x)}..${Math.round(t.x + t.width)}; vùng ô hỏi bắt đầu x=${Math.round(q.x)}`
  })
  await ev.step('Chờ 6 s (tự ẩn ≤ 5 s)', 'Thông báo không còn', async () => {
    await page.waitForTimeout(6000)
    await expect(page.locator('.toast')).toHaveCount(0)
  })
})
