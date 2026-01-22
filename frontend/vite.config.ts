/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { storybookTest } from '@storybook/addon-vitest/vitest-plugin';
import { playwright } from '@vitest/browser-playwright';
const dirname = typeof __dirname !== 'undefined' ? __dirname : path.dirname(fileURLToPath(import.meta.url));

// More info at: https://storybook.js.org/docs/next/writing-tests/integrations/vitest-addon
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: path => {
          // Keep /api/portfolios/... as-is (new cockpit contract)
          if (path.startsWith('/api/portfolios')) return path;

          // Keep /api/tenants/... as-is (portfolios route)
          if (path.startsWith('/api/tenants/')) return path;

          // Rewrite /api/market/... to /v1/market/...
          if (path.startsWith('/api/market/')) return path.replace(/^\/api/, '/v1');

          // Rewrite /api/v1/... to /v1/...
          if (path.startsWith('/api/v1/')) return path.replace(/^\/api/, '');

          // Default: rewrite /api to /v1 for other routes
          return path.replace(/^\/api/, '/v1');
        }
      },
      // Optional: allow calling backend directly in dev
      '/v1': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  },
  test: {
    projects: [{
      extends: true,
      plugins: [
      // The plugin will run tests for the stories defined in your Storybook config
      // See options at: https://storybook.js.org/docs/next/writing-tests/integrations/vitest-addon#storybooktest
      storybookTest({
        configDir: path.join(dirname, '.storybook')
      })],
      test: {
        name: 'storybook',
        browser: {
          enabled: true,
          headless: true,
          provider: playwright({}),
          instances: [{
            browser: 'chromium'
          }]
        },
        setupFiles: ['.storybook/vitest.setup.ts']
      }
    }]
  }
});