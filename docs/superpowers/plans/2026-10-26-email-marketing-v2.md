# E-Mail-Marketing v2 (Fit-Priorisierung, Pilot, Sequenz, messbare Ergebnisse) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die knappen Versandplätze (2 Postfächer, harte Obergrenze 35/Tag/Postfach) auf die Leads mit dem höchsten Ertrag lenken, mit zielgruppengerechten Texten und einer kurzen Folgesequenz, und den Nutzen an qualifizierten Antworten messen, nicht an Entwurfszahlen.

**Architecture:** Reihenfolge nach Codex-Strategiereview: (A) Listenhygiene und Fit-Score → (B) Texte v2 + Folgekontakte + Antwortprozess → (C) Hochlauf mit Stopp-Regeln → (D) begrenzter Pilot mit vorab festgelegten Entscheidungsregeln → erst danach breiter Entwurfsaustausch. Alles im bestehenden Sales-OS (Sheets → Python-Engine → All-Inkl IMAP/SMTP), Website-Teil als Cloudflare Pages Functions.

**Tech Stack:** Python 3.14 (pytest), TypeScript Pages Functions (vitest), Google Sheets API, IMAP/SMTP All-Inkl, GA4 Measurement Protocol.

**Spec:** Nutzerauftrag 26.10.2026 (Chat); Messungen und Quellen unten; Codex-Strategiereview 26.10.2026 (needs-attention, 5 high / 2 medium, alle eingearbeitet); Tavily-Research 26.10.2026 (Quellen unter „Belege“).

## Ist-Stand (gemessen 26.10.2026, nur Zählungen)

- CRM `ALL_LEADS` 6.424: Architekten 4.812 (davon Fit-Schlagworte positiv 502, negativ Innen/Landschaft/Wohnen 454, unklar 3.856), Getränke/Lebensmittel 1.612. `Tier`, `Score`, `Segment`, `Belastungsart` leer. `Website` 6.423×, `Ansprechpartner` 4.815×.
- Historie (1.069 gesendet): Reaktionen Produktion 7/134 ≈ 5 %, Architekten 8/935 ≈ 0,9 %; **Bounces 63/1.069 = 5,9 %** (Branchengrenze < 2 %).
- Entwürfe Joel 3.080 / Jordie 2.538: nur HTML, 6 Links, Betreff bis > 120 Zeichen, Produktions-Text auch an Architekten, `/flyer` → 302 → PDF (GA4 sieht nichts), E-Mail-Adresse im Abmeldelink, altes `Reply-To`.
- Zustellung: SPF ✅, DKIM ✅ (`kas202609210853`, dkimpy verify), DMARC `p=none` ohne `rua`, `List-Unsubscribe` ✅, Domain seit 21.09.2026.
- GA4 `543244027`: E-Mail-Besuche verteilt auf `outbound_email` und `outreach` (uneinheitlich).

## Belege (Auswahl)

- Sequenz 3–5 Kontakte, z. B. Tag 0/3–4/7–10/14; Folgekontakte liefern einen großen Teil der Antworten (Instantly Benchmark 2026; Belkins 7,5 Mio. Mails).
- Durchschnittliche Reply-Rate 2026 ≈ 3,4 %, „gut“ 5–10 %; Food & Beverage ≈ 3,5 %; Termine aus Kaltakquise ≈ 0,5–2 % (Instantly 2026, Belkins).
- Klartext statt HTML, ≤ 80–125 Wörter, 0–1 Link im Erstkontakt, keine Pixel (Instantly, Validity, Suped, Warmforge, Unify GTM 2026).
- Neue Domain: Hochlauf über Wochen, Bounce < 2 %, Beschwerden < 0,1–0,3 % (Lemlist, Litemail, Topo).
- Personalisierung mit echtem Bezug: deutlich höhere Antwortraten als reine Platzhalter (Woodpecker 20 Mio. Mails: ≈ 17 % vs. 7–9 %).

## Global Constraints

- Kundenversand bleibt aus: kein Task setzt `HSB_CUSTOMER_SEND_ENABLED` oder ruft `dispatch_verified(dry_run=False)` auf. Der Pilotversand (Task 9) startet nur nach ausdrücklicher Nutzerfreigabe im Chat.
- Nie Entwürfe löschen: Austausch verschiebt v1 nach `Entwürfe-Archiv-v1` (COPY/MOVE vor jedem EXPUNGE einer einzelnen UID).
- Versand- und Sperrhistorie wird nie zurückgesetzt; Folgekontakte zählen zur selben Tagesgrenze wie Erstkontakte, domainweit (beide Postfächer zusammen ≤ 70/Tag).
- Einzige CRM-Wahrheit Spreadsheet `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg`; Schreiben nur über `crm_write_readback`; nur leere Zellen in `Tier`/`Score` werden befüllt, vorhandene Werte bleiben.
- In keiner URL eine E-Mail-Adresse, kein Name, keine Lead-ID an Google: GA4 bekommt nur Kampagnen-Parameter.
- UTM: `utm_source=hsb_outreach`, `utm_medium=email`, `utm_campaign=iboden_v2_<architekten|produktion>`, `utm_content=<JOEL|JORDI>_<cta-a|cta-b>`.
- Text v2: Betreff ≤ 50 Zeichen, Siezen, Fließtext 60–110 Wörter, multipart/alternative mit `text/plain` zuerst, kein Anhang, kein Bild, kein `Reply-To`, genau ein Inhaltslink (`/flyer`) im Erstkontakt, Folgekontakte ohne Inhaltslink; Pflichtangaben (Firma, Anschrift, Sitz, Registergericht, HRB, Geschäftsführung) als Text im Footer; Abmeldelink + Abmeldezeile.
- `python3 scripts/verify_ssot.py` Exit 0 vor jedem Commit; Name „Jordie Post“.

## Bewusste Entscheidungen (vom Nutzer überprüfbar)

1. **Keine Öffnungs-Pixel**: verschlechtern die Zustellung, Outlook blockiert Bilder, Apple/Gmail laden vor → falsche Daten. Gemessen werden Antworten (primär) und Flyer-Abrufe (sekundär, als „unbestätigter Abruf“, da Mail-Scanner Links vorab öffnen).
2. **Produktion vor Architekten**: historische Reaktionsquote ≈ 5 % vs. ≈ 0,9 %. Architekten nur mit Fit-Signal im Pilot; Innen-/Landschafts-/Wohnarchitekten werden zurückgestellt (nicht gelöscht).
3. **Pilot vor Komplettaustausch**: 120 Leads, zwei Texte (CTA-A niedrige Hürde „Ist das bei Ihnen gerade ein Thema?“, CTA-B konkretes Angebot Termin bzw. LV-Baustein); Entscheidung nach Regeln in Task 9.

## Review Focus

- Lead ohne `Ansprechpartner` → „Guten Tag,“; nie „Sehr geehrte/r“ oder leere Platzhalter.
- Firmenname > 40 Zeichen (z. B. „maiermaier innen:architektur, … Partnerschaftsgesellschaft“) → `short_company` kürzt, Betreff bleibt ≤ 50 Zeichen.
- Abbruch mitten im Entwurfsaustausch → keine doppelten v2-Entwürfe, kein verlorener v1 (Journal `PLANNED → APPENDED → ARCHIVED → CRM_DONE`).
- Antwort, Opt-out, Bounce oder Abwesenheit kommt zwischen zwei Sequenzschritten → nächster Schritt entfällt bzw. verschiebt sich auf `Follow-up-Datum`.
- Bounce-Spitze am ersten Versandtag → automatische Pause greift vor dem nächsten Versand, nicht erst am Folgetag.

---

### Phase A — Grundlagen

### Task 1: Listenhygiene (Bounce-Quote von 5,9 % unter 2 %)

**Files:** Create `apps/sales-os/engine/lead_quality.py`; Modify `apps/sales-os/engine/hsb_core.py` (`check_eligibility`); Test `apps/sales-os/tests/test_lead_quality.py`

**Interfaces:**
- Consumes: `enrich_company_names.check_domain_mx(domain) -> bool`.
- Produces: `deliverability_flags(lead: dict, mx_cache: dict[str,bool]) -> list[str]` mit Werten `NO_MX`, `SYNTAX_INVALID`, `ROLE_ONLY_NOREPLY` (noreply/postmaster/abuse), `PREVIOUS_HARD_BOUNCE`, `DOMAIN_BOUNCED_BEFORE` (anderer Lead derselben Domain hart gebounct); `check_eligibility` blockiert bei jedem Flag außer `DOMAIN_BOUNCED_BEFORE` (nur Warnung).

- [ ] **Step 1: Failing tests** — `test_no_mx_blocks`, `test_syntax_invalid_blocks`, `test_noreply_blocks`, `test_previous_hard_bounce_blocks`, `test_domain_bounced_before_is_warning_only`, `test_mx_checked_once_per_domain` (Cache).
- [ ] **Step 2: Run, expect FAIL** — `cd apps/sales-os && PYTHONPATH=. pytest tests/test_lead_quality.py -q`
- [ ] **Step 3: Implement** (kein SMTP-RCPT-Probing — vermeidet zusätzliche Reputationsrisiken).
- [ ] **Step 4: PASS** + gesamte Suite + `verify_ssot.py`.
- [ ] **Step 5: Commit** `feat(sales-os): deliverability flags gate eligibility`.

### Task 2: Fit-Score und Prioritätswarteschlange

**Files:** Modify `apps/sales-os/engine/lead_quality.py`; Modify `apps/sales-os/engine/sales_reconciliation.py` (Queue-Sortierung); Modify `apps/sales-os/engine/hsb_cli.py` (Subcommand `score-leads [--apply]`); Test `apps/sales-os/tests/test_fit_score.py`

**Interfaces:**
- Produces: `segment_for(lead) -> Literal["architekten","produktion"]` (Branche enthält „architekt“ → architekten, sonst produktion); `fit_score(lead) -> tuple[int, str, list[str]]` = (0–100, Tier `A|B|C|Z`, Gründe). Regeln: produktion Basis 70; architekten Basis 30, +40 bei Fit-Schlagworten (`industrie|gewerbe|hallen|logistik|lebensmittel|produktion|fabrik|werk|ingenieur|tragwerk|generalplan|technische geb|anlagen|labor|pharma|klinik|kranken` in Firma/Website/Notizen/Projektart), Tier `Z` bei `innenarchitekt|interior|innen:|landschaft|garten|freiraum|wohn|möbel|design|einrichtung|messe` ohne positives Schlagwort; +10 bei `Ansprechpartner` (> 3 Zeichen); −20 bei `DOMAIN_BOUNCED_BEFORE`. Tier: A ≥ 75, B 50–74, C < 50, Z = zurückgestellt. Queue-Sortierung: Tier, dann Score absteigend, dann Owner-Ausgleich.

- [ ] **Step 1: Failing tests** — `test_production_lead_is_tier_a_with_contact` (Getraenkeindustrie + Ansprechpartner → 80, A); `test_industrial_architect_is_tier_a` („Ingenieurbüro Hallenbau“ → 80, A); `test_interior_architect_is_tier_z`; `test_unclear_architect_is_tier_c`; `test_queue_orders_by_tier_then_score`; `test_score_leads_writes_only_empty_cells` (bestehender `Tier`-Wert bleibt).
- [ ] **Steps 2–4:** FAIL → Implementierung → PASS + Suite + `verify_ssot.py`.
- [ ] **Step 5: Commit** `feat(sales-os): fit score and prioritized queue`.

### Task 3: Abmeldelink ohne E-Mail-Adresse

**Files:** Modify `apps/website/src/pages/abmelden/index.astro:30-45`; GA4-Loader (`rg "gtag\('config'" apps/website/src`); Modify `apps/sales-os/engine/sales_reconciliation.py` (`PERSONAL_OPTOUT_LINK_MISSING`); Tests `apps/website/tests/abmelden.test.ts`, `apps/sales-os/tests/test_sales_completion.py`

**Interfaces:** Produces URL `https://www.hsb-boden.de/abmelden?lid=<Lead-ID>&o=<JOEL|JORDI>`; Seite baut `mailto:<owner-mailbox>?subject=Abmelden&body=HSB-ABMELDUNG%3A%20<Lead-ID>` (Token wie `outbound_safety.UNSUBSCRIBE_TOKEN_RE`).

- [ ] **Step 1: Failing tests** — `builds_token_mailto_for_owner` (`?lid=HSB-20260708-01170&o=JORDI` → `mailto:j-post@hsb-boden.com?subject=Abmelden&body=HSB-ABMELDUNG%3A%20HSB-20260708-01170`); `legacy_email_param_still_works`; `ga4_page_location_has_no_query_on_abmelden`; pytest `test_optout_link_with_lid_is_personal`.
- [ ] **Steps 2–4:** `npx vitest run tests/abmelden.test.ts`, `PYTHONPATH=. pytest tests/test_sales_completion.py -q`, `npm run check`.
- [ ] **Step 5: Commit** `fix(website,sales-os): token unsubscribe link without e-mail address`.

### Task 4: `/flyer` als messbare Weiterleitung ohne Personenbezug

**Files:** Create `apps/website/functions/flyer.ts`; Modify `apps/website/public/_redirects` (vier `/flyer`-Zeilen entfernen); Test `apps/website/tests/flyer-function.test.ts`

**Interfaces:** `onRequestGet(context)` → `302 Location: /HSB-Flyer-Geschaeftsfuehrer.pdf`, `Cache-Control: no-store`; per `context.waitUntil` GA4-Event `email_flyer_open_unconfirmed` mit nur `campaign_source/medium/name/content` und zufälliger `client_id` pro Abruf; `HEAD`-Anfragen und User-Agents mit `bot|crawler|preview|scanner|safelinks|proofpoint|mimecast|barracuda` → Weiterleitung ohne Event.

- [ ] **Step 1: Failing tests** — `redirects_302_to_pdf`, `sends_event_with_campaign_only` (Body ohne `lid`, ohne Lead-Bezug), `scanner_user_agent_sends_no_event`, `head_request_sends_no_event`, `missing_secret_or_ga4_failure_still_redirects`.
- [ ] **Steps 2–4:** `npx vitest run tests/flyer-function.test.ts`, `npm run test:run`, `npm run build`, `npm run deploy:dry-run`.
- [ ] **Step 5: Commit** `feat(website): measurable /flyer redirect, campaign-level GA4 only`.

### Phase B — Inhalte, Sequenz, Antworten

### Task 5: Vorlage v2 (2 Segmente × 2 CTAs) und Folgekontakte

**Files:** Modify `apps/sales-os/engine/canonical_template_factory.py`; Modify `apps/sales-os/engine/com_mailbox_manager.py:166-200` (`build_draft_message`: `body_text`-Parameter, multipart/alternative, `In-Reply-To`/`References` optional); Test `apps/sales-os/tests/test_template_v2.py`

**Interfaces:** Produces `short_company(name: str) -> str` (Rechtsformen `GmbH|mbH|AG|KG|GbR|PartG|PartGmbB|Partnerschaftsgesellschaft|e.K.|UG` und Zusätze nach Komma entfernt, ≤ 40 Zeichen); `render_email_v2(lead: dict, owner: str, cta: Literal["a","b"], step: Literal[1,2,3]=1, thread: dict|None=None) -> dict` mit `subject, body_text, body_html, to_email, lead_id, segment, template_id` (`v2-<segment>-<cta>-s<step>`), Schritt 2/3 mit `Re: <Betreff Schritt 1>` und Thread-Headern.

Inhalte: architekten — Systemwahl nach Belastungsprofil, Detailpunkte Rinnen/Fugen/Gefälle, Unterstützung bei LV; CTA-A „Planen Sie aktuell ein Projekt mit Industrie- oder Lebensmittelboden?“, CTA-B „Darf ich Ihnen einen LV-Textbaustein für Ihr nächstes Projekt senden?“. produktion — Risse/Ablösungen, offene Fugen, stehendes Wasser, Rinnen; Sanierung im Stillstandsfenster; CTA-A „Ist der Boden bei Ihnen gerade ein Thema?“, CTA-B „Wann passt Ihnen eine kurze Vor-Ort-Einschätzung?“. Schritt 2 (Tag 7): ein konkreter Nutzen in 2–3 Sätzen, ohne Link. Schritt 3 (Tag 14): kurzer Abschluss („Soll ich das Thema schließen?“), ohne Link.

- [ ] **Step 1: Failing tests** — `test_subject_max_50_contains_short_company`; `test_short_company_strips_legal_form` (`"maiermaier innen:architektur, Innenarchitektin und Architektin Partnerschaftsgesellschaft"` → `"maiermaier innen:architektur"`); `test_body_word_count_60_to_110`; `test_step1_exactly_one_content_link_steps_2_3_none`; `test_urls_contain_no_email_name_or_lead_to_google` (Flyer-URL ohne `lid`); `test_mime_plain_first_no_attachment_no_reply_to`; `test_greeting_without_contact_is_guten_tag`; `test_followup_threads_with_in_reply_to`; `test_v2_passes_assess_message_without_issues`.
- [ ] **Steps 2–4:** `PYTHONPATH=. pytest tests/test_template_v2.py -q`, Suite, `verify_ssot.py`.
- [ ] **Step 5: Commit** `feat(sales-os): v2 templates with two CTAs and two follow-ups`.

### Task 6: Sequenzsteuerung und Antwortprozess

**Files:** Create `apps/sales-os/engine/sequence.py`; Modify `apps/sales-os/engine/closed_loop_crm.py` (`sync_inbounds`: bei `HOT_LEAD`/`NEUTRAL` → `Pipeline`, `Nächste Aktion`, `Follow-up-Datum`); Test `apps/sales-os/tests/test_sequence.py`

**Interfaces:** Produces `next_step_due(lead: dict, today: date) -> int|None` (Schritt 2 ab Tag 7, Schritt 3 ab Tag 14 nach Schritt 1; `None` bei Antwort/Opt-out/Bounce/Suppressed oder `Follow-up-Datum` in der Zukunft); Journal-Tabelle `sequence(lead_id, step, message_id, sent_at)` in derselben SQLite wie `SendJournal`; Antworten setzen `Pipeline="Antwort – Sichtung"`, `Nächste Aktion="Antwort bearbeiten"`, `Follow-up-Datum=nächster Werktag`, Abwesenheit setzt `Follow-up-Datum` auf Rückkehrdatum + 1 Werktag.

- [ ] **Step 1: Failing tests** — `test_step2_due_after_7_days`, `test_no_step_after_reply_optout_bounce`, `test_ooo_postpones_to_return_date`, `test_steps_share_daily_cap_with_first_contacts`, `test_positive_reply_sets_pipeline_and_due_date`, `test_history_never_reset`.
- [ ] **Steps 2–4:** `PYTHONPATH=. pytest tests/test_sequence.py -q`, Suite, `verify_ssot.py`.
- [ ] **Step 5: Commit** `feat(sales-os): two-step follow-up sequence and reply SLA`.

### Task 7: Hochlauf mit Stopp-Regeln

**Files:** Modify `apps/sales-os/engine/send_governance.py`; Modify `apps/sales-os/engine/outbound_safety.py` (`dispatch_verified` liest Budget/Pause); Test `apps/sales-os/tests/test_ramp.py`

**Interfaces:** Produces `daily_budget(first_send_date: date, today: date) -> int` je Postfach: Woche 1 = 10, Woche 2 = 20, ab Woche 3 = 35 (Obergrenze unverändert); `pause_reason(stats: dict) -> str|None` mit Pause bei Hard-Bounces > 2 % der letzten 100 (oder ≥ 3 bei < 100), ≥ 3 SMTP-4xx-Deferrals am Tag, jeder Beschwerde-/Spam-Rückmeldung, jedem Authentifizierungsfehler; Pause gilt domainweit und bleibt bis manueller Freigabe (`HSB_SEND_PAUSE_ACK`).

- [ ] **Step 1: Failing tests** — `test_budget_week1_10_week2_20_then_35`, `test_hard_bounce_over_2pct_pauses_both_mailboxes`, `test_three_bounces_under_100_sends_pauses`, `test_deferrals_pause`, `test_pause_checked_before_each_send`.
- [ ] **Steps 2–4:** `PYTHONPATH=. pytest tests/test_ramp.py -q`, Suite, `verify_ssot.py`.
- [ ] **Step 5: Commit** `feat(sales-os): staged ramp and automatic send pause`.

### Task 8: Entwurfsaustausch v1 → v2 und Linkprüfung

**Files:** Create `apps/sales-os/engine/draft_upgrade.py`; Modify `apps/sales-os/engine/hsb_cli.py` (`upgrade-drafts --owner --limit --cohort pilot|all [--apply]`); Modify `apps/sales-os/engine/sales_reconciliation.py` (Linkprüfung je eindeutiger URL ohne Query, Issue `LINK_BROKEN:<host><path>`); Tests `apps/sales-os/tests/test_draft_upgrade.py`, `apps/sales-os/tests/test_link_health.py`

**Interfaces:** Consumes `render_email_v2` (Task 5), `fit_score` (Task 2), `drafts.json` aus `run_audit`. Produces `upgrade_drafts(owner, limit, cohort, apply, journal_path) -> dict` (`selected, appended, archived, crm_updated, skipped_reasons`); CRM `Draft_ID`, `Email_Template_ID`, `Drafted_At`, `Tier`, `Score`.

- [ ] **Step 1: Failing tests** — `test_dry_run_changes_nothing`; `test_apply_appends_v2_moves_v1_updates_crm`; `test_resume_after_append_no_duplicate`; `test_changed_v1_hash_skipped`; `test_tier_z_and_ineligible_untouched`; `test_never_expunges_without_successful_copy`; `test_broken_link_marks_issue`; `test_each_unique_link_probed_once`.
- [ ] **Steps 2–4:** beide Testdateien, Suite, `verify_ssot.py`.
- [ ] **Step 5: Commit** `feat(sales-os): resumable draft upgrade with archive and link health`.

### Phase C — Pilot und Rollout (operativ)

### Task 9: Pilot mit Entscheidungsregeln

- [ ] **Step 1:** PR (Tasks 1–8), CI grün, Codex `adversarial-review --base origin/main` ohne offene high-Befunde, Merge; Website-Deploy über `deploy-production.yml`; Check `curl -sI https://www.hsb-boden.de/flyer` → 302, GA4 Realtime zeigt `email_flyer_open_unconfirmed` nach Test mit Browser-User-Agent.
- [ ] **Step 2:** `score-leads --apply`; Kohorte: 60 Produktion Tier A + 60 Architekten Tier A, je Segment 50 % CTA-A / 50 % CTA-B, je Owner gleich verteilt; `upgrade-drafts --cohort pilot --apply`; 5 Entwürfe in Webmail sichtbar prüfen.
- [ ] **Step 3:** **Nutzerfreigabe im Chat einholen** für Pilotversand; Versand nur über `dispatch_verified` unter Budget/Pause (Task 7).
- [ ] **Step 4 (nach 21 Tagen inkl. Folgekontakten):** Kennzahlen je Segment × CTA: positive Antworten je kontaktiertem Unternehmen (primär), Termine/LV-Anfragen, Opt-outs, Bounces, Flyer-Abrufe (sekundär). Regeln: Fortsetzen, wenn positive Antworten ≥ 2 % der Kontakte im Segment; CTA mit mehr positiven Antworten wird Standard (bei Gleichstand CTA-A); Segment überarbeiten, wenn < 1 % und 0 Termine; sofort stoppen bei Pause-Grund aus Task 7 oder Opt-outs > 3 %.
- [ ] **Step 5:** Ergebnis nach `operations/verification/`; danach `upgrade-drafts --cohort all` in 200er-Batches für Tier A → B → C (Tier Z bleibt zurückgestellt); Versand weiter nur unter Budget/Pause.

**Nutzeraktionen (ohne Zugang nicht automatisierbar):** DMARC `rua` und Google Postmaster Tools (DNS-TXT bei All-Inkl/KAS); `www.hsb-boden.com`-CNAME → `hsb-boden.pages.dev`; Google Search Console einmalig per OAuth verbinden; LV-Textbausteine/Systemunterlagen bereitstellen, bevor CTA-B für Architekten verschickt wird.
