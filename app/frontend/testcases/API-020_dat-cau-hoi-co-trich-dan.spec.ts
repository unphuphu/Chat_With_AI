import { expect, test } from '../evidence/fixture'
import { ask$, bodyOf, conversationId, prep, Q_PAY } from './_h'

test('Đặt câu hỏi có trích dẫn', async ({ ev }) => {
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf và chờ Sẵn sàng', 'Dòng Sẵn sàng', async () => prep(ev, 'p2', ['hop-dong-A.pdf']))
  let ans: Record<string, unknown> = {}
  await ev.step('POST /conversations/{id}/messages', '200; ANSWERED; answer chứa "30 ngày" và [1]', async () => {
    const r = await ask$(ev, await conversationId(ev), Q_PAY)
    ans = bodyOf(r)
    expect(r.status).toBe(200)
    expect(ans.status).toBe('ANSWERED')
    expect(String(ans.answer)).toContain('30 ngày')
    expect(String(ans.answer)).toContain('[1]')
  })
  await ev.step('Đối chiếu citations', 'citations[0]: ordinal=1, hop-dong-A.pdf, page_number=2, deleted=false', async () => {
    expect((ans.citations as unknown[])[0]).toMatchObject({ ordinal: 1, document_name: 'hop-dong-A.pdf', page_number: 2, deleted: false })
  })
  await ev.step('Đối chiếu latency_ms', '> 0 và ≤ 15000', async () => {
    expect(ans.latency_ms as number).toBeGreaterThan(0)
    expect(ans.latency_ms as number).toBeLessThanOrEqual(15000)
    return `latency_ms=${ans.latency_ms}`
  })
})
