import fs from 'node:fs'
import path from 'node:path'
import { expect, test } from '../evidence/fixture'
import { bodyOf, prep, py } from './_h'

type Doc = { status: string; failure_code: string | null }

test('Xử lý file biên 20 MB / 300 trang', async ({ ev, page }) => {
  test.setTimeout(900_000)
  const out = path.join(process.env.TEMP ?? '/tmp', 'bien-300-trang.pdf')
  await ev.step('Tạo PDF 300 trang có chữ, gần 20 MB (văn bản + ảnh nhiễu để đạt dung lượng)', 'File hợp lệ: ≤ 20 MB, 300 trang', async () => {
    const code = `
import io, os, random, pathlib
from fpdf import FPDF
from PIL import Image
from tests.fixtures.pdfgen import _font
random.seed(7)
pdf = FPDF(); pdf.add_font("U", "", str(_font())); pdf.set_font("U", size=11)
for i in range(300):
    pdf.add_page()
    pdf.multi_cell(0, 6, f"Trang {i+1}. Điều khoản số {i+1}: Bên B thanh toán trong vòng {10+i%50} ngày kể từ ngày nhận hóa đơn hợp lệ. " * 6)
    im = Image.frombytes("RGB", (150, 150), os.urandom(150*150*3)); b = io.BytesIO(); im.save(b, "PNG"); b.seek(0)
    pdf.image(b, x=10, y=150, w=60)
pdf.output(r'${out}')
print(os.path.getsize(r'${out}'))`
    const size = Number(py(['-c', code]).trim())
    expect(size).toBeLessThanOrEqual(20 * 1024 * 1024)
    return `${(size / 1024 / 1024).toFixed(1)} MB, 300 trang`
  })
  let seconds = 0
  await ev.step('Tải lên trên giao diện, bấm giờ tới khi Sẵn sàng', 'Tài liệu Sẵn sàng', async () => {
    await prep(ev, 'p2')
    const t0 = Date.now()
    await page.locator('input[type=file]').setInputFiles(out)
    await expect(page.locator('li.row', { hasText: 'bien-300-trang.pdf' }).getByText(/Sẵn sàng|Thất bại/)).toBeVisible({ timeout: 800_000 })
    seconds = (Date.now() - t0) / 1000
    const d = (bodyOf(await ev.api('GET', '/api/v1/documents')).items as Doc[])[0]
    expect(d.status, `failure_code=${d.failure_code}`).toBe('READY')
    return `Từ lúc chọn file tới Sẵn sàng: ${seconds.toFixed(0)} s`
  })
  await ev.step('So sánh với ngưỡng NFR-002', '≤ 3 phút (180 s)', async () => {
    const ok = seconds <= 180
    ev.note(`PERF-003 trên ENV-DEV (PGlite, embedding hashing, máy dev): ${seconds.toFixed(0)} s. Chỉ để tham khảo – NFR-002 chính thức cần đo trên staging (embedding bge-m3, PostgreSQL thật).`)
    expect(ok, `${seconds.toFixed(0)} s > 180 s`).toBe(true)
    return `${seconds.toFixed(0)} s ≤ 180 s (tham khảo ENV-DEV)`
  })
  fs.rmSync(out, { force: true })
})
