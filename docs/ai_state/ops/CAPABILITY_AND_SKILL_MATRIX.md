# Capability- und Skill-Matrix — hsb-boden

Stand: 2026-07-12 (Fable-5-Session, Capability-Discovery read-only).
Nur Metadaten — keine Tokens, Secrets oder OAuth-Daten.

## Ausführungsumgebung

| Komponente | Wert | Status |
|---|---|---|
| Claude Code Modell | Fable 5 (`claude-fable-5`) | READY |
| Agent Teams | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` | READY |
| Codex CLI | 0.144.1, ChatGPT-Login | READY (Quota-abhängig) |
| Codex-Plugin (`openai-codex/codex`) | 1.0.6 — setup, review, adversarial-review, rescue, transfer, status, result, cancel | READY |
| Wrangler (projektlokal) | 4.106.0, Account `Info@hsb-boden.de` | READY |
| gh CLI | Accounts `cherinojoel-lang` (aktiv) + `HSBHexagon` | READY |

## Relevante Skills (Auswahl für dieses Projekt)

| Skill | Herkunft | Zweck / Trigger | Side Effects | Status |
|---|---|---|---|---|
| superpowers:* (worktrees, TDD, verification, plans, debugging) | Plugin superpowers 6.1.1 (offiziell) | Prozess-Gates im Implementierungsablauf | keine | READY |
| codex:rescue / codex:setup | Plugin openai-codex 1.0.6 (offiziell) | unabhängige Zweitmodell-Perspektive | Codex-API-Verbrauch | READY |
| commit / review / deploy (projekt-/userlokal) | User-Skills | Conventional Commits, Reviews, Deploy-Checkliste | keine | READY |
| seo-content-reviewer | projektlokal `.claude/agents/` | SEO-/Content-Review | keine | READY |
| hsb-digital-flyer-design-review | projektlokal `.claude/skills/` | Flyer-Design-Review | keine | READY, NOT_RELEVANT für Web-Track |
| claude-flow-/sparc-/swarm-Skills | claude-flow-Ökosystem | Schwarm-Orchestrierung | MCP-Abhängigkeit | NOT_RELEVANT (natives Agent-Teaming genügt; YAGNI) |

## MCP-Server (verbunden, Auswahl)

| Server | Zweck | Vertrauensniveau | Einsatz in diesem Projekt |
|---|---|---|---|
| plugin:github | PR-/Issue-API | offiziell | Inventare, Draft-PRs |
| plugin:cloudflare (api/bindings/observability/builds) | Cloudflare read/write | offiziell | read-only Audits; Mutationen gated |
| google-workspace-hsb-boden | GA4/GSC/Drive-Kontext | OAuth eingeschränkt | Growth-Track (Phase später) |
| claude-in-chrome / playwright / chrome-devtools | Browser-Verifikation | offiziell | UI-/A11y-/Lighthouse-Checks |
| notion, apify, computer-use | Dashboard / Scraping / Desktop | vorhanden | NOT_RELEVANT für aktuellen Scope |

## Fehlende / zu klärende Capabilities

| Bedarf | Klassifikation |
|---|---|
| Paginiertes PR-Inventar als wiederholbarer Ablauf | REUSE (gh api --paginate, dokumentiert in PR-Triage-Report) |
| Leadpfad-E2E-Verifikation | CREATE_PROJECT_LOCAL-Kandidat (Testmodus nötig → OWNER_GATE für synthetische Anfrage) |
| Secret-Scanning-Status-Prüfung | OWNER_GATE (Token ohne `security_events`-Scope, API 404) |
| Evidenzbasierter Completion-Gate | REUSE (superpowers:verification-before-completion) |
