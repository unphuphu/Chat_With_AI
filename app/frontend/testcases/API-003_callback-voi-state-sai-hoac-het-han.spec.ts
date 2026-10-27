import { expect, test } from '../evidence/fixture'

test('Callback với state sai hoặc hết hạn', async ({ ev, page }) => {
  await ev.step('Mở /api/v1/auth/callback?code=p1&state=sai', '302 tới /login-error?ref=<request_id>', async () => {
    await page.goto('/api/v1/auth/callback?code=p1&state=sai')
    await expect(page.getByRole('heading', { name: 'Không thể đăng nhập' })).toBeVisible()
    const u = new URL(page.url())
    expect(u.pathname).toBe('/login-error')
    expect(u.searchParams.get('ref')).toBeTruthy()
    return `URL: ${u.pathname}${u.search}`
  })
  await ev.step('Quan sát trang lỗi', 'Có mã tham chiếu và nút Thử đăng nhập lại', async () => {
    await expect(page.locator('.ref-code')).toBeVisible()
    await expect(page.getByRole('link', { name: 'Thử đăng nhập lại' })).toBeVisible()
  })
  await ev.step('GET /api/v1/me', '401 – không có phiên', async () => {
    expect((await ev.api('GET', '/api/v1/me')).status).toBe(401)
  })
  await ev.step('Bấm Thử đăng nhập lại và chọn P1', 'Đăng nhập thành công', async () => {
    await page.bringToFront()
    await page.getByRole('link', { name: 'Thử đăng nhập lại' }).click()
    await page.getByRole('button', { name: /Nguyễn Lan/ }).click()
    await expect(page.getByRole('heading', { name: 'Tài liệu', exact: true })).toBeVisible()
  })
})
