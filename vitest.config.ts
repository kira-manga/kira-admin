import { fileURLToPath } from 'node:url';

import { defineConfig } from 'vitest/config';

export default defineConfig({
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  test: {
    environmentOptions: {
      jsdom: { runScripts: 'outside-only', url: 'http://localhost:3100' },
    },
  },
});
