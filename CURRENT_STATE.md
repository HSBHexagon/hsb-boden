# CURRENT_STATE — Live-Fortschritt & Taskboard (SSOT)

> **Stand:** 2026-09-20 17:56 CEST  
> **Aktiver Git-Branch:** `feat/b2b-copy-purge`  
> **Aktiver PR:** [#405 auf GitHub](https://github.com/HSBHexagon/hsb-boden/pull/405)  
> **System-Status:** 467/467 TESTS PASS (100% GRÜN) &middot; `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0`

---

## 1. Abgeschlossene Meilensteine (DONE)

- [x] **Dev-Dummy Bereinigung:** 4 Entwicklungs-Mails (`test@example.com`, Knopftest) restlos aus Exchange gelöscht.
- [x] **Inbound Automation Workers:**
  - `ingest_bounces.py` mit `--owner ALL --apply` ausgeführt (NDRs überwacht, Bounces im CRM gesperrt).
  - `ingest_optouts.py` mit `--owner ALL --apply` ausgeführt (NLP/Regex Opt-outs überwacht).
- [x] **Pre-Send DNS/MX-Guard:** `check_domain_mx` fängt ungültige Domains automatisch ab (z. B. `weingut-montigny.de` vor Hard-Bounce bewahrt).
- [x] **Pilot-Veredelung Joel (49 Leads):** 49 Entwürfe in Joels Postfach in-place überarbeitet (Firmennamen, AGI S 40 Copy, Logo, Abmeldetabelle, 241 KB Flyer) und in `ALL_LEADS` synchronisiert.
- [x] **Kanonisches Namens-Hardening auf `Jordie Post`:** 18 Dateien auf kanonische Schreibweise `Jordie Post` (mit *-ie*) gemaess CURRENT_HANDOFF.md zurueckgestellt (Revert-Commit `89dee47`).
- [x] **Multi-Owner Overhaul Runner:** `overhaul_drafts.py` um `--owner {JOEL,JORDI,ALL}` erweitert.
- [x] **Testsuite-Verifikation:** 75 Pytest + 362 Apps Script + 30 FlowConnect = 467 Tests bestanden.
- [x] **SSOT-Architektur verankert:** `PROJECT_TRUTH.md` und `scripts/verify_ssot.py` im Repo-Root etabliert.

---

## 2. In Bearbeitung / Nächste Schritte (TODO)

- [ ] **Jordie Postfach-Veredelung:** Ausführung von `overhaul_drafts.py --owner JORDI --limit 50 --apply` über Jordies Power Automate Flow / Apps Script.
- [ ] **PR #405 Merge:** Nach Abschluss der Jordi-Tranche Merge in `main`.

---

## 3. Tool-Start-Anweisung für KIs (Claude, Gemini, Cursor)
Vor jeder Bearbeitung:
1. Lies `PROJECT_TRUTH.md`
2. Lies `CURRENT_STATE.md`
3. Führe nach Änderungen `python3 scripts/verify_ssot.py` aus.
