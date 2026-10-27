import fs from 'node:fs'
import { expect, test } from '../evidence/fixture'
import { pdf, prep, waitReady } from './_h'

test('Vượt giới hạn số file và hạn mức', async ({ ev, page }) => {
  test.setTimeout(420_000)
  const buf = fs.readFileSync(pdf('bang-gia-Q4.pdf'))
  const many = (n: number) => Array.from({ length: n }, (_, i) => ({ name: `tai-lieu-${i + 1}.pdf`, mimeType: 'application/pdf', buffer: buf }))
  try {
    await ev.step('Đăng nhập P2, xóa tài liệu cũ; chọn 12 file PDF cùng lúc', 'Thông báo "Mỗi lần chỉ tải tối đa 10 file – bạn đã chọn 12 file"; danh sách không đổi', async () => {
      await prep(ev, 'p2')
      await page.locator('input[type=file]').setInputFiles(many(12))
      await expect(page.getByText('Chưa có file nào được tải lên.')).toBeVisible()
      await expect(page.getByText('bạn đã chọn 12 file')).toBeVisible()
      await expect(page.locator('.docs li.row')).toHaveCount(0)
    })
    await ev.step('Khởi động lại với MAX_DOCS_PER_WORKSPACE=6; tải 2 file', 'Cảnh báo "Sắp đạt giới hạn… còn 4 tài liệu"; huy hiệu hạn mức màu cảnh báo', async () => {
      await ev.restartApp({ MAX_DOCS_PER_WORKSPACE: '6' })
      await page.locator('.docs .empty, .docs li.row').first().waitFor()
      await page.locator('input[type=file]').setInputFiles(many(2))
      await waitReady(page, 'tai-lieu-1.pdf')
      await waitReady(page, 'tai-lieu-2.pdf')
      await expect(page.getByText('Sắp đạt giới hạn tài liệu')).toBeVisible()
      await expect(page.getByText('còn có thể thêm 4 tài liệu')).toBeVisible()
      await expect(page.locator('.quota.near')).toBeVisible()
    })
    await ev.step('Chọn 5 file', 'Thông báo chỉ còn thêm được 4 tài liệu; không file nào tải lên', async () => {
      await page.locator('input[type=file]').setInputFiles(many(5).map((f, i) => ({ ...f, name: `them-${i}.pdf` })))
      await expect(page.getByText('Bạn chỉ còn có thể thêm 4 tài liệu')).toBeVisible()
      await expect(page.locator('.docs li.row')).toHaveCount(2)
    })
  } finally {
    await ev.restartApp()
  }
})
