import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      "cloudflare:workers": fileURLToPath(
        new URL("./tests/__mocks__/cloudflare-workers.ts", import.meta.url),
      ),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    // Lokale git-worktrees liegen innerhalb des Repos (.worktrees/, .claude/worktrees/)
    // und sind gitignored. Ohne diesen Ausschluss sammelt Vitest deren veraltete
    // Testdateien mit ein: der Lauf ist dann weder deterministisch noch aussagekraeftig
    // fuer den aktuellen Stand. CI klont frisch und ist davon nicht betroffen.
    exclude: [
      "**/node_modules/**",
      "**/dist/**",
      "**/.worktrees/**",
      "**/.claude/worktrees/**",
    ],
  },
});
