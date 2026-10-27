import { expect, test } from '../evidence/fixture'
import { prep, row, upload, waitReady } from './_h'

test('Mất mạng khi tải lên và tải lại', async ({ ev, page }) => {
  await ev.step('Đăng nhập P2, xóa tài liệu cũ', 'Danh sách rỗng', async () => prep(ev, 'p2'))
  await ev.step('Chặn request PUT tải file (abort internetdisconnected)', 'Đã bật chặn', async () => {
    await page.route('**/upload-batches/*/files/*', (r) => r.abort('internetdisconnected'))
  })
  await ev.step('Chọn hop-dong-A.pdf', 'Dòng Tải lên thất bại – "Mất kết nối…", có nút Tải lại; không ở mục Tài liệu của bạn', async () => {
    await upload(page, 'hop-dong-A.pdf')
    await expect(page.getByText('Tải lên thất bại')).toBeVisible()
    await expect(page.getByText('Mất kết nối khi đang tải lên')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Tải lại' })).toBeVisible()
    await expect(page.getByText('Tài liệu sẽ xuất hiện ở đây khi tải lên xong')).toBeVisible()
  })
  await ev.step('Bỏ chặn, bấm Tải lại', 'File tải lên thành công → Đang xử lý → Sẵn sàng', async () => {
    await page.unroute('**/upload-batches/*/files/*')
    await page.getByRole('button', { name: 'Tải lại' }).click()
    await waitReady(page, 'hop-dong-A.pdf')
  })
  await ev.step('Kiểm tra danh sách và hạn mức', 'Đúng 1 tài liệu hop-dong-A.pdf; 1/100 tài liệu', async () => {
    await expect(page.locator('.docs li.row')).toHaveCount(1)
    await expect(row(page, 'hop-dong-A.pdf')).toBeVisible()
    await expect(page.locator('.quota')).toHaveText('1/100 tài liệu')
  })
})
