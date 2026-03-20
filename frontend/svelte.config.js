import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({
      fallback: 'index.html', // SPA mode: all routes fall back to index.html
    }),
    alias: {
      $components: 'src/components',
      $stores: 'src/lib/stores',
      $api: 'src/lib/api',
    },
  },
};

export default config;
