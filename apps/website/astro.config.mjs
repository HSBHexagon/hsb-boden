// @ts-check
import { defineConfig, fontProviders } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  site: "https://www.hsb-boden.de",
  output: "static",
  fonts: [
    {
      provider: fontProviders.fontsource(),
      name: "Outfit",
      cssVariable: "--font-outfit",
      styles: ["normal"],
      weights: ["100 900"],
      subsets: ["latin"],
      fallbacks: ["sans-serif"],
    },
  ],
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
