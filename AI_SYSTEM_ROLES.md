# AI_SYSTEM_ROLES — HSB / HEXAFLOOR

| System | Rolle | Übergabe |
|--------|-------|----------|
| ChatGPT | Obersteuerung | gibt Prompts/Entscheidungen |
| Claude Code | Umsetzung | schreibt Reports/Handoff |
| Codex | Review | gibt Freigabe/Blocker |
| Gemini | Deep Research | liefert Quellenprüfung |
| Perplexity | SEO/Quellen | liefert externe Validierung |
| n8n | Automation | nutzt Freigabe |
| Google Sheets | CRM-Light | Zielsystem |
| Cloudflare | Hosting/Workers | Preview/Production nach Freigabe |

## Grundsatz
Research (Gemini/Perplexity) = Quelle, nicht Wahrheit. Umsetzung = Claude Code nach Freigabe. Review = Codex. Steuerung = ChatGPT.
