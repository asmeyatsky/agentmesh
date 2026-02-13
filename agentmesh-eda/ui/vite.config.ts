import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3001,
    host: true,
    open: true,
    cors: true,
    proxy: {
      // Proxy API requests to backend during development
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    target: 'es2015',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          agentMesh: [
            './src/components',
            './src/pages',
            './src/hooks',
            './src/services',
            './src/utils',
            './src/types',
            './src/state'
          ]
        }
      }
    }
  },
  optimize: {
    deps: {
      react: 'react',
      'react-dom': 'react-dom'
    }
  }
})