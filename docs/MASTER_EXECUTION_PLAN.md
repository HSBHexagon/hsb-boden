# MASTER_EXECUTION_PLAN — HSB-Boden / HEXAFLOOR

> **Dies ist die einzige kanonische Ausführungs-Roadmap des Projekts.**
> Keine konkurrierende Roadmap existiert. Alle anderen Phasendokumente (`PHASED_EXECUTION_PLAN.md`, `PHASE_STATUS.md`) verweisen auf diese Datei und werden nicht mehr eigenständig gepflegt.
>
> Stand: 2026-06-26. Rekonstruiert aus: `PHASE_STATUS.md`, `CHECKPOINT_STATE.json`, `PROJECT_TRUTH.md`, `AI_EXECUTION_PLAYBOOK.md`, `ACQUISITION_SYSTEM_PLAN.md`, `AGENTS.md`, `CLAUDE.md`, `brain/CURRENT_HANDOFF.md`.

---

## Projekt-Snapshot

| Feld | Wert |
|------|------|
| **Aktuelle Phase** | `internal-base-ready-awaiting-dns-and-leads` · Phase 7 wartet auf reale Lead-Daten; Phase 12 bleibt extern blockiert |
| **Letzte abgeschlossene Phase** | Phase 11 — Go-live-Vorbereitung |
| **Nächste geplante Phase** | DNS/NS-Switch abwarten + spätere 5.000-Lead-Dateneinfügung; danach erst kontrolliertes Phase-7-Testbatch |
| **Gesamt-Fortschritt** | Website ~95% · Go-live-Readiness ~90% · Akquise-System ~50% |
| **Operativer Blocker** | Externer NS-/DNS-Switch (Zone `hsb-boden.de` = `pending`, Domain-Admin) |
| **Letzter Commit `main`** | `296d757` — `docs(hsb): add final operator handoff freeze` |

---

## Gesamtziel

Parallel zur bestehenden WordPress-Live-Site eine neue Astro/Cloudflare-Website (`hsb-boden.de`) aufbauen, die als **Premium-Vertrauensanker und B2B-Akquise-System** für organische Industrieboden-Leads dient — bis zur finalen Freigabe des Cutover.

---

## Phasenmodell

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

**Status:** ⏳ PENDING — gate-prepared-awaiting-lead-data

**Objective:** Compliance-/Import-Gate fuer einen spaeteren kontrollierten manuellen B2B-Testversand vorbereiten, ohne die Kampagne zu starten.

**Deliverables:**
- `docs/launch/PHASE_7_COMPLIANCE_GATE.md`
- `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md`
- Lead-Liste, Empfaengerbasis, Opt-out-Logik und Versandfreigabe als Pflicht-Gates dokumentiert
- Manuelles Testbatch spaeter auf max. `10-20` A-Leads begrenzt

**Exit Criteria:** Das Gate ist vorbereitet. Ein echter Testversand bleibt blockiert, bis reale Lead-Daten vorliegen, alle Batch-Zeilen freigegeben sind, die Compliance-Dokumentation vorliegt und der Owner das exakte Batch explizit freigibt.

**Blockiert durch:** Fehlende reale Lead-Daten, fehlende Batch-Freigabe, fehlende Compliance-/Opt-out-Freigabe pro Einsatz.

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

**Status:** 🟡 CURRENT — blocked-awaiting-dns-ns-switch

**Objective:** Neue Astro/Cloudflare-Website unter `hsb-boden.de` live schalten und Lead-Pipeline auf der Produktionsdomäne verifizieren.

**Deliverables:**
- Externer NS-/DNS-Switch: Domain-Admin setzt Nameserver → Zone `hsb-boden.de` wechselt von `pending` auf `active`
- Zwei Worker-Routes setzen (Zone `2aefa04f69a2339b2f9f3f2876d7e35c`):
  - `hsb-boden.de/*` → script `hsb-boden`
  - `www.hsb-boden.de/*` → script `hsb-boden`
- Live-Verify: `curl -sI https://hsb-boden.de` = 200 vom Worker; echtes Browser-Formular auf `/kontakt/` → Zeile im CRM-Sheet
- Tracking produktiv aktivieren (GA4/GSC/GTM, vorbereitet in `SEO_GO_LIVE_CHECKLIST.md`)

**Durchführung:** Strikt nach `docs/PHASE_C_CUTOVER_RUNBOOK.md`, Schritte 5–6. Worker **vor** Routes prüfen — nach NS-Switch greift die Route sofort.

**Exit Criteria:**
- Zone `active` (nach NS-Switch durch Domain-Admin)
- `curl -sI https://hsb-boden.de` → 200 vom Worker (nicht WordPress)
- Echtes Kontakt-Formular → Zeile im CRM-Sheet
- Alter WordPress-Fallback verifiziert nicht mehr erreichbar

**Blockiert durch:** NS-/DNS-Switch (externer Domain-Admin, Zone `hsb-boden.de` = `pending`, Stand 2026-06-26). Danach freigabepflichtig.

---

## Nach Phase 12 — Governance

Kein formaler Phasennummern-Block, aber geplante Aufgaben nach Go-live:

- **PR-Triage (prioritär):** Security/Dependabot-PRs zuerst (#46/#47/#48/#74/#81/#82); danach ~27 Jules-/Performance-PRs als Sammelentscheidung
- **Branch-Protection:** Ruleset „Protect Main" nachschärfen (Admin-Bypass war in diesem Projekt mehrfach notwendig und ist ein Risiko)
- **PR #76 (Major-Bump React 19/Zod 4/TS 6/Vite 8):** eigene dedizierte Migration, nicht autonom mergebar
- **Untracked Planungsdocs:** Entscheidung über `PROJECT_AUDIT.md`, `docs/ops/*` (außer dieser Datei), `docs/brain/*`, `src/OPTIMIZATION.md`, `.agents/`, `.codex/`

## Final Freeze / External Input Gates

- Die Roadmap ist intern reconciled und bleibt bis zu einem externen Trigger eingefroren.
- Das Projekt soll operativ nicht weiterlaufen, solange weder der DNS/NS-Switch noch der reale 5.000-Lead-Datensatz vorliegt.
- Phase 12 folgt ausschließlich `docs/PHASE_C_CUTOVER_RUNBOOK.md`.
- Lead-Daten folgen ausschließlich `docs/launch/LEAD_IMPORT_5000_CHECKLIST.md`.
- Phase 8 und Phase 9 bleiben gesperrt, bis Phase 7 mit realen Lead-Daten, Lead-Validierung und Batch-Freigabe fortgesetzt werden darf.

---

## Referenzen

| Dokument | Rolle |
|----------|-------|
| `docs/MASTER_EXECUTION_PLAN.md` | Diese Datei — einzige kanonische Roadmap |
| `PROJECT_TRUTH.md` | Technischer Realstand (Cloudflare, Repo, Stack, offene Schritte) |
| `CHECKPOINT_STATE.json` | Maschinenlesbarer Ausführungsstand |
| `~/KI-System/ObsidianVault/brain/CURRENT_HANDOFF.md` | Genau eine aktuelle Implementierungsaufgabe |
| `AGENTS.md` | Repository-weite Arbeitsregeln (Non-Negotiables, Deploy Gate) |
| `CLAUDE.md` | Claude-spezifische Workflow-Anweisungen |
| `docs/FINAL_OPERATOR_HANDOFF.md` | Finaler Freeze-/Trigger-Handoff fuer den naechsten Operator |
| `docs/FINAL_COMPLETION_REPORT.md` | Abschlussbericht der intern vervollstaendigten Vorbereitung |
| `docs/PHASE_C_CUTOVER_RUNBOOK.md` | Schritt-für-Schritt-Anleitung Phase 12 |
| `CRM_LIGHT_SCHEMA.md` | CRM-Spaltenstruktur |
| `SEO_GO_LIVE_CHECKLIST.md` | SEO/Tracking Go-live-Checkliste |
| `ACQUISITION_SYSTEM_PLAN.md` | Akquise-Gesamtplan (Zielgruppen, Stufen, Mail) |
| `PHASED_EXECUTION_PLAN.md` | Veraltet — verweist auf diese Datei |
| `docs/ops/PHASE_STATUS.md` | Veraltet — verweist auf diese Datei |
