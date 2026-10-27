import { expect, test } from '../evidence/fixture'
import { conversationId, newCrid, prep, Q_PAY } from './_h'

test('Request trùng đang chạy', async ({ ev, page }) => {
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf và chờ Sẵn sàng', 'Dòng Sẵn sàng', async () => prep(ev, 'p2', ['hop-dong-A.pdf']))
  await ev.step('Gửi đồng thời 6 POST cùng client_request_id R và cùng câu hỏi', 'Các phản hồi là 200 (cùng kết quả) hoặc 409 request_in_progress; không có lỗi khác', async () => {
    const conv = await conversationId(ev)
    const crid = newCrid()
    const csrf = (await page.context().cookies()).find((c) => c.name === 'csrf_token')!.value
    const rs = await Promise.all(
      Array.from({ length: 6 }, () =>
        page.request.post(`/api/v1/conversations/${conv}/messages`, {
          headers: { 'X-CSRF-Token': csrf },
          data: { client_request_id: crid, question: Q_PAY },
        }),
      ),
    )
    const codes = rs.map((r) => r.status())
    for (const c of codes) expect([200, 409]).toContain(c)
    expect(codes).toContain(200)
    const detail = await Promise.all(rs.map(async (r) => (r.status() === 409 ? ((await r.json()) as { code: string }).code : 'ANSWERED')))
    const msgs = ((await (await page.request.get('/api/v1/conversations/current')).json()) as { messages: { client_request_id: string }[] }).messages
    expect(msgs.filter((m) => m.client_request_id === crid)).toHaveLength(1)
    const got409 = codes.includes(409)
    ev.note(got409 ? 'Quan sát được 409 request_in_progress.' : 'Không quan sát được 409: bộ trả lời trích xuất quá nhanh; chỉ kiểm chứng được "mỗi R chỉ có 1 lượt" – xem ghi chú test case.')
    return `Mã trả về: ${codes.join(', ')} (${detail.join(', ')}); chỉ 1 lượt cho R`
  }, { review: false })
})
