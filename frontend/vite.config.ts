import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // 关闭代理缓冲，确保流式响应实时传递（SSE/streaming）
        configure: (proxy) => {
          proxy.on('proxyRes', (proxyRes) => {
            // 如果后端标记为流式响应，禁用缓冲
            if (proxyRes.headers['content-type']?.includes('text/plain')) {
              proxyRes.headers['X-Accel-Buffering'] = 'no'
              proxyRes.headers['Cache-Control'] = 'no-cache'
            }
          })
        }
      }
    }
  }
})
