import { expect, test } from '../evidence/fixture'
import { ask$, bodyOf, conversationId, prep } from './_h'

/** Chờ tới đầu phút UTC kế tiếp (cửa sổ rate limit cố định 60 s căn theo phút) để cả loạt nằm trong cùng một cửa sổ. */
async function alignToMinute() {
  const ms = 60_000 - (Date.now() % 60_000)
  if (ms < 58_000) await new Promise((r) => setTimeout(r, ms + 600))
}

test('Rate limit câu hỏi', async ({ ev }) => {
  test.setTimeout(240_000)
  await ev.step('Đăng nhập Quản trị viên, tải hop-dong-A.pdf và chờ Sẵn sàng', 'Dòng Sẵn sàng', async () => prep(ev, 'admin', ['hop-dong-A.pdf']))
  let conv = ''
  const statuses: number[] = []
  await ev.step('Gửi 10 câu hỏi khác nhau liên tiếp trong cùng một phút', '10 phản hồi 200', async () => {
    conv = await conversationId(ev)
    await alignToMinute()
    for (let i = 0; i < 10; i++) statuses.push((await ask$(ev, conv, `Câu hỏi số ${i + 1}: thanh toán trong bao nhiêu ngày?`)).status)
    expect(statuses).toEqual(Array(10).fill(200))
  })
  let retry = 0
  await ev.step('Gửi câu thứ 11', '429 rate_limited; Retry-After > 0; RateLimit-Remaining: 0', async () => {
    const r = await ask$(ev, conv, 'Câu hỏi số 11?')
    expect(r.status).toBe(429)
    expect(bodyOf(r).code).toBe('rate_limited')
    retry = Number(r.headers['retry-after'])
    expect(retry).toBeGreaterThan(0)
    expect(r.headers['ratelimit-remaining']).toBe('0')
    return `Retry-After=${retry}, RateLimit-Limit=${r.headers['ratelimit-limit']}`
  })
  await ev.step('Chờ hết Retry-After rồi gửi lại', '200', async () => {
    await new Promise((r) => setTimeout(r, (retry + 1) * 1000))
    expect((await ask$(ev, conv, 'Câu hỏi sau khi hết giới hạn?')).status).toBe(200)
  })
})
