import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    host: true,
    port: 5173,
    // Bind mount từ Windows không phát sinh sự kiện inotify trong container,
    // nên bật polling để HMR nhận được thay đổi file.
    watch: { usePolling: true },
  },
})
