# HSB SALES OS — GESAMTES SITZUNGSPROTOKOLL & KANONISCHE EINZIGE WAHRHEIT (SSOT)
**Datum:** 08. November 2026  
**Status:** Vollständig finalisiert, Altlasten bereinigt & verbindlich verankert  
**Repository:** `HSBHexagon/hsb-boden` (Branch: `main`)  
**Betreiber:** Joel Cherino Diaz (`j-cherino@hsb-boden.de` / `cherinodiaz@outlook.com`)

---

## 1. Verpflichtende Einzige Wahrheit (Binding Monorepo SSOT)

Ab sofort gilt für alle beteiligten Personen und KI-Systeme (ChatGPT, Claude Code, Antigravity, Copilot, Codex) ausschließlich folgende **unverrückbare Wahrheit**:

1. **Einziges aktives Monorepo:** [`HSBHexagon/hsb-boden`](https://github.com/HSBHexagon/hsb-boden) auf Branch `main`. Alle älteren Repositories (z. B. separates `hsb-sales-os`) sind archiviert.
2. **Einziger CRM-Master (SSOT):** Google Spreadsheet `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg` (*„HSB CRM MASTER SSOT (EINZIGE WAHRHEIT 6424 LEADS) – 2026“*).
   * Tab `ALL_LEADS`: 6.424 Leads (3.212 Joel / 3.212 Jordie).
   * Tab `PROJECT_CHRONOLOGY`: Lückenlos gepflegt von Seq 1 bis Seq 37.
   * Sämtliche historischen Neben-Sheets (Airtable, Jordi-Alt, Joel-Alt, Master v2 Alt) sind als Altlasten gesperrt und verboten.
3. **Web-Infrastruktur & Live-Status:**
   * Cloudflare Pages Projekt `hsb-boden` auf Account `01dc37803d1c687b4f9d6249ec89f700` mit `production_deployments_enabled: true`.
   * Live-URL: [https://www.hsb-boden.de](https://www.hsb-boden.de). Aktives Deployment: `b590068e` (100 % SUCCESS).
4. **Analytics & Search Console:**
   * GA4 Property-ID: `543244027`.
   * GA4 Measurement-ID: `G-VC4BJBEFTV` (im Astro-Frontend integriert).
5. **E-Mail- & Postfach-Architektur:**
   * Absender: `j-cherino@hsb-boden.com` & `j-post@hsb-boden.com` (All-Inkl IMAPS/SMTPS).
   * Unterordner `Unzustellbar`: Bounces/NDRs werden per UID atomar aus der `INBOX` dorthin verschoben (`move_message_by_uid`).
   * Bounce-Rescue-Pipeline: `bounce_rescue_agent.py` ermittelt via Firmenwebsite/Impressum automatisch Alternativadressen für unzustellbare Kontakte mit Fail-Closed MX-Prüfung.
   * Entwürfe: Format „Reparatur zuerst“ (`REPARATUR_COPY_REV 2026-11-05`), kein Anhang, einziger Link `/reparatur/`. Veraltete Formate werden vom System in place aktualisiert; manuell editierte Entwürfe (`HUMAN_EDITED`) oder gesperrte Kontakte (`OPTOUT`/`BOUNCE`) werden dauerhaft gehalten.
   * Täglicher Cap: Maximal 100 Mails/Tag je Postfach.

---

## 2. Vollständiges Protokoll des heutigen Arbeitsprozesses

### A. ChatGPT-Aussagen & CRM-Prüfung
* **Hintergrund:** ChatGPT behauptete pauschal, im CRM seien noch gravierende Fehler vorhanden.
* **Prüfung:** Die Detailanalyse ergab, dass diese Aussagen auf historischen, längst behobenen Alt-Ständen basierten. Im aktuellen Monorepo fangen die SSOT-Prüfungen (`verify_ssot.py`) alle Daten- und Namensinvarianten strikt ab.
* **Entscheidung (Ponytail Ultra):** Ablehnung von unnötigem UI-/Dashboard-Overhead (React, Figma, Stitch). Das Master-Sheet fungiert als das performante, intuitive Interface.

### B. Entsperrung Cloudflare Pages
* **Problem:** Cloudflare Pages übersprang alle Produktions-Builds auf `main` (`skip_reason: production_deployments_disabled`).
* **Lösung:** Per Cloudflare MCP API wurde `production_deployments_enabled: true` gesetzt. Folge-Deployments (`ebb30e8d`, `d9c9f709`, `b590068e`) bauten in unter 45 Sekunden und sind live.

### C. Echter Live-Versand (GitHub Actions)
* **Durchführung:** Start des Workflows `sales-os-safety.yml` (Run `42452989345`) im Modus `send`, Count 5.
* **Ergebnis:** 3 Mails für JORDI erfolgreich via SMTP an reale Empfänger zugestellt. 2 Domains ohne MX wurden vorab ohne Bounce abgefangen (`SKIP Deliverability=NO_MX`).
* **Code-Härtung:** Summary-Parser in `apps/sales-os/bin/versand-tranche.sh` für Multi-JSON-Ausgaben repariert (Commit `0467061`).

### D. IMAP-Unterordner `Unzustellbar`
* **Implementierung:** In `apps/sales-os/engine/com_mailbox_manager.py` wurden `ensure_folder("Unzustellbar")` und atomares `move_message_by_uid()` per UID COPY + STORE \Deleted + EXPUNGE integriert.
* **Verifikation:** `ingest_bounces.py` und `reconcile_cloud_mailbox.py` aktualisiert; 5 Unittests erfolgreich bestanden.

### E. Automatisierte Adressermittlung (Bounce Rescue)
* **Implementierung:** `bounce_rescue_agent.py` scannt Websites unzustellbarer Leads SSRF-geschützt nach Mailadressen und validiert DNS-MX.
* **Integration:** In `closed_loop_crm.py` (`rescue_crm_bounces`) und `hsb_cli.py` angebunden; Integrationstest `test_bounce_rescue_integration.py` bestanden (Commit `ccfc33f`).

### F. Bestands-Audit der Entwürfe
* **Prüfung:** Alle 4.708 Bestandsentwürfe in beiden Postfächern wurden gescannt und standardisiert.
* **Screenshot-Audit:** Analyse der 10 sichtbaren Entwürfe aus Outlook mobil: 6 perfekt versandbereit, 4 Datenmängel (inaktive Domains bzw. Tippfehler `.de.de` und `.netin`), die durch den Fail-Closed MX-Schutz sicher vor dem Versand blockiert werden.

### G. Fortführung der Projekt-Chronologie
* **Ergänzung:** Der Tab `PROJECT_CHRONOLOGY` im Master-Sheet wurde um die Meilensteine Seq 29 bis Seq 37 (September bis November 2026) erweitert und im Monorepo committet ([Commit `db3b2f0`](https://github.com/HSBHexagon/hsb-boden/commit/db3b2f0)).
* **Zustellung:** Bericht und Chronologie wurden als Markdown auf dem Desktop abgelegt und an `cherinodiaz@outlook.com` sowie `cherinodiaz@icloud.com` übermittelt.

---

## 3. Bereinigung von Altlasten

* Sämtliche temporären Debug-Artefakte und ungetrackten Dateien wurden bereinigt.
* Das Monorepo ist auf `main` vollkommen sauber (`git status`: clean).
* Alle 7 neuen Mailbox- und Rescue-Tests laufen in 0.080s fehlerfrei durch.
* `python apps/website/scripts/verify_ssot.py` endet mit Exit-Code 0.

---

## 4. Verbindlicher Beschluss

Für alle künftigen Entwicklungen, Erweiterungen und Fragen gilt:
> **Nur noch dieses Monorepo [`HSBHexagon/hsb-boden`](https://github.com/HSBHexagon/hsb-boden) und die Datei [`PROJECT_TRUTH.md`](file:///C:/Users/Joel/.copilot/repos/copilot-worktrees/hsb-boden/sales-os-final-execution/PROJECT_TRUTH.md) stellen die gültige Realität dar.** 
> Alle abweichenden Vorschläge oder Alt-Dateien sind ungültig.
