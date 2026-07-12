// @ts-check
import { defineConfig } from "astro/config";
import react from "@astrojs/react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  site: "https://www.hsb-boden.de",
  output: "static",
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
