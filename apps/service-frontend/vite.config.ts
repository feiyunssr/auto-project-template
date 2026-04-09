import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const appScheme = env.APP_SCHEME || 'http'
  const appHostIp = env.APP_HOST_IP || '192.168.1.242'
  const proxyTarget = env.VITE_DEV_PROXY_TARGET || `${appScheme}://${appHostIp}:11010`

  return {
    plugins: [vue()],
    server: {
      host: '0.0.0.0',
      port: 11011,
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
        },
        '/.well-known': {
          target: proxyTarget,
          changeOrigin: true,
        },
        '/healthz': {
          target: proxyTarget,
          changeOrigin: true,
        },
      },
    },
  }
})
