import { expect, test } from '../evidence/fixture'
import { ask, ask$, bodyOf, prep, Q_PAY } from './_h'

test('Cách ly tài liệu giữa người dùng (IDOR)', async ({ ev, page }) => {
  let docP1 = ''
  let convP1 = ''
  await ev.step('Đăng nhập P1, đảm bảo có tài liệu Sẵn sàng, ghi id tài liệu và id hội thoại', 'Có id', async () => {
    await ev.login('p1')
    if ((await page.locator('li.row', { hasText: 'Sẵn sàng' }).count()) === 0) {
      await page.locator('input[type=file]').setInputFiles('../sample-pdfs/hop-dong-A.pdf')
      await expect(page.locator('li.row', { hasText: 'Sẵn sàng' }).first()).toBeVisible({ timeout: 90_000 })
    }
    const docs = bodyOf(await ev.api('GET', '/api/v1/documents')).items as { id: string; status: string }[]
    docP1 = docs.find((d) => d.status === 'READY')!.id
    convP1 = bodyOf(await ev.api('GET', '/api/v1/conversations/current')).id as string
  })
  await ev.step('Đăng xuất; đăng nhập P2 (chỉ có bảng giá)', 'Màn hình P2', async () => {
    await ev.api('POST', '/api/v1/auth/logout')
    await prep(ev, 'p2', ['bang-gia-Q4.pdf'])
  })
  await ev.step('GET /documents của P2', 'Không có tài liệu của P1', async () => {
    const items = bodyOf(await ev.api('GET', '/api/v1/documents')).items as { id: string }[]
    expect(items.map((d) => d.id)).not.toContain(docP1)
  })
  await ev.step('GET file, DELETE, POST reprocess trên id tài liệu P1', 'Mỗi request 404 not_found', async () => {
    for (const [m, u] of [['GET', `/api/v1/documents/${docP1}/file`], ['DELETE', `/api/v1/documents/${docP1}`], ['POST', `/api/v1/documents/${docP1}/reprocess`]] as const) {
      const r = await ev.api(m, u)
      expect(r.status, `${m} ${u}`).toBe(404)
    }
  })
  await ev.step('POST /messages vào hội thoại của P1', '404 hoặc 409 – không trả nội dung của P1', async () => {
    const r = await ask$(ev, convP1, Q_PAY)
    expect([404, 409]).toContain(r.status)
    expect(JSON.stringify(r.body)).not.toContain('hop-dong')
    return `HTTP ${r.status}`
  })
  await ev.step('P2 hỏi câu chỉ có trong tài liệu của P1', 'Không trích dẫn và không nêu nội dung tài liệu P1', async () => {
    await page.bringToFront()
    const a = await ask(page, Q_PAY)
    await expect(a).toContainText('Chưa đủ thông tin')
    await expect(a).not.toContainText('30 ngày')
  })
  await ev.step('Đăng nhập lại P1', 'Tài liệu của P1 còn nguyên', async () => {
    await ev.api('POST', '/api/v1/auth/logout')
    await ev.login('p1')
    const items = bodyOf(await ev.api('GET', '/api/v1/documents')).items as { id: string }[]
    expect(items.map((d) => d.id)).toContain(docP1)
  })
})
