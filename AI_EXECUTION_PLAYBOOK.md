# AI_EXECUTION_PLAYBOOK — HSB-Boden / HEXAFLOOR

> Wie KI-Systeme an diesem Projekt zusammenarbeiten. Stand: 2026-06-17.

## Ziel
Die Website als Premium-Vertrauensanker **und** Akquise-System für organische B2B-Leads (Industrieboden/Sanierung). Parallele Astro/Cloudflare-Lösung neben der bestehenden WordPress-Live-Site, bis zur finalen Freigabe.

## Wahrheits- und Plattform-Grundsätze
- **Cloudflare** bleibt Hauptplattform (Workers Preview = Staging, Production später).
- **GitHub** (`cherinojoel-lang/hsb-boden`) bleibt Code-Wahrheit.
- **Obsidian/brain** (`~/KI-System/ObsidianVault/brain`) bleibt Memory-/Handoff-Wahrheit.
- Kanonischer HSB-Repo-Pfad kommt **ausschließlich** aus `~/KI-System/08_System/config/canonical-projects.json`.
- Keine Plattformwechsel ohne dokumentierten Nutzen.
- Keine Secrets in Code/Frontend. Kein Push/Deploy ohne Freigabe.

## Rollen
- **Claude Code** — Inventur, Umsetzung, kontrollierte Dateiarbeit.
- **Codex** — Review / Zweitprüfung.
- **ChatGPT** — Steuerung / QA / Prompts.
- **Gemini** — Deep Research / PDF-Gegenprüfung.
- **Perplexity** — Quellen / SEO / Semrush / Wettbewerber.
- **n8n** — Automationsschicht (Lead-Intake, Follow-up, Reports).
- **Google Sheets** — CRM-Light Start.
- **Google Cloud** — nur minimal für API/OAuth (Sheets/Drive), siehe `GOOGLE_API_SETUP.md`.

## Standard-Loop
1. `handoff.sh read` + Registry + `assert_canonical_project_path.sh hsb-boden`.
2. Aufgabe gegen `PROJECT_TRUTH.md` einordnen.
3. Umsetzen mit Verifikations-Gate (`AGENTS.md` Deploy Gate).
4. `brain/CURRENT_HANDOFF.md` + `handoff.sh write` aktualisieren.

## Verweise
- `PROJECT_TRUTH.md`, `SEO_GO_LIVE_CHECKLIST.md`, `CRM_LIGHT_SCHEMA.md`, `N8N_AUTOMATION_PLAN.md`, `CLOUDFLARE_AI_GATEWAY_PLAN.md`, `GOOGLE_API_SETUP.md`, `ACQUISITION_SYSTEM_PLAN.md`.

## Update 2026-06-17 — Gemini-Depriorisierung
Gemini Account 1/2 bleiben ergänzend für Deep Research und Gegenprüfung. Gemini CLI und Gemini Code Assist sind wegen Nutzerbeobachtung langsam/nicht zuverlässig und wegen Googles angekündigtem Stopp für Individuals/Google AI Pro/Ultra ab 2026-06-18 nicht mehr Teil des operativen kritischen Pfads. Siehe `docs/ops/AI_TOOL_STACK.md`, `docs/ops/AI_MODEL_ROUTING.md`, `docs/ops/GEMINI_DEEP_RESEARCH_TASKS.md` und `docs/ops/GEMINI_CODE_ASSIST_SETUP.md`.
