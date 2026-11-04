# Übergabe E-Mail-Marketing v2 — Stand 28.10.2026 (Claude Code)

Zweck: Ein anderes Modell oder ein Mensch kann ab hier ohne Rückfrage weiterarbeiten. Alle Zahlen sind gemessen (Befehl in Klammern). Nichts hier ist eine Rechtsbewertung; der Nutzer hat Rechtsfragen selbst geklärt und wünscht keine Einschätzungen dazu.

## 1. Ziel (Nutzerauftrag 26.10.)

B2B-Kaltakquise von HSB Hexagon Säurebau GmbH (säurefeste Industrieböden) über die zwei Postfächer `j-cherino@hsb-boden.com` (Owner JOEL) und `j-post@hsb-boden.com` (Owner JORDI, „Jordie Post“). Ziel jeder Mail: **eine Antwort** (Gespräch / Unterlagen). Teilaufgaben: Zugänge prüfen, Klickmessung, Zustellbarkeit nach Best Practice, alle vorbereiteten Entwürfe verbessern, funktionierende Links. Rahmen: nur vorhandene Infrastruktur, **kein Zugriff auf All-Inkl KAS/DNS**.

Das Modell des Nutzers (verbindlich): **Lead → E-Mail-Entwurf → Versand → Status im CRM; Antwort → Status; Abmeldung → „abgemeldet“.**

## 2. Systemaufbau (Engine)

- Repo `HSBHexagon/hsb-boden`, Python-Engine `apps/sales-os/engine/`, Website `apps/website/` (Astro auf Cloudflare Pages, Projekt `hsb-boden`, Account `01dc37803d1c687b4f9d6249ec89f700`).
- CRM = Google Sheet `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg`, Tab `ALL_LEADS` (6.424 Zeilen, 73 Spalten). Einzige Wahrheit.
- Postfächer: All-Inkl IMAP/SMTP (`w0221a9f.kasserver.com`), Ordner `Entw&APw-rfe` (Entwürfe), `Entw&APw-rfe-Archiv-v1` (Archiv, neu), IMAP kann MOVE/UIDPLUS.
- Zugangsdaten: nur in `projects/active/hsb/boden/apps/sales-os/.env` (Haupt-Checkout). Nie kopieren/ausgeben.
- Wrapper `~/KI-System/services/system/bin/hsb-sales <befehl>`: führt `hsb_cli.py` im Worktree `.worktrees/email-marketing-v2` aus und lädt die `.env` zur Laufzeit. `hsb-sales audit --output <dir>` = Lese-Audit. `--bindings-verified` als erstes Argument setzt `HSB_CRM_BINDINGS_VERIFIED=yes`.
- Laufdaten (Audit, Journale, Logs): `~/KI-System/.tools/hsb-sales-os/runs/20261028/` (dauerhaft, nicht im Git). Versand-Status-DB: `~/.local/state/hsb-sales-os/`.
- Geheimnis Klickzähler: macOS-Schlüsselbund, Dienst `hsb-click-secret`; gleiches Secret als Pages-Secret `CLICK_SECRET`.

### Module (alle mit Tests in `apps/sales-os/tests/`)
| Modul | Aufgabe |
|---|---|
| `lead_quality.py` | DSN-Klassen (hard/soft/policy), Zustellbarkeits-Flags (NO_MX, SYNTAX_INVALID, ROLE_NOREPLY, PREVIOUS_HARD_BOUNCE), `segment_for`, `fit_score` (Tier A/B/C/Z), `daily_selection` |
| `seed_test.py` | Seed-Test an eigene Testpostfächer, Auswertung `Authentication-Results`, Blocklisten-Abfrage (7 DNSBL mit Testeintrag-Prüfung) |
| `website_signals.py` | Website-Text (SSRF-gehärtet, robots.txt, 2 MB/20 s), Stichwortsignale mit wörtlichem Zitat |
| `canonical_template_factory.render_email_v2` | Texte v2, reiner Text, 2 Segmente × 3 Schritte |
| `click_sync.py` | Klick-Token (HMAC), `click_url`, Abgleich KV → CRM-Tab `CLICK_EVENTS` |
| `apps/website/functions/r/[token].ts` | Klickzähler `/r/<token>` → 302 auf `/flyer/`, Bot-Filter, KV `EMAIL_CLICKS` |
| `sequence.py` | Folgemails Tag 4/10 im Thread, Antwort-SLA |
| `send_governance.py`, `outbound_safety.dispatch_verified` | Hochlauf 10/20/30 (max 35) je Postfach, automatische Pause (Bounces > 2 %, Policy-Bounce, Deferrals), Versand nur `HSB_CUSTOMER_SEND_ENABLED=yes` |
| `draft_upgrade.py` + `crm_bindings.py` | Alter Weg: v1-Entwurf durch v2 ersetzen über CRM-Zeilenbindungen. **Aufgegeben** (zu komplex, Sheets-Quoten 60 Lesen/min, Metadaten-Limit 30.000 Zeichen). |
| `new_drafts.py` (`create-v2-drafts`) | **Neuer Weg:** Lead aus CRM → v2-Entwurf. Nur sendefähige Leads (`check_eligibility`), Empfänger nur einmal im CRM, kein zweiter v2-Entwurf je Lead, 80/20 Produktion/Architekten, Tier A→B→C, Sperre je Postfach. Versendet nie. |

## 3. Chronologie mit Nachweisen

1. 26.10. PR #473/#475 gemerged: List-Unsubscribe, Härtung, stündlicher CRM-Abgleich (LaunchAgent `de.hsb-boden.crm-sync-trigger`, `sales-os-safety.yml mode=inbound-sync`).
2. 27.10. Plan `docs/superpowers/plans/2026-10-26-email-marketing-v2.md`; Tasks 1–6 Claude (subagent-gesteuert, Review je Task), Tasks 7–9 Codex. **PR #503 gemerged** (`c0599b8`).
3. 28.10.
   - Klickspeicher KV `hsb-email-clicks` (`6d4dc654acc84379bac943cbf1d5f76b`) an Production + Preview gebunden, `CLICK_SECRET` gesetzt, **Production-Deploy** (Run 40661416201, success). Live: `/flyer/` 200, `/Flyer` 301, `/r/<gültig>` 302 + KV-Eintrag `human`, ungültig → `click:invalid:<Minute>`.
   - `bounce-report --com-only`: 47 Bounces (33 hard, 10 soft, 3 policy, 1 unknown). `.de`-Inbound nicht lesbar (Office365-Connector HTTP 403).
   - `blocklist-check 85.13.130.17`: alle 7 Listen clean. Spamhaus nur manuell.
   - Linkprüfung meldete Logo-PNG fälschlich als defekt → **PR #504 gemerged** (`b4a81e0`): Bildprüfung per Pillow/XML, CRM-Bindungen, Codex-Befunde behoben.
   - CRM: Anrede Zeile 1115 (`HSB-20260708-01114`) von „Guten Tag Günther Jauch“ auf „Herr Günther Jauch“ korrigiert (Readback ok). `score-leads --apply` (Tier/Score/Segment in leere Zellen) durch Timeout **unvollständig** — wiederholbar, schreibt nur leere Zellen.
   - **Alle 5.605 v1-Entwürfe** (JOEL 3.070, JORDI 2.535) ins Archiv verschoben; Grund: nach dem Linkfix galten 3.947 v1 als versandbereit. Bilanz exakt geprüft.
   - Neuer Weg `create-v2-drafts` (PR #505, **offen**, Head `cb7afca`): angelegt JOEL 610, JORDI 575.
   - **Fehler erkannt:** Architekten-Text verspricht „herstellerneutrale LV-Bausteine und Detailzeichnungen“, die es nicht gibt. Alle 705 v2-Architekten-Entwürfe ins Archiv verschoben.

## 4. Stand jetzt

- **Versendet: 0 Kundenmails.** `HSB_CUSTOMER_SEND_ENABLED` nicht gesetzt.
- Entwürfe: JOEL **480** (alle Produktion v2; Anrede 478× „Guten Tag,“, 2× „Sehr geehrter Herr“; keine fehlerhaften Anreden), JORDI **0**. Archiv: alle v1 + 705 v2-Architekten.
- CRM: 6.424 Leads = 4.760 Architekten DE + 52 AT (Import „Architekten Deutschland/Oesterreich Excel 2026-07-08“) + 1.612 Produktion (Getränke/Lebensmittel). 1.609 Leads ohne Ansprechpartner (fast alle Produktion).
- Historie: 1.069 gesendet; Antworten Produktion 7/134 (~5 %), Architekten 8/935 (~0,9 %); Bounce 5,9 %.
- Tests: Sales-OS 405 passed, 1 skipped (Branch `feat/create-v2-drafts`).

## 5. Offene Punkte (Reihenfolge)

1. **Nutzerentscheidung:** Architekten pausieren und nur Produktion versenden? (Empfehlung: ja.) Architekten-Text nur mit Angeboten, die HSB wirklich liefern kann.
2. PR #505: Codex-Nachprüfung der Fixes (Empfängersperre, Postfach-Sperre, Kapazität), dann Merge (Dauerfreigabe nach grüner CI + Codex ohne high).
3. Seed-Test: Nutzer muss Testadressen (Gmail, Outlook.com, GMX, Web.de, T-Online) nennen → `config/seed_inboxes.json` → `seed-send` → `seed-read`.
4. Versandstart: `HSB_CUSTOMER_SEND_ENABLED=yes` + `dispatch_verified(count_per_owner=10, dry_run=False)` täglich, nur nach ausdrücklichem Nutzer-„Versand freigeben“.
5. Lücken der Status-Übersicht: Ersatzadresse nach Bounce (`bounce_rescue_agent`) läuft nicht automatisch; Verschiebung von Folgemails nach Abwesenheit (`Follow-up-Datum`) live unverifiziert; eigener Übersichts-Tab „Versand-Übersicht“ fehlt.
6. `score-leads --apply` erneut laufen lassen (fortsetzbar).
7. DNS (Nutzer → DNS-Verwalter): `_dmarc` TXT `v=DMARC1; p=none; rua=mailto:j-cherino@hsb-boden.com; fo=1`; Google-Postmaster-TXT nach Anmeldung auf postmaster.google.com.
8. `.de`-Inbound: Office365-Connector-ACL (HTTP 403) reparieren lassen.

## 6. Sperren (nie ohne Nutzerfreigabe)

- Kein Kundenversand, kein `HSB_CUSTOMER_SEND_ENABLED=yes`.
- Nichts löschen; „entfernen“ = in `Entw&APw-rfe-Archiv-v1` verschieben.
- Kein KAS/DNS. Keine Rechtsbewertungen. Keine Behauptungen über HSB (Zertifikate, Referenzen, Angebote), die nicht belegt sind.
- Kein Production-Deploy ohne Anlass; Merges in hsb-boden per Dauerfreigabe nur nach grüner CI + Codex ohne high.

## 7. Lehren (für das nächste Modell)

- Ein Plan-Element, das Nutzerzuarbeit braucht (LV-Bausteine), darf nicht vor deren Lieferung in Kundentexte.
- Erst das Modell des Nutzers bauen (Lead → Entwurf → Versand → Status), dann Spezialfälle. Der Austausch einzelner Alt-Entwürfe war unnötig komplex.
- Google Sheets: 60 Lese-/Schreibzugriffe pro Minute je Nutzer; Developer-Metadaten max. 30.000 Zeichen je Tabelle.
- Vor jedem Massenlauf eine echte Stichprobe zeigen (Vorher/Nachher hat die doppelte Anrede aufgedeckt).
