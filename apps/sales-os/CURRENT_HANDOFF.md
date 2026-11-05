# CURRENT_HANDOFF — 2026-11-04 (Reparatur-zuerst-Vorlagen, Duplikat-Bereinigung, SSOT-Checks)

- **Betreiber:** Joel Cherino Diaz · **Ausführung:** Claude Code
- **Branch:** `claude/marketing-strategy-url-bug-ddllet` (PR #465), enthält zusätzlich `main`, PR #515, #516, #517
- **Kundenversand in diesem Lauf:** 0. Keine Postfach-Änderung aus dieser Cloud-Sitzung (kein IMAP-/Sheet-Zugang hier).

## Owner-Entscheidung 2026-11-04 (jetzt in PROJECT_TRUTH.md)
- Akquise-Entwürfe: kein Anhang, kein Flyer-Link, kein Klick-Token im Sichttext. Einziger Link `https://www.hsb-boden.de/reparatur/` (302 auf die Reparaturseite).
- Vorlage „Reparatur zuerst": Produktion über den konkreten Schadensfall (Foto, Ersteinschätzung binnen eines Arbeitstags kostenfrei — Owner-Zusage, nicht auf der Website belegt); Planer über Bestandsprüfung vor der Ausschreibung. Floskel „Ist das für ein aktuelles Vorhaben in Ihrem Büro interessant?" entfernt.
- Anrede nur mit belegter Anrede + Nachname, sonst „Sehr geehrte Damen und Herren,". Keine CRM-Firmen-/Titelangaben im Fließtext.
- MIME: multipart/alternative (text/plain + text/html), CRLF, quoted-printable (Absätze bleiben in Outlook beim Bearbeiten erhalten).
- `/flyer`-Weiterleitungen aus #466 bleiben aktiv.

## Umgesetzt (Code, getestet)
- `canonical_template_factory.py`: neue Reparatur-Texte, `anrede_v2`, `REPAIR_URL`, `REPARATUR_COPY_REV`.
- `com_mailbox_manager.py`: `plaintext_to_html`, v2-Entwürfe als multipart/alternative mit `X-HSB-Copy-Rev`.
- `sales_reconciliation.py`: `OUTDATED_REPAIR_COPY`, `ALREADY_CONTACTED_DOMAIN`, Reparatur-Link-Regel.
- `draft_upgrade.py`: ersetzt veraltete Reparatur-/Planer-Fassungen beider Segmente.
- `draft_dedupe.py` + `hsb_cli.py dedupe-drafts`: ein Entwurf je Empfänger, Dubletten per UID MOVE ins Archiv, geschützte Gruppen unberührt.
- `verify_ssot.py`: Asset-Hashes, neutraler Anhangsname, Mail-URLs (statisch; `--live` per HTTP). Production-Deploy prüft die Links danach live.
- `_redirects`: `/reparatur` und `/reparatur/` → `/leistungen/boden-reparatur-instandsetzung/` (302).
- Nachweis: 556 Python-Tests, 366 Website-Tests, Astro-Check 0/0/0, 59 Seiten, Worker-Dry-Run ok, `verify_ssot.py` Exit 0.

## Offen (Reihenfolge einhalten)
1. PR #465 mergen und Production-Deploy auslösen; danach muss `python3 scripts/verify_ssot.py --live` grün sein (`/reparatur/` liefert vor dem Deploy 404).
2. Auf dem Mac: frischer Audit `python3 apps/sales-os/engine/sales_reconciliation.py --output <dir>`.
3. `hsb_cli.py dedupe-drafts --audit-dir <dir>` (Dry-Run), Zahlen prüfen, dann `--apply`.
4. Erneut auditieren, dann `hsb_cli.py upgrade-drafts --owner JOEL|JORDI --variant reparatur --cohort all --limit 100 --audit-dir <dir>` (Dry-Run), danach mit `--apply` in Schleifen bis 0 ausgewählt.
5. Stichprobe in Outlook (Desktop + Mobil): Entwurf öffnen, bearbeiten, Absätze prüfen.

---

# Nachtrag — 2026-09-26 (fehlender Handoff, aus Git-Historie rekonstruiert)

- An diesem Tag entstanden ohne Handoff-Eintrag u. a. `.com`-Migration (KASServer IMAP/SMTP), Rapid-Batch-Runner, `hsb_cli.py`, Cockpit, Bounce-Engine, 2×100 Entwürfe und in Commit `4527f90` `dual_delivery_helper.py`.
- `dual_delivery_helper.py` sah „PDF-Anhang + CDN-Link" vor; der Link `https://www.hsb-boden.de/flyer/HSB-Flyer-*_FINAL.pdf` existierte nie (HTTP 404). Der Helper war nirgends eingebunden; der tote Link ist nun entfernt und per `verify_ssot.py` gesperrt.
- Ein späterer Korrekturversuch (ChatGPT) brach ab und hinterließ keinen Commit; ungesicherte lokale Änderungen auf dem Mac sind von hier aus nicht prüfbar.

---

# CURRENT_HANDOFF — 2026-09-21 (HSB Sales OS Ultimate Pipeline Merge)

- **Datum / Uhrzeit:** 2026-09-21T16:18:00+02:00
- **Betreiber:** Joel Cherino Diaz
- **Status:** PIPELINE GEMERGT & VERIFIZIERT auf `main` (`REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0`)
- **Git HEAD:** `main` @ `957922a` — Squash-Merge von PR #405
- **Branch:** `feat/b2b-copy-purge` gelöscht (lokal + remote)

---

## 1. Was wurde gebaut (5 neue TDD-Module)

| # | Modul | Datei | Tests | Commit |
|---|-------|-------|-------|--------|
| 1 | **Canonical Template Factory** | `engine/canonical_template_factory.py` | 5 Tests | `aac14ed` |
| 2 | **SQLite Shadow Event-Store** | `engine/sqlite_shadow_store.py` | 2 Tests | `8fb323a` |
| 3 | **Graph Batch Worker** | `engine/graph_batch_worker.py` | 1 Test | `d83fd52` |
| 4 | **Async Sheets 2D Sync Daemon** | `engine/async_sheet_sync_daemon.py` | 1 Test | `312903e` |
| 5 | **Master Orchestrator CLI** | `engine/master_mailbox_orchestrator.py` | 2 Tests | `8783c9e` |

**Gesamt-Testsuite:** 15/15 passed in 0.13s (inkl. pre-existing Send-Governance).

---

## 2. Architektur-Übersicht

```
Leads (ALL_LEADS Sheet)
  │
  ▼
render_canonical_email()  ← Fail-closed: ValueError bei fehlender/ungültiger E-Mail
  │
  ▼
process_batch_chunk()     ← Graph $batch (20 Calls pro Request, 429-Backoff)
  │
  ▼
SQLiteShadowStore         ← WAL-Modus, ACID, decoupled von Sheets-Quota
  │
  ▼
flush_pending_to_sheets() ← Async 2D-Bulk nach ALL_LEADS (AO:AR Spalten)
  │
  ▼
master_mailbox_orchestrator.py --owner JOEL --batches 10 [--apply]
```

---

## 3. Invarianten (VERIFIZIERT)

- ✅ `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` — ausschließlich Drafts
- ✅ Geschäftsführer: `Jordie Post` (mit `-ie`, niemals `Jordi`) — § 35a GmbHG
- ✅ Fail-Closed Recipient Gate: `if not to_addr or "@" not in to_addr: raise ValueError`
- ✅ Kanonische Flyer: `HSB-Flyer-Joel-Cherino_FINAL.pdf` (241 KB) + `HSB-Flyer-Jordie-Post_FINAL.pdf`
- ✅ Logo: 102×75px bicubic `hsb-boden-logo.png`

---

## 4. Offene Aufgaben (TODO — nächstes Modell)

### P0 — Sofort
- [ ] **CURRENT_STATE.md aktualisieren:** PR #405 ist gemergt, TODO-Liste bereinigen
- [ ] **Untracked Files committen oder .gitignore:** 6 untracked Engine-Dateien + 2 Plan-Dokumente

### P1 — Nächster Schritt
- [ ] **Jordie Postfach-Veredelung:** `overhaul_drafts.py --owner JORDI --limit 50 --apply`
  - Jordies 797 Drafts auf 2026-Standard bringen
  - Benötigt: Jordies Power Automate Flow / Access Token
- [ ] **Joel Restliche 1.031 Drafts:** `overhaul_drafts.py --owner JOEL --limit 100 --apply`
  - Bereits 49 Pilot-Drafts verifiziert, weitere 1.031 offen

### P2 — Optimierung
- [ ] **Master Orchestrator CLI Live-Einsatz testen:**
  ```bash
  python3 engine/master_mailbox_orchestrator.py --owner JOEL --batches 5
  ```
- [ ] **Graph Batch Worker mit echtem Access Token testen** (bisher nur Mock-Tests)
- [ ] **4.081 verbleibende Leads:** Golden Blueprint via `canonical_template_factory` + `graph_batch_worker`

### P3 — Langfristig
- [ ] **Flyer-Kompression:** 1,58 MB → < 450 KB (EOP-Immunität)
- [ ] **Web Performance:** First-Party Edge Analytics, Immutable Caching
- [ ] **Data Hygiene Gate:** 323 Leads mit `Versandfreigabe=yes` aber `Legal_Basis=UNKNOWN`

---

## 5. Dateien-Referenz für nächstes Modell

| Datei | Zweck |
|-------|-------|
| `PROJECT_TRUTH.md` | SSOT-Regeln und Wahrheitsquelle |
| `CURRENT_STATE.md` | Live-Taskboard (veraltet, muss aktualisiert werden) |
| `apps/sales-os/CURRENT_HANDOFF.md` | **Diese Datei** — letzte Übergabe |
| `apps/sales-os/PROJECT_STATE.md` | Kanonischer Projektstatus |
| `docs/superpowers/plans/2026-09-21-hsb-sales-os-ultimate-execution-plan.md` | Ausführungsplan (100% abgehakt) |

## 6. Anweisung an nachfolgendes Modell

1. Lies zuerst `PROJECT_TRUTH.md`
2. Lies dann diese `CURRENT_HANDOFF.md`
3. Prüfe `CURRENT_STATE.md` und aktualisiere die TODO-Liste
4. Führe nach Änderungen `python3 apps/website/scripts/verify_ssot.py` aus
5. Teste mit `pytest apps/sales-os/tests/ -q`

### Ein-Befehl-Abläufe (04.11.2026, ergänzt)
- `bash apps/sales-os/bin/postfach-lauf.sh` zeigt im Probelauf alle Zahlen; mit `--apply` laufen Audit, Dubletten-Archiv, Audit, Reparatur-Erneuerung in 100er-Tranchen und das Abschluss-Audit. Versendet wird dabei nichts.
- `bash apps/sales-os/bin/versand-tranche.sh <1-35>` ist ein Probelauf. Mit `--apply` gehen bis zu N Entwürfe je Postfach raus, 45–90 s Abstand, höchstens 35 je Postfach und Tag, alle Sperren werden vorher frisch geprüft.
- Beide Skripte laden die Zugangsdaten aus der Umgebung oder aus `~/.config/hsb-sales-os/env` (nicht im Repo). Laufen müssen sie auf dem Mac, weil nur dort der Google-Zugang liegt. WG01 erreicht IMAP, hat aber keinen CRM-Zugang.
- Geräteunabhängig (ohne Mac): GitHub → Actions → „Sales OS safety and inbound“ → Run workflow. Modus `prepare-drafts-preview` liefert nur Zahlen, `prepare-drafts` führt aus. `send-preview` bzw. `send` mit `count` 1–35 je Postfach. Zugang über die vorhandenen Secrets `HSB_SALES_GOOGLE_AUTH` / `HSB_SALES_MAILBOXES_JSON`.

### Stand 04.11.2026, 23:00 Uhr: prepare-drafts

- Lauf-Kette: Kontrakt `docs/ai_state/loops/2026-11-04-prepare-drafts-kette.md`. Erster Kettenlauf per einmaligem Cron `55 1 5 11 *`; die Weitergabe ist erst nach dem ersten Lauf nachgewiesen. Nach Abschluss die Cron-Zeile und den Job `chain-start` entfernen.
- Ursache der Abbrüche nach je 100 Entwürfen: Die Sperr-Verbindung blieb ungenutzt offen, All-Inkl trennte sie nach etwa 12 Minuten, das Lösen der Sperre schlug fehl. Behoben: Die Sperre nutzt je Schritt eine frische Verbindung.
- Codex-Review zu #524 umgesetzt: Inhaber-Kennung statt `force_unlock`; ein Neustart übernimmt vorhandene Ersatzentwürfe live, statt einen zweiten anzulegen.
- CRM-Stand vor dem Neustart: 204 Entwürfe umgestellt. Kundenversand: 0.

### Stand 05.11.2026, 10:40 UTC: Entwürfe fertig, versandbereit
- audit-3 von Lauf 268: JOEL sendable 2.784/2.830, JORDI 1.924/1.955. Kundenversand: 0.
- Lauf 268: refresh-signature (Schnellweg) ohne Auswahl, weil die 673 JORDI-Reste im CRM an andere Draft_IDs gebunden waren; der langsame Weg hat 674 Entwürfe in 7 Tranchen neu aufgebaut und das CRM nachgezogen.
- send-preview 5 (Lauf 269): je Postfach 5 ausgewählt, 0 gesendet.
- Nächster Schritt nur auf Betreiberkommando: mode `send`, count 5–10 zum Start (Warm-up), DKIM im KAS aktivieren. § 7 UWG ist vom Betreiber geklärt.
