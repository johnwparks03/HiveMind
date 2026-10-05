import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Fixed origin: the local agent's CORS allowlist is hardcoded to this exact
  // origin (agent/app/config.py FRONTEND_ORIGIN), per CLAUDE.md.
  server: {
    port: 5173,
    strictPort: true,
  },
})
