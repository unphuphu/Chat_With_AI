import fs from 'node:fs'
import path from 'node:path'
import { expect, test } from '../evidence/fixture'
import { ask, prep, Q_OUT, Q_PAY, row, upload, waitReady } from './_h'

const DESIGN = path.resolve(process.cwd(), '../../doc/04-design/html_design')

test('So sánh giao diện với thiết kế', async ({ ev, page }) => {
  test.setTimeout(420_000)
  const ctx = page.context()
  /** Chụp trang thiết kế HTML (ẩn bảng ghi chú thiết kế) rồi ghép cạnh ảnh thực tế thành một ảnh so sánh. */
  const compare = async (sid: string, file: string, label: string) => {
    const actual = await page.screenshot()
    const d = await ctx.newPage()
    await d.setViewportSize({ width: 1440, height: 900 })
    await d.goto('file:///' + path.join(DESIGN, file).replace(/\\/g, '/'))
    await d.addStyleTag({ content: '.spec{display:none!important}' })
    await d.waitForTimeout(400)
    const design = await d.screenshot()
    await d.close()
    const c = await ctx.newPage()
    await c.setViewportSize({ width: 1500, height: 560 })
    const img = (b: Buffer) => `data:image/png;base64,${b.toString('base64')}`
    await c.setContent(`<body style="margin:0;background:#222;color:#fff;font:14px Segoe UI"><div style="display:flex;gap:8px;padding:8px">
      <div><div style="padding:4px">THIẾT KẾ – ${sid} ${label}</div><img style="width:740px;border:1px solid #888" src="${img(design)}"></div>
      <div><div style="padding:4px">THỰC TẾ – http://localhost:8080/</div><img style="width:740px;border:1px solid #888" src="${img(actual)}"></div></div></body>`)
    await ev.shot(`${sid}-so-sanh`, c)
    await c.close()
    return `Ảnh so sánh ${sid}: thiết kế (${file}) và thực tế đặt cạnh nhau – Designer đánh giá bố cục, chữ, trạng thái.`
  }
  const rv = { review: true }
  await ev.step('S01 Màn hình chính – chưa có tài liệu', 'Bố cục, chữ, trạng thái khớp thiết kế', async () => {
    await prep(ev, 'p2')
    return compare('S01', 'S01_main_empty.html', 'Màn hình chính – chưa có tài liệu')
  }, rv)
  await ev.step('S08 Vượt giới hạn tải lên (chọn 12 file)', 'Khớp thiết kế', async () => {
    const buf = fs.readFileSync(path.resolve(process.cwd(), '../sample-pdfs/bang-gia-Q4.pdf'))
    await page.locator('input[type=file]').setInputFiles(Array.from({ length: 12 }, (_, i) => ({ name: `t${i}.pdf`, mimeType: 'application/pdf', buffer: buf })))
    await expect(page.getByText('bạn đã chọn 12 file')).toBeVisible()
    return compare('S08', 'S08_upload_limits.html', 'Vượt giới hạn tải lên')
  }, rv)
  await ev.step('S03 Trạng thái tài liệu (Sẵn sàng, Thất bại)', 'Khớp thiết kế', async () => {
    await page.reload()
    await upload(page, 'hop-dong-A.pdf', 'ho-so-scan-2019.pdf', 'bang-gia-Q4.pdf')
    await waitReady(page, 'hop-dong-A.pdf')
    await expect(row(page, 'ho-so-scan-2019.pdf').getByText('Thất bại')).toBeVisible({ timeout: 60_000 })
    await page.waitForTimeout(5500)
    return compare('S03', 'S03_main_document_states.html', 'Trạng thái tài liệu')
  }, rv)
  await ev.step('S04 Hỏi đáp có trích dẫn + Chưa đủ thông tin', 'Khớp thiết kế', async () => {
    await ask(page, Q_PAY)
    await ask(page, Q_OUT)
    return compare('S04', 'S04_main_chat_answers.html', 'Hỏi đáp có trích dẫn')
  }, rv)
  await ev.step('S06 Trình xem tài liệu gốc', 'Khớp thiết kế', async () => {
    await page.locator('article.a').first().getByRole('button', { name: /Mở nguồn 1/ }).click()
    await page.waitForTimeout(2000)
    const r = await compare('S06', 'S06_pdf_viewer.html', 'Trình xem PDF')
    await page.keyboard.press('Escape')
    return r
  }, rv)
  await ev.step('S07 Xác nhận xóa', 'Khớp thiết kế', async () => {
    await row(page, 'bang-gia-Q4.pdf').getByRole('button', { name: /^Xóa / }).click()
    const r = await compare('S07', 'S07_delete_confirm.html', 'Xác nhận xóa')
    await page.keyboard.press('Escape')
    return r
  }, rv)
  await ev.step('S05 Lỗi khi hỏi (mất mạng)', 'Khớp thiết kế', async () => {
    await page.route('**/messages', (r) => r.abort('internetdisconnected'))
    await page.locator('#q').fill('Lãi chậm trả là bao nhiêu?')
    await page.keyboard.press('Enter')
    await expect(page.locator('article.a.failed')).toBeVisible()
    const r = await compare('S05', 'S05_main_chat_errors.html', 'Lỗi khi hỏi')
    await page.unroute('**/messages')
    return r
  }, rv)
  for (const [sid, url, file, label] of [
    ['S09', '/access-denied', 'S09_access_denied.html', 'Chưa được cấp quyền'],
    ['S10', '/login-error?ref=2b7f0d1e-9a43-4f7e-9d0a-1c1a2f3b4c5d', 'S10_login_error.html', 'Lỗi đăng nhập'],
    ['S11', '/session-expired', 'S11_session_expired.html', 'Phiên hết hạn'],
  ] as const) {
    await ev.step(`${sid} ${label}`, 'Khớp thiết kế', async () => {
      await page.goto(url)
      await page.waitForTimeout(500)
      return compare(sid, file, label)
    }, rv)
  }
})
