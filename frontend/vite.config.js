import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: false,
    proxy: {
      // Proxy all backend routes to FastAPI backend on port 8000
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/microsoft365': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/slack': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
