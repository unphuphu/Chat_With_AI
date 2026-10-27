import { expect, test } from '../evidence/fixture'
import { ask, bodyOf, prep, Q_PAY } from './_h'

test('Tải file gốc để xem', async ({ ev, page }) => {
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf và chờ Sẵn sàng', 'Dòng Sẵn sàng', async () => prep(ev, 'p2', ['hop-dong-A.pdf']))
  let id = ''
  await ev.step('GET /documents/{id}/file?from=citation&page=2', '200; content-type application/pdf; body bắt đầu %PDF-', async () => {
    id = ((bodyOf(await ev.api('GET', '/api/v1/documents')).items as { id: string }[])[0]).id
    const r = await ev.api('GET', `/api/v1/documents/${id}/file?from=citation&page=2`)
    expect(r.status).toBe(200)
    expect(r.headers['content-type']).toBe('application/pdf')
    expect((await r.raw.body()).subarray(0, 5).toString()).toBe('%PDF-')
  })
  await ev.step('Kiểm tra header', 'Content-Disposition chứa hop-dong-A.pdf; X-Frame-Options: SAMEORIGIN; Cache-Control: private, no-store', async () => {
    const r = await ev.api('GET', `/api/v1/documents/${id}/file?from=citation&page=2`)
    expect(r.headers['content-disposition']).toContain('hop-dong-A.pdf')
    expect(r.headers['x-frame-options']).toBe('SAMEORIGIN')
    expect(r.headers['cache-control']).toBe('private, no-store')
    return `CD=${r.headers['content-disposition']}; XFO=${r.headers['x-frame-options']}; CC=${r.headers['cache-control']}`
  })
  await ev.step('Mở file qua nguồn trích dẫn trên giao diện', 'Trình xem PDF của Edge hiển thị tài liệu', async () => {
    await page.bringToFront()
    const a = await ask(page, Q_PAY)
    await a.getByRole('button', { name: /Mở nguồn 1/ }).click()
    await expect(page.getByRole('dialog')).toContainText('trang 2')
    await page.waitForTimeout(2500)
  })
})
