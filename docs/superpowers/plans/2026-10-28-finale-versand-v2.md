# Finale: Versand v2 auf dem bestehenden CRM-Cockpit — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die zugeschnittenen v2-Mails (Produktion/Architekten) fehlerfrei erzeugen, über die zwei `.com`-Postfächer mit Hochlauf versenden und jeden Versand, jede Antwort, Abmeldung, jeden Bounce und Klick im **bestehenden** CRM-Cockpit (Tab `DASHBOARD`) und in Google Analytics sichtbar machen.

**Architecture:** Kein neues Werkzeug, kein neues CRM. Das Google Sheet `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg` bleibt Steuerzentrale; das Cockpit (`engine/operator_layer/crm_dashboard.py`, Formeln auf `ALL_LEADS`) wird um die fehlenden `.com`-/v2-/Klick-Kennzahlen ergänzt. Entwürfe entstehen mit `create-v2-drafts` (PR #505), Versand über `dispatch_verified` (Hochlauf 10/20/30, Pause), Status über den stündlichen Abgleich (`sync_inbounds`).

**Tech Stack:** Python 3.14 (pytest), Google Sheets API, All-Inkl IMAP/SMTP, Cloudflare Pages/KV, GA4 (Property `543244027`), Looker Studio.

**Spec:** Übergabe `docs/verification/email-marketing-v2-handoff-2026-10-28.md`; Nutzerziele 28.10.: (1) Texte technisch fehlerfrei und auf den Betrieb zugeschnitten, (2) Anti-Spam-Versand, (3) CRM als Dashboard inkl. der `.de`-Versendungen, (4) Nutzen messbar, auch in GA4 über Schlüsselergebnisse.

## Ist-Stand (gemessen 28.10.)

- Cockpit `DASHBOARD` vorhanden und aktiv (`.de`-Abgleich 13:36/13:40), `DE_VERSENDUNGEN_FORENSIK` 1.323 `.de`-Sendungen, `VERSAND`, `POSTEINGANG`, `INBOUND_EVENTS`.
- Cockpit-Fehler: **Bounces = 0**, weil die Formel `ALL_LEADS!BE` (Pipeline) = "Bounce" zählt; der Abgleich schreibt aber `Bounce_Status` (Spalte **AQ**) = `hard_bounce`/`bounce_review`. Gemessen: 47 `.com`-Bounces.
- Entwürfe: JOEL 480 v2 Produktion **mit Fehlern** (Klick-Link ohne Token, weil Schlüssel im Hintergrundlauf fehlte); JORDI 0; Archiv: alle v1 + 705 v2-Architekten (Text war korrekt, Archivierung unnötig; Anrede „Herr Per Grunwald“ fehlerhaft).
- Code-Fixes auf PR #505 (`e8d847c`): Anrede nur Nachname, Klick-Token Pflicht, Empfängersperre, Postfach-Sperre. Tests 406 passed.
- Versendet: 0.

## Global Constraints

- Spalten `ALL_LEADS`: Tier **F**, Verantwortlicher **AA**, Segment **AD**, Email_Template_ID **AF**, Send_Status **AO**, Send_Datum **AP**, Bounce_Status **AQ**, Reply_Status **AR**, Suppressed **AT**, Opt-out-Status **Y**, Follow-up-Datum **R**, Pipeline **BE**.
- Cockpit-Formeln mit Semikolon (deutsche Sheet-Locale), wie im bestehenden `crm_dashboard.py`.
- Nichts löschen; „entfernen“ = IMAP-MOVE nach `Entw&APw-rfe-Archiv-v1`, vorher/nachher zählen.
- Kundenversand nur mit `HSB_CUSTOMER_SEND_ENABLED=yes` im Versandjob und erst nach ausdrücklichem Nutzer-„Versand freigeben“ im Chat.
- Hochlauf je Postfach: Woche 1 = 10/Tag, Woche 2 = 20, ab Woche 3 = 30, max 35; nur Werktage 09:00–16:00 Europe/Berlin.
- Keine Behauptungen über HSB, die nicht belegt sind; Texte nur über `render_email_v2`.
- `python3 scripts/verify_ssot.py` Exit 0 vor jedem Commit; exakte Pfade stagen; nach pytest `git checkout -- apps/sales-os/engine/__pycache__`.

## Review Focus

- Lead mit Ansprechpartner „Herr Dr. Max von Müller“ → „Sehr geehrter Herr Dr. von Müller,“ (Test in PR #505 vorhanden, in Task 3 an echter Stichprobe prüfen).
- Entwurfserzeugung ohne Schlüsselbundzugriff → Abbruch, kein Entwurf ohne Klick-Token (Task 3 Stichprobe zählt `/r/`-Links = Entwürfe).
- Cockpit bei leerem `CLICK_EVENTS`-Tab → 0 statt Formelfehler (Task 1).
- Versand eines Entwurfs, dessen Lead zwischenzeitlich geantwortet/abgemeldet hat → nicht senden (bestehender Live-Gate in `dispatch_verified`; Task 4 Dry-Run zeigt Gate-Zählung).
- Zweiter Versandjob am selben Tag → Tagesgrenze greift (Task 4 Test).

---

### Task 1: Cockpit ergänzen und Bounce-Formel korrigieren

**Files:** Modify `apps/sales-os/engine/operator_layer/crm_dashboard.py`; Test `apps/sales-os/tests/test_crm_dashboard.py` (neu, falls nicht vorhanden)

**Interfaces:**
- Produces: `dashboard_rows() -> list[list[str]]` mit zusätzlichen Zeilen (Labels exakt): „Bounces“ (korrigiert), „Antworten gesamt“, „v2 versendet Produktion“, „v2 versendet Architekten“, „v2 Antworten Produktion“, „v2 Antworten Architekten“, „Klicks (echt)“, „Entwürfe bereit (v2)“-Hinweiszeile ohne Formel. Bestehende Zeilen 1–17 und Batch-Block bleiben in Reihenfolge erhalten; neue Zeilen kommen **nach** dem Batch-Block (ab Zeile 29), damit vorhandene Formatierung (`formatting_requests`) gültig bleibt.

- [ ] **Step 1: Failing tests** — `test_bounce_formula_reads_bounce_status_column` (Zeile „Bounces“ enthält `ALL_LEADS!AQ2:AQ` und `"hard_bounce"`, nicht `BE2:BE`); `test_v2_rows_count_template_ids` (Formeln enthalten `ALL_LEADS!AF2:AF; "v2-produktion*"` bzw. `"v2-architekten*"` und `ALL_LEADS!AO2:AO; "sent"`); `test_v2_reply_rows_use_reply_status` (`ALL_LEADS!AR2:AR; "<>"` kombiniert mit AF-Filter); `test_click_row_is_error_safe` (Formel beginnt mit `=IFERROR(` und zählt `CLICK_EVENTS!D2:D; "human"`); `test_existing_rows_unchanged` (Zeilen 1–17 identisch zum Stand `origin/main` außer „Bounces“).
- [ ] **Step 2: Run, expect FAIL** — `cd apps/sales-os && PYTHONPATH=. pytest tests/test_crm_dashboard.py -q`
- [ ] **Step 3: Implement** — Bounces: `=COUNTIFS(ALL_LEADS!AQ2:AQ; "hard_bounce")+COUNTIFS(ALL_LEADS!AQ2:AQ; "bounce_review")` (je Owner mit `AA` wie bestehend).
- [ ] **Step 4: PASS + Suite + `verify_ssot.py`**; Dry-Run live: `hsb-sales`-Umgebung, `python -m operator_layer.crm_dashboard` ohne `--apply` zeigt Zeilenzahl.
- [ ] **Step 5: Commit** `fix(sales-os): cockpit counts .com bounces and v2 sends, replies and clicks`.

### Task 2: Versand schreibt Template und Segment ins CRM

**Files:** Modify `apps/sales-os/engine/outbound_safety.py` (`complete_delivery`); Test `apps/sales-os/tests/test_outbound_safety.py` (bestehend erweitern) oder neu `tests/test_delivery_crm_fields.py`

**Interfaces:**
- Consumes: Entwurf mit Header `X-HSB-Template-ID: v2-<segment>-s<step>` (aus `build_draft_message`).
- Produces: nach erfolgreichem Versand zusätzlich `Email_Template_ID` = Header-Wert und `Segment` = `produktion|architekten` im CRM, über denselben `crm_write_readback`-Aufruf wie `Send_Status`/`Send_Datum`.

- [ ] **Step 1: Failing test** — `test_complete_delivery_writes_template_and_segment` (Fake-svc: erwartete Felder enthalten `Email_Template_ID='v2-produktion-s1'`, `Segment='produktion'`); `test_v1_message_without_header_leaves_fields_untouched`.
- [ ] **Steps 2–4:** FAIL → Implementierung → PASS + Suite.
- [ ] **Step 5: Commit** `feat(sales-os): record template id and segment on delivery`.

### Task 3: Alle Entwürfe neu erzeugen (operativ)

**Voraussetzung:** PR #505 inkl. Task 1+2 gemerged (Task 5); Wrapper `services/system/bin/hsb-sales` zeigt auf `origin/main`.

- [ ] **Step 1:** Fehlerhafte v2-Entwürfe archivieren: in beiden Postfächern alle Nachrichten in `Entw&APw-rfe` mit Header `X-HSB-Template-ID: v2-` per UID MOVE nach `Entw&APw-rfe-Archiv-v1`; Bilanz vorher/nachher je Postfach ausgeben (Erwartung JOEL 480 → 0, JORDI 0 → 0).
- [ ] **Step 2:** Schlüsselprüfung im Vordergrund: `hsb-sales create-v2-drafts --owner JOEL --limit 1` (Dry-Run) und `python -c "import new_drafts as nd; assert nd.click_secret()"`.
- [ ] **Step 3:** Seriell je Owner bis `selected: 0`: `hsb-sales create-v2-drafts --owner <O> --limit 200 --apply`. Läuft im Vordergrund oder mit erreichbarem Schlüsselbund.
- [ ] **Step 4:** Stichprobe 10 Entwürfe je Postfach lesen (IMAP readonly): Anrede ohne Vorname, genau 1 Link mit `/r/`, kein „Guten Tag Guten Tag“, Firmenname korrekt. Zählung: Entwürfe = Entwürfe mit `/r/`-Link.
- [ ] **Step 5:** Ergebnis (Zahlen je Owner/Segment) in `docs/verification/` und `ai-state event`.

### Task 4: Täglicher Versandjob mit Hochlauf

**Files:** Create `apps/sales-os/deploy/mac/de.hsb-boden.daily-dispatch.plist`; Create `services/system/bin/hsb-dispatch-daily` (KI-System, nicht im Repo); Test `apps/sales-os/tests/test_ramp.py` (bestehend) um `test_second_run_same_day_respects_cap` ergänzen.

**Interfaces:** Consumes `dispatch_verified(count_per_owner, owners, dry_run, cap)` und `send_governance.daily_budget(first_send_date, today)`.

- [ ] **Step 1: Failing test** `test_second_run_same_day_respects_cap` (zweiter Aufruf am selben Tag sendet 0, wenn Budget erschöpft).
- [ ] **Steps 2–4:** FAIL → (falls nötig) Implementierung → PASS + Suite.
- [ ] **Step 5:** `hsb-dispatch-daily`: Werktag-Prüfung, `count_per_owner=daily_budget(...)`, setzt `HSB_CUSTOMER_SEND_ENABLED=yes` nur im eigenen Prozess, schreibt Log nach `~/.local/state/hsb-sales-os/dispatch-YYYY-MM-DD.log`; danach Cockpit-Update (`crm_dashboard --apply`).
- [ ] **Step 6:** Dry-Run live: `dispatch_verified(count_per_owner=10, dry_run=True)` → Zählung je Owner, `customer_emails_sent=0`.
- [ ] **Step 7:** LaunchAgent (Mo–Fr 09:30) **erst nach Nutzerfreigabe** laden.
- [ ] **Step 8: Commit** `feat(sales-os): daily ramped dispatch job`.

### Task 5: PR abschließen

- [ ] **Step 1:** Tasks 1, 2, 4 auf Branch `feat/create-v2-drafts` (PR #505).
- [ ] **Step 2:** CI grün (8 Pflicht-Checks), Codex `adversarial-review --base origin/main` ohne high.
- [ ] **Step 3:** `gh pr merge 505 --squash --admin`; Wrapper-Worktree auf `origin/main`.

### Task 6: Google Analytics und Looker Studio

- [ ] **Step 1:** GA4 (Property `543244027`): Ereignis `flyer_download` als **Schlüsselereignis** markieren (Admin → Ereignisse). Nutzerschritt im Browser, falls die API-Rechte fehlen; Prüfung per `ga4 run_report` (Ereignis taucht mit `isKeyEvent` auf).
- [ ] **Step 2:** GA4-Bericht prüfen: Sitzungen mit `sessionCampaignName` `iboden_v2_produktion` / `iboden_v2_architekten` (`ga4 run_report`).
- [ ] **Step 3:** Looker Studio: neuer Bericht mit zwei Datenquellen — Google Sheets (`DASHBOARD`, `ALL_LEADS`, `CLICK_EVENTS`) und GA4 (`543244027`); Seiten: Übersicht (Versendet/Antworten/Bounces/Abmeldungen je Woche und Owner, inkl. `.de` aus `DE_VERSENDUNGEN_FORENSIK`), Kampagne v2 (Antworten je Segment, Klicks echt, Flyer-Aufrufe und -Downloads aus GA4). Link im `DASHBOARD!A1`-Hinweis.

### Task 7: Seed-Test und Versandstart

- [ ] **Step 1:** Nutzer nennt Testadressen → `apps/sales-os/config/seed_inboxes.json` → `seed-send` (mit `HSB_INTERNAL_TEST_SEND_ENABLED=yes`) → Nutzer meldet Posteingang/Spam je Anbieter oder speichert „Original anzeigen“ → `seed-read --raw-file`.
- [ ] **Step 2:** **Nutzer-„Versand freigeben“ im Chat.**
- [ ] **Step 3:** LaunchAgent laden; erster Lauf manuell beobachten (10 je Postfach), Cockpit danach prüfen (Versendet +20).
- [ ] **Step 4:** Nach 5 Werktagen: Bounce-Quote < 2 %, keine Pause → Woche 2 automatisch 20/Tag.

## Ohne KAS / außerhalb dieses Plans

- DMARC-`rua` und Google-Postmaster-TXT (Nutzer → DNS-Verwalter).
- `.de`-Inbound-Connector (HTTP 403) reparieren.
- Ersatzadresse nach Bounce (`bounce_rescue_agent`) automatisch einbinden — Folgeauftrag.
