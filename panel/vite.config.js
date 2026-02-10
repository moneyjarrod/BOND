import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api/doctrine': 'http://localhost:3000',
      '/api/config': 'http://localhost:3000',
      '/api/mcp': 'http://localhost:3000',
      '/api/modules': 'http://localhost:3000',
      '/api/state': 'http://localhost:3000',
      '/api/bindings': 'http://localhost:3000'
    }
  }
});
