# AI-Subscription- und Entitlement-Matrix — hsb-boden

Stand: 2026-07-12. Klassen: SUBSCRIPTION_INCLUDED / FREE_QUOTA / API_BILLED / UNKNOWN.
Keine Keys, keine Billing-Details — nur Verfügbarkeitsklassen mit Beleg.

| System | Zugangsweg | Klasse | Beleg (2026-07-12) | Reviewer-Eignung |
|---|---|---|---|---|
| Claude Code (Fable 5) | Anthropic-Abo | SUBSCRIPTION_INCLUDED | aktive Session | Lead + unabhängige Claude-QA-Subagenten |
| Codex CLI/Plugin 1.0.6 | ChatGPT-Login | SUBSCRIPTION_INCLUDED, quota-limitiert | `codex login status`: "Logged in using ChatGPT"; Usage-Limit-Fehler beobachtet → zeitweise BLOCKED_BY_QUOTA | Zweitmodell-Review (wenn Quota frei) |
| Codex GitHub App | `chatgpt-codex-connector[bot]` | SUBSCRIPTION_INCLUDED | Bot-Kommentar im Repo vorhanden | PR-Review via App möglich |
| Jules (`google-labs-jules[bot]`) | Google Labs | FREE_QUOTA | 37 Bot-Kommentare, Autor von ~45 Draft-PRs | Implementierer — genehmigt NIEMALS eigene Arbeit |
| Gemini CLI / Code Assist | Individuals-Kontext | UNKNOWN / eingeschränkt | KI-System-Regel 2026-06-18: nicht mehr operative Hauptschiene; keine `.gemini/config.yaml` im Repo | höchstens ergänzend; NICHT für `.github/workflows/**` |
| CodeRabbit | App/CLI | UNKNOWN — keine Spur | keine `.coderabbit.yaml`, keine Bot-Kommentare | erst nach Installation/Owner-Freigabe |
| GitHub Copilot Review | Lizenz | UNKNOWN | nicht verifizierbar ohne Org-Einblick | erst nach Lizenzbestätigung |
| GitHub Models | Actions | ENTFERNT zu verifizieren | kein Workflow-Verweis gefunden (grep 2026-07-12) | — |
| Direkte OpenAI-/Gemini-API in Actions | Keys | NICHT EINGERICHTET | keine Secrets-Verweise in Workflows außer CLOUDFLARE_API_TOKEN | nur mit Billing + Spend Cap + Owner-Freigabe |

Regel: Kein Reviewer-Erfolg wird behauptet, wenn das Tool fehlte, nicht authentifiziert war oder kein Ergebnis am aktuellen Head-SHA lieferte.
