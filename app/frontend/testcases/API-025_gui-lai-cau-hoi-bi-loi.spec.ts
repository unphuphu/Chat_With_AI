import { expect, test } from '../evidence/fixture'
import { ask$, bodyOf, conversationId, newCrid, prep, Q_PAY } from './_h'

type Msg = { client_request_id: string; status: string }

test('Gửi lại câu hỏi bị lỗi', async ({ ev }) => {
  test.setTimeout(420_000)
  const crid = newCrid()
  let conv = ''
  try {
    await ev.step('Tạo lượt FAILED: khởi động với LLM lỗi, tải tài liệu, hỏi (client_request_id = R)', 'Lượt hỏi FAILED (503)', async () => {
      await ev.restartApp({ LLM_PROVIDER: 'anthropic', LLM_API_KEY: 'sk-ant-invalid' })
      await prep(ev, 'p2', ['hop-dong-A.pdf'])
      conv = await conversationId(ev)
      const r = await ask$(ev, conv, Q_PAY, crid)
      expect(r.status).toBe(503)
    })
  } finally {
    await ev.step('Khởi động lại với LLM_PROVIDER=extractive; kiểm tra phiên còn hiệu lực', 'Ứng dụng sẵn sàng, /me = 200', async () => {
      await ev.restartApp()
      expect((await ev.api('GET', '/api/v1/me')).status).toBe(200)
    })
  }
  await ev.step('POST lại cùng R và cùng câu hỏi', '200 ANSWERED', async () => {
    const r = await ask$(ev, conv, Q_PAY, crid)
    expect(r.status).toBe(200)
    expect(bodyOf(r).status).toBe('ANSWERED')
  })
  await ev.step('GET /conversations/current', 'Chỉ 1 lượt cho R, status=ANSWERED (không tạo lượt mới)', async () => {
    const msgs = bodyOf(await ev.api('GET', '/api/v1/conversations/current')).messages as Msg[]
    const mine = msgs.filter((m) => m.client_request_id === crid)
    expect(mine).toHaveLength(1)
    expect(mine[0].status).toBe('ANSWERED')
    expect(msgs).toHaveLength(1)
  })
})
