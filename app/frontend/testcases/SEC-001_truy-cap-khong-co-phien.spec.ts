import { expect, test } from '../evidence/fixture'

test('Truy cập không có phiên', async ({ ev, page }) => {
  await ev.step('Gọi /me, /documents, /conversations/current, /events khi chưa đăng nhập', 'Mỗi request 401 unauthenticated', async () => {
    for (const u of ['/api/v1/me', '/api/v1/documents', '/api/v1/conversations/current', '/api/v1/events']) {
      const r = await ev.api('GET', u, { csrf: false })
      expect(r.status, u).toBe(401)
    }
  })
  await ev.step('Mở http://localhost:8080/', 'Chuyển tới trang IdP', async () => {
    await page.bringToFront()
    await page.goto('/')
    await expect(page.getByText('Chọn tài khoản để đăng nhập')).toBeVisible()
  })
  await ev.step('Đăng nhập P1, đăng xuất; gọi lại GET /documents', '401', async () => {
    await ev.login('p1')
    expect((await ev.api('POST', '/api/v1/auth/logout')).status).toBe(204)
    expect((await ev.api('GET', '/api/v1/documents')).status).toBe(401)
  })
  await ev.step('Gửi cookie sid giả rồi gọi /me', '401', async () => {
    await page.context().addCookies([{ name: 'sid', value: 'gia-mao-0123456789', domain: 'localhost', path: '/' }])
    const r = await ev.api('GET', '/api/v1/me', { csrf: false })
    expect(r.status).toBe(401)
  })
})
