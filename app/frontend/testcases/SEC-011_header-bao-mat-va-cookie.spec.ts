import { expect, test } from '../evidence/fixture'
import { bodyOf, prep } from './_h'

test('Header bảo mật và cookie', async ({ ev, page }) => {
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf và chờ Sẵn sàng', 'Dòng Sẵn sàng', async () => prep(ev, 'p2', ['hop-dong-A.pdf']))
  await ev.step('GET /api/v1/documents; đọc header', 'nosniff, no-referrer, X-Frame-Options DENY, CSP có frame-ancestors \'none\', Cache-Control private no-store, có X-Request-ID', async () => {
    const h = (await ev.api('GET', '/api/v1/documents')).headers
    expect(h['x-content-type-options']).toBe('nosniff')
    expect(h['referrer-policy']).toBe('no-referrer')
    expect(h['x-frame-options']).toBe('DENY')
    expect(h['content-security-policy']).toContain("frame-ancestors 'none'")
    expect(h['cache-control']).toBe('private, no-store')
    expect(h['x-request-id']).toBeTruthy()
    return `XCTO=${h['x-content-type-options']}; RP=${h['referrer-policy']}; XFO=${h['x-frame-options']}; CC=${h['cache-control']}`
  })
  await ev.step('GET /documents/{id}/file', 'X-Frame-Options: SAMEORIGIN; CSP frame-ancestors \'self\'', async () => {
    const id = ((bodyOf(await ev.api('GET', '/api/v1/documents')).items as { id: string }[])[0]).id
    const h = (await ev.api('GET', `/api/v1/documents/${id}/file`)).headers
    expect(h['x-frame-options']).toBe('SAMEORIGIN')
    expect(h['content-security-policy']).toContain("frame-ancestors 'self'")
  })
  await ev.step('Đọc cookie', 'sid: HttpOnly, Lax; csrf_token: Strict; Secure=false trên localhost (staging phải true)', async () => {
    const ck = await page.context().cookies()
    const sid = ck.find((c) => c.name === 'sid')!
    const csrf = ck.find((c) => c.name === 'csrf_token')!
    expect(sid).toMatchObject({ httpOnly: true, sameSite: 'Lax' })
    expect(csrf.sameSite).toBe('Strict')
    return `sid.secure=${sid.secure}, csrf_token.secure=${csrf.secure} (localhost/HTTP)`
  })
  await ev.step('GET /api/v1/khong-co', '404 problem+json, không lộ stack trace', async () => {
    const r = await ev.api('GET', '/api/v1/khong-co', { csrf: false })
    expect(r.status).toBe(404)
    expect(r.headers['content-type']).toContain('application/problem+json')
    expect(JSON.stringify(r.body)).not.toMatch(/Traceback|File "/)
  })
})
