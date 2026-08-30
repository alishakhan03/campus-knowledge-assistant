import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite 4.x is intentionally used here (not Vite 5+) because Vite 5 requires
// Node 18+, and this project targets Node 16 for macOS High Sierra compatibility.
export default defineConfig({
  plugins: [react()],
  server: {
    host: 'localhost', // pin to 'localhost' explicitly so it always matches
    port: 5173,          // FRONTEND_URL in backend/.env exactly - Vite otherwise
  },                      // sometimes binds/reports 127.0.0.1 instead, which
                          // browsers treat as a different CORS origin.
})
