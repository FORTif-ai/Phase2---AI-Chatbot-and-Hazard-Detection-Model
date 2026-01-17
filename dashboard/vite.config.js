import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // Dashboard API endpoints go to RAG API server (port 8000)
      '/api/dashboard': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Other API endpoints go to Node.js server (port 3001)
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
    },
  },
})
