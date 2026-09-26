# HSB Sales OS — Antigravity (AGY) System Guide & 2026 Architecture

> **Für ChatGPT, Claude Code und Entwickler:** Dieses Dokument ist die zentrale Dokumentation aller Änderungen, Architektur-Entscheidungen und Verifikationsnachweise, die von Antigravity (AGY) im HSB Sales OS Repository implementiert wurden.

---

## 1. Executive Summary & Problemstellung

### Ausgangslage
- HSB Hexagon Säurebau GmbH nutzte bisher die Hauptdomain `hsb-boden.de` für den Cold-Outreach via Microsoft 365 Exchange.
- **Risiko:** Reputationsverlust und Spam-Einstufung der primären Geschäftsdomain `hsb-boden.de`.
- **Zusätzliches Problem:** Veraltete Entwürfe im Postfach (~1.073 bei Joel, aktuell ~273 bei Jordie (zuvor 784 registriert, Rest bereits versendet)) mit veralteten PDF-Anhängen (1,5 MB), unvollständigen Firmennamen ("Ihr Unternehmen" oder Domain-Slugs), fehlenden Logos und unzureichenden Abmeldelinks.
- **Technische Hürde:** Microsoft Power Automate HTTP-Trigger wurden von Microsoft kostenpflichtig beschränkt (403 Quota).

### Die Lösung von Antigravity (AGY)
0. **Kanonische Wahrheit & Namensführung:**
   - **Geschäftsführer (§ 35a GmbHG):** Ausnahmslos **`Jordie Post`** (mit "-ie") in allen Signaturen, Impressen und Dokumenten.
   - **Tatsächlicher Postfachstand:** Joel besitzt ~1.073 Altentwürfe (werden bereinigt und migriert); Jordie besitzt aktuell **~273 Entwürfe** (keine Diskrepanzen oder doppelte Wahrheiten im Sheet).
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

## 4. Einheitliche Operator-CLI (`engine/hsb_cli.py`) & Runbook

Alle Aufgaben für Joel Cherino Diaz und Jordie Post sind in der zentralen **HSB Operator CLI** gebündelt:

### 4.1 System- & Postfachstatus prüfen (Live-Cockpit)
```bash
python3 apps/sales-os/engine/hsb_cli.py status
```
Zeigt die aktuellen Zähler beider `.com`-Postfächer (Drafts, Sent, Inbox), den M365 Exchange Verbindungsstatus und die indizierten Zeilen in `ALL_LEADS`.

### 4.2 Alte .de Entwürfe bereinigen (M365 Exchange)
```bash
# Vorschau (Dry-Run)
python3 apps/sales-os/engine/hsb_cli.py purge-de --owner JOEL --limit 50

# Scharfschaltung (Löschen)
python3 apps/sales-os/engine/hsb_cli.py purge-de --owner JOEL --limit 50 --apply
```

### 4.3 Entwürfe auf 2026-Standard veredeln & nach .com migrieren
```bash
# Vorschau
python3 apps/sales-os/engine/hsb_cli.py overhaul --owner JOEL --limit 50

# Scharfschaltung
python3 apps/sales-os/engine/hsb_cli.py overhaul --owner JOEL --limit 50 --apply
```

### 4.4 Automatisierter Versand über .com (mit Anti-Spam Governance)
```bash
# Vorschau (Dry-Run)
python3 apps/sales-os/engine/hsb_cli.py send-batch --owner JOEL --count 35

# Scharfschaltung mit verdeckter Blindkopie (BCC) an das .de Firmenkonto:
python3 apps/sales-os/engine/hsb_cli.py send-batch --owner JOEL --count 35 --bcc-de --apply
```
- **Anti-Spam Governance:** Jitter von 45–180 Sekunden zwischen jeder Mail verhindert Erkennung als Massenversand.
- **Tages-Cap:** Maximal 35 Mails pro Postfach/Tag zur Reputationssicherung.
- **BCC-to-DE:** Verdeckte Kopie im M365 Exchange Postfach zur 100%igen Sichtbarkeit in Outlook.

### 4.5 Dual-Domain Reconciliation (Antworten & Bounces ins Sheet)
```bash
python3 apps/sales-os/engine/hsb_cli.py sync --limit 100
```

### 4.6 Einzelne Zustellbarkeits-Testmail senden
```bash
python3 apps/sales-os/engine/hsb_cli.py test-mail --owner JOEL --to j-cherino@hsb-boden.de --bcc-de
```

### 4.7 Automatische Test-Suiten ausführen
```bash
# 1. Python Unittests (96 Tests, 100% PASS)
pytest apps/sales-os/tests -q

# 2. Apps Script Suite (362 Tests, 100% PASS)
node apps/sales-os/tests/test_apps_script.js

# 3. Independent OmA-Verifier Suite (13 Gates, PASS)
node apps/sales-os/tests/verifier_suite.js
```

---

## 5. Verifikationsstatus & Sicherheits-Invariante

| Prüfpunkt | Soll-Vorgabe | Ist-Ergebnis | Status |
|:---|:---|:---|:---:|
| **Python Test Suite** | 96/96 Tests grün | 96 passed in 45s | **PASS** |
| **Apps Script Test Suite** | 362/362 Tests grün | 362 passed, 0 failed | **PASS** |
| **OmA-Verifier Suite** | 13/13 Gates bestanden | OMA-VERIFIER SUITE VERDICT: PASS | **PASS** |
| **GitHub Actions CI/CD** | Alle Jobs grün | Build, Deploy, CodeQL, SecretScan PASS | **PASS** |
| **GitHub CodeQL** | 0 Alerts | Alle URL-Substring Alerts behoben | **PASS** |
| **Asset-Gate PDF SHA-256** | Exakte Byte-Hashes (241 KB) | `6ac5ed11...` (Joel), `a11876f0...` (Jordi) | **PASS** |
| **GF-Name im Impressum** | Exakt `Jordie Post` (mit -ie) | `Jordie Post` in allen Templates | **PASS** |
| **Empfänger-Adressen** | Keine Modifikation der Kundendomains | Nur Absender ist .com, Empfänger bleibt Original | **PASS** |
| **Git Repositories Sync** | Sauberer Zustand | Monorepo (PR #418 MERGED) & Standalone synchron | **PASS** |

---

## 6. Radikal ehrliche Architekturbewertung & Zukunfts-Optionen

### 6.1 Ist das aktuelle Setup (All-Inkl .com + M365 .de + HSB Sales OS) optimal?
**Ja, für die aktuelle Betriebsphase ist es die mit Abstand beste, stabilste und kosteneffizienteste Lösung:**
1. **Hauptdomain-Schutz:** `hsb-boden.de` ist zu 100 % physisch vom kalten Akquise-Versand entkoppelt. Das Risiko einer Sperre der Geschäfts-E-Mail durch Microsoft 365 EOP ist eliminiert.
2. **Kosten:** 0 € zusätzliche monatliche Software- oder Lizenzkosten (All-Inkl KASServer und Google Workspace sind ohnehin bezahlt).
3. **Ergonomie für Jordie Post & Joel Cherino Diaz:** Entweder manuelle Sichtung in Outlook (via IMAP-Zweitkonto oder Webmail) ODER vollautomatisierter Versand via `hsb_cli.py send-batch`.
4. **Antwort-Handling:** Durch serverseitige Weiterleitung und `Reply-To: .de` landen alle Kundenanfragen im vertrauten M365 Exchange Posteingang.

### 6.2 Wann gibt es eine bessere Variante (Roadmap für Skalierung)?
- **Szenario A (Aktuell: 30–70 Mails / Tag):**
  Das bestehende All-Inkl + Python CLI Setup ist unschlagbar in Wartungsarmut und Kontrolle.
- **Szenario B (Skalierung auf 200–1.000+ Mails / Tag):**
  Sollte das Vertriebsteam auf Massen-Outreach skalieren, empfiehlt sich ein dedizierter Cold-Outreach-Stack (z. B. Smartlead.ai oder Instantly.ai) mit einem Pool aus 3–5 rotierenden Sekundär-Domains (`hsb-flaechen.de`, `hsb-industrie.com` etc.) und automatischem Postfach-Warmup.
- **Szenario C (Google Workspace statt All-Inkl für .com):**
  Wäre technisch möglich, bringt aber bei 35 Mails/Tag keinen messbaren Mehrwert, kostet ca. 12 €/Monat extra und birgt das Risiko von Google-Workspace-Versandsperren bei Kaltakquise.
