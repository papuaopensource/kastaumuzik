import { defineConfig } from 'astro/config';

import alpinejs from "@astrojs/alpinejs";
import cloudflare from "@astrojs/cloudflare";
import tailwindcss from "@tailwindcss/vite";

// https://astro.build/config
export default defineConfig({
  site: "https://kastaumuzik.com",

  // Prerendered. The adapter is here for one route,
  // src/pages/api/submissions.ts, which opts out with `prerender = false`.
  output: "static",
  adapter: cloudflare(),

  integrations: [alpinejs({ entrypoint: "/src/alpine.ts" })],
  vite: {
    plugins: [tailwindcss()]
  }
});
