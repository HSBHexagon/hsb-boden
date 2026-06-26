# PROJECT_TRUTH — HSB-Boden / HEXAFLOOR

> Single Source of Truth fuer den **aktuellen** Projektstand. Stand: 2026-06-26.
> Historischer Verlauf gehoert in `SESSION_LOG.md` oder Archive, nicht hier hinein.
> Unklare Punkte sind als `unklar / zu pruefen` markiert.

## 1. Kanonischer Arbeitsort
- Repo: `/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden`
- Legacy-Pfade wie `_MERGED_20260613`, alte Klone oder Backups sind **nicht** kanonisch.

## 2. Aktueller Repo-Zustand
- Branch: `main`
- Lokaler Stand: entspricht `origin/main`
- Aktueller HEAD: `92bda23`
- Website-Code-Diff: `0`
- Lokale bekannte Nicht-Commit-Datei: `.astro/data-store.json`

## 3. Aktueller Projektzustand
- Die Lead-Pipeline ist end-to-end live und verifiziert.
- Der Production-Worker `hsb-boden` ist route-los deployed und erreichbar.
- Das Production-Secret `LEAD_WEBHOOK_URL` ist gesetzt.
- Die Website ist **noch nicht live auf der Domain**, weil weiterhin keine Worker-Routes gesetzt sind.
- Die bestehende WordPress-Live-Seite bleibt bis zum Cutover aktiv.

## 4. Aktueller Cloudflare- und Domain-Stand
- Preview-Worker: `hsb-boden-preview`
- Production-Worker: `hsb-boden`
- Production-Routes sind bewusst noch nicht gesetzt.
- Zone `hsb-boden.de` steht weiterhin auf `pending`.
- Der externe NS-/DNS-Switch durch den Domain-Admin ist der aktuelle externe Hauptblocker.

## 5. Aktueller Lead- und CRM-Stand
- Das Kontaktformular postet an `/api/lead`.
- Der Worker leitet an die Google-Apps-Script-Web-App weiter.
- Zielsystem ist das Google Sheet `HSB CRM Light`.
- Die End-to-End-Zustellung wurde verifiziert.
- `ops/n8n/` ist historisch/deprecated und nicht die aktive Loesung.

## 6. Aktuelle offene Punkte
- NS-/DNS-Switch der Domain durch den Domain-Admin
- Danach: zwei Worker-Routes fuer `hsb-boden.de/*` und `www.hsb-boden.de/*` setzen
- Danach: Live-Verifikation auf der echten Domain
- Vorbereitende Themen ohne Cutover: Search Console, GA4/GTM, Consent

## 6a. Verifizierte Phasenlage
- Phase 3 ist abgeschlossen: lokale Lighthouse-Evidenz vom 2026-06-26 gegen `https://hsb-boden.cherinojoel.workers.dev/` belegt Performance 95, Accessibility 100, Best Practices 100 und SEO 100.
- Phase 4 ist abgeschlossen: Materialien, Referenzclaims, kanonischer Outreach-Kanal und Owner-Freigabe fuer kontrolliertes manuelles Outreach-Material sind repo-belegt bzw. durch die vorliegende Owner-Entscheidung geschlossen.
- Rechtstext-Abnahme gilt fuer die aktuelle Statusfuehrung als erledigt.
- Kein realer Versand ist dadurch freigegeben: Dispatch bleibt blockiert, bis Lead-Liste, Empfaengerbasis, Opt-out-Handling und Compliance/Freigabe pro Einsatz dokumentiert sind.

## 7. Aktuelle Freigabegates
- Kein Push ohne Freigabe
- Kein Production-Deploy/Cutover ohne Freigabe
- Kein Setzen der Domain-Routes vor erfolgreichem NS-/DNS-Switch

## 8. Naechster sichere Schritt
Phase 7 nur dokumentarisch vorbereiten: Lead-Liste, Empfaengerbasis, Opt-out-Handling und Compliance/Freigabe fuer einen kontrollierten manuellen Testversand separat nachweisen. Phase 12 bleibt bis zum externen DNS-Switch blockiert.
