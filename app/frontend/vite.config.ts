import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'

// Tương đương `client_max_body_size` của reverse proxy ở production (BLUEPRINT T05-01): chặn body quá lớn ngay tại
// proxy và trả 413 problem+json. Nếu không có, proxy dev của Vite báo 500 rỗng khi API đóng kết nối sớm.
// 21 MB = MAX_FILE_MB (20) + 1 MB dư cho multipart; giữ khớp với BodySizeLimitMiddleware của API.
const MAX_BODY = 21 * 1024 * 1024
const bodyLimit = (): Plugin => ({
  name: 'api-body-limit',
  configureServer(server) {
    server.middlewares.use('/api', (req, res, next) => {
      if (Number(req.headers['content-length'] ?? 0) <= MAX_BODY) return next()
      req.resume() // đọc bỏ phần thân còn lại để client không gặp EPIPE
      req.on('end', () => {
        res.statusCode = 413
        res.setHeader('Content-Type', 'application/problem+json')
        res.setHeader('Connection', 'close')
        res.end(
          JSON.stringify({
            type: 'https://errors.aichat.local/too_large',
            title: 'File quá dung lượng',
            status: 413,
            code: 'too_large',
            detail: 'File vượt quá dung lượng cho phép.',
          }),
        )
      })
    })
  },
})

// SPA ở :8080, /api proxy tới FastAPI :8000 (cùng origin → cookie SameSite hoạt động như production)
export default defineConfig({
  plugins: [react(), bodyLimit()],
  server: {
    port: 8080,
    strictPort: true,
    proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: false } },
  },
  preview: { port: 8080, proxy: { '/api': 'http://127.0.0.1:8000' } },
})
