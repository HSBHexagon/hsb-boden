# PROJECT_TRUTH — HSB-Boden / HEXAFLOOR

> Single Source of Truth fuer den **aktuellen** Projektstand. Stand: 2026-06-26.
> Historischer Verlauf gehoert in `SESSION_LOG.md` oder Archive, nicht hier hinein.
> Unklare Punkte sind als `unklar / zu pruefen` markiert.
>
> Gesamturteil: `sales-operations-max-ready-awaiting-dns-and-leads`

## 1. Kanonischer Arbeitsort
- Repo: `/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden`
- Legacy-Pfade wie `_MERGED_20260613`, alte Klone oder Backups sind **nicht** kanonisch.

## 2. Aktueller Repo-Zustand
- Branch: `main`
- Lokaler Commit-Stand: entspricht `origin/main`
- Aktueller HEAD: `bf0f998`
- Website-Code-Diff: `0`
- Lokale bekannte Nicht-Commit-Dateien: aktuelle Doku-Audits dieses Sweeps (`PROJECT_TRUTH.md`, `CHECKPOINT_STATE.json`, `SESSION_LOG.md`, `docs/MASTER_EXECUTION_PLAN.md`, `docs/FINAL_OPERATOR_HANDOFF.md`, `docs/FINAL_COMPLETION_REPORT.md`, `docs/FINAL_ADVERSARIAL_AUDIT.md`, `docs/FINAL_PHASE_BY_PHASE_AUDIT.md`, `docs/FINAL_CLOUDFLARE_WORKERS_READINESS_AUDIT.md`)

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

## 7a. Operator-Handoff und kanonischer Readiness-Stack (aktuell)

### Tier 1 — Kanonische Readiness-Wahrheit
- Cloudflare Provider Readiness: `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md`
- E-Mail/Deliverability Readiness: `docs/email/EMAIL_ROUTING_AND_DELIVERABILITY_MAX_READINESS.md`
- Analytics Readiness (GA4/GTM/GSC): `docs/analytics/GA4_GTM_GSC_MAX_READINESS.md`
- Asset/PDF Readiness: `docs/assets/ASSET_PACKAGE_AND_PUBLIC_DOWNLOAD_MAX_READINESS.md`
- CRM-Light Readiness: `docs/crm/CRM_LIGHT_MAX_READINESS.md`
- Automation Blueprints (optional): `docs/automation/STATUS_UPDATE_AUTOMATION_BLUEPRINT.md`
- Joel/JORDIE Operator Runbook: `docs/handoff/JOEL_JORDIE_OPERATOR_RUNBOOK.md`

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
DNS/NS-Switch fuer `hsb-boden.de` und spaetere Einfuegung der realen 5.000 Lead-Daten abwarten. Import bleibt CRM-Datenvorbereitung, kein Versand.
