# E-Mail-Marketing v2 (Zielgruppengerechte Entwürfe, GA4-Klickmessung, Zustellbarkeit) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aus den ~5.600 vorbereiteten `.com`-Entwürfen den größtmöglichen Nutzen ziehen: zielgruppengerechte Texte (Architekten vs. Getränke/Lebensmittel), jede Interaktion in GA4 sichtbar, Zustellbarkeit nach aktuellem Community-Stand, alle Links funktionieren.

**Architecture:** Neue Vorlage v2 im bestehenden Generator (`canonical_template_factory.py`) mit zwei Segment-Texten, Text-zuerst-MIME und genau einem Inhaltslink. Der Flyer-Link zeigt auf eine Cloudflare-Pages-Function `/flyer`, die ein GA4-Ereignis serverseitig (Measurement Protocol, Secret existiert bereits für `functions/api/collect.ts`) sendet und dann zum PDF weiterleitet. Ein Austausch-Werkzeug ersetzt Entwürfe in IMAP batchweise: neuer Entwurf anhängen → alter Entwurf in Archivordner verschieben (nie löschen) → CRM `Draft_ID`/`Email_Template_ID` zurückschreiben.

**Tech Stack:** Python 3.14 (Sales-OS-Engine, pytest), TypeScript Cloudflare Pages Functions (vitest), Google Sheets API, IMAP (All-Inkl), GA4 Measurement Protocol.

**Spec:** Nutzerauftrag vom 26.10.2026 (Chat) + Befunde dieses Abends: `operations/verification/2026-10-26_iterm-chunk-tavily-claude.md` im KI-System-Root.

## Ist-Stand (gemessen 26.10.2026)

- CRM `ALL_LEADS`: 6.424 Leads; `Branche`: Architekten 4.760, Architekten-Ingenieure 52, Getraenkeindustrie 1.587, Brauerei/Getränke 12, Molkerei/Lebensmittel 13. `Segment`/`Belastungsart` leer, `Website` 6.423× gefüllt, `Ansprechpartner` 4.815×.
- Entwürfe: Joel 3.080, Jordie 2.538 (`Entw&APw-rfe`). Stichprobe: nur `text/html` (kein Textteil), 6 Links, Betreff bis >120 Zeichen, Text für Produktionsbetriebe („Keimnester in Nassbereichen“) auch an Architekten, PDF-Flyer-Verweis über `/flyer` → 302 → PDF (GA4 sieht den Klick nicht), Abmeldelink enthält die E-Mail-Adresse im Query (PII landet bei Einwilligung in GA4 `page_location`), historisches `Reply-To`.
- GA4 Property `543244027` (30 Tage): `outbound_email / email` 2 Sitzungen, `outreach / email` 1 — uneinheitliche UTM-Quellen.
- Zustellung: SPF ✅, DKIM ✅ (`kas202609210853`, dkimpy verify), DMARC `p=none` ohne `rua`, `List-Unsubscribe` ✅ (PR #473), Domain `hsb-boden.com` seit 21.09.2026.

## Global Constraints

- Kundenversand bleibt aus: `HSB_CUSTOMER_SEND_ENABLED` wird von keinem Task gesetzt; kein Task ruft `dispatch_verified(dry_run=False)` auf.
- Kein Löschen von Entwürfen: alte Entwürfe werden nach `Entwürfe-Archiv-v1` verschoben (IMAP `MOVE`/`COPY`+Flag), nie expunged ohne vorheriges erfolgreiches `COPY`.
- Einzige CRM-Wahrheit: Spreadsheet `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg`; Schreiben nur über `crm_write_readback`.
- Website-Änderungen sind freigegeben (Nutzer 26.10.2026); Production-Deploy (`deploy-production.yml`) nur nach grüner CI, nicht durch die Tasks selbst.
- Name immer „Jordie Post“; `python3 scripts/verify_ssot.py` muss vor jedem Commit Exit 0 liefern.
- UTM einheitlich: `utm_source=hsb_outreach`, `utm_medium=email`, `utm_campaign=industrieboden_v2_<architekten|produktion>`, `utm_content=<JOEL|JORDI>`.
- Lead-Kennung in URLs nur als `lid=<Lead-ID>`; keine E-Mail-Adresse, kein Name in irgendeiner URL.
- Text v2: Betreff ≤ 60 Zeichen, Fließtext (ohne Signatur/Pflichtangaben) 70–120 Wörter, genau ein Inhaltslink (`/flyer`), dazu ein Abmeldelink; kein Anhang, kein Bild, kein `Reply-To`, `text/plain` + leichtes `text/html` (multipart/alternative).
- Pflichtangaben bleiben im Footer als Text: Firma, Anschrift, Sitz, Registergericht, HRB, Geschäftsführung.
- Keine Öffnungs-Pixel (Entscheidung, siehe Task 2-Begründung im Abschnitt „Bewusste Entscheidungen“).

## Bewusste Entscheidungen (vom Nutzer überprüfbar)

1. **Keine Öffnungsmessung per Pixel.** Community-Konsens 2026: Pixel verschlechtern die Spam-Einstufung, Outlook/Firmenmail blockieren Bilder standardmäßig, Apple Mail lädt Bilder vorab (falsche „Öffnungen“). Gemessen wird stattdessen jede echte Handlung: Klick (GA4 serverseitig, Task 2), Antwort/Abmeldung/Bounce (CRM-Abgleich, besteht). Wer Pixel trotzdem will: eigener Folgeauftrag.
2. **Zwei Segmenttexte statt einem**, abgeleitet aus `Branche`: `architekten` (Architekten, Architekten-Ingenieure) und `produktion` (alle übrigen).
3. **Austausch nur für versandfähige, nicht kontaktierte Leads** (`check_eligibility` grün, `Send_Status` ≠ sent, nicht suppressed). Alle anderen Entwürfe bleiben unverändert.

## Review Focus

- Lead ohne `Ansprechpartner` und ohne verwertbaren Firmennamen → neutrale Anrede „Guten Tag,“ und Firmenbezug aus Website-Domain; nie „Sehr geehrte/r“ oder leerer Platzhalter.
- Firmenname > 45 Zeichen (z. B. „maiermaier innen:architektur, … Partnerschaftsgesellschaft“) → Betreff kürzt auf Rechtsform-freien Kernnamen, Betreff bleibt ≤ 60 Zeichen.
- Austausch bricht mitten im Batch ab (Netz, IMAP-Timeout) → Wiederaufnahme legt keinen zweiten v2-Entwurf an und verliert keinen v1-Entwurf (Journal-Zustände `APPENDED`, `ARCHIVED`, `CRM_DONE`).
- `/flyer` ohne `lid` oder mit manipuliertem `lid` → Weiterleitung zum PDF funktioniert immer; GA4-Fehler/Timeout verzögert die Weiterleitung nicht (Ereignis via `waitUntil`).
- Abmeldeseite mit altem Link (`email=` im Query, v1-Entwürfe) funktioniert weiter, erzeugt aber keinen GA4-`page_view` mit der Adresse.

---

### Task 1: Abmeldelink ohne E-Mail-Adresse, GA4-sicher

**Files:**
- Modify: `apps/website/src/pages/abmelden/index.astro:30-45`
- Modify: `apps/website/src/layouts/*` bzw. GA4-Loader (die Stelle, die `gtag('config', …)` setzt; per `rg "gtag\('config'" apps/website/src` finden)
- Modify: `apps/sales-os/engine/sales_reconciliation.py` (`assess_message`, Prüfung `PERSONAL_OPTOUT_LINK_MISSING`)
- Test: `apps/website/tests/abmelden.test.ts`, `apps/sales-os/tests/test_sales_completion.py`

**Interfaces:**
- Produces: Abmelde-URL-Schema `https://www.hsb-boden.de/abmelden?lid=<Lead-ID>&o=<JOEL|JORDI>`; Seite baut `mailto:<owner-mailbox>?subject=Abmelden&body=HSB-ABMELDUNG%3A%20<Lead-ID>` (gleiches Token wie `outbound_safety.UNSUBSCRIBE_TOKEN_RE`).

- [ ] **Step 1: Failing tests** — `test_abmelden_builds_token_mailto_for_owner` (vitest, jsdom: `?lid=HSB-20260708-01170&o=JORDI` → Link-`href` == `mailto:j-post@hsb-boden.com?subject=Abmelden&body=HSB-ABMELDUNG%3A%20HSB-20260708-01170`), `test_abmelden_legacy_email_param_still_works` (`?email=a@b.de` → mailto-Body enthält Adresse wie bisher), `test_ga4_page_location_strips_query_on_abmelden` (Loader setzt für `/abmelden` `page_location` ohne Query); pytest `test_optout_link_with_lid_is_personal` (Link `…/abmelden?lid=<lead_id>&o=JOEL` ohne `email` → kein `PERSONAL_OPTOUT_LINK_MISSING`).
- [ ] **Step 2: Run, expect FAIL** — `cd apps/website && npx vitest run tests/abmelden.test.ts`; `cd apps/sales-os && PYTHONPATH=. pytest tests/test_sales_completion.py -k optout -q`.
- [ ] **Step 3: Implement** — Seite liest `lid` (Regex `^HSB-\d{8}-\d+$`) und `o` (`JOEL`→`j-cherino@`, `JORDI`→`j-post@hsb-boden.com`, Default Joel); alter `email`-Pfad bleibt. GA4-Loader übergibt `page_location: location.origin + location.pathname` wenn Pfad mit `/abmelden` beginnt. `assess_message` akzeptiert als persönlichen Link: `lid` == Lead-ID des Entwurfs **oder** (alt) Empfängeradresse im Link.
- [ ] **Step 4: Run, expect PASS** — beide Befehle aus Step 2 sowie `npm run check`.
- [ ] **Step 5: Commit** — `fix(website,sales-os): token-based unsubscribe link without e-mail address`.

### Task 2: `/flyer` als messbare Weiterleitung (GA4 serverseitig)

**Files:**
- Create: `apps/website/functions/flyer.ts`
- Modify: `apps/website/public/_redirects` (die vier `/flyer`-Zeilen entfernen; PDF-Alias-Zeile bleibt)
- Test: `apps/website/tests/flyer-function.test.ts`

**Interfaces:**
- Consumes: Env `GA4_MEASUREMENT_ID`, `GA4_API_SECRET` (wie `functions/api/collect.ts`).
- Produces: `onRequestGet(context): Promise<Response>` → `302 Location: /HSB-Flyer-Geschaeftsfuehrer.pdf`; GA4-Event `email_flyer_click` mit Params `campaign_source`, `campaign_medium`, `campaign_name`, `campaign_content` (aus UTM), `lead_ref` (= `lid`, nur wenn Regex `^HSB-\d{8}-\d+$`), `client_id` = SHA-256(`lid` oder Zufall) gekürzt auf 16 Hex.

- [ ] **Step 1: Failing tests** — `redirects_to_pdf_with_302`, `sends_ga4_event_via_waituntil_with_utm_params` (fetch-Mock erhält `mp/collect`, Body `events[0].name == "email_flyer_click"`, `params.campaign_name == "industrieboden_v2_architekten"`), `invalid_lid_is_dropped_but_redirect_works`, `missing_ga4_secret_still_redirects`, `ga4_failure_does_not_block_redirect` (fetch rejected → Status 302).
- [ ] **Step 2: Run, expect FAIL** — `cd apps/website && npx vitest run tests/flyer-function.test.ts`.
- [ ] **Step 3: Implement `functions/flyer.ts`** — Event via `context.waitUntil(fetch(...))`; keine Cookies, keine IP-Weitergabe; Antwort-Header `Cache-Control: no-store`.
- [ ] **Step 4: Run, expect PASS** — Test aus Step 2, `npm run test:run`, `npm run build`, `npm run deploy:dry-run`.
- [ ] **Step 5: Commit** — `feat(website): measurable /flyer redirect with server-side GA4 event`.

### Task 3: Vorlage v2 mit Segmenttexten

**Files:**
- Modify: `apps/sales-os/engine/canonical_template_factory.py` (neue Funktion, alte bleibt)
- Modify: `apps/sales-os/engine/com_mailbox_manager.py:166-200` (`build_draft_message`: Parameter `body_text`, multipart/alternative ohne `mixed`, kein Anhang wenn `flyer_bytes is None`)
- Test: `apps/sales-os/tests/test_template_v2.py`

**Interfaces:**
- Produces: `segment_for(lead: dict) -> Literal["architekten","produktion"]`; `render_email_v2(lead: dict, owner: Literal["JOEL","JORDI"]) -> dict` mit Schlüsseln `subject`, `body_text`, `body_html`, `to_email`, `lead_id`, `segment`, `template_id` (= `"v2-architekten"`/`"v2-produktion"`); `short_company(name: str) -> str` (Rechtsformen `GmbH|mbH|AG|KG|GbR|PartG|PartGmbB|Partnerschaftsgesellschaft|e.K.|UG` und Zusätze nach Komma entfernt, ≤ 40 Zeichen).

Textvorgaben (exakte Kernaussagen, Wortlaut darf der Implementierer glätten, Kriterien aus Global Constraints gelten):
- `architekten`: Bezug auf Planung/Ausschreibung von Industrie- und Lebensmittelböden; Angebot: Unterstützung bei Leistungsverzeichnis, Systemwahl nach Belastungsprofil (chemisch, thermisch, mechanisch), Detailpunkte Rinnen/Fugen/Gefälle; Call-to-Action: „Darf ich Ihnen bei Ihrem nächsten Projekt einen Systemvorschlag oder LV-Textbaustein zusenden?“
- `produktion`: Bezug auf laufenden Betrieb (Getränke/Lebensmittel); Probleme Risse/Ablösungen, offene Fugen, stehendes Wasser, defekte Rinnen; Sanierung in Stillstandsfenstern; Call-to-Action: „Wann passt Ihnen ein kurzer Termin für eine Vor-Ort-Einschätzung?“
- Betreff: `architekten` → „Industrieböden in Ihren Projekten – {short_company}“; `produktion` → „Boden in der Produktion bei {short_company}“; jeweils auf 60 Zeichen gekürzt.

- [ ] **Step 1: Failing tests** — `test_segment_for_architects_and_production` (Branche „Architekten“, „Architekten-Ingenieure“ → architekten; „Getraenkeindustrie“, „Molkerei / Lebensmittelproduktion“, leer → produktion); `test_v2_subject_max_60_and_contains_short_company`; `test_short_company_strips_legal_form` (`"maiermaier innen:architektur, Innenarchitektin und Architektin Partnerschaftsgesellschaft"` → `"maiermaier innen:architektur"`); `test_v2_body_word_count_70_to_120` (ohne Signatur/Footer); `test_v2_exactly_one_content_link_and_one_optout_link` (Links ohne `mailto:`, Impressum/Datenschutz als Text-URL zählen nicht als `<a>`); `test_v2_urls_contain_no_email_or_name`; `test_v2_mime_is_multipart_alternative_with_plain_first_no_attachment_no_reply_to`; `test_v2_greeting_without_contact_is_guten_tag`; `test_v2_passes_assess_message_without_issues` (über `sales_reconciliation.assess_message`).
- [ ] **Step 2: Run, expect FAIL** — `cd apps/sales-os && PYTHONPATH=. pytest tests/test_template_v2.py -q`.
- [ ] **Step 3: Implement** — Flyer-URL `https://www.hsb-boden.de/flyer?utm_source=hsb_outreach&utm_medium=email&utm_campaign=industrieboden_v2_<segment>&utm_content=<owner>&lid=<lead_id>`; Abmelde-URL nach Task 1; `X-HSB-Lead-ID` und `X-HSB-Template: v2-<segment>` Header.
- [ ] **Step 4: Run, expect PASS** — Step-2-Befehl, dann gesamte Suite `PYTHONPATH=. pytest tests -q` und `python3 ../../scripts/verify_ssot.py`.
- [ ] **Step 5: Commit** — `feat(sales-os): segment-specific v2 outreach template, plain-text first`.

### Task 4: Entwurfs-Austausch v1 → v2 (wiederanlaufsicher)

**Files:**
- Create: `apps/sales-os/engine/draft_upgrade.py`
- Modify: `apps/sales-os/engine/hsb_cli.py` (Subcommand `upgrade-drafts --owner JOEL|JORDI --limit N [--apply]`)
- Test: `apps/sales-os/tests/test_draft_upgrade.py`

**Interfaces:**
- Consumes: `render_email_v2` (Task 3), `ComMailboxClient.build_draft_message`, `crm_write_readback`, `check_eligibility`, `sales_reconciliation.run_audit` Ausgabe `drafts.json` (Felder `lead_id`, `uid`, `uidvalidity`, `sha256`, `folder`).
- Produces: `upgrade_drafts(owner: str, limit: int, apply: bool, journal_path: Path) -> dict` mit Zählern `selected`, `appended`, `archived`, `crm_updated`, `skipped_reasons: dict[str,int]`; Journal SQLite-Tabelle `upgrade(lead_id PK, state, old_uid, old_sha256, new_message_id, updated_at)`, Zustände `PLANNED → APPENDED → ARCHIVED → CRM_DONE`.

- [ ] **Step 1: Failing tests** (Fake-IMAP wie in `tests/test_com_mailbox_manager.py`) — `test_dry_run_changes_nothing`; `test_apply_appends_v2_then_moves_v1_to_archive_then_updates_crm` (CRM-Felder `Draft_ID`=neue Message-ID, `Email_Template_ID`=`v2-<segment>`, `Drafted_At`); `test_resume_after_append_does_not_append_twice`; `test_changed_v1_hash_is_skipped` (`sha256` weicht ab → `skipped_reasons["DRAFT_CHANGED"]`); `test_ineligible_or_contacted_leads_are_not_touched`; `test_archive_folder_created_once`; `test_never_expunges_without_successful_copy`.
- [ ] **Step 2: Run, expect FAIL** — `PYTHONPATH=. pytest tests/test_draft_upgrade.py -q`.
- [ ] **Step 3: Implement** — Archivordner `Entwürfe-Archiv-v1` (IMAP-UTF-7 korrekt kodieren); `MOVE` wenn Server-Capability, sonst `COPY` → `\Deleted` → `UID EXPUNGE <uid>` nur für diese UID; Default `limit=50`.
- [ ] **Step 4: Run, expect PASS** — Step-2-Befehl, gesamte Suite, `verify_ssot.py`.
- [ ] **Step 5: Commit** — `feat(sales-os): resumable v1→v2 draft upgrade with archive, never delete`.

### Task 5: Linkprüfung aller Entwürfe

**Files:**
- Modify: `apps/sales-os/engine/sales_reconciliation.py` (Linkprüfung pro eindeutiger URL ohne Query, Cache je Lauf)
- Test: `apps/sales-os/tests/test_link_health.py`

**Interfaces:**
- Consumes: bestehendes `probe_url(url) -> dict` (`reachable`, `valid`).
- Produces: Issue `LINK_BROKEN:<host><path>` in `assess_message`-Ergebnis; Zusammenfassung `link_health: {url: status}` im Audit-JSON.

- [ ] **Step 1: Failing tests** — `test_broken_link_marks_issue` (probe 404 → Issue), `test_each_unique_link_probed_once_per_run` (1.000 Entwürfe, gleiche URL → 1 Probe), `test_redirect_to_pdf_counts_as_ok`.
- [ ] **Step 2–4:** wie oben (FAIL → Implementierung → PASS + Suite).
- [ ] **Step 5: Commit** — `feat(sales-os): verify every outreach link once per reconciliation`.

### Task 6: Rollout und Nachweis (operativ, kein neuer Code)

- [ ] **Step 1:** PR mit Tasks 1–5, CI grün, Codex `adversarial-review --base origin/main` ohne offene high-Befunde, Merge (Dauerfreigabe).
- [ ] **Step 2:** `deploy-production.yml` manuell starten (Website-Teil: `/flyer`, `/abmelden`); danach `curl -sI https://www.hsb-boden.de/flyer?lid=HSB-20260708-01170` → `302` auf PDF; GA4 Realtime (`mcp__ga4-hsb__run_realtime_report`, `eventName = email_flyer_click`) zeigt das Testereignis.
- [ ] **Step 3:** `hsb_cli.py upgrade-drafts --owner JOEL --limit 5 --apply` → 5 Entwürfe in Outlook/Webmail sichtbar prüfen (Text, Links, Abmeldelink), Journal `CRM_DONE` = 5; dann Joel/Jordie je 200er-Batches bis alle versandfähigen Leads v2 haben.
- [ ] **Step 4:** `sales-os-safety.yml mode=audit` → Audit-JSON: `HISTORICAL_VARIANT_REQUIRES_REVIEW`, `BODY_NOT_COMPANY_OR_CONTACT_SPECIFIC`, `LINK_BROKEN` = 0 für alle v2-Entwürfe; Bericht nach `operations/verification/`.
- [ ] **Step 5:** Nutzer-Aktionen dokumentieren (nicht automatisierbar ohne Zugang): Google Postmaster Tools für `hsb-boden.com` verifizieren (DNS-TXT, braucht KAS), DMARC `rua`, `www.hsb-boden.com`-CNAME → Pages. Versand-Hochlauf bleibt bei `DAILY_CAP_PER_MAILBOX = 35` und 45–90 s Abstand, bis Bounce < 2 % und Beschwerden < 0,1 % über 2 Wochen belegt sind.
