import fs from 'node:fs'
import { expect, test } from '../evidence/fixture'
import { bodyOf, pdf, purge } from './_h'

test('Hiệu năng giao diện', async ({ ev, page }) => {
  test.setTimeout(900_000)
  await ev.step('Đăng nhập Quản trị viên, xóa tài liệu cũ; tải 100 tài liệu (10 lô × 10 file)', 'documents_used = 100', async () => {
    await ev.login('admin')
    await purge(page)
    const buf = fs.readFileSync(pdf('bang-gia-Q4.pdf'))
    for (let b = 0; b < 10; b++) {
      const files = Array.from({ length: 10 }, (_, i) => ({ name: `hs-${b * 10 + i + 1}.pdf`, size_bytes: buf.length }))
      const batch = bodyOf(await ev.api('POST', '/api/v1/upload-batches', { json: { files } }).then((r) => ({ body: r.body }))).batch_id as string
      for (const f of files) {
        const r = await page.request.put(`/api/v1/upload-batches/${batch}/files/${crypto.randomUUID()}`, {
          headers: { 'X-CSRF-Token': (await page.context().cookies()).find((c) => c.name === 'csrf_token')!.value },
          multipart: { file: { name: f.name, mimeType: 'application/pdf', buffer: buf } },
        })
        expect(r.status()).toBe(201)
      }
    }
    await expect
      .poll(async () => ((bodyOf(await ev.api('GET', '/api/v1/documents')).items as { status: string }[]).filter((d) => d.status === 'READY').length), { timeout: 600_000, intervals: [10_000] })
      .toBe(100)
  })
  const lcp = async () =>
    page.evaluate(
      () =>
        new Promise<number>((resolve) => {
          let v = 0
          new PerformanceObserver((l) => {
            for (const e of l.getEntries()) v = e.startTime
          }).observe({ type: 'largest-contentful-paint', buffered: true })
          setTimeout(() => resolve(v), 1500)
        }),
    )
  await ev.step('Tải lại trang với 100 tài liệu; đo LCP', 'LCP < 2,5 s', async () => {
    await page.reload()
    await expect(page.locator('.docs li.row')).toHaveCount(100, { timeout: 30_000 })
    const v = await lcp()
    expect(v).toBeLessThan(2500)
    return `LCP = ${Math.round(v)} ms`
  })
  await ev.step('Cuộn danh sách 100 tài liệu từ đầu tới cuối', 'Không lỗi console; cuộn được', async () => {
    const errors: string[] = []
    page.on('pageerror', (e) => errors.push(e.message))
    await page.locator('.docs .scroll').evaluate(async (el) => {
      for (let y = 0; y <= el.scrollHeight; y += 200) {
        el.scrollTop = y
        await new Promise((r) => setTimeout(r, 40))
      }
    })
    expect(errors).toEqual([])
    return `Chiều cao danh sách ${await page.locator('.docs .scroll').evaluate((e) => e.scrollHeight)} px; 0 lỗi trang`
  })
  await ev.step('Bật CPU throttling 4×, tải lại, đo LCP', 'LCP < 4 s (ghi nhận)', async () => {
    const cdp = await page.context().newCDPSession(page)
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 })
    await page.reload()
    await expect(page.locator('.docs li.row')).toHaveCount(100, { timeout: 60_000 })
    const v = await lcp()
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: 1 })
    expect(v).toBeLessThan(4000)
    return `LCP (CPU 4×) = ${Math.round(v)} ms`
  })
  await ev.step('Dọn dẹp: xóa 100 tài liệu thử', 'Danh sách rỗng', async () => {
    await purge(page)
  })
})
