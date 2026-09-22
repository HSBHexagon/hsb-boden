# CURRENT_STATE — Live-Fortschritt & Taskboard (SSOT)

> **Stand:** 2026-09-22 19:36 CEST  
> **Aktiver Git-Branch:** `main`  
> **Letzter Merge:** PR #405 → Squash `957922a` (21. Sep. 2026)  
> **System-Status:** 15/15 TESTS PASS (100% GRÜN) · `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0`

---

## 1. Abgeschlossene Meilensteine (DONE)

- [x] **Dev-Dummy Bereinigung:** 4 Entwicklungs-Mails restlos aus Exchange gelöscht.
- [x] **Inbound Automation Workers:** `ingest_bounces.py` + `ingest_optouts.py` implementiert und ausgeführt.
- [x] **Pre-Send DNS/MX-Guard:** `check_domain_mx` fängt ungültige Domains automatisch ab.
- [x] **Pilot-Veredelung Joel (49 Leads):** 49 Entwürfe in-place überarbeitet und synchronisiert.
- [x] **Kanonisches Namens-Hardening:** `Jordie Post` (mit -ie) in allen 18 Dateien.
- [x] **Multi-Owner Overhaul Runner:** `overhaul_drafts.py --owner {JOEL,JORDI,ALL}` implementiert.
- [x] **SSOT-Architektur:** `PROJECT_TRUTH.md` und `scripts/verify_ssot.py` etabliert.
- [x] **Ultimate Execution Pipeline (5 Module, TDD):**
  - `canonical_template_factory.py` — Fail-closed Recipient Gate
  - `sqlite_shadow_store.py` — ACID WAL-Modus Event-Store
  - `graph_batch_worker.py` — Graph $batch 20-Call Worker
  - `async_sheet_sync_daemon.py` — 2D-Bulk Sheets Sync
  - `master_mailbox_orchestrator.py` — CLI mit SSOT+DNS Preflight
- [x] **PR #405 gemergt:** Squash-Merge auf `main` @ `957922a`.
- [x] **Feature-Branch aufgeräumt:** `feat/b2b-copy-purge` lokal + remote gelöscht.

---

## 2. Nächste Schritte (TODO)

### P1 — Operativ
- [ ] **Jordie Postfach-Veredelung:** `overhaul_drafts.py --owner JORDI --limit 50 --apply`
- [ ] **Joel Restliche Drafts:** `overhaul_drafts.py --owner JOEL --limit 100 --apply`
- [ ] **Untracked Files bereinigen:** 6 Engine-Dateien + 2 Plan-Docs committen oder .gitignore

### P2 — Integration
- [ ] **Master Orchestrator Live-Test:** `master_mailbox_orchestrator.py --owner JOEL --batches 5`
- [ ] **Graph Batch Worker Live-Test:** Echter Access Token statt Mock
- [ ] **4.081 verbleibende Leads:** Golden Blueprint generieren

### P3 — Langfristig
- [ ] **Flyer-Kompression:** 1,58 MB → < 450 KB
- [ ] **Data Hygiene Gate:** 323 Leads mit Legal_Basis=UNKNOWN
- [ ] **Web Performance Optimierungen**

---

## 3. Tool-Start-Anweisung für KIs

Vor jeder Bearbeitung:
1. Lies `PROJECT_TRUTH.md`
2. Lies `apps/sales-os/CURRENT_HANDOFF.md`
3. Lies `CURRENT_STATE.md` (diese Datei)
4. Führe nach Änderungen `python3 apps/website/scripts/verify_ssot.py` aus
5. Teste mit `pytest apps/sales-os/tests/ -q`
