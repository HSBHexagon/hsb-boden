// @ts-check
import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  site: "https://www.hsb-boden.de",
  output: "static",
  integrations: [],
  prefetch: {
    prefetchAll: true,
    defaultStrategy: "hover",
  },
  devToolbar: { enabled: false },
  server: {
    allowedHosts: true,
    host: true,
  },
  vite: {
    cacheDir: "node_modules/.cache/.vite",
    plugins: [tailwindcss()],
    optimizeDeps: {
      include: ["zod", "clsx", "tailwind-merge"],
    },
  },
});
