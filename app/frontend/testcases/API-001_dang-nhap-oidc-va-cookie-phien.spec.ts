import { expect, test } from '../evidence/fixture'
import { bodyOf } from './_h'

test('Đăng nhập OIDC và cookie phiên', async ({ ev, page }) => {
  await ev.step('Mở http://localhost:8080/ khi chưa đăng nhập', 'Chuyển tới IdP :8090/authorize, có state và code_challenge_method=S256', async () => {
    await page.goto('/')
    await expect(page.getByText('Chọn tài khoản để đăng nhập')).toBeVisible()
    const u = new URL(page.url())
    expect(u.port).toBe('8090')
    expect(u.pathname).toBe('/authorize')
    expect(u.searchParams.get('state')).toBeTruthy()
    expect(u.searchParams.get('code_challenge_method')).toBe('S256')
    return `URL: ${u.origin}${u.pathname}?state=…&code_challenge_method=S256`
  })
  await ev.step('Chọn P1', 'Quay về http://localhost:8080/; hiển thị lan.nguyen@congty.vn', async () => {
    await page.getByRole('button', { name: /Nguyễn Lan/ }).click()
    await expect(page.getByText('lan.nguyen@congty.vn')).toBeVisible()
    expect(page.url()).toBe('http://localhost:8080/')
  })
  await ev.step('Đọc cookie trình duyệt', 'sid: HttpOnly, SameSite=Lax; csrf_token: SameSite=Strict, không HttpOnly', async () => {
    const ck = await page.context().cookies()
    const sid = ck.find((c) => c.name === 'sid')!
    const csrf = ck.find((c) => c.name === 'csrf_token')!
    expect(sid.httpOnly).toBe(true)
    expect(sid.sameSite).toBe('Lax')
    expect(csrf.sameSite).toBe('Strict')
    expect(csrf.httpOnly).toBe(false)
    return `sid(httpOnly=${sid.httpOnly}, sameSite=${sid.sameSite}); csrf_token(httpOnly=${csrf.httpOnly}, sameSite=${csrf.sameSite})`
  })
  let docs1 = ''
  await ev.step('GET /api/v1/me', '200; email, documents_limit=100, limits.max_files_per_batch=10, session_expires_at', async () => {
    const r = await ev.api('GET', '/api/v1/me')
    const b = bodyOf(r)
    expect(r.status).toBe(200)
    expect(b.email).toBe('lan.nguyen@congty.vn')
    expect(b.documents_limit).toBe(100)
    expect((b.limits as { max_files_per_batch: number }).max_files_per_batch).toBe(10)
    expect(b.session_expires_at).toBeTruthy()
    docs1 = JSON.stringify(bodyOf(await ev.api('GET', '/api/v1/documents')).items)
    return `email=${b.email}, expires=${b.session_expires_at}`
  })
  await ev.step('Đăng xuất rồi đăng nhập lại P1; GET /documents', 'Cùng workspace: danh sách tài liệu giống trước', async () => {
    await ev.api('POST', '/api/v1/auth/logout')
    await ev.login('p1')
    const r = await ev.api('GET', '/api/v1/documents')
    expect(JSON.stringify(bodyOf(r).items)).toBe(docs1)
  })
})
