import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const internalApiKey = env.INTERNAL_API_KEY || ''

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      proxy: {
        '/api': {
          target: 'https://dehon-ai-backend.onrender.com',
          changeOrigin: true,
          secure: false,
          headers: {
            'Authorization': `Bearer ${internalApiKey}`
          }
        }
      }
    }
  }
})
