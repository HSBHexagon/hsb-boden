# Multi-AI-Review-Quorum — hsb-boden

Stand: 2026-07-12. Risikoklassen und erforderliche Review-Quoren.

## Risikoklassen

| Klasse | Definition | Beispiele |
|---|---|---|
| R0_DOCS | reine Doku, kein Runtime-Pfad | Triage-Reports, ops-Dokumente |
| R1_LOW | kleine Code-/Test-Änderung ohne Security-/Lead-Pfad | Unused-Import-Cleanups, Testergänzungen |
| R2_STANDARD | Feature/Fix in Runtime-Pfaden | LCP-Optimierung, Content-Caching |
| R3_PROTECTED | Workflows, Lead-/Consent-/Analytics-Pfad, Architektur | PR #48 (React-Removal), `.github/workflows/**`, `functions/api/lead.ts` |

## Quorum je Klasse

| Klasse | Deterministische Checks | Claude-QA (unabhängig) | Zweitmodell (Codex/CodeRabbit) | Workflow-Security-Spezialprüfung | Owner |
|---|---|---|---|---|---|
| R0_DOCS | CI grün | empfohlen | optional | — | Merge |
| R1_LOW | CI grün | Pflicht | empfohlen | — | Merge |
| R2_STANDARD | CI grün | Pflicht | Pflicht (sobald verfügbar) | — | Merge |
| R3_PROTECTED | CI grün | Pflicht | Pflicht | Pflicht (actionlint/zizmor + manuelles Audit) | Pflicht, explizit |

## Regeln

- Gemini Code Assist zählt NICHT als vollständiger Reviewer für `.github/workflows/**`.
- Jules implementiert, genehmigt aber niemals die eigene Arbeit.
- Ein blockierter Reviewer (BLOCKED_BY_QUOTA / REVIEWER_TEMPORARILY_UNAVAILABLE) hält Draft-PRs nicht auf, wohl aber Ready-for-Review bei R2/R3.
- Reviews gelten nur am aktuellen Head-SHA; nach jedem Push erneut erforderlich.
- Kein Auto-Merge für R2/R3; R3 nie vollautomatisch.
