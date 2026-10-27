import { expect, test } from '../evidence/fixture'

test('Callback từ chối người ngoài nhóm và open redirect', async ({ ev, page }) => {
  await ev.step('Mở /api/v1/auth/login?return_to=https://evil.example rồi chọn P1', 'Sau callback về http://localhost:8080/ (không tới evil.example)', async () => {
    await page.goto('/api/v1/auth/login?return_to=https%3A%2F%2Fevil.example')
    await page.getByRole('button', { name: /Nguyễn Lan/ }).click()
    await expect(page.getByRole('heading', { name: 'Tài liệu', exact: true })).toBeVisible()
    expect(page.url()).toBe('http://localhost:8080/')
  })
  await ev.step('Đăng xuất; mở / và chọn Người ngoài nhóm', 'URL /access-denied; trang Bạn chưa được cấp quyền', async () => {
    await ev.api('POST', '/api/v1/auth/logout')
    await ev.login('outsider')
    expect(new URL(page.url()).pathname).toBe('/access-denied')
  })
  await ev.step('GET /api/v1/me trong phiên đó', '401 unauthenticated – không có phiên', async () => {
    const r = await ev.api('GET', '/api/v1/me')
    expect(r.status).toBe(401)
    expect((r.body as { code: string }).code).toBe('unauthenticated')
  })
})
