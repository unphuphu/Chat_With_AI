import { expect, test } from '../evidence/fixture'
import { prep, purge, row, upload } from './_h'

test('Trạng thái trống và lỗi', async ({ ev, page }) => {
  await ev.step('Chưa có tài liệu (E-01)', 'Chưa có tài liệu nào + hướng dẫn 3 bước; ô hỏi khóa: "Cần ít nhất một tài liệu Sẵn sàng…"', async () => {
    await prep(ev, 'p2')
    await expect(page.getByText('Chưa có tài liệu nào')).toBeVisible()
    await expect(page.locator('.steps li')).toHaveCount(3)
    await expect(page.locator('.locked-reason')).toContainText('Cần ít nhất một tài liệu Sẵn sàng')
  })
  await ev.step('Tải 1 file, chụp ngay khi đang xử lý (E-02)', 'Ô hỏi khóa: "Đang xử lý tài liệu, bạn có thể hỏi khi…"', async () => {
    await page.route('**/upload-batches/*/files/*', async (r) => {
      await r.continue()
    })
    await upload(page, 'bang-gia-Q4.pdf')
    await expect(page.locator('.locked-reason')).toContainText('Đang xử lý tài liệu', { timeout: 20_000 })
    await page.unroute('**/upload-batches/*/files/*')
  })
  await ev.step('Xóa hết, chỉ tải ho-so-scan-2019.pdf (mọi tài liệu Thất bại – E-03)', 'Ô hỏi khóa; dòng Thất bại có lý do', async () => {
    await page.waitForTimeout(8000)
    await purge(page)
    await upload(page, 'ho-so-scan-2019.pdf')
    await expect(row(page, 'ho-so-scan-2019.pdf').getByText('Thất bại')).toBeVisible({ timeout: 60_000 })
    await expect(page.locator('#q')).toBeDisabled()
    await expect(page.locator('.locked-reason')).toBeVisible()
    await expect(row(page, 'ho-so-scan-2019.pdf')).toContainText('PDF scan')
  })
  await ev.step('So với PRD E-03: có gợi ý "kiểm tra lý do và tải file khác" ở ô hỏi không', 'Ghi nhận', async () => {
    const reason = await page.locator('.locked-reason').innerText()
    ev.note(`E-03: ô hỏi chỉ hiện "${reason.trim()}" – chưa có gợi ý riêng "kiểm tra lý do và tải file khác" như PRD E-03; lý do thất bại hiển thị trên dòng tài liệu.`)
    return `Lời nhắc ở ô hỏi: "${reason.trim()}". PRD E-03 yêu cầu thêm gợi ý kiểm tra lý do/tải file khác → khác biệt nhỏ, cần người xác nhận.`
  }, { review: true })
})
