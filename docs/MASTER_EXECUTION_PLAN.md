# MASTER_EXECUTION_PLAN — HSB-Boden / HEXAFLOOR

> **Dies ist die einzige kanonische Ausführungs-Roadmap des Projekts.**
> Keine konkurrierende Roadmap existiert. Alle anderen Phasendokumente (`PHASED_EXECUTION_PLAN.md`, `PHASE_STATUS.md`) verweisen auf diese Datei und werden nicht mehr eigenständig gepflegt.
>
> Stand: 2026-07-15, 12:06 CEST. Der Abschnitt „Aktuelle
> Ausfuehrungsreihenfolge“ ist handlungsleitend. Das nachfolgende alte
> Phasenmodell bleibt als historische Entscheidungs- und Auditspur erhalten und
> darf bei Widerspruch nicht ausgefuehrt werden.

---

## Projekt-Snapshot

| Feld | Wert |
|------|------|
| **Aktuelle Phase** | `post-deploy-security-and-owner-gates` |
| **Letzte abgeschlossene Phase** | Website-Schaltung: Pages live, Apex 301 auf www, Soft-404 und Lead-Upstream-Fehlerbehandlung produktiv behoben |
| **Nächste geplante Phase** | P0 neuen authentifizierten Pfad dual-kompatibel bauen, in Preview testen, Production atomar umstellen und alte Endpunkte zuletzt invalidieren |
| **Gesamt-Fortschritt** | Website technisch produktiv · 6.424 Outbound-Leads vorhanden und gesperrt · externe Security-, Analytics-, Google-, Compliance- und GBP-Gates offen |
| **Operativer Blocker** | Zwei oeffentlich dokumentierte Apps-Script-Endpunkte sind kompromittiert; kein Abschlussclaim und kein echter Testlead vor Invalidation/Authentifizierung |
| **Letzter Remote-Commit `main`** | `f202cb6` — Doku-Nachtrag nach Production-Deploy von `bf0a257` |
| **Kanonischer Readiness-Stack (Tier 1)** | `docs/cloudflare/CLOUDFLARE_PROVIDER_MAX_READINESS.md`, `docs/email/EMAIL_ROUTING_AND_DELIVERABILITY_MAX_READINESS.md`, `docs/analytics/GA4_GTM_GSC_MAX_READINESS.md`, `docs/assets/ASSET_PACKAGE_AND_PUBLIC_DOWNLOAD_MAX_READINESS.md`, `docs/crm/CRM_LIGHT_MAX_READINESS.md`, `docs/automation/STATUS_UPDATE_AUTOMATION_BLUEPRINT.md` |
| **Kanonischer Readiness-Stack (Tier 2, 2026-06-26)** | `docs/cloudflare/GO_LIVE_MAX_PREFLIGHT_UI_INVENTORY.md`, `docs/cloudflare/WAF_CACHE_RATE_LIMIT_READINESS.md`, `docs/cloudflare/R2_ASSET_UPLOAD_STRATEGY.md`, `docs/cloudflare/TURNSTILE_FORM_PROTECTION_READINESS.md`, `docs/analytics/GA4_GSC_EVENT_TRACKING_READINESS.md`, `docs/email/EMAIL_DELIVERABILITY_AND_TEMPLATE_READINESS.md`, `docs/assets/UTM_QR_DOWNLOAD_MATRIX.md`, `docs/crm/CRM_LIGHT_OPERATOR_READINESS.md`, `docs/automation/N8N_APPS_SCRIPT_SAFE_AUTOMATION_READINESS.md`, `docs/ops/MULTI_PC_OPERATOR_SYNC_PROTOCOL.md`, `docs/launch/PRE_DNS_GO_LIVE_MAX_CHECKLIST.md` |

---

## Gesamtziel

Die Astro-/Cloudflare-Pages-Website als belastbaren B2B-Vertrauensanker und
Lead-System betreiben: technisch sicher, suchmaschinenfaehig, messbar und mit
einer kontrollierten CRM-/Outreach-Kette. Ein Abschluss ist erst belastbar,
wenn technische Live-Evidenz und verbleibende Owner-Gates klar getrennt sind.

---

## Aktuelle Ausfuehrungsreihenfolge

### P0 — Apps-Script-Webhook absichern

**Status:** 🔴 OWNER/SECURITY GATE

Aktueller Tree redigiert zwei vormals oeffentliche Endpoint-Werte. Da beide in
der Git-Historie bleiben und anonym erreichbar waren, ist Redaktion allein
keine Behebung. Am 2026-07-15 wurde das Attributionsmapping im bestehenden
Legacy-Deployment auf Version 4 aktualisiert und mit einer danach geloeschten
Testzeile verifiziert. Das belegt das Mapping, **nicht** die Authentifizierung;
der Legacy-Pfad bleibt bis zum folgenden Cutover kompromittiert.

Reihenfolge:

1. Einen **neuen** Apps-Script-Deployment-Pfad vorbereiten, waehrend der alte
   Produktionspfad unveraendert bleibt.
2. Einen unabhaengigen Webhook-Schluessel als Apps-Script-Property verwalten;
   keine Klartextwerte in Git oder Chat.
3. Apps Script muss den Schluessel serverseitig pruefen, bevor eine Zeile
   geschrieben wird. URL-Geheimhaltung ist kein Authentifizierungsverfahren.
4. Die Pages Function in einem separaten TDD-PR dual-kompatibel erweitern:
   ohne neues Secret unveraendert Legacy-URL + Plain-Lead; mit genau **einem**
   JSON-Secret `LEAD_WEBHOOK_CONFIG` (`url` + `token`) den von Apps Script
   lesbaren Auth-Envelope senden. Ein ungueltiges konfiguriertes JSON muss
   fail-closed reagieren.
5. Den fehlenden-Config-Fallback per Unit-Test und ausschliesslich im Preview
   pruefen. Den Legacy-only-Modus **nicht** als neuen Production-Stand deployen.
6. Den neuen Apps-Script-Pfad und `LEAD_WEBHOOK_CONFIG` ausschliesslich im
   Preview-Environment mit einem eigenen Testtoken/Testziel pruefen: falscher
   Schluessel darf keine Zeile schreiben; ein markierter Testlead wird nach der
   Pruefung entfernt. Production-Token niemals in Preview verwenden.
7. Nach Preview-Freigabe `LEAD_WEBHOOK_CONFIG` zuerst als verschluesseltes
   Production-Secret setzen und danach den **gleichen geprueften
   dual-kompatiblen Commit** erstmals ueber den manuellen, approval-gated
   Production-Workflow deployen. Der bisherige Production-Deploy bleibt bis
   zu diesem atomaren Wechsel unveraendert auf dem Legacy-Pfad.
8. Im neuen Deployment das Vorhandensein der Binding-Namen ohne Ausgabe ihrer
   Werte verifizieren. URL und Auth-Vertrag wechseln damit gemeinsam beim
   Deployment, nicht bereits beim blossen Setzen des Secrets.
9. Genau einen synthetischen, loeschbaren End-to-End-Test ueber Production mit
   aktivem Sheet-Zugriff und dokumentiertem Cleanup ausfuehren.
10. Erst nach erfolgreicher Verifikation das Legacy-Secret entfernen und
   **danach** beide alten Deployment-IDs invalidieren.

**Exit:** Alte Deployments unbrauchbar, neuer Endpoint ohne gueltige
Authentifizierung ablehnend, Pages→Apps Script→CRM einmal kontrolliert belegt.

### P1 — Google/CRM-Wahrheit herstellen

**Status:** 🟠 OWNER ACCOUNT GATE

1. Profil `cherinojoel` explizit neu authentifizieren und
   `cherinojoel@gmail.com` auswaehlen.
2. Inbound-Tab und 29-Spalten-Outbound-MASTER nicht vermischen.
3. HISTORICAL COMPLETE 2026-07-15: Live-Header und Apps-Script-Attribution
   wurden gegen `docs/crm/ATTRIBUTION_CONNECTOR_PATCH.md` geprueft; sechs
   Attributionsfelder waren korrekt, die markierte Testzeile wurde entfernt.
4. CRM-Zielmodell aus `docs/crm/CRM_DEEP_DIVE_2026-07-15.md` nur additiv
   vorbereiten; bestehende Joel-/Jordi-Tabs nur nach Backup und Freigabe ersetzen.

**Exit:** Kontoidentitaet belegt, Header/Mapping belegt, keine unkontrollierte
Sheet-Mutation, Testlead nach P0 nachvollziehbar entfernt.

### P2 — GA4-Lead-Conversion belastbar machen

**Status:** 🟡 BASIC-CONSENT-CUTOVER IM GESTAPELTEN REVIEW; OWNER/LEGAL VERIFICATION OPEN

1. Basic Consent ist im Review umgesetzt: `gtag.js` wird erst nach aktiver
   Statistik-Einwilligung geladen; Code, Events und Dokumentation sind darauf
   ausgerichtet. Die Datenschutzerklärung bleibt vor Veröffentlichung rechtlich
   gegen den tatsächlich eingesetzten Dienst zu prüfen.
2. Der Cutover transportiert `generate_lead` mit PII-Allowlist, `send_to` und
   Callback-Timeout. Die Transportlogik bleibt exklusiv: `gtag` **oder**
   `dataLayer`-Fallback, nicht beide parallel.
3. Nach Preview und Merge Netzwerkrequest/DebugView real belegen und das
   kanonische Event erst dann als Key Event markieren.
4. Den nicht mergebaren PR #86 erst nach Review des neuen Cutovers als überholt
   schließen.

**Exit:** Consent-Vertrag konsistent, erfolgreicher Submit verliert das Event
nicht beim Redirect, kein PII-Pfad, DebugView/Key-Event belegt.

### P3 — Outreach-Readiness

**Status:** 🔴 GESPERRT

- 6.424 Leads sind lokal verifiziert, `Versandfreigabe` bleibt 0/6.424.
- Rechtsgrundlage, Empfaengerbasis, Opt-out, exaktes Testbatch und Owner-
  Freigabe gemaess `docs/launch/PHASE_7_COMPLIANCE_GATE.md` dokumentieren.
- M365-DKIM fuer den Versandkanal aktivieren und verifizieren.
- Kein Massenversand, kein n8n-/Apps-Script-Autodispatch.

**Exit:** Compliance und DKIM belegt; hoechstens ein separat freigegebenes
kleines Testbatch. Phase 8/9 bleiben bis zur Auswertung gesperrt.

### P4 — Nicht blockierende Owner-Cleanups

- GBP anlegen und physisch verifizieren.
- Alten Cloudflare-Preview-Worker stilllegen oder `noindex` setzen, doppelte
  Zone bereinigen und exponierte Tokens rotieren.
- Voller NS-Cutover nur optional mit neuem Pages-/Mail-DNS-Runbook; das
  historische Worker-Cutover-Runbook nicht ausfuehren.
- PR #74 als deaktivierten Draft belassen, bis echte AI-Gateway-Inferenz und
  separate Produktfreigabe belegt sind.
- Offene Alt-PRs anhand aktueller Diffs triagieren; keine Sammel-Merges.

## Historisches Phasenmodell — Auditspur, nicht direkt ausfuehren

> Die folgenden Phase-1-bis-12-Abschnitte enthalten historische Worker-, React-,
> Pages-Migrations-, Apex- und Lead-Daten-Aussagen. Sie bleiben fuer
> Nachvollziehbarkeit erhalten. Bei jedem Widerspruch gewinnen
> `PROJECT_TRUTH.md`, `CHECKPOINT_STATE.json` und die aktuelle Reihenfolge oben.

### Phase 1 — Website-Konzept & Zielbild

**Status:** ✅ COMPLETED

**Objective:** Zielbild der neuen Website und des Akquise-Systems dokumentieren; Technologieentscheidungen treffen (Astro, Cloudflare Workers, mehrsprachig).

**Deliverables:**
- Technologie-Stack definiert (Astro + Cloudflare Workers + React + Tailwind + Zod)
- Mehrsprachigkeit beschlossen (de default, en/fr/nl/pl/tr)
- Akquise-Ziel dokumentiert: organische B2B-Leads, Zielgruppe Entscheider Industrie

**Exit Criteria:** Stack, Sprachen, Zielgruppe und Parallelstrategie (neben WordPress) entschieden und dokumentiert.

---

### Phase 2 — Website-Aufbau (Astro/Cloudflare, Inhalte, Assets)

**Status:** ✅ COMPLETED

**Objective:** Vollständige Astro/Cloudflare-Website bauen: Routen, Inhalte, mehrsprachige Seiten, Assets, Dependency-Stack produktionstauglich machen.

**Deliverables:**
- Alle Seiten vorhanden: index, leistungen/[slug], branchen/[slug], wissen/[slug], referenzen, kontakt, karriere, impressum, datenschutz, danke-projektanfrage
- Strukturierte Inhalte unter `src/data/`
- Flyer-Assets committed (`9ac994a`): `public/HSB-Flyer-*.pdf`, `marketing/flyer/final/`
- Foto-Tausch auf `/referenzen/` (`f578320` → `96b9a26`): Rinnenmotiv → `saeulen-anschluss-keramik.webp`
- `services.ts`-Refactor: Modularisierung nach `src/data/services/` (`f4ece9c`)
- Dependency-Migration Astro 5→6, Tailwind 3→4 (native `@tailwindcss/vite`), `@astrojs/cloudflare` 12→13, Vite 6→7 (`5030504`)
- CI/CD: `deploy-preview.yml` auf push+PR (`ad81b4c`), Node 20→22 in 4 Workflows (`8b4b0c0`), CodeQL `permissions` fixes (`7cf06c4`)
- Tests 51/51 grün, Build grün, `npm run check` grün

**Exit Criteria:** `npm run test:run` + `npm run check` + `npm run build` grün. CI-Pipeline auf `main` durchgehend grün.

---

### Phase 3 — Website-QA & Trust-Härtung

**Status:** ✅ COMPLETED

**Objective:** Qualität, Trust-Signale und rechtliche Korrektheit der Website sicherstellen.

**Deliverables (erledigt):**
- Performance- und Accessibility-Reports vorhanden
- `npm run test:run` grün (51/51, zuletzt 2026-06-24)
- Security: CodeQL Medium-Findings behoben; AGENTS.md Non-Negotiables aktiv
- Lokale Lighthouse-Evidenz vom 2026-06-26: Performance 95, Accessibility 100, Best Practices 100, SEO 100
- Rechtstext-Abnahme abgeschlossen

**Exit Criteria:** Erfuellt.

---

### Phase 4 — Flyer- & E-Mail-Finalisierung

**Status:** ✅ COMPLETED

**Objective:** Marketing-Materialien (Flyer, Mail-Templates) auf aktuelle Website-Struktur und Rechtsstatus abgleichen.

**Deliverables (erledigt):**
- Flyer-PDFs committed und in `public/` für Direktlink verfügbar
- Mail-Templates finalisiert
- Kanonischer Outreach-Kanal dokumentiert: `j-cherino@hsb-boden.de`
- `info@hsb-boden.de` bleibt allgemeine/legal Mailbox
- `cherinodiaz@outlook.com` ist nur historischer/interner Fallback
- Materialien sind owner-approved fuer kontrolliertes manuelles Outreach-Material

**Exit Criteria:** Erfuellt. Kein realer Dispatch dadurch freigegeben.

---

### Phase 5 — CRM-Light & Lead-Control

**Status:** ✅ COMPLETED — template-ready-awaiting-lead-data

**Objective:** Minimales CRM-System für erste Lead-Erfassung und -Verwaltung aufbauen.

**Deliverables:**
- Google-Sheet „HSB CRM Light" (`1d0zZXXwYGo38ZKf0oUSSJpoZ_WVG545rDalXAdItm80`, Account `cherinojoel@gmail.com`) live
- 27 Spalten, Status-Feld `neu`, Telefon als Text (führende Null erhalten)
- Schema in `CRM_LIGHT_SCHEMA.md` dokumentiert
- Statusmodell: `neu → kontaktiert → interessiert → Angebot → gewonnen | verloren | opt-out`

**Exit Criteria:** Sheet live und erreichbar; Schema dokumentiert; Testzeilen erfolgreich geschrieben und geleert.

---

### Phase 6 — Lead-Pipeline technisch [P0B]

**Status:** ✅ COMPLETED

**Objective:** Vollständige, sichere Lead-Intake-Pipeline vom Webformular bis ins CRM implementieren und live beweisen.

**Deliverables:**
- `src/pages/api/lead.ts`: Zod-Validierung, Rate-Limit, Honeypot, Origin-Check (`hsb-boden.de`/`www`), Payload-Größen-Guard
- `src/lib/leadSchema.ts`: gemeinsames Schema (27 Felder)
- `LeadForm.tsx` → `POST /api/lead`, Flag `PUBLIC_LEAD_FORM_ENABLED`
- Google-Apps-Script-Web-App (Projekt `HSBBODEN`, cherinojoel@gmail.com) deployed: `doPost`/`doGet`, 27-Spalten-Mapping, Telefon als Text
- **n8n verworfen** (Nutzervorgabe „gratis und bleibt gratis"): ersetzt durch Apps-Script (keine Subscription)
- Secret `LEAD_WEBHOOK_URL` auf Preview-Worker und Prod-Worker gesetzt
- End-to-End verifiziert (zuletzt 2026-06-24): server-seitiger POST → `{ok:true}` → echte Zeile `WEB-20260624-023525` im CRM-Sheet; alle 27 Spalten korrekt; Testzeile geleert

**Commits:** `9df0355` (P0B Endpoint), `cf79b35` (Cloudflare-Fixes), `6203095` (n8n→Apps-Script), `a016b8c` (Merge nach main)

**Exit Criteria:** End-to-End-POST (server-seitig, kein Origin) → 200 `{ok:true}` → echte Zeile im CRM-Sheet. ✓ bestätigt.

---

### Phase 7 — Testkampagne (kontrolliert)

**Status:** ⏳ PENDING — lead-data-imported-awaiting-compliance-and-batch-approval

**Objective:** Compliance-/Import-Gate fuer einen spaeteren kontrollierten manuellen B2B-Testversand vorbereiten, ohne die Kampagne zu starten.

**Deliverables:**
- `docs/launch/PHASE_7_COMPLIANCE_GATE.md`
- `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md`
- Lead-Liste, Empfaengerbasis, Opt-out-Logik und Versandfreigabe als Pflicht-Gates dokumentiert
- Zwei-Personen-Bearbeitung vorbereitet: Joel Cherino Diaz und Jordi Post erhalten jeweils ca. 2.500 Datensaetze; passende Flyer-Anhaenge sind dokumentiert
- Manuelles Testbatch spaeter auf max. `10-20` A-Leads begrenzt
- **Neu (verifiziert 2026-07-08):** Reale Lead-Daten liegen jetzt vor. 6.424 Datensaetze lokal erzeugt (`data/lead-import/output/*.csv`) und in drei Google Sheets uebertragen (Account `cherinojoel@gmail.com`):
  - `HSB CRM Light — Kaltakquise Kampagne 2026-07 (MASTER) v2` (`1tmNuC_Wqr8blRfZCHLqpwXXOe7zyO-3SzsotaBxOzSk`), Tab `Sheet1`, 6.433 Zeilen, 23 Spalten
  - `HSB CRM Light — Jordi Post — Kaltakquise 2026-07` (`1uMbZAteSPjRBLGwpfT_evqA9hPbSTdDqPOK5TBXoFu4`), Tab `Sheet1`, 3.221 Zeilen
  - `HSB CRM Light — Joel Cherino — Kaltakquise 2026-07` (`1ha1iOX1pIWxF1c3FTRTxydqpa0uvPcBbbQ__ht1rAC8`), Tab `Sheet1`, 3.231 Zeilen
  - Diese drei Sheets sind **Kaltakquise-Ausgangslisten fuer manuellen Versand**, kein Eingang fuer die Website-Lead-Pipeline. Sie sind nicht mit `LEAD_WEBHOOK_URL` oder einem Apps-Script-Webhook verbunden und sollen es nach aktuellem Stand auch nicht sein.
  - Schema-Drift festgestellt, noch nicht bereinigt: Die Spaltenkoepfe im MASTER-Sheet (`Lead-ID, Firma, Standort, Region, Branche, Rolle, Tier, Ansprechpartner, E-Mail, ...`, 23 Spalten) weichen von `CRM_LIGHT_SCHEMA.md` (27 Spalten) und vom urspruenglichen `HSB CRM Light`-Sheet-Tab „Leads" (27 Spalten, andere Feldnamen wie `Zielrollen-Kategorie`, `Antwortstatus`) ab. Ursache nicht rekonstruiert; vor einem echten Versand sollte geklaert werden, welches Schema kanonisch ist.
  - Das urspruengliche Sheet `HSB CRM Light` (`1d0zZXXwYGo38ZKf0oUSSJpoZ_WVG545rDalXAdItm80`, Tab „Leads") bleibt das Ziel-Sheet der Website-Lead-Pipeline und ist davon unberuehrt.

**Exit Criteria:** Das Gate ist vorbereitet. Ein echter Testversand bleibt blockiert, bis alle Batch-Zeilen freigegeben sind, die Compliance-Dokumentation vorliegt, die Schema-Drift geklaert ist und der Owner das exakte Batch explizit freigibt.

**Blockiert durch:** Batch-Freigabe, Compliance-/Opt-out-Freigabe pro Einsatz, Klaerung der Schema-Drift. Reale Lead-Daten liegen nicht mehr als Blocker vor (siehe oben).

---

### Phase 8 — Hauptakquise (Skalierung)

**Status:** ⏳ PENDING

**Objective:** Skalierte B2B-Outreach-Kampagne (bis zu 5.000 Kontakte) nach Auswertung der Testkampagne.

**Deliverables:**
- Auswertung Testkampagne (Öffnungsraten, Antworten, Opt-outs)
- Skalierungsstrategie (Segmentierung A/B/C, Timing, Kanalwahl)
- 5.000er-Kampagne, sofern freigegeben

**Exit Criteria:** Testkampagne erfolgreich ausgewertet; Skalierungsfreigabe durch Inhaber.

**Blockiert durch:** Phase 7 (Testkampagne abgeschlossen); explizite Freigabe 5.000er-Kampagne.

---

### Phase 9 — Follow-up-System

**Status:** ⏳ PENDING

**Objective:** Strukturierten Follow-up-Prozess für kontaktierte Leads aufbauen.

**Deliverables:**
- Follow-up-Stufen 1–3 (4–7 Tage / 10–14 Tage / Abschluss)
- Templates für jede Stufe
- CRM-Status-Übergänge `kontaktiert → interessiert → Angebot → gewonnen/verloren/opt-out`
- Optional: Apps-Script-Automation für Reminder

**Exit Criteria:** Follow-up-Prozess dokumentiert und für mind. eine abgeschlossene Kampagnenrunde angewendet.

---

### Phase 10 — Automatisierungsausbau (Apps-Script-Basis)

**Status:** ⏸ OPTIONAL / dokumentiert deaktiviert

**Objective:** Automationsbasis über die initiale Lead-Intake-Pipeline hinaus ausbauen (Reporting, Follow-up-Trigger, Datenpflege).

**Deliverables (erledigt):**
- Apps-Script-Web-App als Webhook-Basis live (Phase 6)
- `ops/n8n/` als deprecated markiert

**Deliverables (offen/geplant):**
- Tagesreport-Aggregation im CRM-Sheet (optional)
- Follow-up-Reminder via Apps-Script (optional, nach Phase 9)
- Erweiterung nur nach expliziter Freigabe; n8n bleibt verworfen und nicht aktiv

**Exit Criteria:** Kern-Automation (Lead-Intake) stabil; optionale Erweiterungen nur nach spaeterer expliziter Freigabe.

---

### Phase 11 — Go-live-Vorbereitung

**Status:** ✅ COMPLETED

**Objective:** Alle technischen Voraussetzungen für den Production-Cutover herstellen, ohne die Live-Site zu berühren.

**Deliverables:**
- Build/Check/Dry-run grün (`npm run test:run`, `npm run check`, `npm run build`, `npm run deploy:dry-run`)
- Cutover-Bug dokumentiert und Workaround verifiziert: `wrangler deploy --env production` ignoriert `--env` mit Astro-6-Adapter still → Workaround `wrangler deploy --name hsb-boden --var ENVIRONMENT:production`
- Production-Worker `hsb-boden` **route-los deployed** (URL `https://hsb-boden.cherinojoel.workers.dev`, Version `27f7a6a0`, ENVIRONMENT=production, KV `hsb-boden-session` provisioniert)
- Secret `LEAD_WEBHOOK_URL` auf Production-Worker gesetzt
- End-to-End auf route-losem Prod-Worker verifiziert (`WEB-20260624-023525` im CRM-Sheet, 2026-06-24)
- Cutover-Runbook geschrieben: `docs/PHASE_C_CUTOVER_RUNBOOK.md`
- PR-Triage: 4 obsolete Jules-Drafts (#84/#70/#68/#54) geschlossen; 31 PRs offen (eingefroren bis Go-live)

**Exit Criteria:** Prod-Worker live und verifiziert; Secret gesetzt; Runbook vorhanden; keine Routes (Seite noch nicht live). ✓ bestätigt.

---

### Phase 12 — DNS + Live-Schaltung (Production-Cutover)

**Status:** 🟡 CURRENT — partially-live-on-pages-www-awaiting-apex-and-main-consolidation

**Objective:** Neue Astro/Cloudflare-Website unter `www.hsb-boden.de` und `hsb-boden.de` konsistent live halten und Lead-Pipeline auf der Produktionsdomäne verifizieren.

**Deliverables:**
- Erledigt: `www.hsb-boden.de/referenzen/` liefert HTTP 200 ueber Cloudflare Pages und enthaelt die korrigierten Referenzen `KESSLER-ZINK GmbH`, `Weingut Dohlmühle-Genussreich` und `Flonheim` (verifiziert 2026-07-08).
- Offen: `hsb-boden.de` ohne `www` zeigt weiterhin WordPress/Apache; `/referenzen/` liefert dort 404. Apex-Redirect auf `www` oder DNS-Anpassung bleibt freigabepflichtig.
- Offen: Pages-Worktree `pages-static-migration` muss nach Freigabe in `main` konsolidiert werden; bis dahin ist `www`-Live-Schiene nicht sauber mit `main` vereinheitlicht.
- Historisch/optional: Worker-Routes aus dem alten Runbook sind nicht mehr die aktuelle Live-Schiene fuer `www`.
- Live-Verify nach finaler Konsolidierung: `https://www.hsb-boden.de` und `https://hsb-boden.de` muessen denselben Zielzustand liefern; echtes Browser-Formular auf `/kontakt/` → Zeile im CRM-Sheet erst nach separater Formularfreigabe.
- Tracking produktiv aktivieren (GA4/GSC/GTM, vorbereitet in `SEO_GO_LIVE_CHECKLIST.md`)

**Durchführung:** Die kanonische Ausfuehrung muss zuerst die Cloudflare-Pages-Realitaet abbilden. `docs/PHASE_C_CUTOVER_RUNBOOK.md` ist fuer die historische Worker-Route-Schiene weiter Evidenz, aber nicht mehr alleinige Cutover-Wahrheit.

**Exit Criteria:**
- `curl -sI https://www.hsb-boden.de/referenzen/` → 200 ueber Cloudflare Pages
- `curl -sI https://hsb-boden.de/referenzen/` → konsistenter Zielzustand, nicht WordPress-404
- Pages-Worktree und `main` sind konsolidiert; keine zweite Code-/Deploy-Wahrheit bleibt offen
- Echtes Kontakt-Formular → Zeile im CRM-Sheet
- Alter WordPress-Fallback verifiziert nicht mehr unter produktiven Nutzerpfaden erreichbar

**Blockiert durch:** Apex-Entscheidung/DNS- oder Redirect-Freigabe, Konsolidierung des Pages-Worktrees in `main`, und spaetere Formular-/Lead-Freigabe.

---

## Nach Phase 12 — Governance

Kein formaler Phasennummern-Block, aber geplante Aufgaben nach Go-live:

- **PR-Triage (prioritär):** Security/Dependabot-PRs zuerst (#46/#47/#48/#74/#81/#82); danach ~27 Jules-/Performance-PRs als Sammelentscheidung
- **Branch-Protection:** Ruleset „Protect Main" nachschärfen (Admin-Bypass war in diesem Projekt mehrfach notwendig und ist ein Risiko)
- **PR #76 (Major-Bump React 19/Zod 4/TS 6/Vite 8):** eigene dedizierte Migration, nicht autonom mergebar
- **Untracked Planungsdocs:** Entscheidung über `PROJECT_AUDIT.md`, `docs/ops/*` (außer dieser Datei), `docs/brain/*`, `src/OPTIMIZATION.md`, `.agents/`, `.codex/`

## Final Freeze / External Input Gates

- Keine weiteren parallelen Merges oder Production-Deploys, bevor P0 und diese
  Truth-Reconciliation reviewt sind.
- Das historische `docs/PHASE_C_CUTOVER_RUNBOOK.md` darf nicht ausgefuehrt werden.
- Kein echter Lead-Test ohne authentifizierten neuen Endpoint, richtigen
  Google-Sheet-Zugriff und garantierten Testzeilen-Cleanup.
- Kein Outreach, bis Phase 7 Compliance und DKIM erfuellt sind.
- DNS/NS, Cloudflare-Altaccount, Credentials, GBP und Codex-Cloud-Umgebung sind
  separate Owner-Gates; breite Freigabe ersetzt keine physische oder
  kontogebundene Aktion.

---

## Referenzen

| Dokument | Rolle |
|----------|-------|
| `docs/MASTER_EXECUTION_PLAN.md` | Diese Datei — einzige kanonische Roadmap |
| `PROJECT_TRUTH.md` | Technischer Realstand (Cloudflare, Repo, Stack, offene Schritte) |
| `CHECKPOINT_STATE.json` | Maschinenlesbarer Ausführungsstand |
| `~/KI-System/ObsidianVault/brain/CURRENT_HANDOFF.md` | Genau eine aktuelle Implementierungsaufgabe |
| `AGENTS.md` | Repository-weite Arbeitsregeln (Non-Negotiables, Deploy Gate) |
| `docs/FINAL_PHASE_BY_PHASE_AUDIT.md` | Abschlussbeleg fuer Phasen 1-12 |
| `docs/FINAL_CLOUDFLARE_WORKERS_READINESS_AUDIT.md` | Read-only Cutover- und Workers-Readiness-Audit |
| `CLAUDE.md` | Claude-spezifische Workflow-Anweisungen |
| `docs/FINAL_OPERATOR_HANDOFF.md` | Historischer/superseded Operator-Snapshot; nicht als Resume-Start verwenden |
| `docs/FINAL_COMPLETION_REPORT.md` | Abschlussbericht der intern vervollstaendigten Vorbereitung |
| `docs/PHASE_C_CUTOVER_RUNBOOK.md` | Historische/superseded Worker-Anleitung; nicht ausfuehren |
| `CRM_LIGHT_SCHEMA.md` | CRM-Spaltenstruktur |
| `SEO_GO_LIVE_CHECKLIST.md` | SEO/Tracking Go-live-Checkliste |
| `ACQUISITION_SYSTEM_PLAN.md` | Akquise-Gesamtplan (Zielgruppen, Stufen, Mail) |
| `PHASED_EXECUTION_PLAN.md` | Veraltet — verweist auf diese Datei |
| `docs/ops/PHASE_STATUS.md` | Veraltet — verweist auf diese Datei |
