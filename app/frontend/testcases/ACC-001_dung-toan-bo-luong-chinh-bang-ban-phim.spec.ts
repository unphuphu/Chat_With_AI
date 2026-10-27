import { expect, test } from '../evidence/fixture'
import { pdf, prep, Q_PAY, row, waitReady } from './_h'

test('Dùng toàn bộ luồng chính bằng bàn phím', async ({ ev, page }) => {
  test.setTimeout(240_000)
  const active = () => page.evaluate(() => `${document.activeElement?.tagName}|${document.activeElement?.id}|${document.activeElement?.getAttribute('aria-label') ?? ''}|${(document.activeElement as HTMLElement | null)?.innerText?.slice(0, 40) ?? ''}`)
  const tabUntil = async (pred: (a: string) => boolean, max = 60) => {
    for (let i = 0; i < max; i++) {
      await page.keyboard.press('Tab')
      const a = await active()
      if (pred(a)) return a
    }
    throw new Error(`Không tab tới được phần tử mong muốn sau ${max} lần Tab`)
  }
  await ev.step('Đăng nhập P2, xóa tài liệu cũ', 'Màn hình chính', async () => prep(ev, 'p2'))
  await ev.step('Nhấn Tab từ đầu trang', 'Phần tử đầu tiên là "Bỏ qua tới nội dung chính"', async () => {
    await page.evaluate(() => (document.activeElement as HTMLElement | null)?.blur())
    await page.keyboard.press('Tab')
    const a = await active()
    expect(a).toContain('Bỏ qua tới nội dung chính')
    return a
  })
  await ev.step('Tab tới "Chọn file PDF", Enter, chọn file', 'File được tải lên (hộp thoại chọn file mở bằng bàn phím)', async () => {
    await tabUntil((a) => a.includes('Chọn file PDF'))
    const chooser = page.waitForEvent('filechooser')
    await page.keyboard.press('Enter')
    await (await chooser).setFiles(pdf('hop-dong-A.pdf'))
    await waitReady(page, 'hop-dong-A.pdf')
  })
  await ev.step('Tab tới ô hỏi, gõ câu hỏi, Shift + Enter, Enter', 'Xuống dòng rồi gửi được', async () => {
    await tabUntil((a) => a.startsWith('TEXTAREA|q'))
    await page.keyboard.type(Q_PAY)
    await page.keyboard.press('Shift+Enter')
    expect(await page.locator('#q').inputValue()).toContain('\n')
    await page.keyboard.press('Enter')
    await expect(page.locator('article.a').first()).toContainText('30 ngày', { timeout: 30_000 })
  })
  await ev.step('Tab tới chip nguồn, Enter', 'Trình xem mở; focus ở nút Đóng', async () => {
    await tabUntil((a) => /Mở nguồn 1/.test(a))
    await page.keyboard.press('Enter')
    await expect(page.getByRole('dialog')).toBeVisible()
    expect(await active()).toContain('Đóng trình xem')
    await page.waitForTimeout(1500)
  })
  await ev.step('Esc', 'Trình xem đóng; focus về chip nguồn', async () => {
    await page.keyboard.press('Escape')
    await expect(page.getByRole('dialog')).toBeHidden()
    expect(await active()).toContain('Mở nguồn 1')
  })
  await ev.step('Tab tới nút xóa tài liệu, Enter; Enter trên Hủy', 'Hộp xác nhận mở, focus mặc định ở Hủy; Enter đóng hộp, tài liệu còn', async () => {
    await page.evaluate(() => document.querySelector<HTMLElement>('main')?.focus())
    await page.keyboard.press('Shift+Tab')
    await tabUntil((a) => a.includes('Xóa hop-dong-A.pdf'), 80)
    await page.keyboard.press('Enter')
    await expect(page.getByRole('alertdialog')).toBeVisible()
    expect(await active()).toContain('Hủy')
    await page.keyboard.press('Enter')
    await expect(page.getByRole('alertdialog')).toBeHidden()
    await expect(row(page, 'hop-dong-A.pdf')).toBeVisible()
  })
  await ev.step('Xem video: thứ tự focus hợp lý, không bị kẹt', 'Đúng', async () => 'Toàn bộ luồng thực hiện chỉ bằng bàn phím (trừ bước đăng nhập qua IdP giả lập) – người đánh giá xem video để xác nhận thứ tự focus.', { review: true })
})
