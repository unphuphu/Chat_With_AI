import fs from 'node:fs'
import { expect, test } from '../evidence/fixture'
import { pdf, prep, waitReady } from './_h'

test('Tải 10 file song song', async ({ ev, page }) => {
  test.setTimeout(420_000)
  await ev.step('Đăng nhập P2, xóa tài liệu cũ', 'Danh sách rỗng', async () => prep(ev, 'p2'))
  let maxConcurrent = 0
  await ev.step('Chọn 10 PDF hợp lệ (làm chậm request PUT 2 s để quan sát hàng đợi)', 'Hàng đợi 10 dòng; tại mọi thời điểm ≤ 3 dòng Đang tải lên, còn lại Đang chờ tải lên', async () => {
    await page.route('**/upload-batches/*/files/*', async (route) => {
      await new Promise((r) => setTimeout(r, 2000))
      await route.continue()
    })
    const src = ['hop-dong-A.pdf', 'chinh-sach-ban-hang-2026.pdf', 'bang-gia-Q4.pdf'].map((n) => fs.readFileSync(pdf(n)))
    const files = Array.from({ length: 10 }, (_, i) => ({ name: `mau-${String(i + 1).padStart(2, '0')}.pdf`, mimeType: 'application/pdf', buffer: src[i % 3] }))
    await page.locator('input[type=file]').setInputFiles(files)
    const t0 = Date.now()
    while (Date.now() - t0 < 6000) {
      const n = await page.locator('.status.st-uploading', { hasText: 'Đang tải lên' }).count()
      maxConcurrent = Math.max(maxConcurrent, n)
      await page.waitForTimeout(150)
    }
    expect(maxConcurrent).toBeGreaterThan(0)
    expect(maxConcurrent).toBeLessThanOrEqual(3)
    return `Số dòng "Đang tải lên" đồng thời tối đa quan sát được: ${maxConcurrent}`
  })
  await ev.step('Chụp ảnh khi đang tải', 'Thấy đồng thời trạng thái đang tải và đang chờ', async () => {
    const waiting = await page.getByText('Đang chờ tải lên').count()
    const total = await page.locator('.docs li.row').count()
    return `Dòng đang chờ: ${waiting}; tổng dòng đang hiển thị: ${total}`
  })
  await ev.step('Chờ tất cả xử lý xong', '10 dòng Sẵn sàng; hạn mức 10/100 tài liệu', async () => {
    await page.unroute('**/upload-batches/*/files/*')
    for (let i = 1; i <= 10; i++) await waitReady(page, `mau-${String(i).padStart(2, '0')}.pdf`, 240_000)
    await expect(page.locator('.docs li.row')).toHaveCount(10)
    // Hạn mức gồm cả chỗ đặt của lô tải lỗi trước đó (giữ 10 phút – ADR-014) nên có thể lớn hơn 10
    const used = Number((await page.locator('.quota').innerText()).split('/')[0])
    expect(used).toBeGreaterThanOrEqual(10)
    return `10 dòng Sẵn sàng; hạn mức hiển thị ${used}/100 (gồm chỗ đặt của lô khác chưa hết hạn)`
  })
})
