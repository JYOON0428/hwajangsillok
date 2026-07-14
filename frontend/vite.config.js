import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  // 정적 서버와 Netlify 모두에서 assets 경로가 안전하게 동작하도록 상대 경로 사용
  base: './',
  server: {
    port: 5173,
  },
})
