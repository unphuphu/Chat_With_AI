// Test case: doc/07-verification/test_cases/API-023_kiem-tra-cau-hoi-khong-hop-le.md
import path from 'node:path'
import { expect, test } from '../evidence/fixture'

const SAMPLES = path.resolve(process.cwd(), '../sample-pdfs')

test('Kiểm tra câu hỏi không hợp lệ', async ({ ev, page }) => {
  let conv = ''
  await ev.step('Đăng nhập P1 và đảm bảo có ít nhất 1 tài liệu Sẵn sàng', 'Danh sách có tài liệu trạng thái Sẵn sàng', async () => {
    await ev.login('p1')
    if ((await page.locator('li.row', { hasText: 'Sẵn sàng' }).count()) === 0) {
      await page.locator('input[type=file]').setInputFiles(path.join(SAMPLES, 'hop-dong-A.pdf'))
      await expect(page.locator('li.row', { hasText: 'Sẵn sàng' }).first()).toBeVisible({ timeout: 60_000 })
    }
  })
  await ev.step('Lấy hội thoại hiện tại', '200, có id hội thoại', async () => {
    const r = await ev.api('GET', '/api/v1/conversations/current')
    expect(r.status).toBe(200)
    conv = (r.body as { id: string }).id
    return `conversation_id=${conv}`
  })
  const ask = (question: string, id = conv) =>
    ev.api('POST', `/api/v1/conversations/${id}/messages`, { json: { client_request_id: crypto.randomUUID(), question } })

  await ev.step('Gửi câu hỏi chỉ có khoảng trắng', '422, code = empty_question, application/problem+json', async () => {
    const r = await ask('   ')
    expect(r.status).toBe(422)
    expect((r.body as { code: string }).code).toBe('empty_question')
    expect(r.headers['content-type']).toContain('application/problem+json')
    return `HTTP ${r.status} ${(r.body as { code: string }).code}`
  })
  await ev.step('Gửi câu hỏi 2.001 ký tự', '422, code = question_too_long', async () => {
    const r = await ask('x'.repeat(2001))
    expect(r.status).toBe(422)
    expect((r.body as { code: string }).code).toBe('question_too_long')
    return `HTTP ${r.status} ${(r.body as { code: string }).code}`
  })
  await ev.step('Gửi câu hỏi vào hội thoại không tồn tại', '404', async () => {
    const r = await ask('Điều khoản thanh toán?', crypto.randomUUID())
    expect(r.status).toBe(404)
    return `HTTP ${r.status}`
  })
  await ev.step('Kiểm tra giao diện: không gửi được câu trống', 'Nút Gửi bị vô hiệu khi ô hỏi chỉ có khoảng trắng', async () => {
    await page.bringToFront()
    await page.locator('#q').fill('    ')
    await expect(page.getByRole('button', { name: 'Gửi' })).toBeDisabled()
  })
})
