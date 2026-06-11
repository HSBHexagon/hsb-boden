# FINAL_WEBSITE_COMPLETION_TASKS.md

Stand: 2026-06-11
Fokus: Herstellung der 100%igen Vertriebsreife

| Prio | Maßnahme | Hebel | Aufwand | Status |
|---|---|---|---|---|
| 1 | **Lead-Infrastruktur scharfschalten:** Webhook-URL in `.env` eintragen und `npm run build` zur Verifizierung ausführen. | Conversion | Minimal | ⬜ |
| 2 | **E2E-Test:** Projektanfrage im Browser absenden und Eingang im n8n-Workflow/E-Mail bestätigen. | Conversion | Niedrig | ⬜ |
| 3 | **Header-Bereinigung (Sprachen):** Permanentes 6-Sprachen-Menü aus `Header.astro` entfernen (B2B-Fokus stärken). | Vertrauen | Minimal | ⬜ |
| 4 | **Medien-Zuordnung (Prio):** Die 12 vorhandenen Projektbilder den 5 Referenzen in `src/data/references.ts` zuordnen (Arrays befüllen). | Vertrauen | Niedrig | ⬜ |
| 5 | **ProofMedia-Expansion:** 2-3 weitere Bild-Kacheln in `src/components/sections/ProofMediaSection.astro` ergänzen, um die volle Bandbreite (Chemie, Molkerei, Sanierung) zu zeigen. | Vertrauen | Niedrig | ⬜ |
| 6 | **Rechtstexte-Check:** Letzte Prüfung von Impressum/DSGVO auf Vollständigkeit (St.-Nr., Handelsregister). | Rechtlich | Niedrig | ⬜ |
| 7 | **Favicon & OG-Bilder:** Verifizieren, dass das HEXAFLOOR-Logo in Browser-Tabs und Link-Vorschauen korrekt erscheint. | Branding | Niedrig | ⬜ |
| 8 | **Performance-Check (Cloudflare):** Aktivierung von Cloudflare Rocket Loader und Auto-Minify für maximale Ladegeschwindigkeit bei mobilen Technikern vor Ort. | UX | Minimal | ⬜ |
| 9 | **Merge & Go-Live:** Zusammenführen des Recovery-Branches in den `main` Branch und Deployment auf die Ziel-Domain. | Ops | Niedrig | ⬜ |

---
**Nächster logischer Schritt:** Task 1 & 2. Ohne funktionierendes Formular ist die Website ein reines Kosten-Zentrum. Mit Formular wird sie zum Profit-Center.
