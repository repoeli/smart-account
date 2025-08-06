import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // React and React DOM
          react: ['react', 'react-dom'],
          // Redux and state management
          redux: ['@reduxjs/toolkit', 'react-redux'],
          // Router
          router: ['react-router-dom'],
          // Form libraries
          forms: ['react-hook-form', '@hookform/resolvers', 'zod'],
          // UI components
          ui: ['@headlessui/react', '@heroicons/react', 'clsx'],
          // HTTP client
          http: ['axios'],
          // Utilities
          utils: ['react-hot-toast', 'react-dropzone', 'recharts'],
        },
      },
    },
    chunkSizeWarningLimit: 600,
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@reduxjs/toolkit',
      'react-redux',
      'axios',
      'react-hook-form',
      '@hookform/resolvers',
      'zod',
      '@headlessui/react',
      '@heroicons/react/24/outline',
      'clsx',
      'react-hot-toast',
    ],
  },
})
