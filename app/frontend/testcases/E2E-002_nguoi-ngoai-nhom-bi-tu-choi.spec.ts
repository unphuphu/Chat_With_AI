// Test case: doc/07-verification/test_cases/E2E-002_nguoi-ngoai-nhom-bi-tu-choi.md
import { expect, test } from '../evidence/fixture'

test('Người ngoài nhóm bị từ chối truy cập', async ({ ev, page }) => {
  await ev.step('Mở ứng dụng khi chưa đăng nhập', 'Chuyển tới trang chọn tài khoản của IdP', async () => {
    await page.goto('/')
    await expect(page.getByText('Chọn tài khoản để đăng nhập')).toBeVisible()
  })
  await ev.step('Chọn tài khoản "Người ngoài nhóm" (khach@congty.vn)', 'Trang "Bạn chưa được cấp quyền dùng ứng dụng"', async () => {
    await page.getByRole('button', { name: /Người ngoài nhóm/ }).click()
    await expect(page.getByRole('heading', { name: 'Bạn chưa được cấp quyền dùng ứng dụng' })).toBeVisible()
    return `URL: ${new URL(page.url()).pathname}`
  })
  await ev.step('Kiểm tra không lộ dữ liệu ứng dụng', 'Không có khu vực Tài liệu, ô hỏi; có nút "Đăng nhập lại"', async () => {
    await expect(page.getByRole('heading', { name: 'Tài liệu', exact: true })).toHaveCount(0)
    await expect(page.locator('#q')).toHaveCount(0)
    await expect(page.getByRole('link', { name: 'Đăng nhập lại' })).toBeVisible()
  })
  await ev.step('Gọi API /me trực tiếp', '401 – không có phiên', async () => {
    const r = await ev.api('GET', '/api/v1/me')
    expect(r.status).toBe(401)
    return `HTTP ${r.status}, code=${(r.body as { code?: string }).code}`
  })
})
