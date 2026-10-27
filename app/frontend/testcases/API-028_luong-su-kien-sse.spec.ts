import { expect, test } from '../evidence/fixture'
import { bodyOf, file, purge, putFiles } from './_h'

declare global {
  interface Window {
    __sse: { name: string; at: number }[]
    __es: EventSource
  }
}

test('Luồng sự kiện SSE', async ({ ev, page }) => {
  test.setTimeout(240_000)
  await ev.step('GET /api/v1/events khi chưa đăng nhập', '401', async () => {
    const r = await ev.api('GET', '/api/v1/events', { csrf: false })
    expect(r.status).toBe(401)
  })
  await ev.step('Đăng nhập P2, xóa tài liệu; mở EventSource trong trang', 'Kết nối mở (readyState = OPEN)', async () => {
    await ev.login('p2')
    await purge(page)
    await page.evaluate(() => {
      window.__sse = []
      const es = new EventSource('/api/v1/events')
      window.__es = es
      for (const n of ['document.status_changed', 'quota.changed', 'session.expiring']) es.addEventListener(n, () => window.__sse.push({ name: n, at: Date.now() }))
    })
    await expect.poll(() => page.evaluate(() => window.__es.readyState)).toBe(1)
  })
  await ev.step('Tải hop-dong-A.pdf qua API', 'Nhận document.status_changed (PROCESSING rồi READY) và quota.changed', async () => {
    await putFiles(ev, [file('hop-dong-A.pdf')])
    await expect
      .poll(async () => (await page.evaluate(() => window.__sse.map((e) => e.name))).filter((n) => n === 'document.status_changed').length, { timeout: 60_000 })
      .toBeGreaterThanOrEqual(2)
    const names = await page.evaluate(() => window.__sse.map((e) => e.name))
    expect(names).toContain('quota.changed')
    return `Sự kiện nhận được: ${names.join(', ')}`
  })
  await ev.step('Xóa tài liệu', 'Nhận thêm quota.changed', async () => {
    const before = (await page.evaluate(() => window.__sse.filter((e) => e.name === 'quota.changed').length))
    const id = ((bodyOf(await ev.api('GET', '/api/v1/documents')).items as { id: string }[])[0]).id
    await ev.api('DELETE', `/api/v1/documents/${id}`)
    await expect.poll(() => page.evaluate(() => window.__sse.filter((e) => e.name === 'quota.changed').length)).toBeGreaterThan(before)
  })
  await ev.step('Giữ kết nối 30 s', 'Kết nối vẫn mở (ping 25 s giữ kết nối; EventSource không hiển thị dòng comment)', async () => {
    await page.waitForTimeout(30_000)
    expect(await page.evaluate(() => window.__es.readyState)).toBe(1)
  })
  ev.note('Dòng ": ping" là comment SSE nên EventSource không phát ra sự kiện; kiểm chứng gián tiếp bằng việc kết nối giữ mở > 25 s.')
})
