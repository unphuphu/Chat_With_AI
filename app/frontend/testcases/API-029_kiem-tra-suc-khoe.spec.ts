import { expect, test } from '../evidence/fixture'

test('Kiểm tra sức khỏe', async ({ ev, page }) => {
  await ev.step('GET /api/v1/healthz', '200 {"status":"ok"}', async () => {
    const r = await ev.api('GET', '/api/v1/healthz', { csrf: false })
    expect(r.status).toBe(200)
    expect(r.body).toEqual({ status: 'ok' })
  })
  await ev.step('GET /api/v1/readyz', '200 {"status":"ready"}', async () => {
    const r = await ev.api('GET', '/api/v1/readyz', { csrf: false })
    expect(r.status).toBe(200)
    expect(r.body).toEqual({ status: 'ready' })
  })
  await ev.step('Mở /api/v1/readyz trên trình duyệt', 'Hiển thị {"status":"ready"}', async () => {
    await page.bringToFront()
    await page.goto('/api/v1/readyz')
    await expect(page.locator('body')).toContainText('ready')
  })
  ev.note('Bước tùy chọn "dừng devdb rồi gọi readyz → 503" không thực hiện (sẽ làm gián đoạn ứng dụng đang dùng chung).')
})
