import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  // For GitHub Pages the app is served under /<repo>/; the deploy workflow sets VITE_BASE.
  // Defaults to '/' for local dev and root-hosted deploys (e.g. Vercel).
  base: process.env.VITE_BASE || '/',
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // Node.js server handles voice, text, and hazard detection on port 3001
      '/api/process-voice': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
      '/api/process-text': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
      '/api/hazard-detection': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
      '/api/hazard-images': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
      // RAG FastAPI serves /api/dashboard, /api/query, /api/ingest on port 8000
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
