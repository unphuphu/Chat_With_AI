import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// SPA ở :8080, /api proxy tới FastAPI :8000 (cùng origin → cookie SameSite hoạt động như production)
export default defineConfig({
  plugins: [react()],
  server: {
    port: 8080,
    strictPort: true,
    proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: false } },
  },
  preview: { port: 8080, proxy: { '/api': 'http://127.0.0.1:8000' } },
})
