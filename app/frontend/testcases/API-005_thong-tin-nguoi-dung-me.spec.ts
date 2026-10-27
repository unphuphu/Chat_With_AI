import { expect, test } from '../evidence/fixture'
import { bodyOf } from './_h'

test('Thông tin người dùng /me', async ({ ev, page }) => {
  await ev.step('Đăng nhập P1', 'Màn hình chính', async () => {
    await ev.login('p1')
  })
  let limits: Record<string, number> = {}
  await ev.step('GET /api/v1/me', '200; user_id, email, role, documents_used, documents_limit, session_expires_at (ISO, Z)', async () => {
    const r = await ev.api('GET', '/api/v1/me')
    const b = bodyOf(r)
    expect(r.status).toBe(200)
    for (const k of ['user_id', 'email', 'role', 'documents_used', 'documents_limit', 'session_expires_at', 'limits']) expect(b).toHaveProperty(k)
    expect(String(b.session_expires_at)).toMatch(/Z$/)
    limits = b.limits as Record<string, number>
    return JSON.stringify({ role: b.role, used: b.documents_used, limit: b.documents_limit })
  })
  await ev.step('Đối chiếu limits với giao diện', 'max_file_mb=20, max_pages=300, max_files_per_batch=10, question_max_chars=2000 khớp chữ trên màn hình', async () => {
    expect(limits).toMatchObject({ max_file_mb: 20, max_pages: 300, max_files_per_batch: 10, question_max_chars: 2000 })
    await page.bringToFront()
    const text = await page.locator('.drop').innerText()
    expect(text).toContain('Tối đa 10 file')
    expect(text).toContain('20 MB')
    expect(text).toContain('300 trang')
    await expect(page.locator('.counter')).toHaveText('0/2.000')
  })
})
