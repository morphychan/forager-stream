import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: {
      '/rss-articles': {
        target: 'http://192.168.41.31:8000',
        changeOrigin: true,
        // rewrite: path => path.replace(/^\/api/, '') // if there is a prefix, add it
      },
      '/rss-feeds': {
        target: 'http://192.168.41.31:8000',
        changeOrigin: true,
      }
    }
  }
})
