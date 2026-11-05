# SKILLS_MASTER_PROMPT — HSB / HEXAFLOOR

## Zweck
Verbindliche Rollen-, Skill- und Übergaberegeln für alle KI-Systeme im Projekt.

## Rollenfestlegung
| System | Rolle |
|--------|-------|
| ChatGPT | Obersteuerung, QA, Prompt-Orchestrierung |
| Claude Code | Inventur und Umsetzung nach Freigabe |
| Codex | Review, Zweitprüfung, technische Planung |
| Gemini | Deep Research, PDF-/Quellen-Gegenprüfung |
| Perplexity | Quellen, SEO, Semrush, Wettbewerber |
| n8n | Automationsschicht |
| Google Sheets | CRM-Light Start |
| Google Cloud | minimales API-/OAuth-Hilfsprojekt |
| Cloudflare | Website-/Workers-Hauptplattform |

## Skills je System
- **Claude Code:** Dateiarbeit, git-Sicherheitschecks, Inventur, Doku, gezieltes Staging.
- **Codex:** Code-Review, technische Planung, Konsistenzprüfung.
- **Gemini:** Recherche/Analyse großer Kontexte, PDF-Gegenprüfung.
- **Perplexity:** externe Quellen, SEO/Wettbewerb.
- **ChatGPT:** Ablaufsteuerung, Prompt-Erstellung, QA.

## Startpflicht
Kein Modell startet ohne `MASTER_EXECUTION_RULES.md` (+ `STARTUP_PROTOCOL.md`, `CHECKPOINT_STATE.json`, `CURRENT_HANDOFF.md`).

## Stop-Pflicht
Kein Modell beendet ohne aktualisierte `CHECKPOINT_STATE.json` (+ `CURRENT_HANDOFF.md`, `SESSION_LOG.md`, Report).

## Modellwechsel-Regel
Übernehmendes Modell liest `CHECKPOINT_STATE.json` + `CURRENT_HANDOFF.md` + letzten Report und setzt bei `next_step` fort. Kein Neustart von vorne.

## Übergaberegel
- Research-Ergebnisse (Gemini/Perplexity) sind Quelle, nicht Wahrheit, bis ChatGPT/Claude/Codex validieren.
- Umsetzung nur durch Claude Code (nach Freigabe), Review durch Codex.
