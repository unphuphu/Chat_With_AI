import path from 'node:path'
import { chromium, type Browser, type Page } from '@playwright/test'
import { expect, test } from '../evidence/fixture'
import { ask, Q_OUT, Q_PAY, row, waitReady } from './_h'

async function flow(page: Page, ev: { shot: (n: string, p?: Page) => Promise<string> }, tag: string) {
  await page.goto('http://localhost:8080/')
  await page.getByRole('button', { name: /Trần Minh/ }).click()
  await page.locator('.docs .empty, .docs li.row').first().waitFor()
  for (const d of await page.getByRole('button', { name: /^Xóa / }).all()) {
    await d.click()
    await page.getByRole('button', { name: 'Xóa tài liệu' }).click()
  }
  await page.locator('input[type=file]').setInputFiles('../sample-pdfs/hop-dong-A.pdf')
  await waitReady(page, 'hop-dong-A.pdf')
  await ask(page, Q_PAY)
  const a = page.locator('article.a').first() // ask() trả về locator .last() nên không dùng lại sau câu hỏi thứ hai
  await expect(a).toContainText('30 ngày')
  await expect(a.getByRole('button', { name: /hop-dong-A\.pdf · tr\.2/ })).toBeVisible()
  const b = await ask(page, Q_OUT)
  await expect(b).toContainText('Chưa đủ thông tin')
  await a.getByRole('button', { name: /Mở nguồn 1/ }).click()
  await expect(page.getByRole('dialog')).toContainText('trang 2')
  await page.waitForTimeout(2000)
  await ev.shot(`${tag}-trinh-xem`, page)
  await page.keyboard.press('Escape')
  await row(page, 'hop-dong-A.pdf').getByRole('button', { name: /^Xóa / }).click()
  await page.getByRole('button', { name: 'Xóa tài liệu' }).click()
  await expect(row(page, 'hop-dong-A.pdf')).toBeHidden()
}

test('Tương thích Chrome và Edge', async ({ ev }) => {
  test.setTimeout(300_000)
  const versions: string[] = []
  for (const [channel, label] of [['msedge', 'Edge'], ['chrome', 'Chrome']] as const) {
    await ev.step(`Chạy luồng chính trên ${label}`, 'Đăng nhập → tải → hỏi → xem nguồn → xóa đều đạt', async () => {
      let browser: Browser
      try {
        // tracesDir riêng cho mỗi trình duyệt: tránh xung đột thư mục trace tạm khi chạy 2 trình duyệt trong một test
        browser = await chromium.launch({ channel, tracesDir: path.join(process.env.TEMP ?? '/tmp', `pw-traces-${channel}-${Date.now()}`) })
      } catch (e) {
        return `BỊ CHẶN: không khởi chạy được ${label}: ${(e as Error).message.split('\n')[0]}`
      }
      const ctx = await browser.newContext({ locale: 'vi-VN', viewport: { width: 1440, height: 900 } })
      const page = await ctx.newPage()
      try {
        await flow(page, ev, label)
        versions.push(`${label} ${browser.version()}`)
        return `${label} ${browser.version()}: luồng chính đạt`
      } finally {
        await ctx.close()
        await browser.close()
      }
    })
  }
  ev.note(`Phiên bản trình duyệt đã kiểm: ${versions.join('; ') || '(không có)'}. NFR-017 yêu cầu 2 phiên bản mới nhất của mỗi trình duyệt – lần chạy này chỉ có 1 phiên bản mỗi loại.`)
})
