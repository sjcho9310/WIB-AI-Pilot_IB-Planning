import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Firebase Studio (Cloud IDE) 호환 설정:
// - host 0.0.0.0: 컨테이너 외부 접근 허용
// - allowedHosts true: *.cloudworkstations.dev 같은 IDX 프록시 도메인 허용
// - hmr.clientPort 443: HMR WebSocket 이 HTTPS 프록시(443)로 연결되도록 강제
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: Number(process.env.PORT) || 5173,
    allowedHosts: true,
    hmr: {
      clientPort: 443,
    },
  },
})
