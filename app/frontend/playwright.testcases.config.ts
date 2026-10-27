import { defineConfig } from '@playwright/test'

// Chạy spec của từng test case (doc/07-verification/test_cases) trên ứng dụng tại http://localhost:8080/.
// Bằng chứng (video, ảnh, report.md) do evidence/fixture.ts ghi vào ./test_reports/<tên test case>/.
//   npx playwright test -c playwright.testcases.config.ts <tên test case>
export default defineConfig({
  testDir: 'testcases',
  timeout: 180_000,
  workers: 1, // CSDL dev (PGlite) chỉ nhận một kết nối; các test case dùng chung tài khoản mẫu
  reporter: [['list']],
  outputDir: '../../test_reports/_playwright-output',
  use: {
    baseURL: process.env.APP_URL ?? 'http://localhost:8080/',
    channel: 'msedge',
    locale: 'vi-VN',
    viewport: { width: 1440, height: 900 },
    video: { mode: 'on', size: { width: 1440, height: 900 } },
    trace: 'retain-on-failure',
    actionTimeout: 30_000, // không chờ vô hạn một thao tác (click/fill…) khi phần tử không xuất hiện
    navigationTimeout: 60_000,
  },
})
