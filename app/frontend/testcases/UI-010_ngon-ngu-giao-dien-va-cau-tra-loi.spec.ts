import { expect, test } from '../evidence/fixture'
import { ask, prep } from './_h'

test('Ngôn ngữ giao diện và câu trả lời', async ({ ev, page }) => {
  await ev.step('Đăng nhập P2, tải hop-dong-A.pdf; kiểm tra chữ trên giao diện', 'Toàn bộ tiếng Việt, đúng dấu', async () => {
    await prep(ev, 'p2', ['hop-dong-A.pdf'])
    const text = await page.locator('body').innerText()
    for (const s of ['Tài liệu', 'Hỏi đáp', 'Kéo thả file PDF vào đây', 'Đăng xuất', 'Sẵn sàng']) expect(text).toContain(s)
    expect(await page.locator('html').getAttribute('lang')).toBe('vi')
  })
  await ev.step('Hỏi "What is the payment term for party B?"', 'Có câu trả lời kèm nguồn hoặc "Chưa đủ thông tin"', async () => {
    const a = await ask(page, 'What is the payment term for party B?')
    const t = await a.innerText()
    expect(t).toMatch(/30 ngày|Chưa đủ thông tin/)
    return `Kết quả: ${t.replace(/\s+/g, ' ').slice(0, 160)}`
  })
  await ev.step('Với LLM thật: câu trả lời dùng đúng ngôn ngữ câu hỏi (NFR-016)', 'Trả lời bằng tiếng Anh', async () =>
    'Bộ trả lời trích xuất (offline) chỉ trích nguyên văn tiếng Việt, không dịch → NFR-016 "trả lời theo ngôn ngữ câu hỏi" chưa kiểm chứng được; cần LLM thật (LLM_PROVIDER=anthropic).', { review: true })
})
