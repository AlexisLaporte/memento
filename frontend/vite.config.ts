import { fileURLToPath } from 'url'
import { dirname, resolve } from 'path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const __dirname = dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    allowedHosts: ['mento.local'],
    proxy: {
      '/auth': 'http://localhost:5002',
      '/api': 'http://localhost:5002',
      '^/[a-z0-9-]+/api/': {
        target: 'http://localhost:5002',
        changeOrigin: true,
      },
    },
  },
})
