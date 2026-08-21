# PROJECT_TRUTH — HSB-Boden / HEXAFLOOR

> Single Source of Truth fuer den **aktuellen** Projektstand. Stand: 2026-08-11, siehe Abschnitt 2b.
> Historischer Verlauf gehoert in `SESSION_LOG.md` oder Archive, nicht hier hinein.
> Unklare Punkte sind als `unklar / zu pruefen` markiert.
>
> Gesamturteil: `pages-live-website-audit-abgeschlossen-owner-gates-remain`
>
> Historische Worker-, WordPress-, Pages-Migrations- und PR-Snapshots sind nicht
> mehr handlungsleitend. Zeitgebundene Zahlen (PR-Anzahl, Deployment-Run-IDs)
> gelten nur zum jeweils genannten Zeitpunkt.

## 1. Kanonischer Arbeitsort
- Repo: `/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden`
- Legacy-Pfade wie `_MERGED_20260613`, alte Klone oder Backups sind **nicht** kanonisch.

## 2. Aktueller Repo-Zustand
- Remote-HEAD: `6dd7095` (`origin/main`, verifiziert 2026-08-07 18:00 CEST).
  Das lokale Root-Worktree ist auf demselben Commit; getrackte Dateien waren zu
  Sitzungsbeginn unveraendert.
- Zum Snapshot 2026-08-07 sind 12 Pull Requests offen; diese Zahl ist
  zeitgebunden und keine dauerhafte Projekteigenschaft.
- PR #59 (3D-Site-Survey/KAGETEC) ist offen und `MERGEABLE`, bleibt aber bewusst
  ungemergt, solange die Medien-/Markenfreigaben fehlen. Die Website ist ohne
  PR #59 vollstaendig.
- Website-Finalisierungsaudit 2026-08-07: Branch `chore/website-final-audit`
  (siehe Abschnitt 2a). Nicht gepusht, nicht gemergt, nicht deployt.

### 2a. Website-Finalisierungsaudit 2026-08-07
Behoben auf `chore/website-final-audit`, ausgehend von `6dd7095`:
- **Referenz-Duplikate (P0):** `Meggle` und `Biovegan GmbH` waren gleichzeitig
  freigegebene Referenz und Kundenstandort und erschienen doppelt — im LogoCloud
  der Startseite, als doppelter Kartenmarker und in der Liste "Weitere
  Kundenstandorte" auf `/` und `/referenzen/`. Zuordnung laeuft jetzt ueber eine
  kanonische `referenceId` in `clientLocations.ts`, nicht ueber Namensvergleich;
  die freigegebene Referenz hat Vorrang. Guard: `tests/reference-deduplication.test.ts`.
- **Testlauf war nicht aussagekraeftig (P0):** `vitest` sammelte die Testdateien
  der lokalen `.worktrees/`-Kopien mit ein (136 statt 19 Dateien, zwei Fehler aus
  altem Worktree-Code). `vitest.config.ts` schliesst diese Pfade jetzt aus.
- **WebSite-Schema fehlte (P1):** Die Startseite lieferte kein `WebSite`-JSON-LD
  und damit keinen definierten Sitenamen. Ergaenzt, bewusst ohne `SearchAction`
  (die Website hat keine Suchfunktion).
- **Sitemap unvollstaendig (P1):** `/impressum/` und `/datenschutz/` sind
  indexierbar und im Footer verlinkt, fehlten aber in `sitemap.xml`.
  `scripts/check-sitemap-consistency.mjs` prueft jetzt beide Richtungen.
- **Formular (P2):** `autocomplete`-Tokens auf den Personenfeldern ergaenzt
  (WCAG 1.3.5).

Gemessen, aber bewusst **nicht** geaendert (Owner-Entscheidung):
- **CLS beim Sprachbanner.** `LanguageSuggest.astro` ist initial `hidden` und
  wird per JS eingeblendet, wenn die Browsersprache nicht Deutsch ist. Das
  schiebt den gesamten Inhalt um 16 px nach unten. Gemessen auf `/`:
  de-DE 0.092 mobile / 0.004 desktop (beide im gruenen Bereich <= 0.1),
  en-US 0.264 mobile / 0.046 desktop. Die deutsche Hauptzielgruppe ist also
  nicht betroffen, internationale Besucher der deutschen Startseite schon.
  Ein sauberer Fix muesste die Sprachentscheidung vor dem ersten Paint treffen
  (synchrones `<head>`-Script + CSS-Klasse auf `<html>` statt `hidden`-Toggle)
  und tauscht damit CLS gegen ein render-blockendes Skript — das ist eine
  Abwaegung fuer den Owner, kein reines Polishing, deshalb hier nur belegt.
- **Meta-Descriptions ueber 160 Zeichen** auf 15 Seiten (166–217). Werden in der
  Suche abgeschnitten, sind aber inhaltlich korrekt; ein Umschreiben aller
  Texte waere ein Content-Refactoring ausserhalb dieses Audits.

### 2b. Website-Finalisierungsaudit 2026-08-11 (JobPosting/Legal), auf `chore/website-final-audit`
Ausgehend von `origin/main` = `6dd7095` (verifiziert per `git fetch` + `git log`). Lokaler
Branch war zu Sitzungsbeginn 2 Commits vor `origin/main` (Referenz-Dedup vom 2026-08-07,
siehe 2a) und working tree clean.

- **JobPosting-Array (P0, Search-Console-Fund):** `/karriere/` enthielt ein JSON-LD-Array
  aus 3 `JobPosting`-Objekten in einer URL — Google erwartet eine Seite pro Stelle. Behoben:
  `/karriere/` ist jetzt reine Übersicht ohne JobPosting-Markup, drei neue Detailseiten
  `/karriere/fliesenleger/`, `/karriere/bauhelfer/`, `/karriere/projektleitung-industrieboden/`
  mit je genau einem `JobPosting`. Sichtbarer Text und JSON-LD-`description` sind identisch
  (`job.fullDescription`). Guard: `tests/jobposting-structure.test.ts`.
  - `datePosted`: `2026-06-05`, belegt per `git log --follow -- src/pages/karriere/index.astro`
    (initialer Commit `6b6d85e`, die drei Rollen waren von Anfang an sichtbar). Nicht das
    zuvor erfundene `2026-01-01`.
  - `jobLocation`: Benzstraße 6, 48599 Gronau, Nordrhein-Westfalen, DE — vom Owner in dieser
    Sitzung explizit bestätigt als realer Meldeort/Dispositionsbasis, auch wenn die Tätigkeit
    auf wechselnden Kundenbaustellen stattfindet.
  - `baseSalary`, `validThrough`, `directApply`: bewusst **nicht** gesetzt (INTENTIONALLY
    OMITTED) — kein belegter Gehaltswert, keine reale Bewerbungsfrist, kein dedizierter
    Direct-Apply-Flow (Bewerbung läuft über die allgemeine Kontaktseite `/kontakt/`).
- **Legal-Runtime-Mismatch (P1):** Impressum zitierte noch `§ 7, §§ 8-10 TMG` → jetzt `DDG`
  (TMG durch das Digitale-Dienste-Gesetz abgeloest, Paragraphenzaehlung fuer diese Normen
  unveraendert). Datenschutzerklaerung zitierte `§ 25 TTDSG` (5 Stellen) → jetzt `TDDDG`
  (gleiche Umbenennung, TTDSG → Telekommunikation-Digitale-Dienste-Datenschutz-Gesetz).
  Hosting-Absatz nannte noch All-Inkl, obwohl die Website seit dem Pages-Cutover auf
  Cloudflare Pages laeuft — Absatz auf Cloudflare (inkl. EU-Niederlassung, Privacy-Policy-Link)
  umgestellt.
- **Nicht angefasst, dokumentiert offen:** Die Absaetze zu "Real Cookie Banner" (WordPress-
  Plugin) und "Meta Conversions API" in `datenschutz/index.astro` beschreiben Dienste, die im
  aktuellen Astro/Cloudflare-Code nicht auffindbar sind (kein Treffer fuer `RealCookieBanner`,
  `devowl`, `facebook`/`fbclid`/`_fbp`/`graph.facebook` im Quellcode außer im Text selbst).
  Tatsaechlich implementiert: eigene `CookieConsent.astro`-Komponente, GA4 via `gtag.js`
  (`G-VC4BJBEFTV`, `src/lib/analytics.ts`), Cloudflare Web Analytics Beacon
  (`static.cloudflareinsights.com`, `src/layouts/BaseLayout.astro`). OWNER/LEGAL REVIEW
  REQUIRED: pruefen, ob diese zwei Absaetze aus einer fruehereren WordPress-Fassung stammen
  und entfernt/ersetzt werden muessen, oder ob die Dienste serverseitig außerhalb dieses Repos
  tatsaechlich noch laufen. Nicht eigenmaechtig geloescht, da bereits bestehender Rechtstext.
- **CSP (P2, unveraendert):** `public/_headers` setzt `frame-ancestors`, `base-uri`,
  `form-action`, aber keine `script-src`/`connect-src`/`img-src`/`default-src` — bewusst als
  separates Audit zurueckgestellt (Kommentar im Header-File), keine Regression durch diese
  Sitzung.
- **Security/Contact-API (verifiziert, keine Aenderung noetig):** `functions/api/lead.ts`
  hat eigene Header (`Cache-Control: no-store`, `nosniff`, `Referrer-Policy: no-referrer`),
  strikte Origin-Allowlist, Payload-Limit 16 KB, JSON-Tiefenlimit, IP-/E-Mail-Rate-Limiting
  ueber KV, 6s-Webhook-Timeout, Acknowledgement-Pflicht, keine PII in Logs. Kein P0/P1-Fund.
- **Frisch verifiziert (2026-08-11):** `npm run test:run` 178/178 gruen (23 Dateien),
  `npm run check` 0 Fehler/0 Warnungen/6 Hints (vorbestehend, nicht in dieser Sitzung
  geaendert), `npm run build` 50 Seiten, `npm run check:sitemap` OK (49 URLs konsistent),
  `npm run deploy:dry-run` Pages-Function-Build erfolgreich — jeweils zweimal frisch
  ausgefuehrt: einmal vom implementierenden Agenten, einmal unabhaengig vom
  Reviewer-Subagenten (siehe unten), beide Male mit identischem Ergebnis.
- **Unabhaengiges Review (2026-08-11, abgeschlossen):** Ein frischer Subagent ohne
  Implementierungskontext hat den Diff gegen `origin/main`, die JobPosting-Struktur im
  gebauten `dist/`, `datePosted` gegen `git log --follow`, den Production-Deploy-Run und
  die Konventionstreue zu `leistungen/[slug].astro` geprueft. Ein P1 wurde dabei gefunden
  und sofort behoben: eine fruehere Fassung dieses Abschnitts hatte das Review-Ergebnis im
  Perfekt beschrieben, bevor die Pruefung abgeschlossen war (unbelegte Fertig-Behauptung).
  Nach Abschluss der Pruefung: keine weiteren P0/P1 in den auditierten Dateien. Die
  TMG→DDG/TTDSG→TDDDG-Rechtsbehauptung (2024 in Kraft, gleiche Paragraphenzaehlung) ist
  repo-seitig nicht verifizierbar und bleibt insofern eine technische Korrektur ohne
  eigene juristische Zweitmeinung — OWNER/LEGAL REVIEW REQUIRED bei Zweifel.
- **Production-Stand (frisch verifiziert per `gh run list`):** Letzter erfolgreicher
  `Deploy Production`-Run `30833838880` (2026-08-03T16:48:26Z) deployte Commit `6a946ca`.
  `origin/main` steht seither einen Commit weiter auf `6dd7095` (PR #228, 2026-08-04) —
  Production ist also **einen Commit hinter `main`** (Referenzen-Fix/Content-Cluster/
  Standortseiten aus #228 sind auf `main`, aber noch nicht deployt). Kein Deploy in dieser
  Sitzung ausgeloest.
- Nicht in dieser Sitzung angefasst: PR #59 (3D/KAGETEC, bleibt ungemergt), CRM/Outreach,
  n8n, DNS, alle in Abschnitt 6/7 gelisteten Owner-Gates.

### 2c. CRM/Outreach-Finalisierungslauf 2026-08-11 (kein Code-Diff, nur Doku/Analyse)
Reconciliation gegen einen extern zugelieferten Masterauftrag (HEXAFLOOR
CRM+Outreach Finalization Command). Details, Zahlen, Tool-Recherche und
DNS-Korrektur: `docs/crm/CRM_FINALIZATION_2026-08-11.md`. Kernpunkte:
- CSV-Parsing-Fehler einer früheren Session korrigiert: `Versandfreigabe = no`
  für alle 6.424 Leads bestätigt (nicht `unknown`, wie `CRM_DATENQUELLE_WAHRHEIT.md`
  vorher fälschlich zeigte) — Wert bewusst **nicht** verändert.
- `MASTER_5000`-Exportwelle als veraltet identifiziert (712 Owner-Neuzuordnungen
  ggü. der gültigen 6.424er-Welle); `RESERVE`-Datei (1.424 Zeilen) überlappt
  zu 100 % mit `ALL_MASTER`, ist keine zusätzliche Quelle.
- DNS-Korrektur: `hsb-boden.de` ist per `dig NS` autoritativ bei
  All-Inkl/Kasserver (`ns5/ns6.kasserver.com`), nicht Cloudflare — Cloudflare-Zone
  bleibt `pending` (siehe Abschnitt 4). Jede künftige Outreach-DNS-Änderung muss
  im Kasserver-Kundenmenü erfolgen, nicht im Cloudflare-Dashboard.
- Versandtool-Recherche (offizielle Quellen): Smartlead (Pro-Plan) als
  `BEST_OVERALL_TOOL` empfohlen, da eigene Sende-Infrastruktur den
  M365-DKIM-Blocker umgeht; Mailmeteor bestätigt ungeeignet (sendet über die
  bestehende M365-Mailbox, erbt die DKIM-Lücke); keine tragfähige
  Free-/Zero-Cost-Option für 6.424 Leads gefunden (ehrlich benannt).
- Kein Versand, kein DNS-Write, kein Tool-Kauf, kein Commit/Push in diesem Lauf.
  `docs/crm/CRM_DATENQUELLE_WAHRHEIT.md` korrigiert (additiv).

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

### 3a. WHG-Fachbetrieb-Zertifizierung (Owner-Bestaetigung 2026-08-03)

Der Claim "Zertifizierter WHG-Fachbetrieb" (Startseite-Hero, Chemieindustrie-
Branchenseite) wurde am 2026-08-03 vom Owner (Joel Cherino Diaz) muendlich
bestaetigt: ein echtes Zertifikat/eine echte Urkunde existiert, wird aber
bewusst nicht ins Repo hochgeladen (Zertifikate gehoeren nicht in ein
oeffentliches Git-Repo). Kein Dokumentbeleg im Repo einsehbar oder erforderlich
fuer Claude Code — dieser Vermerk haelt die Owner-Aussage fest, damit der Claim
bei zukuenftigen Audits nicht faelschlich als unbelegt markiert wird. Der Claim
bleibt auf der Website unveraendert bestehen.

## 4. Aktueller Cloudflare- und Domain-Stand
- Cloudflare Pages Projekt: `hsb-boden`
- Aktuelle Live-Schiene fuer `www.hsb-boden.de`: Cloudflare Pages (`hsb-boden.pages.dev`)
- Letzter dokumentierter Production-Source-Commit: `bf0a257` (Deployment-Run
  `29404977846`, Stand 2026-07-15). Seither **nicht erneut verifiziert** — der
  Audit vom 2026-08-07 hat bewusst nichts deployt. Vor der naechsten Freigabe
  den tatsaechlichen Production-Stand in Cloudflare Pages selbst nachsehen,
  diese Zeile nicht als aktuelle Deploy-Wahrheit lesen.
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
