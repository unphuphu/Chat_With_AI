import { expect, test } from '../evidence/fixture'
import { prep, row, upload, waitReady } from './_h'

test('Xử lý lại tài liệu lỗi tạm thời', async ({ ev, page }) => {
  test.setTimeout(600_000)
  try {
    await ev.step('Khởi động lại với dịch vụ embedding không tồn tại', 'Ứng dụng sẵn sàng', async () => {
      await ev.restartApp({ EMBEDDING_PROVIDER: 'http', EMBEDDING_URL: 'http://127.0.0.1:9' })
    })
    await ev.step('Đăng nhập P2, tải hop-dong-A.pdf và ho-so-scan-2019.pdf', 'Đang xử lý', async () => {
      await prep(ev, 'p2')
      await upload(page, 'hop-dong-A.pdf', 'ho-so-scan-2019.pdf')
      await expect(row(page, 'hop-dong-A.pdf').getByText('Đang xử lý')).toBeVisible({ timeout: 30_000 })
    })
    await ev.step('Chờ hết 3 lần thử (backoff 30 s + 120 s)', 'Dòng Thất bại – "Lỗi xử lý tạm thời…", có nút Xử lý lại', async () => {
      const r = row(page, 'hop-dong-A.pdf')
      await expect(r.getByText('Thất bại')).toBeVisible({ timeout: 360_000 })
      await expect(r).toContainText('Lỗi xử lý tạm thời')
      await expect(r.getByRole('button', { name: 'Xử lý lại' })).toBeVisible()
    })
    await ev.step('So sánh với ho-so-scan-2019.pdf (R-03)', 'Không có nút Xử lý lại', async () => {
      const s = row(page, 'ho-so-scan-2019.pdf')
      await expect(s.getByText('Thất bại')).toBeVisible()
      await expect(s.getByRole('button', { name: 'Xử lý lại' })).toHaveCount(0)
    })
  } finally {
    await ev.restartApp()
  }
  await ev.step('Cấu hình mặc định đã khôi phục; tải lại trang', 'Dòng hop-dong-A.pdf vẫn Thất bại R-04', async () => {
    await page.reload()
    await expect(row(page, 'hop-dong-A.pdf').getByRole('button', { name: 'Xử lý lại' })).toBeVisible()
  })
  await ev.step('Bấm Xử lý lại', 'Dòng chuyển Đang xử lý → Sẵn sàng; không phải tải lại file', async () => {
    await row(page, 'hop-dong-A.pdf').getByRole('button', { name: 'Xử lý lại' }).click()
    await waitReady(page, 'hop-dong-A.pdf', 120_000)
  })
})
