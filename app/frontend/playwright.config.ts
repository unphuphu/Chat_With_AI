import { defineConfig } from '@playwright/test'

// Chạy trên môi trường dev đang chạy (python run.py --sample). Dùng Edge có sẵn – không tải trình duyệt.
export default defineConfig({
  testDir: 'e2e',
  timeout: 120_000,
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:8080',
    channel: 'msedge',
    locale: 'vi-VN',
    viewport: { width: 1440, height: 900 },
    screenshot: 'only-on-failure',
  },
  outputDir: process.env.E2E_OUT ?? 'test-results',
})
