# CURRENT_STATE — Live-Fortschritt & Taskboard (SSOT)

> **Stand:** 2026-10-12 16:05 CEST  
> **Aktiver Git-Branch:** `main`  
> **System-Status:** 798/798 TESTS PASS (100% GRÜN) · `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` · `.COM` SHIELD AKTIV

---

## 1. Abgeschlossene Meilensteine (DONE)

- [x] **Dev-Dummy Bereinigung:** 4 Entwicklungs-Mails restlos aus Exchange gelöscht.
- [x] **Inbound Automation Workers:** `ingest_bounces.py` + `ingest_optouts.py` implementiert und ausgeführt.
- [x] **Pre-Send DNS/MX-Guard:** `check_domain_mx` fängt ungültige Domains automatisch ab.
- [x] **Kanonisches Namens-Hardening:** `Jordie Post` (mit -ie) in allen Dateien verankert (§ 35a GmbHG).
- [x] **SSOT-Architektur:** `PROJECT_TRUTH.md` und `scripts/verify_ssot.py` etabliert.
- [x] **Kanonische Vektor-Flyer (241 KB):** Joel & Jordie Master-PDFs mit SHA-256 Gates integriert.
- [x] **.COM Outbound Akquise-Shield (All-Inkl):** 
  - `j-cherino@hsb-boden.com`: 102 Entwürfe (IMAP/SMTP OK)
  - `j-post@hsb-boden.com`: 52 Entwürfe (IMAP/SMTP OK)
  - `Reply-To: ...@hsb-boden.de` für M365-Antwort-Routing verifiziert
- [x] **Cloudflare 301 Redirect:** `hsb-boden.com` leitet live per 301 auf `https://www.hsb-boden.de/` weiter.
- [x] **Google Sheet SSOT Sync:** 50 Leads für Jordie (`COM-JORDI-20261012`) auf `drafted` synchronisiert (300 Zellen).
- [x] **Live-Testversand an Betreiber:** Erfolgreiche Test-Zustellung an `cherinodiaz@outlook.com` ohne Bounces.

---

## 2. Nächste operative Schritte (TODO)

### P1 — Operative Akquise & Vertrieb
- [ ] **Tägliche Outlook-Sichtung:** Joel & Jordie sichten und versenden Tranchen aus dem Ordner `Entwürfe`.
- [ ] **Nächster Entwurfs-Batch:** Bei Bedarf nächste 50–100 Leads via `run_com_batch.py` nachladen.
- [ ] **Dual-Domain Reconciliation:** Regelmäßiger Abgleich via `python3 apps/sales-os/engine/hsb_cli.py sync`.

### P2 — Wartung & GitHub
- [ ] **Dependabot PR #457:** Bump sharp/wrangler in `apps/website` final abschließen (nach CodeQL-Freigabe).
- [ ] **4.000+ verbleibende Leads:** Sukzessive Vorbereitung im Google Sheet `ALL_LEADS`.

---

## 3. Tool-Start-Anweisung für KIs

Vor jeder Bearbeitung:
1. Lies `PROJECT_TRUTH.md`
2. Lies `CURRENT_STATE.md` (diese Datei)
3. Führe nach Änderungen `python3 scripts/verify_ssot.py` aus (Muss Exit 0 sein!)
4. Teste mit `pytest apps/sales-os/tests/ -q`
