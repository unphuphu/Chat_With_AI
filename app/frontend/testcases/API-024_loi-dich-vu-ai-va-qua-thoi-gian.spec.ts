import { expect, test } from '../evidence/fixture'
import { ask$, bodyOf, conversationId, prep, py, Q_PAY } from './_h'

test('Lỗi dịch vụ AI và quá thời gian', async ({ ev }) => {
  test.setTimeout(420_000)
  try {
    await ev.step('Khởi động lại với LLM_PROVIDER=anthropic và LLM_API_KEY không hợp lệ', 'Ứng dụng sẵn sàng', async () => {
      await ev.restartApp({ LLM_PROVIDER: 'anthropic', LLM_API_KEY: 'sk-ant-invalid' })
    })
    await ev.step('Đăng nhập P2, tải hop-dong-A.pdf và chờ Sẵn sàng', 'Dòng Sẵn sàng', async () => prep(ev, 'p2', ['hop-dong-A.pdf']))
    let conv = ''
    await ev.step('POST câu hỏi', '503 ai_unavailable kèm header Retry-After', async () => {
      conv = await conversationId(ev)
      const r = await ask$(ev, conv, Q_PAY)
      expect(r.status).toBe(503)
      expect(bodyOf(r).code).toBe('ai_unavailable')
      expect(Number(r.headers['retry-after'])).toBeGreaterThan(0)
      return `HTTP 503 ai_unavailable, Retry-After=${r.headers['retry-after']}`
    })
    await ev.step('GET /conversations/current', 'Lượt hỏi có status=FAILED, error_code=ai_unavailable', async () => {
      const b = bodyOf(await ev.api('GET', '/api/v1/conversations/current'))
      expect((b.messages as unknown[])[0]).toMatchObject({ status: 'FAILED', error_code: 'ai_unavailable' })
    })
    await ev.step('(504) Chạy test tự động test_ai_timeout (LLM chậm hơn ngân sách thời gian)', 'pytest: 1 passed → API trả 504 ai_timeout', async () => {
      const out = py(['-m', 'pytest', 'tests/integration/test_qa.py::test_ai_timeout', '-q', '-p', 'no:cacheprovider'])
      expect(out).toContain('1 passed')
      ev.note(`504 ai_timeout kiểm bằng pytest: ${out.trim().split('\n').pop()}`)
      return out.trim().split('\n').pop()
    })
  } finally {
    await ev.restartApp()
  }
})
