import { expect, test } from '../evidence/fixture'
import { ask, bodyOf, prep, Q_PAY } from './_h'

type Msg = { question: string; status: string; citations: { document_name: string }[] }

test('Hội thoại hiện tại', async ({ ev, page }) => {
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf và chờ Sẵn sàng', 'Dòng Sẵn sàng', async () => prep(ev, 'p2', ['hop-dong-A.pdf']))
  await ev.step('Hỏi trên giao diện', 'Có câu trả lời', async () => {
    await ask(page, Q_PAY)
  })
  let convId = ''
  await ev.step('GET /conversations/current', '200; 1 lượt: question, status=ANSWERED, citations[0]=hop-dong-A.pdf', async () => {
    const b = bodyOf(await ev.api('GET', '/api/v1/conversations/current'))
    convId = b.id as string
    const m = (b.messages as Msg[])[0]
    expect(m).toMatchObject({ question: Q_PAY, status: 'ANSWERED' })
    expect(m.citations[0].document_name).toBe('hop-dong-A.pdf')
  })
  await ev.step('Tải lại trang rồi gọi lại', 'Cùng id hội thoại; vẫn 1 lượt', async () => {
    await page.bringToFront()
    await page.reload()
    await expect(page.locator('article.a')).toHaveCount(1)
    const b = bodyOf(await ev.api('GET', '/api/v1/conversations/current'))
    expect(b.id).toBe(convId)
    expect((b.messages as Msg[]).length).toBe(1)
  })
})
