// Chụp ảnh minh họa cho guide/HUONG_DAN_SU_DUNG.md. Chỉ chạy khi đặt GUIDE_OUT:
//   GUIDE_OUT=../../guide/images npx playwright test guide-screenshots
import { expect, test, type Page } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

const OUT = process.env.GUIDE_OUT
const SAMPLES = path.resolve(process.cwd(), '../sample-pdfs')
const pdf = (n: string) => path.join(SAMPLES, n)

test.skip(!OUT, 'Đặt GUIDE_OUT để chụp ảnh hướng dẫn')
test.describe.configure({ mode: 'serial' })

const shot = (page: Page, name: string) => page.screenshot({ path: path.join(OUT!, name) })

async function login(page: Page, user: RegExp) {
  await page.goto('/')
  await page.getByRole('button', { name: user }).first().click()
  await page.locator('.docs .empty, .docs li.row').first().waitFor()
}

async function clearDocs(page: Page) {
  while (await page.getByRole('button', { name: /^Xóa / }).count()) {
    await page.getByRole('button', { name: /^Xóa / }).first().click()
    await page.getByRole('button', { name: 'Xóa tài liệu' }).click()
    await expect(page.getByRole('alertdialog')).toBeHidden()
  }
}

async function ask(page: Page, q: string) {
  const n = await page.locator('article.a').count()
  await page.locator('#q').fill(q)
  await page.keyboard.press('Enter')
  await expect(page.locator('article.a')).toHaveCount(n + 1)
  await expect(page.locator('article.a').last()).not.toHaveAttribute('aria-busy', 'true', { timeout: 30_000 })
}

test('ảnh hướng dẫn', async ({ page }) => {
  fs.mkdirSync(OUT!, { recursive: true })

  // 1. Trang đăng nhập
  await page.goto('/')
  await expect(page.getByText('Chọn tài khoản để đăng nhập')).toBeVisible()
  await shot(page, '01-dang-nhap.png')
  await page.getByRole('button', { name: /Nguyễn Lan/ }).click()
  await page.locator('.docs .empty, .docs li.row').first().waitFor()
  await clearDocs(page)
  await page.reload()
  await page.locator('.docs .empty').first().waitFor()
  await page.waitForTimeout(500)

  // 2. Màn hình chính khi chưa có tài liệu
  await shot(page, '02-man-hinh-chinh-trong.png')

  // 3. Tải lên – bắt khoảnh khắc đang tải/đang xử lý
  await page.locator('input[type=file]').setInputFiles([
    pdf('hop-dong-A.pdf'),
    pdf('chinh-sach-ban-hang-2026.pdf'),
    pdf('bang-gia-Q4.pdf'),
  ])
  await expect(page.locator('.status.st-processing, .status.st-uploading').first()).toBeVisible()
  await shot(page, '03-dang-tai-len-va-xu-ly.png')
  for (const n of ['hop-dong-A.pdf', 'chinh-sach-ban-hang-2026.pdf', 'bang-gia-Q4.pdf']) {
    await expect(page.locator('li.row', { hasText: n }).getByText('Sẵn sàng')).toBeVisible({ timeout: 60_000 })
  }

  // 4. File bị từ chối / xử lý thất bại
  await page.locator('input[type=file]').setInputFiles([
    pdf('ho-so-scan-2019.pdf'),
    pdf('hop-dong-mat-khau.pdf'),
    pdf('bao-gia.docx'),
  ])
  await expect(page.locator('li.row', { hasText: 'ho-so-scan-2019.pdf' }).getByText('Thất bại')).toBeVisible({
    timeout: 60_000,
  })
  await expect(page.locator('li.row', { hasText: 'hop-dong-mat-khau.pdf' }).getByText('Không nhận')).toBeVisible()
  await page.waitForTimeout(5500) // chờ thông báo góc dưới tự ẩn
  await page.locator('.docs').screenshot({ path: path.join(OUT!, '04b-khu-vuc-tai-lieu.png') })

  // 5. Hỏi đáp
  await ask(page, 'Bên B thanh toán trong vòng bao nhiêu ngày?')
  await ask(page, 'Giá gói Premium là bao nhiêu?')
  await ask(page, 'Đối thủ cạnh tranh tại thị trường Nhật Bản là ai?')
  await page.locator('#q').fill('Hợp đồng có hiệu lực bao lâu?')
  await shot(page, '05-hoi-dap.png')
  await page.locator('article.a').first().screenshot({ path: path.join(OUT!, '05b-cau-tra-loi-co-nguon.png') })
  await page.locator('article.a').nth(1).screenshot({ path: path.join(OUT!, '05c-nhieu-tai-lieu.png') })
  await page.locator('article.a.insufficient').screenshot({ path: path.join(OUT!, '05d-chua-du-thong-tin.png') })
  await page.locator('#q').fill('')

  // 6. Xem tài liệu gốc tại trang được trích dẫn
  await page.locator('article.a').first().getByRole('button', { name: /Mở nguồn 1/ }).click()
  await expect(page.getByRole('dialog')).toContainText('trang 2')
  await page.waitForTimeout(2500)
  await shot(page, '06-xem-tai-lieu-goc.png')
  await page.keyboard.press('Escape')

  // 7. Vượt giới hạn số file mỗi lần
  const many = Array.from({ length: 12 }, (_, i) => ({
    name: `tai-lieu-${i + 1}.pdf`,
    mimeType: 'application/pdf',
    buffer: Buffer.from('%PDF-1.4'),
  }))
  await page.locator('input[type=file]').setInputFiles(many)
  await expect(page.getByText('Chưa có file nào được tải lên.')).toBeVisible()
  await page.locator('.docs').screenshot({ path: path.join(OUT!, '07-vuot-gioi-han-so-file.png') })

  // 8. Xóa tài liệu
  const row = page.locator('li.row', { hasText: 'hop-dong-A.pdf' })
  await row.getByRole('button', { name: 'Xóa hop-dong-A.pdf' }).click()
  await expect(page.getByRole('alertdialog')).toBeVisible()
  await shot(page, '08-xac-nhan-xoa.png')
  await page.getByRole('button', { name: 'Xóa tài liệu' }).click()
  await expect(row).toBeHidden()
  await expect(page.locator('article.a').first().getByText('(đã xóa)')).toBeVisible({ timeout: 10_000 })
  await page.locator('article.a').first().screenshot({ path: path.join(OUT!, '09-nguon-da-xoa.png') })

  // 10. Đăng xuất
  await page.getByRole('button', { name: 'Đăng xuất' }).click()
  await expect(page.getByText('Chọn tài khoản để đăng nhập')).toBeVisible()
})

test('ảnh: chưa được cấp quyền', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: /Người ngoài nhóm/ }).click()
  await expect(page.getByRole('heading', { name: 'Bạn chưa được cấp quyền dùng ứng dụng' })).toBeVisible()
  await shot(page, '10-chua-duoc-cap-quyen.png')
})

test('ảnh: phiên hết hạn', async ({ page }) => {
  await page.route('**/api/v1/auth/login**', (r) => r.abort()) // giữ trang, không tự chuyển
  await page.goto('/session-expired')
  await expect(page.getByRole('heading', { name: 'Phiên làm việc đã hết hạn' })).toBeVisible()
  await shot(page, '11-phien-het-han.png')
})
