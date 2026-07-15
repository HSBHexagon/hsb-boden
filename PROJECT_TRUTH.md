# PROJECT_TRUTH — HSB-Boden / HEXAFLOOR

> Single Source of Truth fuer den **aktuellen** Projektstand. Stand: 2026-07-15, 12:05 CEST.
> Historischer Verlauf gehoert in `SESSION_LOG.md` oder Archive, nicht hier hinein.
> Unklare Punkte sind als `unklar / zu pruefen` markiert.
>
> Gesamturteil: `pages-live-core-web-fixed-external-owner-gates-remain`
>
> Aktuelle Evidenz und zeitgebundene Detailbefunde stehen in
> `docs/ai_state/TRUTH_MATRIX_2026-07-15.md`. Historische Worker-, WordPress-,
> Pages-Migrations- und PR-Snapshots sind nicht mehr handlungsleitend.

## 1. Kanonischer Arbeitsort
- Repo: `/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden`
- Legacy-Pfade wie `_MERGED_20260613`, alte Klone oder Backups sind **nicht** kanonisch.

## 2. Aktueller Repo-Zustand
- Branch: `main`
- Remote-HEAD: `f202cb6` (`origin/main`, verifiziert 2026-07-15 12:05 CEST).
- Das lokale Root-Worktree ist bei den getrackten Dateien unveraendert und sechs
  Commits hinter `origin/main`; zusaetzlich existiert das ungetrackte Verzeichnis
  `.local-secrets/` aus der laufenden Fable-Sitzung. Es wurde nicht geoeffnet
  oder veraendert. Nicht waehrend dieser Sitzung ungefragt umschalten.
- PR #84, #85, #87, #88, #89 und #90 sind gemergt. Der manuelle
  Production-Deploy-Run `29404977846` fuer `bf0a257` war erfolgreich.
- PR #86 ist offen, konfliktbehaftet und durch PR #87 funktional teilweise
  ueberholt; nicht pauschal mergen. PR #74 bleibt Draft und deaktiviert.
- Zum Snapshot 12:05 CEST sind 40 Pull Requests offen; diese Zahl ist
  zeitgebunden und keine dauerhafte Projekteigenschaft.

## 3. Aktueller Projektzustand
- `www.hsb-boden.de` ist live ueber Cloudflare Pages.
- `https://www.hsb-boden.de/kontakt/` liefert HTTP 200.
- Ein zufaelliger unbekannter Produktionspfad liefert HTTP 404 mit `no-store`;
  der fruehere siteweite Soft-404 ist durch PR #85 behoben.
- `GET /api/lead` liefert HTTP 405; dabei wurde kein Lead erzeugt.
- `hsb-boden.de` leitet per HTTP 301 und unter Erhalt der Query-Parameter auf
  `www` um. Der funktionale Apex-Zielzustand ist damit erreicht; ein voller
  Nameserver-Cutover ist nicht erfolgt und technisch nicht Voraussetzung fuer
  die aktuelle Website-Funktion.
- PR #87 ruft GA4-Events nun direkt ueber `gtag('event', ...)` auf und ist
  produktiv. Der Live-Probe aus PR #90 belegt den Aufrufpfad, nicht jedoch einen
  real abgeschlossenen Lead oder die Sichtbarkeit als GA4-Key-Event.

## 4. Aktueller Cloudflare- und Domain-Stand
- Cloudflare Pages Projekt: `hsb-boden`
- Aktuelle Live-Schiene fuer `www.hsb-boden.de`: Cloudflare Pages (`hsb-boden.pages.dev`)
- Aktueller Production-Source-Commit: `bf0a257`; Deployment-Run
  `29404977846` war erfolgreich.
- Im produktiven Info-Account existieren keine Workers; die Zone
  `hsb-boden.de` bleibt `pending`.
- Ein alter Preview-Worker und eine doppelte Zone liegen im Alt-Account. Deren
  Stilllegung beziehungsweise `noindex`, die doppelte Zone und Token-Rotation
  sind separate Owner-Cleanup-Gates.

## 5. Aktueller Lead- und CRM-Stand
- Das Kontaktformular postet an `/api/lead`.
- Die Pages Function leitet an die Google-Apps-Script-Web-App weiter.
- Zielsystem der Website-Pipeline ist das Google Sheet `HSB CRM Light`, Tab
  `Leads`. IDs und Webhook-URLs gehoeren nicht in diese versionierte SSOT.
- OPERATOR_VERIFIED 2026-07-15 ca. 13:05 CEST: Eine Fable-Browser-Sitzung
  ergaenzte die sechs Attributionsspalten, aktualisierte das bestehende
  Legacy-Deployment auf Version 4 und uebermittelte einen klar markierten
  UTM-Testlead. Alle sechs Felder waren korrekt; die Testzeile wurde danach
  geloescht. Codex hat die Google-UI nicht unabhaengig erneut geoeffnet.
- Dieses Ergebnis belegt Mapping und Zustellung, **nicht** die Sicherheit: Das
  verwendete Legacy-Deployment prueft weiterhin keinen neuen Auth-Vertrag und
  bleibt bis zum P0-Cutover kompromittiert.
- `ops/n8n/` ist historisch/deprecated und nicht die aktive Loesung.
- Die lokalen, bewusst unversionierten Exporte enthalten 6.424 Outbound-Leads:
  Joel 3.212, Jordi 3.212, keine Ueberschneidung. Alle bleiben mit
  `Versandfreigabe = no` und unbekanntem Opt-in/Opt-out gesperrt.
- Der 29-Spalten-Outbound-Bestand und das 27-Spalten-Inbound-Schema sind
  unterschiedliche Modelle. Live-Sheets wurden nicht automatisiert
  umstrukturiert. Details und das additive Zielmodell stehen in
  `docs/crm/CRM_DEEP_DIVE_2026-07-15.md`.
- Das Attribution-Mapping ist operator-verifiziert live. Die eindeutige
  Google-Kontoidentitaet bleibt fuer weitere API-/Admin-Arbeit ein Owner-Gate.

## 6. Aktuelle offene Punkte
- GA4: den fachlich kanonischen Conversion-Namen festlegen, den Event-Transport
  bei erfolgreichem Formular-Submit verlaesslich abschliessen und das Ergebnis
  in DebugView/Realtimedaten als Key Event verifizieren. PR #86 darf wegen
  Konflikten und abweichender Consent-Semantik nicht blind gemergt werden.
- Google/CRM: Profil `cherinojoel` fuer weitere API-/Admin-Pruefungen explizit
  als `cherinojoel@gmail.com` re-authentifizieren. Mapping und loeschbarer
  Testlead sind bereits operator-verifiziert; nicht erneut als offenen Schritt
  ausfuehren.
- Cloudflare: Alt-Account-Worker, doppelte Zone und exponierte Tokens/Endpoint-
  Werte rotieren beziehungsweise stilllegen. Kein NS-Cutover ohne separaten
  Mail-/DNS-Plan.
- Outreach: Rechtsgrundlage, Opt-out, M365-DKIM und Batch-Freigabe abschliessen.
  Kein Versand ist freigegeben.
- Google-Unternehmensprofil: Owner-Anlage und physische Verifizierung.
- Codex GitHub Review: Cloud-Umgebung/Review-Kontingent fehlt; automatische
  Review-Erfolge nicht mit einem manuellen `@codex review` verwechseln.

## 6a. Verifizierte Phasenlage
- Phase 3 ist technisch abgeschlossen; aktuelle CI-/Lighthouse-Checks sind gruen
  und der Production-Soft-404 ist behoben. Historische Worker-Lighthouse-Werte
  sind Evidenz, aber nicht der aktuelle Live-Messpunkt.
- Phase 4 ist abgeschlossen: Materialien, Referenzclaims, kanonischer Outreach-Kanal und Owner-Freigabe fuer kontrolliertes manuelles Outreach-Material sind repo-belegt bzw. durch die vorliegende Owner-Entscheidung geschlossen.
- Phase 5 ist strukturell vorbereitet; das Attributionsmapping ist
  operator-verifiziert, die additiven Live-Sheet-Ansichten und eindeutige
  Kontoidentitaet bleiben offen.
- Phase 6 ist technisch live: Website `/api/lead` -> Pages Function -> Google
  Apps Script -> CRM-Light. Ein frischer UTM-End-to-End-Test ist
  operator-verifiziert und bereinigt; der Auth-Cutover bleibt P0 offen.
- Phase 7 ist `lead-data-imported-awaiting-compliance-and-batch-approval` (Leads liegen seit 2026-07-08 vor, siehe Update oben; HISTORICAL: „awaiting-lead-data“ traf vor diesem Update zu).
- Phase 8 und Phase 9 bleiben pending.
- Phase 10 ist optional und derzeit dokumentiert deaktiviert; n8n ist nicht aktiv.
- Phase 11 ist abgeschlossen.
- Phase 12 ist fuer die Website-Schaltung abgeschlossen: `www` ist live, Apex
  leitet query-erhaltend um, Pages ist in `main`, 404 und Lead-Fehlerbehandlung
  sind produktiv. Externe Owner-Gates bleiben getrennt.
- Rechtstext-Abnahme gilt fuer die aktuelle Statusfuehrung als erledigt.
- Kein realer Versand ist dadurch freigegeben: Dispatch bleibt blockiert, bis
  Empfaengerbasis, Rechtsgrundlage, Opt-out, DKIM, das exakte Batch und die
  Owner-Freigabe dokumentiert sind.

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
- Joel/JORDI Operator Runbook: `docs/handoff/JOEL_JORDIE_OPERATOR_RUNBOOK.md`

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
- Spaeterer optionaler NS-Cutover: neues Pages-/Mail-DNS-Runbook erforderlich;
  `docs/PHASE_C_CUTOVER_RUNBOOK.md` ist historical/superseded und nicht ausfuehrbar
- Lead-Import: `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md`

## 8. Naechster sichere Schritt
Diese Truth-Reconciliation reviewen und mergen. Danach genau einen kleinen
P0-Webhook-Sicherheits-PR mit dual-kompatiblem Legacy-/Auth-Pfad bauen und in
Preview pruefen. Production-Secret und approval-gated Redeploy folgen erst nach
Owner-Zugriff; alte Deployments werden zuletzt invalidiert. Danach den kleinen
GA4-Nachfolge-PR aus dem Diff #87/#86 umsetzen. Google-, Cloudflare-, DNS-,
Credential-, GBP- und Outreach-Aktionen bleiben getrennte Owner-Gates.
