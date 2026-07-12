# Best-Practice-Source-Register — hsb-boden

Primärquellen vor Drittquellen; jede Eintragung mit Abrufdatum und Auswirkung.

| Datum | Quelle | Version/Stand | Kernaussage | Auswirkung |
|---|---|---|---|---|
| 2026-07-12 | `npx wrangler pages deploy --help` (installierte CLI 4.106.0) | 4.106.0 | Es existiert KEIN `--dry-run` für Pages-Deploys; Flags: `--project-name`, `--branch`, `--commit-dirty` | `deploy:dry-run` neu definiert als Build + `wrangler pages deployment list` (ehrliche Semantik) |
| 2026-07-12 | `wrangler pages project list` / `deployment list` (live) | Account `Info@hsb-boden.de` | Projekt `hsb-boden`, Production-Branch `main`, Custom Domain www | Bestätigt Pages als einzige Production-Wahrheit; Workers-Config entfernt |
| 2026-07-12 | GitHub REST (`gh api --paginate`) | live | Search-API und Erste-Seite-Abfragen sind KEIN vollständiges PR-Inventar | Inventar-Methode: paginierte REST + unabhängige Gegenprobe (52/52 konsistent) |
| 2026-07-12 | GitHub Rulesets API | live | Ruleset ersetzt klassische Branch Protection (Branch-Protection-API liefert 404 bei Ruleset-Nutzung) | Guardrail-Doku auf Ruleset umgestellt |
| 2026-07-12 | Codex-Plugin 1.0.6 (installierte Command-Dateien) | 1.0.6 | Verfügbare Kommandos: setup, review, adversarial-review, rescue, transfer, status, result, cancel; Runtime-Contract: Aufrufe nur via `codex:codex-rescue`-Subagent | Review-Ablauf entsprechend implementiert |

Regeln:
- Kein Snippet ungeprüft übernehmen; Syntax immer gegen installierte Version/`--help`/offizielle Referenz validieren.
- Bei Widerspruch gewinnt die Primärquelle (Anthropic, OpenAI, GitHub, Cloudflare, Google Search Central, Astro, W3C, Schema.org).
- Nur entscheidungsrelevante Recherche; jeder Eintrag muss eine Entscheidung oder Umsetzung speisen.
| 2026-07-12 | ai.google.dev/gemini-api/docs/coding-agents + blog.google (offiziell) | live | Gemini Docs MCP (`gemini-api-docs-mcp.dev`, Tool `search_documentation`) und Skills `google-gemini/gemini-skills` sind offiziell; Repo-Maintainer philschmid (Google DeepMind) | Herkunftsprüfung PASS; Registrierung DEFERRED: Endpoint liefert HTTP 429 (überlastet). Nativer Weg statt Fremd-npx: `claude mcp add --transport http gemini-api-docs https://gemini-api-docs-mcp.dev/mcp --scope project`. Skills-Klassifikation: gemini-api-dev/interactions/live = NOT_NEEDED (keine Gemini-API-Arbeit in hsb-boden) |
