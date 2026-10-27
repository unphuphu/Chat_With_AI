import { expect, test } from '../evidence/fixture'
import { ask, prep, Q_PAY } from './_h'

test('Năm câu hỏi liên tiếp', async ({ ev, page }) => {
  test.setTimeout(240_000)
  await ev.step('Đăng nhập Quản trị viên, tải hop-dong-A.pdf và chờ Sẵn sàng', 'Dòng Sẵn sàng', async () => prep(ev, 'admin', ['hop-dong-A.pdf']))
  await ev.step(`Hỏi "${Q_PAY}"`, 'Câu trả lời 1', async () => {
    await expect(await ask(page, Q_PAY)).toContainText('30 ngày')
  })
  const qs = ['Lãi chậm trả là bao nhiêu?', 'Hợp đồng có hiệu lực bao lâu?', 'Thời hạn bảo hành là bao lâu?', 'Giá trị hợp đồng là bao nhiêu?', 'Phạm vi hợp đồng là gì?']
  await ev.step('Hỏi tiếp 5 câu: lãi chậm trả; hiệu lực; bảo hành; giá trị; phạm vi', 'Mỗi câu có câu trả lời (hoặc Chưa đủ thông tin) ngay dưới câu hỏi', async () => {
    for (const q of qs) await ask(page, q)
    await expect(page.locator('article.a')).toHaveCount(6)
  })
  await ev.step('Cuộn hội thoại, chụp ảnh', '6 lượt đúng thứ tự gửi', async () => {
    const asked = await page.locator('.q').allInnerTexts()
    const order = [Q_PAY, ...qs]
    order.forEach((q, i) => expect(asked[i]).toContain(q))
    await expect(page.locator('#q')).toBeEnabled()
    return `Thứ tự ${asked.length} câu hỏi khớp thứ tự gửi`
  })
})
