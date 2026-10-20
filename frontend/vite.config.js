import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // O frontend fala só com a API do Nox, nunca com a exchange (seção 18.2).
    proxy: { '/api': 'http://localhost:8000' },
  },
})
