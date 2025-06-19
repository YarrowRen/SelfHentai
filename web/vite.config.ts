import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  server: {
    host: '0.0.0.0', // 监听所有网络接口
    port: 5173,      // 保持端口不变
  },
  plugins: [vue()],
})
