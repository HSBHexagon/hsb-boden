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
