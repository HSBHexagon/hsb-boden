# WEBSITE_FINALIZATION_TASKS.md

Stand: 2026-06-11
Fokus: Website Go-Live & Conversion-Optimierung

| Prio | Maßnahme | Hebel | Aufwand | Status |
|---|---|---|---|---|
| 1 | **Lead-Pipeline aktivieren:** Webhook-URL in `.env` eintragen und `leadEndpoint` in `site.ts` validieren. | Conversion | Niedrig | ⬜ |
| 2 | **E2E Testanfrage:** Manuellen Lead absenden und n8n-Workflow-Durchlauf verifizieren. | Conversion | Niedrig | ⬜ |
| 3 | **Rechtstexte finalisieren:** Impressum und Datenschutz-Seite auf korrekte Firmendaten und Consent-Logik prüfen. | Vertrauen | Niedrig | ⬜ |
| 4 | **Referenz-Link-Check:** Sicherstellen, dass alle Karten-Marker und Galerie-Bilder korrekt auf die Detailseiten verlinken. | UX | Niedrig | ⬜ |
| 5 | **Hersteller-Visuals:** Optionale Ergänzung kleiner Logos/Icons für BASF/MasterBuilders in `ManufacturerProof.astro`. | Vertrauen | Mittel | ⬜ |
| 6 | **Mobile Menü-Review:** Letzter Check der Navigations-Klickwege auf extrem schmalen Geräten (360px). | UX | Niedrig | ⬜ |
| 7 | **Bilder-Lazy-Loading:** Verifizieren, dass alle neuen Projektfotos `loading="lazy"` und korrekte `alt`-Texte haben. | Performance | Niedrig | ⬜ |
| 8 | **Favicon & OG-Meta:** Korrektheit des HEXAFLOOR-Logos als Favicon und in Social-Sharing-Vorschauen prüfen. | Branding | Niedrig | ⬜ |
| 9 | **Merge PR #5:** Finalen Recovery-Branch in `main` mergen, sobald Tests 1-3 erfolgreich sind. | Ops | Niedrig | ⬜ |
| 10 | **Cleanup Dokumente:** Temporäre Arbeitsdateien (`.tmp`, `*.bak`) aus dem Projektstamm entfernen. | Hygiene | Niedrig | ⬜ |

---
**Nächster Schritt:** Start mit Task 1 (Lead-Infrastruktur), da dies die Website von einer "Visitenkarte" zu einem "Vertriebswerkzeug" transformiert.
