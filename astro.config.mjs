// @ts-check
import { defineConfig } from "astro/config";
import react from "@astrojs/react";
import tailwindcss from "@tailwindcss/vite";
import cloudflare from "@astrojs/cloudflare";

export default defineConfig({
  site: "https://www.hsb-boden.de",
  output: "server",
  adapter: cloudflare(),
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
