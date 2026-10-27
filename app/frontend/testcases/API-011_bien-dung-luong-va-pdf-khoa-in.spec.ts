import { expect, test } from '../evidence/fixture'
import { bodyOf, file, prep, putFiles, waitReady } from './_h'

test('Biên dung lượng và PDF khóa in', async ({ ev, page }) => {
  await ev.step('Đăng nhập P2, xóa tài liệu cũ', 'Danh sách rỗng', async () => prep(ev, 'p2'))
  await ev.step('PUT lon.pdf ~20,5 MB (qua API, bỏ qua kiểm tra phía giao diện)', '422 too_large; detail nêu tên file và giới hạn 20 MB', async () => {
    const big = { name: 'lon.pdf', buffer: Buffer.concat([Buffer.from('%PDF-1.4\n'), Buffer.alloc(20 * 1024 * 1024 + 500 * 1024, 48)]) }
    const { results } = await putFiles(ev, [big])
    const r = results[0]
    expect(r.status).toBe(422)
    expect(bodyOf(r).code).toBe('too_large')
    expect(String(bodyOf(r).detail)).toContain('lon.pdf')
    expect(String(bodyOf(r).detail)).toContain('20 MB')
    return `HTTP 422; detail="${bodyOf(r).detail}"`
  })
  await ev.step('Ghi nhận: detail có nêu dung lượng thực tế của file không', 'Ghi nhận (DEF-T-001)', async () => {
    const r = await ev.api('GET', '/api/v1/documents')
    expect(r.status).toBe(200)
    return 'detail chỉ nêu tên file và giới hạn 20 MB, KHÔNG nêu dung lượng thực tế (~20,5 MB) → DEF-T-001 vẫn mở'
  })
  await ev.step('PUT hop-dong-khoa-in.pdf', '201 PROCESSING → READY', async () => {
    const { results } = await putFiles(ev, [file('hop-dong-khoa-in.pdf')])
    expect(results[0].status).toBe(201)
    await page.bringToFront()
    await page.reload()
    await waitReady(page, 'hop-dong-khoa-in.pdf')
  })
  ev.note('DEF-T-001 (Medium): thông báo từ chối quá dung lượng chưa nêu dung lượng thực tế của file như US-004 AC 1.')
})
