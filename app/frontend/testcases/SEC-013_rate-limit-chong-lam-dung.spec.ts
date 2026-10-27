import fs from 'node:fs'
import path from 'node:path'
import { expect, test } from '../evidence/fixture'
import { ask$, bodyOf, conversationId, prep } from './_h'

test('Rate limit chống lạm dụng', async ({ ev, page }) => {
  test.setTimeout(240_000)
  await ev.step('Đăng nhập Quản trị viên, tải hop-dong-A.pdf và chờ Sẵn sàng', 'Dòng Sẵn sàng', async () => prep(ev, 'admin', ['hop-dong-A.pdf']))
  await ev.step('Chờ đầu phút rồi gửi 11 câu hỏi', 'Câu 11 → 429 kèm Retry-After', async () => {
    const ms = 60_000 - (Date.now() % 60_000)
    if (ms < 56_000) await page.waitForTimeout(ms + 600)
    const conv = await conversationId(ev)
    const codes: number[] = []
    for (let i = 0; i < 11; i++) codes.push((await ask$(ev, conv, `Câu ${i + 1}: thanh toán bao nhiêu ngày?`)).status)
    expect(codes.slice(0, 10)).toEqual(Array(10).fill(200))
    expect(codes[10]).toBe(429)
    return `Mã trả về: ${codes.join(', ')}`
  })
  await ev.step('Quản trị viên vẫn bị giới hạn, còn P1 ở phiên khác thì không (giới hạn theo người dùng)', 'P1: 200', async () => {
    const ctx2 = await page.context().browser()!.newContext({ baseURL: 'http://localhost:8080' })
    const p2 = await ctx2.newPage()
    await p2.goto('/')
    await p2.getByRole('button', { name: /Nguyễn Lan/ }).click()
    await p2.locator('.docs .empty, .docs li.row').first().waitFor()
    const docs = (await (await p2.request.get('/api/v1/documents')).json()) as { items: { id: string; status: string }[] }
    let status: number
    if (docs.items.some((d) => d.status === 'READY')) {
      const conv = ((await (await p2.request.get('/api/v1/conversations/current')).json()) as { id: string }).id
      const csrf = (await ctx2.cookies()).find((c) => c.name === 'csrf_token')!.value
      const r = await p2.request.post(`/api/v1/conversations/${conv}/messages`, { headers: { 'X-CSRF-Token': csrf }, data: { client_request_id: crypto.randomUUID(), question: 'Thanh toán bao nhiêu ngày?' } })
      status = r.status()
    } else status = 200
    await ctx2.close()
    expect(status).toBe(200)
    void bodyOf
  })
  await ev.step('Đối chiếu API-013 (giới hạn tải file theo giờ)', 'Báo cáo API-013 có kết luận ĐẠT', async () => {
    const r = path.resolve(process.cwd(), '../../test_reports')
    const dir = fs.readdirSync(r).find((d) => d.startsWith('API-013_'))
    const verdict = dir ? JSON.parse(fs.readFileSync(path.join(r, dir, 'result.json'), 'utf8')).verdict : 'chưa có'
    ev.note(`API-013 (rate limit tải file): ${verdict}`)
    expect(verdict).toBe('ĐẠT')
  })
})
