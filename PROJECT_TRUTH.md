# PROJECT_TRUTH — HSB-Boden / HEXAFLOOR

> Single Source of Truth fuer den **aktuellen** Projektstand. Stand: 2026-06-26.
> Historischer Verlauf gehoert in `SESSION_LOG.md` oder Archive, nicht hier hinein.
> Unklare Punkte sind als `unklar / zu pruefen` markiert.
>
> Gesamturteil: `internal-base-ready-awaiting-dns-and-leads`

## 1. Kanonischer Arbeitsort
- Repo: `/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden`
- Legacy-Pfade wie `_MERGED_20260613`, alte Klone oder Backups sind **nicht** kanonisch.

## 2. Aktueller Repo-Zustand
- Branch: `main`
- Lokaler Stand: entspricht `origin/main`
- Aktueller HEAD: `296d757`
- Website-Code-Diff: `0`
- Lokale bekannte Nicht-Commit-Datei: keine

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
- CRM-Light ist `template-ready-awaiting-lead-data`.
- Der kuenftige 5.000-Lead-Paste/Import ist `prepared-awaiting-data`.

## 6. Aktuelle offene Punkte
- Externer NS-/DNS-Switch der Domain `hsb-boden.de` durch den Domain-Admin
- Zukunftsinput ausserhalb des Repos: spaetere Einfuegung oder Import der 5.000 Akquise-Leads

## 6a. Verifizierte Phasenlage
- Phase 3 ist abgeschlossen: lokale Lighthouse-Evidenz vom 2026-06-26 gegen `https://hsb-boden.cherinojoel.workers.dev/` belegt Performance 95, Accessibility 100, Best Practices 100 und SEO 100.
- Phase 4 ist abgeschlossen: Materialien, Referenzclaims, kanonischer Outreach-Kanal und Owner-Freigabe fuer kontrolliertes manuelles Outreach-Material sind repo-belegt bzw. durch die vorliegende Owner-Entscheidung geschlossen.
- Phase 5 ist fuer diesen Stand abgeschlossen: CRM-Light ist als leere, importfaehige Struktur dokumentiert.
- Phase 6 ist abgeschlossen: Lead-Intake Website `/api/lead` -> Google Apps Script Web App -> Google Sheets CRM-Light ist die aktive verifizierte Kette.
- Phase 7 ist `gate-prepared-awaiting-lead-data`.
- Phase 8 und Phase 9 bleiben pending.
- Phase 10 ist optional und derzeit dokumentiert deaktiviert; n8n ist nicht aktiv.
- Phase 11 ist abgeschlossen.
- Phase 12 ist `blocked-awaiting-dns-ns-switch`.
- Rechtstext-Abnahme gilt fuer die aktuelle Statusfuehrung als erledigt.
- Kein realer Versand ist dadurch freigegeben: Dispatch bleibt blockiert, bis reale Lead-Daten importiert sind, die Lead-Liste freigegeben ist, Empfaengerbasis und Opt-out dokumentiert sind, das exakte Batch freigegeben ist und die Compliance-Freigabe dokumentiert ist.

## 7. Aktuelle Freigabegates
- Kein Push ohne Freigabe
- Kein Production-Deploy/Cutover ohne Freigabe
- Kein Setzen der Domain-Routes vor erfolgreichem NS-/DNS-Switch
- Kein Dispatch ohne `docs/launch/PHASE_7_COMPLIANCE_GATE.md` und `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md` mit realen Daten und Batch-Freigabe.

## 7a. Operator-Handoff
- Finaler Freeze-/Trigger-Stand: `docs/FINAL_OPERATOR_HANDOFF.md`
- Finaler Abschlussbericht: `docs/FINAL_COMPLETION_REPORT.md`
- Phase-12-Cutover-Pfad: `docs/PHASE_C_CUTOVER_RUNBOOK.md`
- Lead-Import-Pfad: `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md`

## 8. Naechster sichere Schritt
DNS/NS-Switch fuer `hsb-boden.de` und spaetere Einfuegung der realen 5.000 Lead-Daten abwarten. Import bleibt CRM-Datenvorbereitung, kein Versand.
