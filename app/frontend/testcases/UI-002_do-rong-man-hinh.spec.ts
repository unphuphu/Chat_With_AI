import { expect, test } from '../evidence/fixture'
import { prep } from './_h'

test('Độ rộng màn hình', async ({ ev, page }) => {
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf và chờ Sẵn sàng', 'Dòng Sẵn sàng', async () => prep(ev, 'p2', ['hop-dong-A.pdf']))
  for (const [w, h] of [[1280, 800], [1440, 900], [1920, 1080]] as const) {
    await ev.step(`Viewport ${w}×${h}`, 'Không cuộn ngang; thấy cả khu Tài liệu và Hỏi đáp', async () => {
      await page.setViewportSize({ width: w, height: h })
      await page.waitForTimeout(500)
      const m = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }))
      expect(m.sw).toBeLessThanOrEqual(m.cw)
      await expect(page.getByRole('heading', { name: 'Tài liệu', exact: true })).toBeInViewport()
      await expect(page.getByRole('heading', { name: 'Hỏi đáp', exact: true })).toBeInViewport()
      const inner = await page.locator('.thread-inner').evaluate((el) => el.getBoundingClientRect().width)
      return `scrollWidth=${m.sw} ≤ clientWidth=${m.cw}; chiều rộng khung hội thoại=${Math.round(inner)} px`
    })
  }
})
