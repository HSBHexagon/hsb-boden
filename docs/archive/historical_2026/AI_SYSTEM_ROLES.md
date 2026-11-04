# AI_SYSTEM_ROLES — HSB / HEXAFLOOR

| System | Rolle | Übergabe |
|--------|-------|----------|
| ChatGPT | Obersteuerung | gibt Prompts/Entscheidungen |
| Claude Code | Umsetzung | schreibt Reports/Handoff |
| Codex | Review | gibt Freigabe/Blocker |
| Gemini | Ergänzende Research-/Gegenprüfung | liefert Quellenprüfung, nicht kritischer Pfad |
| Perplexity | SEO/Quellen | liefert externe Validierung |
| n8n | Automation | nutzt Freigabe |
| Google Sheets | CRM-Light | Zielsystem |
| Cloudflare | Hosting/Workers | Preview/Production nach Freigabe |

## Grundsatz
Research (Gemini/Perplexity) = Quelle, nicht Wahrheit. Wegen angekündigtem Gemini-CLI-/Code-Assist-Stopp ab 2026-06-18 im Individuals/Google-AI-Pro/Ultra-Kontext wird Gemini nicht als operative Hauptschiene geplant. Umsetzung = Codex/Claude Code nach Freigabe. Review = Codex/Jules. Steuerung = ChatGPT.
