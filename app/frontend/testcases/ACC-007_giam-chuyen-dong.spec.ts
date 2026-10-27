import { expect, test } from '../evidence/fixture'
import { prep, Q_PAY, upload, waitReady } from './_h'

test('Giảm chuyển động', async ({ ev, page }) => {
  const animName = (sel: string) => page.locator(sel).first().evaluate((el) => getComputedStyle(el).animationName)
  await ev.step('Đăng nhập P2; emulateMedia reducedMotion: reduce; tải file (làm chậm 3 s để thấy biểu tượng xoay)', 'Biểu tượng .spin có animation-name: none', async () => {
    await prep(ev, 'p2')
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.route('**/upload-batches/*/files/*', async (route) => {
      await new Promise((r) => setTimeout(r, 3000))
      await route.continue()
    })
    await upload(page, 'hop-dong-A.pdf')
    await expect(page.locator('.spin').first()).toBeVisible()
    const n = await animName('.spin')
    expect(n).toBe('none')
    await page.unroute('**/upload-batches/*/files/*')
    await waitReady(page, 'hop-dong-A.pdf')
    return `animation-name của .spin = ${n}`
  })
  await ev.step('Gửi câu hỏi (làm chậm 3 s)', 'Ba chấm .dots span không có animation', async () => {
    await page.route('**/messages', async (route) => {
      await new Promise((r) => setTimeout(r, 3000))
      await route.continue()
    })
    await page.locator('#q').fill(Q_PAY)
    await page.keyboard.press('Enter')
    await expect(page.locator('.dots span').first()).toBeVisible()
    const n = await animName('.dots span')
    expect(n).toBe('none')
    await page.unroute('**/messages')
    return `animation-name của .dots span = ${n}`
  })
  await ev.step('Đối chứng: tắt reduced-motion', 'Hoạt ảnh trở lại (animation-name ≠ none)', async () => {
    await page.emulateMedia({ reducedMotion: 'no-preference' })
    await page.locator('#q').fill('Lãi chậm trả là bao nhiêu?')
    await page.route('**/messages', async (route) => {
      await new Promise((r) => setTimeout(r, 3000))
      await route.continue()
    })
    await page.keyboard.press('Enter')
    await expect(page.locator('.dots span').first()).toBeVisible()
    const n = await animName('.dots span')
    expect(n).not.toBe('none')
    await page.unroute('**/messages')
    return `animation-name khi no-preference = ${n}`
  })
})
