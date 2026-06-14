# PHASED_EXECUTION_PLAN — HSB / HEXAFLOOR

| Phase | Zweck | Status | Darf | Darf nicht |
|-------|-------|--------|------|------------|
| P0A | Spezifikation Lead-Pipeline | abgeschlossen | Doku/Plan | Code/Live |
| P0A Review | Abnahme P0A | bestanden | Review | Änderungen |
| P0B | technische Umsetzung Lead-Pipeline | wartet auf Freigabe | Endpoint/n8n/Sheets nach Freigabe | Push/Deploy ohne Freigabe |
| P0B Review | Abnahme technischer Umsetzung | offen | prüfen | Live-Cutover |
| P1 | SEO/Trust/CRO | offen | Website-Hardening nach Freigabe | Deploy ohne Freigabe |
| P2 | Go-live-Vorbereitung | offen | Preview/Checks | Production-Cutover |
| P3 | Push/Deploy/Cutover | offen | nur nach Freigabe | alles ohne Freigabe |

## Aktuelle Phase
**P0B-FREIGABE VORBEREITEN** — nächste Entscheidung: `P0B_USER_APPROVAL_REQUEST.md`.
