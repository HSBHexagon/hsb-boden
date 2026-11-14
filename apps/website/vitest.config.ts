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
    // Ab Node 25 existiert ein globales localStorage (Web Storage), das ohne
    // --localstorage-file undefined liefert und das jsdom-localStorage verdeckt.
    // Abschalten, damit lokale Läufe mit neuem Node wie CI (Node 22) verhalten.
    // Node 20 kennt das Flag nicht und bricht sonst ab.
    execArgv:
      Number(process.versions.node.split(".")[0]) >= 25
        ? ["--no-experimental-webstorage"]
        : [],
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
