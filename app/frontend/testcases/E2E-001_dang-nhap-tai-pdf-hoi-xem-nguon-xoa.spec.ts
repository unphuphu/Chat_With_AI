import { expect, test } from '../evidence/fixture'
import { ask, prep, Q_OUT, Q_PAY, row, upload, waitReady } from './_h'

test('Đăng nhập, tải PDF, hỏi, xem nguồn, xóa', async ({ ev, page }) => {
  await ev.step('Đăng nhập P2 (Trần Minh), xóa tài liệu cũ', 'Màn hình chính; Chưa có tài liệu nào; ô hỏi khóa', async () => {
    await prep(ev, 'p2')
    await expect(page.getByText('minh.tran@congty.vn')).toBeVisible()
    await expect(page.getByText('Chưa có tài liệu nào')).toBeVisible()
    await expect(page.locator('#q')).toBeDisabled()
  })
  await ev.step('Chọn cùng lúc hop-dong-A.pdf, ho-so-scan-2019.pdf, bao-gia.docx', 'docx: Không nhận – "không phải file PDF hợp lệ"; 2 PDF vào hàng đợi', async () => {
    await upload(page, 'hop-dong-A.pdf', 'ho-so-scan-2019.pdf', 'bao-gia.docx')
    await expect(page.getByText('không phải file PDF hợp lệ')).toBeVisible()
  })
  await ev.step('Chờ xử lý xong', 'hop-dong-A.pdf Sẵn sàng; ho-so-scan-2019.pdf Thất bại (PDF scan), không có nút Xử lý lại', async () => {
    await waitReady(page, 'hop-dong-A.pdf')
    const scan = row(page, 'ho-so-scan-2019.pdf')
    await expect(scan.getByText('Thất bại')).toBeVisible({ timeout: 60_000 })
    await expect(scan.getByText('PDF scan')).toBeVisible()
    await expect(scan.getByRole('button', { name: 'Xử lý lại' })).toHaveCount(0)
  })
  const a = page.locator('article.a').first() // câu trả lời đầu tiên (ask() trả về locator .last() nên không dùng lại được)
  await ev.step(`Hỏi "${Q_PAY}" (Enter)`, 'Câu trả lời chứa "30 ngày" và chip [1] hop-dong-A.pdf · tr.2', async () => {
    await ask(page, Q_PAY)
    await expect(a).toContainText('30 ngày')
    await expect(a.getByRole('button', { name: /Mở nguồn 1: hop-dong-A\.pdf · tr\.2/ })).toBeVisible()
  })
  await ev.step(`Hỏi "${Q_OUT}"`, 'Thẻ Chưa đủ thông tin, không có phần nguồn', async () => {
    const b = await ask(page, Q_OUT)
    await expect(b).toContainText('Chưa đủ thông tin')
    await expect(b.locator('.sources')).toHaveCount(0)
  })
  await ev.step('Bấm chip [1] hop-dong-A.pdf · tr.2', 'Dialog trình xem: hop-dong-A.pdf, "Mở từ nguồn [1] · trang 2", PDF hiển thị', async () => {
    await a.getByRole('button', { name: /Mở nguồn 1/ }).click()
    await expect(page.getByRole('dialog')).toContainText('trang 2')
    await expect(page.getByRole('dialog')).toContainText('hop-dong-A.pdf')
    await page.waitForTimeout(2500)
  })
  await ev.step('Nhấn Esc', 'Dialog đóng; focus quay lại chip nguồn', async () => {
    await page.keyboard.press('Escape')
    await expect(page.getByRole('dialog')).toBeHidden()
    expect(await page.evaluate(() => document.activeElement?.getAttribute('aria-label'))).toMatch(/Mở nguồn 1/)
  })
  await ev.step('Xóa hop-dong-A.pdf (thùng rác → Xóa tài liệu)', 'Hộp xác nhận nêu "không còn được dùng để trả lời"; sau khi xóa dòng biến mất', async () => {
    await row(page, 'hop-dong-A.pdf').getByRole('button', { name: 'Xóa hop-dong-A.pdf' }).click()
    await expect(page.getByRole('alertdialog')).toContainText('không còn được dùng để trả lời')
    await page.getByRole('button', { name: 'Xóa tài liệu' }).click()
    await expect(row(page, 'hop-dong-A.pdf')).toBeHidden()
  })
  await ev.step('Xem lại câu trả lời cũ', 'Chip nguồn "(đã xóa)", không bấm được; ô hỏi khóa (không còn tài liệu Sẵn sàng)', async () => {
    await expect(a.getByText('(đã xóa)')).toBeVisible({ timeout: 15_000 })
    await expect(page.locator('#q')).toBeDisabled()
  })
})
