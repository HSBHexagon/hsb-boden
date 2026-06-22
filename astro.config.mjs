// @ts-check
import { defineConfig } from "astro/config";
import cloudflare from "@astrojs/cloudflare";
import react from "@astrojs/react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  site: "https://hsb-boden.de",
  output: "server",
  adapter: cloudflare({
    imageService: "passthrough",
  }),
  integrations: [react()],
  devToolbar: { enabled: false },
  server: {
    allowedHosts: true,
    host: true,
  },
  vite: {
    cacheDir: "node_modules/.cache/.vite",
    plugins: [tailwindcss()],
    optimizeDeps: {
      include: ["react", "react-dom", "zod", "clsx", "tailwind-merge", "lucide-react"],
    },
  },
});
