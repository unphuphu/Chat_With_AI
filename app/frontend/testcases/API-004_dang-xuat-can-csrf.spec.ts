import { expect, test } from '../evidence/fixture'

test('Đăng xuất cần CSRF', async ({ ev }) => {
  await ev.step('Đăng nhập P1', 'Vào màn hình chính', async () => {
    await ev.login('p1')
  })
  await ev.step('POST /auth/logout không có X-CSRF-Token', '403 csrf_invalid, application/problem+json', async () => {
    const r = await ev.api('POST', '/api/v1/auth/logout', { csrf: false })
    expect(r.status).toBe(403)
    expect((r.body as { code: string }).code).toBe('csrf_invalid')
    expect(r.headers['content-type']).toContain('application/problem+json')
  })
  await ev.step('POST /auth/logout có X-CSRF-Token', '204', async () => {
    expect((await ev.api('POST', '/api/v1/auth/logout')).status).toBe(204)
  })
  await ev.step('GET /me', '401 unauthenticated', async () => {
    const r = await ev.api('GET', '/api/v1/me')
    expect(r.status).toBe(401)
    expect((r.body as { code: string }).code).toBe('unauthenticated')
  })
})
