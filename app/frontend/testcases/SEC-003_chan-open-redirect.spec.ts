import { expect, test } from '../evidence/fixture'

test('Chặn open redirect', async ({ ev, page }) => {
  test.setTimeout(240_000)
  const attempts: [string, string][] = [
    ['https://evil.example', 'return_to=https://evil.example'],
    ['//evil.example', 'return_to=//evil.example'],
    ['/\\evil.example', 'return_to=/\\evil.example'],
    ['javascript:alert(1)', 'return_to=javascript:alert(1)'],
  ]
  for (const [value, label] of attempts) {
    await ev.step(`Mở /api/v1/auth/login?${label}, chọn P1`, 'Sau callback về http://localhost:8080/ (không tới domain ngoài)', async () => {
      await page.goto(`/api/v1/auth/login?return_to=${encodeURIComponent(value)}`)
      await page.getByRole('button', { name: /Nguyễn Lan/ }).click()
      await expect(page.getByRole('heading', { name: 'Tài liệu', exact: true })).toBeVisible()
      expect(page.url()).toBe('http://localhost:8080/')
      await ev.api('POST', '/api/v1/auth/logout')
    })
  }
  await ev.step('Thử return_to=/ (hợp lệ)', 'Về /', async () => {
    await page.bringToFront()
    await page.goto('/api/v1/auth/login?return_to=%2F')
    await page.getByRole('button', { name: /Nguyễn Lan/ }).click()
    await expect(page.getByRole('heading', { name: 'Tài liệu', exact: true })).toBeVisible()
    expect(new URL(page.url()).pathname).toBe('/')
  })
})
