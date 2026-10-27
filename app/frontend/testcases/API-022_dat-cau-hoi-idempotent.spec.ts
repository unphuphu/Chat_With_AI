import { expect, test } from '../evidence/fixture'
import { ask$, bodyOf, conversationId, newCrid, prep, Q_PAY } from './_h'

test('Đặt câu hỏi idempotent', async ({ ev }) => {
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf và chờ Sẵn sàng', 'Dòng Sẵn sàng', async () => prep(ev, 'p2', ['hop-dong-A.pdf']))
  const crid = newCrid()
  let conv = ''
  let first: Record<string, unknown> = {}
  await ev.step('POST câu hỏi với client_request_id = R', '200, có message_id M', async () => {
    conv = await conversationId(ev)
    const r = await ask$(ev, conv, Q_PAY, crid)
    expect(r.status).toBe(200)
    first = bodyOf(r)
  })
  await ev.step('POST lại cùng R và cùng câu hỏi', '200, cùng message_id, cùng answer', async () => {
    const r = await ask$(ev, conv, Q_PAY, crid)
    expect(r.status).toBe(200)
    expect(bodyOf(r).message_id).toBe(first.message_id)
    expect(bodyOf(r).answer).toBe(first.answer)
  })
  await ev.step('POST R với câu hỏi khác', '422 idempotency_mismatch', async () => {
    const r = await ask$(ev, conv, 'Một câu hỏi khác hẳn?', crid)
    expect(r.status).toBe(422)
    expect(bodyOf(r).code).toBe('idempotency_mismatch')
  })
  await ev.step('GET /conversations/current', 'Chỉ có 1 lượt cho R', async () => {
    const b = bodyOf(await ev.api('GET', '/api/v1/conversations/current'))
    expect((b.messages as { client_request_id: string }[]).filter((m) => m.client_request_id === crid)).toHaveLength(1)
  })
})
