# E-Mail-Marketing v2 ohne DNS-Zugang — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mit ausschließlich vorhandener Infrastruktur (kein KAS/DNS) die Bounce-Quote unter 2 % bringen, die knappen Versandplätze nach Fit priorisieren (Produktion zuerst), zielgruppengerechte 3-Schritt-Sequenzen in reinem Text bereitstellen und den Nutzen an positiven Antworten messen — Klicks nur als Nebensignal, ohne Pixel.

**Architecture:** Bestehendes Sales-OS (Google Sheets CRM → Python-Engine → All-Inkl IMAP/SMTP) wird um Listenhygiene, Fit-Score, Sequenz, Hochlauf/Stopp und Entwurfsaustausch erweitert. Website (Cloudflare Pages, `hsb-boden.de`) bekommt eine echte `/flyer`-Landingpage (GA4 misst dort wie überall nach Einwilligung) und einen Klick-Zähler `/r/<token>` mit Scanner-Filter, der nur in einen eigenen Speicher (Cloudflare KV) schreibt; ein Abgleich überträgt Klicks in einen CRM-Tab `CLICK_EVENTS`.

**Tech Stack:** Python 3.14 (pytest), TypeScript Pages Functions (vitest), Cloudflare KV (Anlage und Binding per Cloudflare-API mit vorhandenem Zugang), Google Sheets API, IMAP/SMTP All-Inkl; Website-Text nur mit Standardbibliothek (`html.parser`) über den gehärteten Fetcher `bounce_rescue_agent.build_public_opener` — keine neue Abhängigkeit.

**Spec:** Bericht `~/KI-System/reports/HSB Kaltakquise ohne DNS Zugriff.md` (Tiefenrecherche 27.10.2026, Notizen in `~/KI-System/research_notes/HSB Kaltakquise ohne DNS Zugriff/`); Codex-Strategiereview 26.10.2026; Nutzervorgabe 27.10.2026: KAS ausgeschlossen, Google-Konten im Browser nutzbar.

## Ist-Stand (gemessen, nur Zählungen)

- CRM 6.424: Architekten 4.812 (Fit-Schlagworte + 502 / − 454 / unklar 3.856), Produktion 1.612 (≈ 1.478 noch nicht kontaktiert).
- Historie 1.069 gesendet: Produktion 7/134 Reaktionen, Architekten 8/935; **Bounces 63 = 5,9 %**.
- Zustellung: SPF ✅, DKIM ✅ `d=hsb-boden.com` (`kas202609210853`, dkimpy verify auf 6 Mails) — damit auch GMX/Web.de-Ausrichtung erfüllt; DMARC `p=none`; Sende-IP 85.13.130.17 auf keiner geprüften Blockliste (26.10.).
- `/flyer` auf `main`: `_redirects` 302 → `/HSB-Flyer-Geschaeftsfuehrer.pdf` („bis zur Landingpage-Freigabe“); eine Landingpage existiert nur auf Branch `feature/closed-loop-tracking-crm` (Commit `3731a83`, `apps/website/src/pages/flyer/index.astro`).
- Entwürfe: nur HTML, 6 Links, lange Betreffs, E-Mail-Adresse im Abmeldelink.

## Global Constraints

- Kein KAS/DNS: keine Aufgabe ändert DNS, DMARC, Postmaster, CNAMEs oder Hosting-Einstellungen.
- Kein Kundenversand: kein Task setzt `HSB_CUSTOMER_SEND_ENABLED` oder ruft `dispatch_verified(dry_run=False)`; der Pilotversand (Task 10) startet nur nach ausdrücklicher Nutzerfreigabe im Chat. Seed-Testmails (Task 2) gehen nur an die vom Nutzer bestätigte Seed-Liste über `HSB_INTERNAL_TEST_SEND_ENABLED`.
- Nie Entwürfe löschen: v1 wird nach `Entwürfe-Archiv-v1` verschoben (COPY vor jedem `UID EXPUNGE` einer einzelnen UID); Ordnernamen in modifiziertem UTF-7, für `UID MOVE` selbst quoten.
- Versand-/Sperrhistorie nie zurücksetzen; Folgekontakte zählen in dieselbe Tagesgrenze, domainweit beide Postfächer zusammen.
- CRM-Schreiben nur über `crm_write_readback`; `Tier`/`Score` nur in leere Zellen.
- In keiner URL E-Mail-Adresse oder Name; an GA4 nie Lead-Bezug (GA4 nur über die normale, einwilligungsabhängige Website-Messung).
- Text v2: reiner Text (`text/plain` als einziger Teil oder multipart/alternative mit Textteil zuerst und minimalem HTML), Siezen, Betreff 2–5 Wörter (≤ 50 Zeichen), Erstmail höchstens ein Link, Folgemails ohne Link, Durchwahl/Mobil in der Signatur, Pflichtangaben als Text, Abmeldezeile („Antworten Sie mit ‚Abmelden‘“) + `List-Unsubscribe`-Header (besteht).
- `python3 scripts/verify_ssot.py` Exit 0 vor jedem Commit; „Jordie Post“.

## Korrekturen nach Verifikation (27.10.2026)

Plan gegen den Code von `main` (`6cb0083`) geprüft; Basis 246 passed, 1 skipped. Alle genannten Schnittstellen existieren. Geändert:

1. **Kein `trafilatura`:** auf dem Mac nicht installierbar ohne Eingriff in Homebrew-Python (PEP 668); Stichwortsignale brauchen keine Boilerplate-Entfernung. Text per `html.parser` (ohne `script/style/nav/footer`), Abruf über `build_public_opener()` (SSRF-Schutz, Redirect-Prüfung) mit 2 MB / 20 s wie in PR #475.
2. **`wrangler.toml` bleibt unverändert:** Bindings werden laut Datei bewusst am Pages-Projekt per API verwaltet. `EMAIL_CLICKS` und `CLICK_SECRET` werden in Task 10 gesetzt; ohne Binding oder Secret liefert `/r/<token>` trotzdem 302 (zählt nicht).
3. **`/Flyer` (großes F) bleibt erreichbar:** Pages unterscheidet Groß-/Kleinschreibung; `_redirects` erhält `/Flyer /flyer/ 301`, nur `/flyer` und `/flyer/` → PDF entfallen; `/HSB-HEXAGON-Industrieboeden-Flyer.pdf` bleibt.
4. **Inhalte gegen `AGENTS.md`-Non-Negotiables:** Landingpage und v2-Texte ohne Zertifizierungs-/Partnerschafts-/Referenzbehauptungen, ohne Kundennamen/Logos/Standorte. IFS/BRC nur als Thema des Empfängers („Ihr nächstes Audit“), nie als Aussage über HSB.
5. **Freigabepunkte in Task 10:** Implementierung, PR, Merge (Dauerfreigabe), lesende Live-Läufe und Dry-Runs laufen ohne Rückfrage. Gebündelt freigegeben werden müssen: Production-Deploy, KV/Secret am Production-Projekt, `score-leads --apply`, `upgrade-drafts --apply` (verschiebt Kundenentwürfe), `seed-send`, Pilotversand.

## Bewusste Entscheidungen

1. **Keine Öffnungs-Pixel; GA4 ohne Lead-Bezug.** Klicks werden first-party gezählt (KV), mit Scanner-Filter, und nur als „unbestätigt/vermutlich Mensch“ ausgewiesen. Primäre Kennzahl: positive Antworten je kontaktiertem Unternehmen.
2. **Produktion zuerst**, Architekten erhalten 15–20 % der Plätze als Testgruppe, bis die Produzenten-Liste ausgeschöpft ist.
3. **Ein großer Test je Zielgruppe** (neuer Text gegen alten), keine Einzeltests von Betreff oder CTA — das Volumen reicht nicht. Architekten-Kontrollgruppe = die 935 historischen Sendungen.
4. **Website-Klassifikation zuerst per Schlagwort**, LLM-Einordnung erst in einem Folgeauftrag (braucht einen API-Schlüssel, der nicht eingerichtet ist).

## Review Focus

- Lead ohne Ansprechpartner → „Guten Tag,“; nie leere Platzhalter.
- Firmenname > 40 Zeichen → `short_company` kürzt; Betreff ≤ 50 Zeichen.
- Abbruch im Entwurfsaustausch → keine Duplikate, kein verlorener v1 (Journal `PLANNED → APPENDED → ARCHIVED → CRM_DONE`).
- Link-Scanner (HEAD, Rechenzentrums-ASN, Mehrfachklick < 10 s, ungültiges Token) → Klick wird als `bot` gespeichert, nie als Mensch.
- Bounce-Spitze am ersten Versandtag → Pause greift vor der nächsten Mail.

---

### Phase A — Messen und bereinigen

### Task 1: Bounce-Auswertung, Sperrliste und Zustellbarkeits-Flags

**Files:** Create `apps/sales-os/engine/lead_quality.py`; Modify `apps/sales-os/engine/hsb_core.py` (`check_eligibility`); Modify `apps/sales-os/engine/hsb_cli.py` (`bounce-report`); Test `apps/sales-os/tests/test_lead_quality.py`

**Interfaces:**
- Consumes: `enrich_company_names.check_domain_mx(domain) -> bool`; Bounce-Nachrichten aus `dual_domain_collector.collect_all_inbounds` (Klassifikation `BOUNCE`).
- Produces: `classify_dsn(text: str) -> Literal["hard","soft","policy","unknown"]` (5.1.x/550 user unknown → hard; 4.x.x/452 → soft; 5.7.x/554 Spam/Policy → policy); `deliverability_flags(lead: dict, mx_cache: dict[str,bool], bounced_domains: set[str]) -> list[str]` mit `NO_MX`, `SYNTAX_INVALID`, `ROLE_NOREPLY`, `PREVIOUS_HARD_BOUNCE`, `DOMAIN_BOUNCED_BEFORE` (Warnung); `bounce-report` gibt Zählung je Klasse und je Domain aus; `check_eligibility` blockiert bei jedem Flag außer `DOMAIN_BOUNCED_BEFORE`.

- [ ] **Step 1: Failing tests** — `test_classify_dsn_hard_soft_policy` (Beispiele `550 5.1.1 User unknown` → hard, `452 4.2.2 Mailbox full` → soft, `554 5.7.1 rejected as spam` → policy); `test_no_mx_blocks`; `test_previous_hard_bounce_blocks`; `test_noreply_blocks`; `test_domain_bounced_before_warns_only`; `test_mx_checked_once_per_domain`.
- [ ] **Step 2: Run, expect FAIL** — `cd apps/sales-os && PYTHONPATH=. pytest tests/test_lead_quality.py -q`
- [ ] **Step 3: Implement** (kein SMTP-RCPT-Probing).
- [ ] **Step 4: PASS** + Suite + `verify_ssot.py`; `hsb_cli.py bounce-report` gegen echte Daten laufen lassen, Ergebnis (nur Zählungen) im PR-Text.
- [ ] **Step 5: Commit** `feat(sales-os): DSN classification and deliverability flags`.

### Task 2: Seed-Test und Blocklisten-Prüfung

**Files:** Create `apps/sales-os/engine/seed_test.py`; Modify `apps/sales-os/engine/hsb_cli.py` (`seed-send`, `seed-read`, `blocklist-check`); Test `apps/sales-os/tests/test_seed_test.py`

**Interfaces:**
- Produces: `parse_auth_results(raw: bytes) -> dict` (`spf`, `dkim`, `dmarc`, `dkim_domain`, `folder`); `blocklist_status(ip: str) -> dict[str, Literal["listed","clean","check_failed"]]` für Barracuda, SpamCop, UCEPROTECT L1–3, PSBL, Mailspike — jede Liste zuerst mit ihrem Testeintrag (`127.0.0.2`) geprüft, Antwort `127.255.255.25x` = `check_failed`; Spamhaus nur manuell (Lizenz/Public-Resolver-Sperre, siehe Bericht).
- Seed-Liste in `apps/sales-os/config/seed_inboxes.json` (vom Nutzer befüllt, nicht im Git: Datei in `.gitignore`); `seed-read` liest Ergebnisse über IMAP-Zugänge in `.env` falls vorhanden, sonst gibt es eine Checkliste für die manuelle Browser-Prüfung aus.

- [ ] **Step 1: Failing tests** — `test_parse_gmail_auth_results_pass`, `test_parse_missing_dkim`, `test_blocklist_testentry_failure_is_check_failed`, `test_seed_send_refuses_non_seed_recipient`, `test_seed_send_requires_internal_flag`.
- [ ] **Steps 2–4:** FAIL → Implementierung → PASS + Suite; `blocklist-check 85.13.130.17` live.
- [ ] **Step 5: Commit** `feat(sales-os): seed placement test and blocklist check`.

### Task 3: Fit-Score mit Website-Signalen

**Files:** Modify `apps/sales-os/engine/lead_quality.py`; Create `apps/sales-os/engine/website_signals.py`; Modify `hsb_cli.py` (`fetch-websites --limit N`, `score-leads [--apply]`); Test `apps/sales-os/tests/test_fit_score.py`

**Interfaces:**
- Produces: `segment_for(lead) -> Literal["architekten","produktion"]`; `website_text(url: str, cache_dir: Path, opener=None) -> str|None` (`html.parser`, `build_public_opener()`, 2 MB/20 s, robots.txt respektiert, 1 Anfrage/s, Cache je Domain); `website_signals(text: str) -> dict` (`positive: list[str]`, `negative: list[str]`, `quotes: list[str]` — wörtliche Fundstellen); `fit_score(lead, signals) -> tuple[int, str, list[str]]` (Tier A ≥ 75, B 50–74, C < 50, Z = zurückgestellt). Gewichte: produktion Basis 70; architekten Basis 30, +40 bei positivem Signal in CRM-Feldern oder Website (`industrie|gewerbe|hallen|logistik|lebensmittel|brauerei|molkerei|produktion|reinraum|pharma|labor|ingenieur|tragwerk|generalplan`), Tier Z bei nur negativen Signalen (`innenarchitekt|interior|landschaft|garten|freiraum|wohnbau|möbel|einrichtung|messebau`); +10 Ansprechpartner; −20 `DOMAIN_BOUNCED_BEFORE`; Exploration: 15 % der Tagesplätze zufällig aus Tier C (Seed fest pro Tag).

- [ ] **Step 1: Failing tests** — `test_production_with_contact_is_a`; `test_architect_with_website_quote_brauerei_is_a`; `test_interior_only_is_z`; `test_unclear_is_c`; `test_signals_keep_verbatim_quote`; `test_score_writes_only_empty_cells`; `test_exploration_share_15_percent_deterministic_per_day`; `test_fetch_respects_robots_disallow` (Fake-Server).
- [ ] **Steps 2–4:** FAIL → Implementierung → PASS + Suite.
- [ ] **Step 5: Commit** `feat(sales-os): fit score with verbatim website signals`.

### Phase B — Inhalte, Klicks, Sequenz

### Task 4: Vorlage v2 (reiner Text, 2 Segmente, 3 Schritte)

**Files:** Modify `apps/sales-os/engine/canonical_template_factory.py`; Modify `apps/sales-os/engine/com_mailbox_manager.py:166-200` (`build_draft_message` mit `body_text`, ohne HTML-Pflicht, Thread-Header); Test `apps/sales-os/tests/test_template_v2.py`

**Interfaces:**
- Produces: `short_company(name) -> str` (Rechtsformen `GmbH|mbH|AG|KG|GbR|PartG|PartGmbB|Partnerschaftsgesellschaft|e.K.|UG`, Zusätze nach Komma entfernt, ≤ 40 Zeichen); `render_email_v2(lead, owner, step: Literal[1,2,3]=1, thread: dict|None=None, click_url: str|None=None) -> dict` (`subject, body_text, to_email, lead_id, segment, template_id="v2-<segment>-s<step>"`).
- Inhalte: architekten — fachlicher Input für LP 5–7 (Gefälle, Rinnen, Fugen, Belastungsprofil), Angebot herstellerneutraler LV-Bausteine/Detailzeichnungen; produktion — Stillstandsfenster/Aushärtezeiten, IFS/BRC-Audit, Fugen/Keimnester, Rutschhemmung, Rinnen; CTA als Interesse-Frage. Schritt 2 (Tag 4–5) kurze Antwort im Thread, Schritt 3 (Tag 10–12) Abschluss, beide ohne Link.

- [ ] **Step 1: Failing tests** — `test_subject_2_to_5_words_max_50`; `test_short_company_strips_legal_form` (`"maiermaier innen:architektur, Innenarchitektin und Architektin Partnerschaftsgesellschaft"` → `"maiermaier innen:architektur"`); `test_body_60_to_120_words`; `test_step1_at_most_one_link_steps_2_3_none`; `test_no_email_or_name_in_urls`; `test_plain_text_part_first_no_attachment_no_reply_to`; `test_signature_contains_phone`; `test_greeting_without_contact`; `test_followups_thread_with_in_reply_to_and_references`; `test_v2_passes_assess_message`.
- [ ] **Steps 2–4:** FAIL → Implementierung → PASS + Suite + `verify_ssot.py`.
- [ ] **Step 5: Commit** `feat(sales-os): plain-text v2 sequence for architects and producers`.

### Task 5: Abmeldelink ohne E-Mail-Adresse

**Files:** Modify `apps/website/src/pages/abmelden/index.astro:30-45`; Modify `apps/sales-os/engine/sales_reconciliation.py` (`PERSONAL_OPTOUT_LINK_MISSING`: `lid` == Lead-ID ODER bisherige Adressform); Tests `apps/website/tests/abmelden.test.ts`, `apps/sales-os/tests/test_sales_completion.py`

**Interfaces:** URL `https://www.hsb-boden.de/abmelden?lid=<Lead-ID>&o=<JOEL|JORDI>` → `mailto:<owner-mailbox>?subject=Abmelden&body=HSB-ABMELDUNG%3A%20<Lead-ID>`.

- [ ] **Step 1: Failing tests** — `builds_token_mailto_for_owner` (`?lid=HSB-20260708-01170&o=JORDI` → `mailto:j-post@hsb-boden.com?subject=Abmelden&body=HSB-ABMELDUNG%3A%20HSB-20260708-01170`); `legacy_email_param_still_works`; pytest `test_optout_link_with_lid_is_personal`.
- [ ] **Steps 2–4:** vitest, pytest, `npm run check`.
- [ ] **Step 5: Commit** `fix(website,sales-os): token unsubscribe link without e-mail address`.

### Task 6: `/flyer`-Landingpage und Klick-Zähler `/r/<token>`

**Files:** Create `apps/website/src/pages/flyer/index.astro` (Basis: `git show 3731a83:apps/website/src/pages/flyer/index.astro`, Download-Ziel `/HSB-Flyer-Geschaeftsfuehrer.pdf`); Modify `apps/website/public/_redirects` (`/flyer`, `/flyer/` entfernen, `/Flyer /flyer/ 301`); Create `apps/website/functions/r/[token].ts` (Binding `EMAIL_CLICKS` und Secret `CLICK_SECRET` am Pages-Projekt, nicht in `wrangler.toml`); Create `apps/sales-os/engine/click_sync.py`; Tests `apps/website/tests/click-redirect.test.ts`, `apps/sales-os/tests/test_click_sync.py`

**Interfaces:**
- Token = `<Lead-ID>.<hmac16>` mit `HMAC-SHA256(CLICK_SECRET, Lead-ID)` gekürzt auf 16 Hex; `CLICK_SECRET` als Pages-Secret und in GitHub Actions/`.env`.
- `onRequestGet` → `302 Location: /flyer/?utm_source=hsb_outreach&utm_medium=email&utm_campaign=iboden_v2_<segment>`, `Cache-Control: no-store`; `onRequestHead` → 302 ohne Zählung; per `waitUntil` KV-Eintrag `click:<lead>:<ts>` = `{class: "human"|"bot", reasons: [...], asn, ua_family}`; `bot` bei HEAD, ungültigem HMAC, `request.cf.asn` in Rechenzentrums-Liste (8075 Microsoft, 15169 Google, 16509/14618 AWS, 13335 Cloudflare, 396982 Google Cloud, 8068 Microsoft, 30238 Mimecast, 26211/52129 Proofpoint), zweitem Klick < 10 s, fehlendem `Accept-Language`.
- `click_sync.sync_clicks(apply: bool) -> dict` liest KV über die Cloudflare-API, schreibt neue Zeilen in CRM-Tab `CLICK_EVENTS` (`event_id, at, lead_id, class, reasons`), idempotent über `event_id`.
- KV-Namespace und Binding per Cloudflare-API in Task 10 (nach Freigabe); kein DNS. Fehlt Binding oder Secret: 302 ohne Zählung.

- [ ] **Step 1: Failing tests** — `valid_token_human_click_redirects_and_records_human`; `invalid_hmac_records_bot_and_still_redirects`; `head_redirects_without_record`; `datacenter_asn_records_bot`; `second_click_within_10s_records_bot`; `kv_failure_still_redirects`; `missing_binding_or_secret_still_redirects`; `uppercase_Flyer_redirects_to_landingpage` (Test liest `_redirects`); pytest `test_sync_appends_new_events_once`, `test_sync_never_writes_bot_as_human`.
- [ ] **Steps 2–4:** `npx vitest run tests/click-redirect.test.ts`, `npm run test:run`, `npm run build`, `npm run deploy:dry-run`, pytest.
- [ ] **Step 5: Commit** `feat(website,sales-os): flyer landing page and first-party click counter`.

### Task 7: Sequenzsteuerung und Antwortprozess

**Files:** Create `apps/sales-os/engine/sequence.py`; Modify `apps/sales-os/engine/closed_loop_crm.py` (`sync_inbounds`); Test `apps/sales-os/tests/test_sequence.py`

**Interfaces:** `next_step_due(lead, journal_rows, today) -> int|None` (Schritt 2 ab Tag 4, Schritt 3 ab Tag 10 nach Schritt 1, Werktage; `None` bei Antwort/Opt-out/Bounce/Suppressed oder `Follow-up-Datum` in der Zukunft); Journal `sequence(lead_id, step, message_id, sent_at)`; positive/unklare Antwort → `Pipeline="Antwort – Sichtung"`, `Nächste Aktion="Antwort bearbeiten"`, `Follow-up-Datum=nächster Werktag`; Abwesenheit → Rückkehr + 1 Werktag; Antworten getrennt nach `positiv/weiterleitung/negativ/abwesend` in `Reply_Status`.

- [ ] **Step 1: Failing tests** — `test_step2_due_after_4_workdays`, `test_no_step_after_reply_optout_bounce`, `test_ooo_postpones`, `test_steps_share_daily_budget`, `test_positive_reply_sets_pipeline_due`, `test_history_never_reset`.
- [ ] **Steps 2–4:** FAIL → Implementierung → PASS + Suite.
- [ ] **Step 5: Commit** `feat(sales-os): three-step sequence and reply SLA`.

### Task 8: Hochlauf und automatische Pause

**Files:** Modify `apps/sales-os/engine/send_governance.py`; Modify `apps/sales-os/engine/outbound_safety.py` (`dispatch_verified` prüft Budget/Pause vor jeder Mail); Test `apps/sales-os/tests/test_ramp.py`

**Interfaces:** `daily_budget(first_send_date, today) -> int` je Postfach: Woche 1 = 10, Woche 2 = 20, ab Woche 3 = 30, Obergrenze 35 unverändert; `pause_reason(stats) -> str|None`: Hard-Bounces > 2 % der letzten 100 (≥ 3 bei < 100), `policy`-Bounces ≥ 1, ≥ 3 4xx-Deferrals/Tag, jede Spam-Rückmeldung, Seed-Test ohne `dkim=pass`; Pause domainweit bis `HSB_SEND_PAUSE_ACK`.

- [ ] **Step 1: Failing tests** — `test_budget_10_20_30_cap_35`, `test_hard_bounce_over_2pct_pauses_both`, `test_policy_bounce_pauses`, `test_deferrals_pause`, `test_pause_checked_before_each_send`.
- [ ] **Steps 2–4:** FAIL → Implementierung → PASS + Suite.
- [ ] **Step 5: Commit** `feat(sales-os): staged ramp with automatic pause`.

### Task 9: Entwurfsaustausch und Linkprüfung

**Files:** Create `apps/sales-os/engine/draft_upgrade.py`; Modify `hsb_cli.py` (`upgrade-drafts --owner --limit --cohort pilot|all [--apply]`); Modify `sales_reconciliation.py` (Linkprüfung je eindeutiger URL ohne Query, Issue `LINK_BROKEN:<host><path>`); Tests `test_draft_upgrade.py`, `test_link_health.py`

**Interfaces:** Consumes `render_email_v2` (Task 4), `fit_score` (Task 3), Token-URL (Task 6), `drafts.json` aus `run_audit`. Produces `upgrade_drafts(owner, limit, cohort, apply, journal_path) -> dict` (`selected, appended, archived, crm_updated, skipped_reasons`); CRM `Draft_ID`, `Email_Template_ID`, `Drafted_At`.

- [ ] **Step 1: Failing tests** — `test_dry_run_changes_nothing`; `test_apply_appends_v2_moves_v1_updates_crm`; `test_resume_no_duplicate`; `test_changed_v1_hash_skipped`; `test_tier_z_and_ineligible_untouched`; `test_never_expunges_without_copy`; `test_archive_folder_name_modified_utf7` (`Entwürfe-Archiv-v1` → `Entw&APw-rfe-Archiv-v1`); `test_broken_link_issue`; `test_each_unique_link_probed_once`.
- [ ] **Steps 2–4:** FAIL → Implementierung → PASS + Suite; vorher `CAPABILITY` des All-Inkl-IMAP lesen (MOVE/UIDPLUS) und Fallback testen.
- [ ] **Step 5: Commit** `feat(sales-os): resumable draft upgrade with archive and link health`.

### Phase C — Pilot (operativ)

### Task 10: Rollout und Pilot

- [ ] **Step 1:** PR (Tasks 1–9), CI grün, Codex `adversarial-review --base origin/main` ohne offene high-Befunde, Merge (Dauerfreigabe). **Freigabe nötig:** KV/Secret am Pages-Projekt, Website-Deploy über `deploy-production.yml`; prüfen: `/flyer/` liefert 200 mit Landingpage, `/r/<gültiges Token>` → 302, KV-Eintrag `human`.
- [ ] **Step 2:** `bounce-report` → Sperrliste angewendet; `blocklist-check` clean; Seed-Test (Nutzer bestätigt Seed-Adressen) mit `dkim=pass` in allen Seeds, Ordner je Anbieter dokumentiert.
- [ ] **Step 3:** `fetch-websites` + `score-leads --apply`; Pilotkohorte: 100 Produktion Tier A + 25 Architekten Tier A (15–20 %-Anteil), gleich auf beide Owner verteilt; `upgrade-drafts --cohort pilot --apply` (**Freigabe nötig**, mit Zählungen aus dem Dry-Run); 5 Entwürfe in Webmail sichtbar prüfen.
- [ ] **Step 4:** **Nutzerfreigabe im Chat** für den Pilotversand; Versand nur über `dispatch_verified` unter Budget/Pause.
- [ ] **Step 5 (nach Abschluss der 3 Schritte + 7 Tage):** Kennzahlen je Segment: positive Antworten je kontaktiertem Unternehmen (primär) gegen historische Quote (Produktion 7/134, Architekten 8/935), Termine/LV-Anfragen, Opt-outs, Bounces, Klicks `human`. Weiter, wenn Bounce < 2 % und keine Pause; neuer Text bleibt Standard, wenn positive Antworten ≥ historische Quote; sonst Text überarbeiten. Ergebnis nach `operations/verification/`; danach `--cohort all` in 200er-Batches Tier A → B → C.

**Nutzeraktionen (vorhandene Konten, kein KAS):** Seed-Postfächer anlegen/bestätigen (Gmail, Outlook.com, GMX, Web.de, T-Online), herstellerneutrale LV-Bausteine/Detailzeichnungen für Architekten bereitstellen, Search Console im Browser mit dem Google-Konto öffnen, das die Property besitzt (optional, für Website-Suchdaten).

**Ohne KAS nicht möglich (bewusst ausgeklammert):** DMARC-Berichte/strengere Policy, Google Postmaster Tools, `www.hsb-boden.com`-CNAME, eigene Sende-IP/rDNS, Microsoft SNDS/JMRP.
