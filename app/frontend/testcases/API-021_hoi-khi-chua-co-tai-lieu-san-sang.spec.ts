import { expect, test } from '../evidence/fixture'
import { ask$, bodyOf, conversationId, prep, Q_PAY, upload } from './_h'

test('Hỏi khi chưa có tài liệu Sẵn sàng', async ({ ev, page }) => {
  let conv = ''
  await ev.step('Đăng nhập P2 (không có tài liệu); POST /messages', '409 no_ready_documents; "Cần ít nhất một tài liệu Sẵn sàng…"', async () => {
    await prep(ev, 'p2')
    conv = await conversationId(ev)
    const r = await ask$(ev, conv, Q_PAY)
    expect(r.status).toBe(409)
    expect(bodyOf(r).code).toBe('no_ready_documents')
    expect(String(bodyOf(r).detail)).toContain('Cần ít nhất một tài liệu Sẵn sàng')
  })
  await ev.step('Tải ho-so-scan-2019.pdf (sẽ Thất bại) rồi hỏi lại', '409 no_ready_documents (E-03)', async () => {
    await page.bringToFront()
    await upload(page, 'ho-so-scan-2019.pdf')
    await expect(page.locator('li.row', { hasText: 'ho-so-scan-2019.pdf' }).getByText('Thất bại')).toBeVisible({ timeout: 60_000 })
    const r = await ask$(ev, conv, Q_PAY)
    expect(r.status).toBe(409)
    expect(bodyOf(r).code).toBe('no_ready_documents')
  })
})
