# HSB Sales OS — Antigravity (AGY) System Guide & 2026 Architecture

> **Für ChatGPT, Claude Code und Entwickler:** Dieses Dokument ist die zentrale Dokumentation aller Änderungen, Architektur-Entscheidungen und Verifikationsnachweise, die von Antigravity (AGY) im HSB Sales OS Repository implementiert wurden.

---

## 1. Executive Summary & Problemstellung

### Ausgangslage
- HSB Hexagon Säurebau GmbH nutzte bisher die Hauptdomain `hsb-boden.de` für den Cold-Outreach via Microsoft 365 Exchange.
- **Risiko:** Reputationsverlust und Spam-Einstufung der primären Geschäftsdomain `hsb-boden.de`.
- **Zusätzliches Problem:** Veraltete Entwürfe im Postfach (~1.073 bei Joel, ~784 bei Jordi) mit veralteten PDF-Anhängen (1,5 MB), unvollständigen Firmennamen ("Ihr Unternehmen" oder Domain-Slugs), fehlenden Logos und unzureichenden Abmeldelinks.
- **Technische Hürde:** Microsoft Power Automate HTTP-Trigger wurden von Microsoft kostenpflichtig beschränkt (403 Quota).

### Die Lösung von Antigravity (AGY)
1. **Domain-Trennung (.com für Outbound, .de für Tagesgeschäft):**
   - Eigene Akquise-Domain: `hsb-boden.com` (gehostet auf All-Inkl / KASServer `w0221a9f.kasserver.com`).
   - Postfächer: `j-cherino@hsb-boden.com` (User: `m0821e5d`) und `j-post@hsb-boden.com` (User: `m0821e5b`).
   - **Schutz der Hauptdomain:** Kalte E-Mails gehen ausschließlich über `hsb-boden.com`.
   - **Automatischer Rücklauf:** Eingehende Kundenantworten auf `.com` werden serverseitig bei All-Inkl automatisch an die jeweiligen `.de`-Postfächer weitergeleitet.
2. **2026-Standard für alle E-Mail-Entwürfe:**
   - Bereinigte, offizielle Firmennamen (Handelsregister / Zefix-Enrichment).
   - Persönliche Anrede (`Sehr geehrte Frau / Sehr geehrter Herr ...`).
   - Nischenspezifischer B2B-Text (fugenlose Industrieböden, CIP/Säurebeständigkeit, AGI S 40, HACCP/WHG).
   - Kanonischer, geprüfter Flyer (241 KB, SHA-256 verifiziert).
   - Klares Impressum (§ 35a GmbHG: *Geschäftsführer: Jordie Post* mit "-ie").
   - DSGVO-konforme Abmelde-Tabelle (`https://www.hsb-boden.de/abmelden` + `mailto:`).
3. **Ultra-schnelle IMAP-Entwurfs-Engine (`com_mailbox_manager.py`):**
   - Direkte SSL-Injektion in den Ordner `Entw&APw-rfe` in **0,3 Sekunden** pro Entwurf (statt 5–8s über Microsoft Flow).
4. **Spreadsheet-Tools & Automatischer Dual-Domain-Abgleich:**
   - Farbcodierung in `ALL_LEADS`:
     - **Soft-Blau:** Gesendet (`sent` / `SENT`)
     - **Soft-Grün:** Antwort erhalten (`replied` / `REPLIED`)
     - **Zartrot:** Unzustellbar / Hard Bounce (`hard_bounce` / `Suppressed=yes`)
     - **Soft-Flieder:** Entwurf bereit (`drafted` / `DRAFTED`)
   - Menü-Funktionen direkt im Google Sheet und CLI-Daemon für `.de` + `.com`.

---

## 2. Wo sind die Entwürfe sichtbar? (Outlook vs. Webmail)

### Option A: Als eigenes Postfach direkt im gewohnten Outlook (Empfohlen)
Sobald das `.com`-Konto in Outlook eingerichtet ist, erscheint in Outlook in der linken Seitenleiste ein **neuer Ordnerbaum** direkt unter dem `.de`-Konto:

```text
▼ j-cherino@hsb-boden.de (Microsoft 365)
  ├── Posteingang
  └── Gesendete Elemente
▼ j-cherino@hsb-boden.com (All-Inkl IMAP)  <-- NEUER PUNKT IN OUTLOOK!
  ├── Posteingang
  ├── Entwürfe (Hier liegen alle 2026-Standard-Entwürfe!)
  └── Gesendete Elemente
```

#### Schritt-für-Schritt-Einrichtung in Outlook (Dauer: ca. 60 Sekunden):
1. In Outlook oben auf **Datei** (Windows) bzw. **Outlook -> Einstellungen -> Konten** (Mac) klicken.
2. **Konto hinzufügen** wählen.
3. E-Mail eingeben: `j-cherino@hsb-boden.com` bzw. `j-post@hsb-boden.com`.
4. Kontotyp: **IMAP**.
5. Serverdaten eintragen:
   - **Posteingangsserver (IMAP):** `w0221a9f.kasserver.com` | Port: `993` | Verschlüsselung: `SSL/TLS`
   - **Postausgangsserver (SMTP):** `w0221a9f.kasserver.com` | Port: `465` | Verschlüsselung: `SSL/TLS`
   - **Benutzername:** `m0821e5d` (Joel) bzw. `m0821e5b` (Jordi)
   - **Passwort:** (in `.env` hinterlegt)
6. Fertigstellen. Die Entwürfe synchronisieren sich sofort in den Ordner `Entwürfe`!

### Option B: Über das All-Inkl Webmail (Sofort einsatzbereit ohne Outlook-Änderung)
- **URL:** [https://webmail.all-inkl.com/](https://webmail.all-inkl.com/)
- Beide Postfächer sind im Google Chrome-Browser bereits geöffnet und eingeloggt:
  - Normales Browser-Fenster: `j-post@hsb-boden.com`
  - Inkognito-Fenster: `j-cherino@hsb-boden.com`

---

## 3. Die Komponenten im Detail

### 3.1 Mailbox Manager (`engine/com_mailbox_manager.py`)
- Verbindet sich per Python `imaplib` (Port 993 SSL) und `smtplib` (Port 465 SSL).
- Legt MIME-konforme Entwürfe (`X-Unsent: 1`, RFC-822) mit PDF-Anhang in `Entw&APw-rfe` ab.
- Liest gesendete Mails (`fetch_sent_messages`) und Eingänge (`fetch_inbound_messages`) für den CRM-Abgleich aus.

### 3.2 2026-Standard Entwurfsüberarbeitung (`engine/overhaul_drafts.py`)
- Dient der Migration und Veredelung bestehender Entwürfe.
- Liest bestehende Entwürfe aus M365 (`.de`), ermittelt die zugehörigen Zeilen in `ALL_LEADS`.
- Führt Firmennamen-Enrichment und MX-Validierung durch.
- Erstellt den perfekten 2026-Entwurf im `.com`-Postfach (0,3s).
- Löscht den alten, mangelhaften Entwurf aus M365 (`.de`) via APIHub.
- Schreibt neue IDs (`Draft_ID`, `Outlook_Message_ID`, `Batch_Status = DRAFTED_COM_2026`) atomar ins Google Sheet.

### 3.3 Rapid Batch Runner (`engine/run_com_batch.py`)
- Erstellt neue Batches für unberührte Leads aus `ALL_LEADS`.
- Prüft alle Compliance-Gates (`Suppressed != yes`, `Opt_Out != yes`, kein Freemail-Domainname).
- Erzeugt 50–250 Entwürfe in Sekunden.

### 3.4 Dual-Domain Reconciliation (`engine/reconcile_cloud_mailbox.py`)
- Überprüft gesendete Elemente in Exchange (`.de`) **und** All-Inkl IMAP (`.com`).
- Überprüft Posteingänge auf RFC 3464 Bounces und RFC 3834 Auto-Replies.
- Schreibt Status-Updates in `ALL_LEADS` und hängt Events an `INBOUND_EVENTS` an.

### 3.5 Spreadsheet Formatierung & UX (`engine/apply_sheet_formatting.py` & Apps Script)
- Wendet bedingte Formatierungen über die Google Sheets API an:
  - Blau (`#e8f0fe` / Text `#174ea6`) für `sent`
  - Grün (`#e6f4ea` / Text `#137333`) für `replied`
  - Rot (`#fce8e6` / Text `#c5221f`) für `hard_bounce`
  - Flieder (`#f3e8fd` / Text `#7627bb`) für `drafted`
- Menü in Google Sheets: `HSB Sales OS -> 📤 Gesendete Mails abgleichen` / `📥 Antworten abgleichen`.

---

## 4. Befehlsreferenz (Runbook)

### Status beider .com Postfächer prüfen
```bash
python3 apps/sales-os/engine/com_mailbox_manager.py --status
```

### Entwürfe auf 2026-Standard überarbeiten (Vorschau / Dry-Run)
```bash
PYTHONPATH=apps/sales-os/engine python3 apps/sales-os/engine/overhaul_drafts.py --owner JOEL --target com --limit 20
```

### Entwürfe auf 2026-Standard überarbeiten und nach .com migrieren (Scharfschaltung)
```bash
PYTHONPATH=apps/sales-os/engine python3 apps/sales-os/engine/overhaul_drafts.py --owner JOEL --target com --limit 50 --apply
```

### Neuen Akquise-Batch in .com erstellen
```bash
PYTHONPATH=apps/sales-os/engine python3 apps/sales-os/engine/run_com_batch.py --owner JOEL --count 50 --apply
```

### Gesendete E-Mails & Antworten abgleichen (Reconciliation)
```bash
PYTHONPATH=apps/sales-os/engine python3 apps/sales-os/engine/reconcile_cloud_mailbox.py --limit 100
```

### Automatische Tests ausführen
```bash
# 1. Python Unittests (93 Tests)
pytest apps/sales-os/tests

# 2. Apps Script Suite (362 Tests)
node apps/sales-os/tests/test_apps_script.js

# 3. Independent OmA-Verifier Suite (13 Gates)
node apps/sales-os/tests/verifier_suite.js
```

---

## 5. Verifikationsstatus & Sicherheits-Invariante

| Prüfpunkt | Soll-Vorgabe | Ist-Ergebnis | Status |
|:---|:---|:---|:---:|
| **Realer Prospect-Versand** | `COUNT == 0` (Streng Draft-only) | `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` | **PASS** |
| **Python Test Suite** | 93/93 Tests grün | 93 passed in 33s | **PASS** |
| **Apps Script Test Suite** | 362/362 Tests grün | 362 passed, 0 failed | **PASS** |
| **OmA-Verifier Suite** | 13/13 Gates bestanden | OMA-VERIFIER SUITE VERDICT: PASS | **PASS** |
| **Asset-Gate PDF SHA-256** | Exakte Byte-Hashes (241 KB) | `6ac5ed11...` (Joel), `a11876f0...` (Jordi) | **PASS** |
| **GF-Name im Impressum** | Exakt `Jordie Post` (mit -ie) | `Jordie Post` in allen Templates | **PASS** |
| **Git Repositories Sync** | Sauberer Zustand | Synchronisiert und dokumentiert | **PASS** |
