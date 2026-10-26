import { expect, test, type Page } from '@playwright/test'
import path from 'node:path'

const SAMPLES = path.resolve(process.cwd(), '../sample-pdfs') // chạy từ app/frontend
const SHOTS = process.env.E2E_OUT ?? 'test-results'

async function login(page: Page, user: string) {
  await page.goto('/')
  await page.getByRole('button', { name: new RegExp(user) }).first().click() // trang chọn người dùng của devidp
  await expect(page.getByRole('heading', { name: 'Tài liệu', exact: true })).toBeVisible()
}

test('tải PDF → Sẵn sàng → hỏi → mở nguồn → xóa', async ({ page }) => {
  await login(page, 'minh.tran')
  // Dọn tài liệu cũ của lần chạy trước (chờ danh sách tải xong)
  await page.locator('.docs .empty, .docs li.row').first().waitFor()
  while (await page.getByRole('button', { name: /^Xóa / }).count()) {
    await page.getByRole('button', { name: /^Xóa / }).first().click()
    await page.getByRole('button', { name: 'Xóa tài liệu' }).click()
    await expect(page.getByRole('alertdialog')).toBeHidden()
  }
  await expect(page.getByText('Chưa có tài liệu nào')).toBeVisible()
  await expect(page.locator('#q')).toBeDisabled()
  await expect(page.locator('.counter')).toHaveText('0/2.000')

  await page.locator('input[type=file]').setInputFiles([
    path.join(SAMPLES, 'hop-dong-A.pdf'),
    path.join(SAMPLES, 'ho-so-scan-2019.pdf'),
    path.join(SAMPLES, 'bao-gia.docx'),
  ])
  await expect(page.getByText('không phải file PDF hợp lệ')).toBeVisible()
  const row = page.locator('li.row', { hasText: 'hop-dong-A.pdf' })
  await expect(row.getByText('Sẵn sàng')).toBeVisible({ timeout: 60_000 })
  await expect(page.locator('li.row', { hasText: 'ho-so-scan-2019.pdf' }).getByText('PDF scan')).toBeVisible({
    timeout: 60_000,
  })
  await page.screenshot({ path: `${SHOTS}/01-documents.png` })

  await page.locator('#q').fill('Bên B thanh toán trong vòng bao nhiêu ngày?')
  await page.keyboard.press('Enter')
  const answer = page.getByRole('article', { name: 'Câu trả lời', exact: true }).first()
  await expect(answer).toContainText('30 ngày', { timeout: 30_000 })
  const chip = answer.getByRole('button', { name: /Mở nguồn 1: hop-dong-A\.pdf · tr\.2/ })
  await expect(chip).toBeVisible()

  await page.locator('#q').fill('Đối thủ cạnh tranh tại thị trường Nhật Bản là ai?')
  await page.getByRole('button', { name: 'Gửi' }).click()
  await expect(page.getByText('Chưa đủ thông tin')).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: `${SHOTS}/02-chat.png` })

  await chip.click()
  const viewer = page.getByRole('dialog')
  await expect(viewer).toContainText('trang 2')
  const fileResp = await page.request.get(await viewer.locator('iframe').getAttribute('src').then((s) => s!.split('#')[0]))
  expect(fileResp.headers()['content-type']).toBe('application/pdf')
  await page.waitForTimeout(1500)
  await page.screenshot({ path: `${SHOTS}/03-viewer.png` })
  await page.keyboard.press('Escape')
  await expect(viewer).toBeHidden()

  await row.getByRole('button', { name: 'Xóa hop-dong-A.pdf' }).click()
  await expect(page.getByRole('alertdialog')).toContainText('không còn được dùng để trả lời')
  await page.getByRole('button', { name: 'Xóa tài liệu' }).click()
  await expect(row).toBeHidden()
  await expect(answer.getByText('(đã xóa)')).toBeVisible({ timeout: 10_000 })
  await page.screenshot({ path: `${SHOTS}/04-deleted.png` })
})

test('người ngoài nhóm thấy trang chưa được cấp quyền', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: /khach/ }).first().click()
  await expect(page.getByRole('heading', { name: 'Bạn chưa được cấp quyền dùng ứng dụng' })).toBeVisible()
})
