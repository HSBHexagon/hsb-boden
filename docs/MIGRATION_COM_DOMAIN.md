# Dokumentation: HSB Sales OS Migration auf .COM-Domain

> **Hinweis für KI-Assistenten (Claude Code, ChatGPT, Codex, Antigravity):**  
> Diese Datei dokumentiert alle Architekturänderungen, die durch **Antigravity (AG)** am 2026-09-26 vorgenommen wurden, um den Outbound-Vertrieb von `hsb-boden.de` auf die isolierte Domain `hsb-boden.com` umzustellen.

---

## 1. Warum wurde umgebaut? (Reputations-Schutz)

- **Problem:** Kalter E-Mail-Outbound über die Hauptdomain `hsb-boden.de` (gehostet auf Microsoft 365) birgt das Risiko von Spam-Listings und Domain-Abwertungen für das gesamte Tagesgeschäft.
- **Lösung:** Vollständige Entkopplung auf die neu erworbene Domain `hsb-boden.com` (gehostet auf All-Inkl / KASServer `w0221a9f.kasserver.com`).
- **Ergebnis:** Die geschäftskritische Hauptdomain `hsb-boden.de` kommt mit keinem ausgehenden Akquise-Paket mehr in Berührung.

---

## 2. Was genau hat Antigravity (AG) geändert?

### A. E-Mail-Infrastruktur & Secret Management
1. **Credentials hinterlegt:** Zugangsdaten für `j-cherino@hsb-boden.com` (`m0821e5d`) und `j-post@hsb-boden.com` (`m0821e5b`) in `.env` eingetragen.
2. **`hsb_config.py` erweitert:** Neue Funktion `get_com_mailbox_config(owner)` lädt IMAP/SMTP-Konfiguration (Port 993 / Port 465 SSL) sicher und isoliert.

### B. Neue Python Engines (Universell für CC, AG & Terminal)
1. **`engine/com_mailbox_manager.py`:**
   - Direkte native IMAP-SSL Verbindung zu All-Inkl.
   - Legt Entwürfe mit Anhang in ~0,3 Sekunden atomar im Ordner `Entw&APw-rfe` ab.
   - Bietet Statusabfrage und automatisierte Bereinigung.
2. **`engine/com_batch_selector.py`:**
   - Filtert autoritativ aus dem Google Sheet `ALL_LEADS`:
     - Nur `Versandfreigabe = yes`
     - Nur noch nicht entworfene (`Drafted_At` leer) & nicht versendete Leads
     - Strikter Ausschluss von Opt-outs, Suppressions und Duplikaten.
3. **`engine/run_com_batch.py`:**
   - Batch-Runner für 10, 20, 50 oder 100 Entwürfe auf Knopfdruck.
   - Verknüpft kanonische PDF-Flyer (Jordie Post / Joel Cherino) und §35a GmbHG Signatur.
   - Unterstützt `--dry-run` und `--apply`.

### C. Google Apps Script ([`apps_script/`](apps_script))
1. **`Config.gs`:** Mailboxen von `@hsb-boden.de` auf `@hsb-boden.com` umgestellt.
2. **`Actions.gs` & `HSB_SALES_OS.gs`:** Message-IDs auf `@hsb-boden.com` angepasst.
3. **Live Clasp Deploy:** Live hochgeladen auf Apps Script Projekt `1Xl6xkMTyn3Hu6UvBoX7gVrdppuyRal04NH6Ei16hnz_Pfuq-JWmh9U4c`.

---

## 3. Wo entstehen die Entwürfe in den Postfächern?

Die Entwürfe entstehen **im Ordner „Entwürfe“ (Drafts) der jeweiligen `.com`-Postfächer**:

1. **Im Webmail (Sofort im Browser verfügbar):**
   - URL: `https://webmail.all-inkl.com/`
   - Ordner: **E-Mail $\rightarrow$ Entwürfe**
2. **In Microsoft Outlook (Desktop-App):**
   - Sobald das Konto `j-cherino@hsb-boden.com` bzw. `j-post@hsb-boden.com` als IMAP-Konto hinzugefügt wird, erscheint in der linken Leiste der neue Kontenbaum:
     ```text
     ▼ 🚀 j-cherino@hsb-boden.com
        └── 📝 Entwürfe  <--- HIER ploppen die Entwürfe auf
     ```

---

## 4. Der Rückkanal (Eingehende Kundenantworten)

Auf dem All-Inkl Server ist die automatische Weiterleitung scharf geschaltet:
- Antworten an `j-cherino@hsb-boden.com` $\rightarrow$ gehen automatisch an `j-cherino@hsb-boden.de`.
- Antworten an `j-post@hsb-boden.com` $\rightarrow$ gehen automatisch an `j-post@hsb-boden.de`.
- **Operator-Vorteil:** Kundenantworten landen direkt im gewohnten Posteingang des Hauptpostfachs!

---

## 5. Cheat-Sheet für Befehle (Claude Code, Terminal, Antigravity)

```bash
# 1. Status und Entwurfszähler beider .com Postfächer anzeigen:
python3 apps/sales-os/engine/com_mailbox_manager.py --status

# 2. Test-Entwurf für Joel oder Jordi erzeugen:
python3 apps/sales-os/engine/com_mailbox_manager.py --owner JOEL --test-draft
python3 apps/sales-os/engine/com_mailbox_manager.py --owner JORDI --test-draft

# 3. Test-Entwürfe wieder sauber löschen:
python3 apps/sales-os/engine/com_mailbox_manager.py --clean-tests

# 4. Batch-Vorschau (Dry-Run) aus ALL_LEADS:
python3 apps/sales-os/engine/run_com_batch.py --owner JOEL --count 10

# 5. Alle Tests ausführen:
pytest apps/sales-os/tests/ -v
```

---

## 6. Verifikations-Nachweis (100% PASS)

- **Python Tests:** 93/93 bestanden (`pytest apps/sales-os/tests/ -q`).
- **Apps Script Tests:** 341/341 bestanden (`node tests/test_apps_script.js`).
- **Invariante:** `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` (Kein automatisierter Versand).
