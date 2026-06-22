# MASTER_EXECUTION_RULES — HSB / HEXAFLOOR

## 1. Zweck
Zentrale Arbeitssteuerung für alle KI-Systeme im Projekt HSB / HEXAFLOOR. Jedes KI-System muss diese Datei vor jeder Arbeit lesen.

Ziel:
- Website als Premium-Vertrauensanker
- Flyer-/Outreach-System
- CRM-Light
- n8n-Automation
- Lead-Pipeline
- Cloudflare-Go-live erst nach Freigabe
- kein Neustart von vorne bei jedem Modellwechsel

## 1a. Garantie-Struktur
Kein KI-System darf ohne diese Dateien arbeiten:
1. `MASTER_EXECUTION_RULES.md`
2. `SKILLS_MASTER_PROMPT.md`
3. `PHASED_EXECUTION_PLAN.md`
4. `PROJECT_TRUTH.md`
5. `AI_EXECUTION_PLAYBOOK.md`
6. `CURRENT_HANDOFF.md`
7. `CHECKPOINT_STATE.json`

Start-/Stop-/Crash-Verhalten: siehe `STARTUP_PROTOCOL.md`, `STOP_PROTOCOL.md`, `CRASH_RECOVERY_PROTOCOL.md`. Fortlaufendes Log: `SESSION_LOG.md`. Rollen: `AI_SYSTEM_ROLES.md`.

## 2. Kanonische Pfade
System Root: `~/KI-System`

Kanonischer HSB-Repo-Pfad ausschließlich über Registry:
`~/KI-System/08_System/config/canonical-projects.json`

Pfadprüfung vor jeder Arbeit:
`~/KI-System/08_System/scripts/assert_canonical_project_path.sh hsb-boden`

Memory/Handoff:
`~/KI-System/ObsidianVault/brain/CURRENT_HANDOFF.md`

Verbotene Pfade:
- Backup-Pfade
- Rohimporte
- leerer `brain/03_projects/hexafloor`
- `/Users/joelcherinodiaz/Projects/hsb-boden`
- nicht validierte Suchtreffer aus `find`

## 3. Wahrheitshierarchie
1. `MASTER_EXECUTION_RULES.md`
2. `PROJECT_TRUTH.md`
3. `AI_EXECUTION_PLAYBOOK.md`
4. `~/KI-System/ObsidianVault/brain/CURRENT_HANDOFF.md`
5. aktuelle Git-Checks
6. Reports unter `~/KI-System/08_System/reports/validation/`

Bei Widerspruch: STOP. Keine eigenmächtige Strukturentscheidung.

## 4. Rollen der Systeme

| System | Rolle | Darf | Darf nicht |
|--------|-------|------|------------|
| ChatGPT | Obersteuerung, QA, Prompt-Orchestrierung | nächste Prompts, Entscheidungen, Ablaufsteuerung | lokale Dateien direkt ändern |
| Claude Code | Inventur und Umsetzung nach Freigabe | Dateien ändern, wenn freigegeben | Push/Deploy ohne Freigabe |
| Codex | Review, Zweitprüfung, technische Planung | prüfen, Doku erstellen, sichere Checks | eigenmächtig Live-Betrieb starten |
| Gemini | Deep Research, PDF-/Quellen-Gegenprüfung | Recherche, Analyse, Gegenprüfung | Repo eigenmächtig ändern |
| Perplexity | Quellen, SEO, Semrush, Wettbewerber | externe Recherche, Validierung | lokale Wahrheit ersetzen |
| n8n | Automationsschicht | Workflows nach Freigabe | ohne Freigabe live gehen |
| Google Sheets | CRM-Light Start | Lead-Daten nach Freigabe aufnehmen | Secrets im Repo speichern |
| Google Cloud | API-/OAuth-Hilfsprojekt | minimale APIs bereitstellen | Hauptplattform werden |
| Cloudflare | Website-/Workers-Hauptplattform | Preview/Staging, später Production nach Freigabe | Production-Cutover ohne Freigabe |

## 5. Aktueller Projektstand
- Flyer-Assets committed: `9ac994a75b71d3ccfe1a4b204c12d1c98fc3efcc`
- Plan-Dateien committed: `3308d91`
- Doku-Konsistenzfix committed: `9f1d211877027b8edc8030720bb3f56631742681`
- P0A Lead-Pipeline-Plan committed: `7c38d7ba8f3e6cc9d38ae23c30e7ec1c27d9a24a`
- P0A Review: bestanden
- P0B-Freigabe empfohlen: ja, mit Auflagen
- Website-Code-Diff: 0
- Push: nein
- Deploy: nein
- `.astro/data-store.json`: bleibt uncommitted

## 6. Aktuelle Phase
**P0B-FREIGABE VORBEREITEN**

Noch nicht erlaubt:
- Endpoint-Code schreiben
- n8n live schalten
- Google Sheets live anbinden
- Push
- Deploy
- Production-Cutover

## 7. P0B-Auflagen aus Review
P0B darf nur starten, wenn zuerst beachtet:
1. `PUBLIC_LEAD_ENDPOINT_SPEC.md` Feldliste an reales Formular angleichen: `firstName`, `lastName`, `privacyConsent`, `areaSize`, `industry`, `projectType`, `loads`, `liveOperation`, `description`.
2. Endpoint-n8n-Mapping gegen vorhandenen Workflow abgleichen: `ops/n8n/hsb-boden-lead-intake.json`.
3. Konkrete Rate-Limit-Werte festlegen.

## 8. Harte Verbote
Immer verboten ohne ausdrückliche Freigabe:
- Push, Deploy, Production-Cutover
- Cloudflare Production Route / Custom Domain
- n8n Live-Webhook
- Google Sheets Live-Schreibzugriff
- Secrets im Repo
- `git add .`, `git reset`, `git restore`, `git clean`
- Änderung an Website-Code außerhalb freigegebener Phase
- `.astro/data-store.json` anfassen/stagen/committen

## 9. Sicherheitscheck vor jeder Arbeit
```bash
REPO="$(~/KI-System/08_System/scripts/resolve_project_path.sh hsb-boden)"
cd "$REPO"
~/KI-System/08_System/scripts/assert_canonical_project_path.sh hsb-boden
git status --short
git log -1 --format="%H | %ci | %s"
git diff -- 'src' 'public' 'components' 'layouts' 'styles' 'astro.config.*' 'vite.config.*' 'wrangler.toml' 'package.json' 'package-lock.json' 'pnpm-lock.yaml' 'bun.lock' 'yarn.lock' | wc -l
```
Wenn Website-Code-Diff unerwartet > 0: STOP.

## 10. Review-Gates
- P0A = Spezifikation
- P0A Review = bestanden
- P0B = technische Umsetzung, nur nach expliziter Freigabe
- P0B Review = Pflicht
- P1 = SEO/Trust/CRO
- P2 = Go-live-Vorbereitung ohne Cutover
- P3 = Push/Deploy/Cutover nur nach Freigabe

## 11. Nächster zulässiger Schritt
1. Diese Datei erstellen/aktualisieren.
2. `AGENTS.md`, `CLAUDE.md`, optional `GEMINI.md` so ergänzen, dass sie diese Datei zuerst lesen.
3. Danach P0B-Freigabeplan prüfen/erstellen.
4. Danach `P0B_USER_APPROVAL_REQUEST.md` erzeugen/aktualisieren.
5. P0B erst nach expliziter Nutzerfreigabe starten.

## 12. Abschlussregel
Am Ende jeder Arbeit:
- Report schreiben
- Handoff aktualisieren
- Git-Status ausgeben
- Website-Code-Diff prüfen
- Push/Deploy weiterhin blockieren, falls nicht ausdrücklich freigegeben
