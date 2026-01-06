import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0', // Allow external connections
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // Local backend
        changeOrigin: true,
        rewrite: (path) => {
          // Keep /api/portfolios/... as-is (new cockpit contract)
          if (path.startsWith('/api/portfolios')) {
            return path;
          }
          // Keep /api/tenants/... as-is (portfolios route)
          if (path.startsWith('/api/tenants/')) {
            return path;
          }
          // Rewrite /api/market/... to /v1/market/...
          if (path.startsWith('/api/market/')) {
            return path.replace(/^\/api/, '/v1');
          }
          // Rewrite /api/v1/... to /v1/... (audit routes)
          if (path.startsWith('/api/v1/')) {
            return path.replace(/^\/api/, '');
          }
          // Default: rewrite /api to /v1 for other routes
          return path.replace(/^\/api/, '/v1');
        },
      },
    },
  },
});
