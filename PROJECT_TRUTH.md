# PROJECT_TRUTH — HSB-Boden / HEXAFLOOR

> Single Source of Truth fuer den **aktuellen** Projektstand. Stand: 2026-07-08.
> Historischer Verlauf gehoert in `SESSION_LOG.md` oder Archive, nicht hier hinein.
> Unklare Punkte sind als `unklar / zu pruefen` markiert.
>
> Gesamturteil: `pages-www-live-awaiting-apex-and-leads`

## 1. Kanonischer Arbeitsort
- Repo: `/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden`
- Legacy-Pfade wie `_MERGED_20260613`, alte Klone oder Backups sind **nicht** kanonisch.

## 2. Aktueller Repo-Zustand
- Branch: `main`
- Lokaler Commit-Stand: entspricht `origin/main`
- Aktueller HEAD: `5e6e184`
- Website-Code-Diff: lokale, noch nicht committete Aenderungen vorhanden (`src/data/clientLocations.ts`, `src/layouts/BaseLayout.astro`) plus Doku-/CRM-Import-Vorbereitung
- Lokale bekannte Nicht-Commit-Dateien: `CHECKPOINT_STATE.json`, `CRM_LIGHT_SCHEMA.md`, `PROJECT_TRUTH.md`, `docs/FINAL_OPERATOR_HANDOFF.md`, `docs/MASTER_EXECUTION_PLAN.md`, `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md`, `src/data/clientLocations.ts`, `src/layouts/BaseLayout.astro`
- Parallel-Worktree: `/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden-pages-static`, Branch `pages-static-migration`, letzter lokaler Commit `926cf6b`, noch nicht in `main` konsolidiert.

## 3. Aktueller Projektzustand
- Die Lead-Pipeline ist end-to-end live und verifiziert.
- Der Production-Worker `hsb-boden` ist route-los deployed und erreichbar.
- Das Production-Secret `LEAD_WEBHOOK_URL` ist gesetzt.
- `www.hsb-boden.de` ist live ueber Cloudflare Pages und wurde am 2026-07-08 gegen `/referenzen/` verifiziert.
- `hsb-boden.de` ohne `www` zeigt weiterhin auf die alte WordPress/Apache-Seite; `/referenzen/` liefert dort 404. Apex-Redirect oder DNS-Anpassung bleibt offen.
- Die Worker-Schiene laeuft parallel weiter, ist aber nicht die aktuelle `www`-Live-Schiene.

## 4. Aktueller Cloudflare- und Domain-Stand
- Preview-Worker: `hsb-boden-preview`
- Production-Worker: `hsb-boden`
- Cloudflare Pages Projekt: `hsb-boden`
- Aktuelle Live-Schiene fuer `www.hsb-boden.de`: Cloudflare Pages (`hsb-boden.pages.dev`)
- Production-Worker-Routes sind weiterhin nicht die kanonische Live-Schiene.
- Offen: Apex `hsb-boden.de` muss auf `www.hsb-boden.de` weiterleiten oder technisch auf die neue Site zeigen.

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
- Phase 12 ist teilweise abgeschlossen: `www.hsb-boden.de` ist live ueber Pages; offen bleibt Apex `hsb-boden.de` und die Konsolidierung des Pages-Worktrees in `main`.
- Rechtstext-Abnahme gilt fuer die aktuelle Statusfuehrung als erledigt.
- Kein realer Versand ist dadurch freigegeben: Dispatch bleibt blockiert, bis reale Lead-Daten importiert sind, die Lead-Liste freigegeben ist, Empfaengerbasis und Opt-out dokumentiert sind, das exakte Batch freigegeben ist und die Compliance-Freigabe dokumentiert ist.

## 7. Aktuelle Freigabegates
- Kein Push ohne Freigabe
- Kein weiterer Production-Deploy/Cutover ohne Freigabe
- Kein Setzen von Domain-Routes, DNS-Records oder Apex-Redirects ohne Freigabe
- Kein Dispatch ohne `docs/launch/PHASE_7_COMPLIANCE_GATE.md` und `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md` mit realen Daten und Batch-Freigabe.

## 7a. Operator-Handoff und kanonischer Readiness-Stack (aktuell)

### Tier 1 — Kanonische Readiness-Wahrheit
- Cloudflare Provider Readiness: `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md`
- E-Mail/Deliverability Readiness: `docs/email/EMAIL_ROUTING_AND_DELIVERABILITY_MAX_READINESS.md`
- Analytics Readiness (GA4/GTM/GSC): `docs/analytics/GA4_GTM_GSC_MAX_READINESS.md`
- Asset/PDF Readiness: `docs/assets/ASSET_PACKAGE_AND_PUBLIC_DOWNLOAD_MAX_READINESS.md`
- CRM-Light Readiness: `docs/crm/CRM_LIGHT_MAX_READINESS.md`
- Automation Blueprints (optional): `docs/automation/STATUS_UPDATE_AUTOMATION_BLUEPRINT.md`
- Joel/JORDI Operator Runbook: `docs/handoff/JOEL_JORDI_OPERATOR_RUNBOOK.md`

### Tier 2 — Erweiterter Readiness-Detail (2026-06-26 Wave)
- Cloudflare UI Preflight Inventory: `docs/cloudflare/GO_LIVE_MAX_PREFLIGHT_UI_INVENTORY.md`
- WAF/Cache/Rate-Limit Readiness: `docs/cloudflare/WAF_CACHE_RATE_LIMIT_READINESS.md`
- R2 Asset-Strategie: `docs/cloudflare/R2_ASSET_UPLOAD_STRATEGY.md`
- Turnstile Formularschutz: `docs/cloudflare/TURNSTILE_FORM_PROTECTION_READINESS.md`
- AI Gateway (nur Zukunft): `docs/cloudflare/AI_GATEWAY_FUTURE_ARCHITECTURE.md`
- GA4 Event-Tracking-Plan: `docs/analytics/GA4_GSC_EVENT_TRACKING_READINESS.md`
- E-Mail-Templates & Deliverability: `docs/email/EMAIL_DELIVERABILITY_AND_TEMPLATE_READINESS.md`
- UTM- und QR-Matrix: `docs/assets/UTM_QR_DOWNLOAD_MATRIX.md`
- CRM Operator-Tagesworkflow: `docs/crm/CRM_LIGHT_OPERATOR_READINESS.md`
- n8n/Apps Script Safe Automation: `docs/automation/N8N_APPS_SCRIPT_SAFE_AUTOMATION_READINESS.md`
- Multi-PC Operator Sync Protocol: `docs/ops/MULTI_PC_OPERATOR_SYNC_PROTOCOL.md`
- Master Go-Live Checklist: `docs/launch/PRE_DNS_GO_LIVE_MAX_CHECKLIST.md`

Historische Finale Docs (Evidenz, nicht aktiv kanonisch fuer Cloudflare):
- Finaler Freeze-/Trigger-Stand: `docs/FINAL_OPERATOR_HANDOFF.md`
- Finaler Abschlussbericht: `docs/FINAL_COMPLETION_REPORT.md`
- Finaler adversarial audit: `docs/FINAL_ADVERSARIAL_AUDIT.md`
- Finaler Phase-fuer-Phase-Audit: `docs/FINAL_PHASE_BY_PHASE_AUDIT.md`
- Cloudflare Workers Readiness Audit (historisch): `docs/FINAL_CLOUDFLARE_WORKERS_READINESS_AUDIT.md`

Ausfuehrungspfade:
- Phase-12-Cutover: `docs/PHASE_C_CUTOVER_RUNBOOK.md`
- Lead-Import: `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md`

## 8. Naechster sichere Schritt
Keine zweite Wahrheit weiterfuehren: Pages-Worktree, `main`, `PROJECT_TRUTH.md`, `docs/MASTER_EXECUTION_PLAN.md`, `docs/FINAL_OPERATOR_HANDOFF.md` und `CHECKPOINT_STATE.json` muessen auf den Pages-`www`-Live-Stand konsolidiert werden. Danach reale Lead-Dateien importbereit auf zwei Operator-Dateien splitten. Import bleibt CRM-Datenvorbereitung, kein Versand.
