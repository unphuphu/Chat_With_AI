import { expect, test } from '../evidence/fixture'
import { py } from './_h'

test('Từ chối theo nhóm IdP và ghi audit', async ({ ev, page }) => {
  await ev.step('Đăng nhập Người ngoài nhóm', 'Trang /access-denied', async () => {
    await ev.login('outsider')
    expect(new URL(page.url()).pathname).toBe('/access-denied')
  })
  await ev.step('Đọc cookie', 'Không có cookie sid', async () => {
    const ck = await page.context().cookies()
    expect(ck.find((c) => c.name === 'sid')).toBeUndefined()
    return `Cookie hiện có: ${ck.map((c) => c.name).join(', ') || '(không có)'}`
  })
  await ev.step('Kiểm tra audit: chạy pytest test_outsider_denied_and_audited', '1 passed – có 1 bản ghi login_denied', async () => {
    const out = py(['-m', 'pytest', 'tests/integration/test_slice1.py::test_outsider_denied_and_audited', '-q', '-p', 'no:cacheprovider'])
    expect(out).toContain('1 passed')
    return out.trim().split('\n').pop()
  })
})
