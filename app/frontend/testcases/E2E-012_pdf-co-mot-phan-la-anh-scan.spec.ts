import path from 'node:path'
import { expect, test } from '../evidence/fixture'
import { ask, BACKEND, prep, py, Q_PAY, upload, waitReady } from './_h'

test('PDF có một phần là ảnh scan', async ({ ev, page }) => {
  const out = path.join(process.env.TEMP ?? '/tmp', 'hon-hop.pdf')
  await ev.step('Tạo hon-hop.pdf: trang 1–2 là hợp đồng A (chữ), trang 3 là ảnh scan', 'File 3 trang', async () => {
    const code = [
      'import sys, pathlib',
      'from pypdf import PdfWriter, PdfReader',
      'from tests.fixtures import pdfgen as g',
      `d = pathlib.Path(r'${path.dirname(out)}')`,
      'g.text_pdf(d/"_t.pdf", g.CONTRACT_A[:2]); g.scan_pdf(d/"_s.pdf", pages=1)',
      'w = PdfWriter()',
      'for f in ("_t.pdf", "_s.pdf"):',
      '    [w.add_page(p) for p in PdfReader(str(d/f)).pages]',
      `w.write(r'${out}'); print(len(w.pages))`,
    ].join('\n')
    const n = py(['-c', code]).trim()
    expect(n).toBe('3')
    void BACKEND
    return `Đã tạo ${out} (${n} trang)`
  })
  await ev.step('Đăng nhập P2, tải hon-hop.pdf', 'Sẵn sàng (không Thất bại)', async () => {
    await prep(ev, 'p2')
    await page.locator('input[type=file]').setInputFiles(out)
    await waitReady(page, 'hon-hop.pdf')
  })
  await ev.step(`Hỏi "${Q_PAY}"`, 'Có "30 ngày", nguồn hon-hop.pdf · tr.2', async () => {
    const a = await ask(page, Q_PAY)
    await expect(a).toContainText('30 ngày')
    await expect(a.getByRole('button', { name: /hon-hop\.pdf · tr\.2/ })).toBeVisible()
  })
  await ev.step('Hỏi về nội dung chỉ có trong trang ảnh ("Trang 3 ghi gì?")', 'Chưa đủ thông tin', async () => {
    const a = await ask(page, 'Trang 3 ghi gì?')
    await expect(a).toContainText('Chưa đủ thông tin')
  })
  void upload
})
