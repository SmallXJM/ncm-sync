import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
// import vueDevTools from 'vite-plugin-vue-devtools'

const backendProxy = {
  '/api': {
    target: 'http://localhost:17666',
    changeOrigin: true,
    secure: false,
  },
  '/ncm': {
    target: 'http://localhost:17666',
    changeOrigin: true,
    secure: false,
  },
  '/local': {
    target: 'http://localhost:17666',
    changeOrigin: true,
    secure: false,
  },
  '/ws': {
    target: 'ws://localhost:17666',
    changeOrigin: true,
    ws: true,
  },
}

// https://vite.dev/config/
export default defineConfig({
  base: '/',
  plugins: [
    vue(),
    // vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    proxy: backendProxy,
  },
  preview: {
    proxy: backendProxy,
  },
})
