import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      // Proxy API calls to the backend during development
      '/api': {
        target: 'http://backend:8080',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://backend:8080',
        changeOrigin: true,
      },
    },
  },
});
