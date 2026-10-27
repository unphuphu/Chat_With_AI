import { expect, test } from '../evidence/fixture'
import { ask, prep, Q_OUT, row, upload, waitReady } from './_h'

test('Trạng thái không chỉ dựa vào màu', async ({ ev, page }) => {
  await ev.step('Đăng nhập P2; tạo đủ 3 trạng thái (Đang xử lý, Sẵn sàng, Thất bại)', 'Mỗi dòng có biểu tượng + chữ trạng thái', async () => {
    await prep(ev, 'p2')
    await page.route('**/upload-batches/*/files/*', async (route) => {
      await new Promise((r) => setTimeout(r, 1500))
      await route.continue()
    })
    await upload(page, 'hop-dong-A.pdf')
    await waitReady(page, 'hop-dong-A.pdf')
    await page.unroute('**/upload-batches/*/files/*')
    await upload(page, 'ho-so-scan-2019.pdf', 'bang-gia-Q4.pdf')
    await expect(row(page, 'ho-so-scan-2019.pdf').getByText('Thất bại')).toBeVisible({ timeout: 60_000 })
    for (const st of ['.st-ready', '.st-failed']) {
      const el = page.locator(`.docs .status${st}`).first()
      await expect(el.locator('svg')).toHaveCount(1)
      expect((await el.innerText()).trim().length).toBeGreaterThan(3)
    }
    await ask(page, Q_OUT)
  })
  await ev.step('Chế độ tương phản cao (forcedColors: active)', 'Vẫn phân biệt được trạng thái', async () => {
    await page.emulateMedia({ forcedColors: 'active' })
    await page.waitForTimeout(500)
    const texts = await page.locator('.docs .status').allInnerTexts()
    expect(texts.join(' ')).toMatch(/Sẵn sàng/)
    expect(texts.join(' ')).toMatch(/Thất bại/)
    return `Trạng thái hiển thị bằng chữ: ${texts.map((t) => t.trim()).join(' | ')}`
  })
  await ev.step('Xem ảnh ở thang xám (grayscale)', 'Phân biệt được Sẵn sàng / Thất bại / Chưa đủ thông tin bằng chữ', async () => {
    await page.emulateMedia({ forcedColors: 'none' })
    await page.addStyleTag({ content: 'html{filter:grayscale(1)}' })
    await page.waitForTimeout(500)
    return 'Ảnh chụp ở thang xám: trạng thái và nhãn loại câu trả lời vẫn đọc được nhờ biểu tượng + chữ (người đánh giá xác nhận bằng ảnh).'
  }, { review: true })
})
