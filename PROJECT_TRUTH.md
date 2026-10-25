# PROJECT_TRUTH — HSB Hexagon Säurebau GmbH &middot; Monorepo SSOT

> **Status:** UNVERRÜCKBARE QUELLE DER WAHRHEIT (SSOT) FÜR ALLE KI-TOOLS  
> **Gültigkeit:** Verbindlich für Claude Code, Gemini CLI (agy), Antigravity, Cursor, Codex und Menschen  
> **Stand:** 2026-10-13 &middot; Monorepo-Konsolidierung: 2026-09-16 &middot; .COM-Live-Audit: 2026-10-13  
> **Verletzungen:** Bei Widerspruch zwischen diesem Dokument und anderen Dateien gilt IMMER dieses Dokument.

---

## 1. Repository-Architektur & Kanonische Pfade

1. **Einziges aktives Monorepo (SSOT):**
   - Remote URL: `https://github.com/HSBHexagon/hsb-boden.git`
   - Lokaler kanonischer Pfad: `/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden` (Symlink: `/Users/joelcherinodiaz/Projekte/hsb-boden`)
   - Struktur:
     - `apps/website/`: Astro 5 / Tailwind / Cloudflare Pages (`www.hsb-boden.de`)
     - `apps/sales-os/`: Python 3.14 CRM-Engine, Inbound Workers, Google Sheets API & Google Apps Script

2. **ARCHIVIERTE & STILLGELEGTE REPOSITORIES (NIEMALS NUTZEN!):**
   - `HSBHexagon/hsb-sales-os`: Seit 2026-09-16 **archiviert**. Jeglicher Code lebt nun unter `apps/sales-os/`. Niemals dorthin pushen, klonen oder prüfen!
   - `auto-hub1` / alte Klone: Stillgelegt.

---

## 2. Personen, Rollen & Rechtsform (Strikte Namensregel)

1. **Geschäftsführer (Gesetzliche Pflichtangabe §35a GmbHG):**
   - **Jordie Post** (Rechtschreibung zwingend mit **-ie** laut Handoff 2026-09-12).
   - **VERBOT:** Niemals *Jordi* oder *Jordy* für die Person oder in E-Mail-Signaturen verwenden. (HRB 21481, Amtsgericht Coesfeld).
   - Mobil: `0170 2340904` &middot; E-Mail: `j-post@hsb-boden.de`
2. **Betreiber, Gesellschafter & Vertriebsleitung:**
   - **Joel Cherino Diaz**
   - Mobil: `0151 21886891` &middot; E-Mail: `j-cherino@hsb-boden.de` &middot; Persönlich: `cherinodiaz@outlook.com`

---

## 3. CRM, Postfächer & 50/50 Lead-Verteilung

- **Single Source of Truth CRM:** Google Sheet `ALL_LEADS` (`1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg`) via Profil `cherinodiaz`.
- **Exakter 50/50 Split (6.424 Leads gesamt):**
  - **Joel Cherino Diaz:** 3.212 Leads (Zeilen 2–3213).
    - Flow: `137601e8-7369-4a74-9564-959f1551e48d` (`Request/Http` Trigger)
  - **Jordie Post:** 3.212 Leads (Zeilen 3214–6425).
    - Flow: `47ee3d7a-626c-4fff-9e16-6d938949e4bd` (`Button` Trigger / LogicFlows Connector via Apps Script)

---

## 4. Harte Sicherheits- & Ausführungs-Invarianten

1. **Belegter tatsächlicher Versandstand statt falscher Null-Invariante:**
   - Am 13.10. wurden im All-Inkl-Gesendet-Ordner von Jordie **100 externe Nachrichten vom 12.10.** mit je eindeutiger Message-ID und CRM-Empfängerzuordnung festgestellt. Eine erfolgreiche Zustellung an jeden Empfänger und die auslösende Aktion sind damit noch nicht bewiesen.
   - Diese 100 Leads wurden am 13.10. im bestehenden Google-Sheet-CRM nachweislich auf `sent` / `SENT_COM_2026` mit dem originalen Sendezeitpunkt und `.com`-Absender abgeglichen. Die bisherige Behauptung `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` war **falsch**.
   - **Governance-Regel unverändert:** kein neuer automatisierter, unautorisierter Prospektversand; vor weiterer Entwurfserstellung und Versendung gelten Opt-out-, Dubletten-, Zustellungs- und dokumentierte Freigabeprüfungen. Leere `Legal_Evidence`/`Legal_Evidence_At` dürfen nicht als Zustimmung umgedeutet werden.
2. **Pre-Send DNS/MX-Prüfung:**
   - Vor Entwurfserstellung wird die Domain via `check_domain_mx()` validiert. Leads ohne gültigen MX (NXDOMAIN) werden übersprungen.
3. **Freemail-Schutz:**
   - Freemail-Provider (`t-online.de`, `gmx.de`, `web.de`, `gmail.com` etc.) dürfen niemals als Firmenname übernommen werden.
4. **Terminal-Präferenz des Betreibers:**
   - Für externe Terminal-Aufrufe (`osascript`) ist **ausnahmslos iTerm2** (`tell application "iTerm"`) zu verwenden, niemals Apple `Terminal.app`.
5. **Kein Ralph-Prompting im agy CLI:**
   - Keine Phrasen wie *„durch alle Ralph-Gates“* in CLI-Prompts übergeben, da dies Heuristik-Loops auslöst. Befehle direkt als Python-Skripte ausführen.

---

## 5. Kanonische Marketing- & E-Mail-Assets

1. **Kanonischer Vektor-Flyer (241 KB, EOP-optimiert):**
   - Anhangsname beim Empfänger immer: `HSB-HEXAGON-Industrieboeden-Flyer.pdf`
   - Joel Master: `apps/sales-os/assets/canonical/HSB-Flyer-Joel-Cherino_FINAL.pdf` (SHA-256: `6ac5ed11...`)
   - Jordie Master: `apps/sales-os/assets/canonical/HSB-Flyer-Jordie-Post_FINAL.pdf` (SHA-256: `a11876f0...`)
2. **Signatur-Logo:**
   - URL: `https://www.hsb-boden.de/brand/hsb-boden-logo.png`
   - Feste Attribute: `width="102" height="75"`, Bicubic Rendering.
3. **Abmeldesystem:**
   - Prominente HTML-Tabelle mit unterstrichenem Link `<u>Hier abmelden</u>` &rarr; `https://www.hsb-boden.de/abmelden?email={email}` + `mailto:`-Fallback.

---

## 6. Kanonische .COM Akquise-Shield-Architektur (Live seit 2026-10-12)

1. **Zweck:** Vollständiger Reputationsschutz der M365-Geschäftsdomain `hsb-boden.de` vor Spam-Blacklisting durch Kaltakquise.
2. **Mailserver-Architektur (Dual-Domain):**
   - **Outbound Kaltakquise-Entwürfe:** Ausschließlich in All-Inkl Postfächern (`w0221a9f.kasserver.com`):
     - `j-cherino@hsb-boden.com` (Joel Cherino Diaz)
     - `j-post@hsb-boden.com` (Jordie Post)
   - **Inbound & Antworten:** Laufen über `Reply-To: ...@hsb-boden.de` direkt in Microsoft 365 Exchange.
   - **Web-Präsenz:** Der HTTPS-Aufruf von `hsb-boden.com` ist am 13.10. **nicht sauber nutzbar**: Origin-Zertifikat lautet auf `*.kasserver.com`; die Cloudflare-Zone ist `pending`, während All-Inkl die autoritativen NS führt. Erst ohne TLS-Prüfung sind die Redirects nach `www.hsb-boden.de` sichtbar. Mail-MX und Nameserver beim Beheben schützen.
3. **Echtzeit-Bestand (read-only IMAP/SMTP-Verifikation 2026-10-13):**
   - Joel Cherino Diaz (`j-cherino@hsb-boden.com`): 102 Entwürfe im IMAP-Ordner `Entw&APw-rfe`
   - Jordie Post (`j-post@hsb-boden.com`): 52 Entwürfe im IMAP-Ordner `Entw&APw-rfe`
   - Beide IMAP-/SMTP-Anmeldungen sind OK. Von 154 serverseitigen Entwürfen sind 150 externe Kundendrafts und 4 interne Tests. Alle besitzen `X-Unsent=1`, `.com`-From, `.de`-Reply-To und je ein PDF. 1 älterer **interner Testentwurf** von Jordie trägt jedoch noch einen 1,5-MB-Anhang ohne regulären Footer; die 50 externen Jordie-Entwürfe enthalten den regulären Namen **Jordie Post** mit **-ie**. Keine externen Draft-Empfänger stehen gleichzeitig im Sent-Ordner desselben Postfachs.
   - **Gesendet-Ordner:** Joel 3 Einträge, Jordie 104 Einträge, davon 100 externe am 12.10.2026. Diese 100 sind im CRM erfasst. Das ist keine unabhängige Zustellbestätigung.
4. **Harte Invariante für alle KIs (Claude, Gemini, Cursor, Codex, Jules):**
   - **Mac-Worker existiert** und verarbeitet per LaunchAgent `com_sheet_dispatcher.py --apply` alle 120 Sekunden ausschließlich angeforderte `COM_REQUESTED`-Entwurfsbatches mit Prüfungen. **Google Cloud Run existiert ebenfalls** (`hsb-com-draft-worker`), sein Cloud Scheduler ist aber am 13.10. **PAUSED** und der dokumentierte Cloud-Schreibmodus deaktiviert. Keinen zweiten schreibenden Worker parallel aktivieren. TinyFish war ausschließlich ein optionales Browser-Prüfwerkzeug, kein produktiver Mailworker.
   - Das alte Repo `HSBHexagon/hsb-sales-os` ist archiviert und darf niemals referenziert werden.

## 7. Verbindliche aktuelle Freigabegrenzen (13.10.2026)

- Kanonischer Servernachweis: `COM_ROLLOUT_GATE!A90:F98` im bestehenden CRM-Master. Für Live-Zahlen ersetzt dieser den historischen 08.–12.10.-Status, ohne dessen Protokolle zu löschen.
- Dokumentiertes `ALL_LEADS!BL:BM`: kein maschinenlesbarer Einzel-Nachweis im betrachteten Bestand. Externe anwaltliche Unterlagen dürfen existieren; daraus folgt **keine automatische Freigabe** jedes Eintrags.
- Vor neuem Kundensendebatch: zuletzt gesendete Message-IDs, Empfänger, Opt-outs, bereits erzeugte Drafts, belegte Freigabe und Senderkonto prüfen. Keine hypothetische Null-Sendungsinvariante.
- Domainstatus: SPF vorhanden, DMARC `p=none`, DKIM-Signatur-/Alignment- und HTTPS-TLS-Abnahme offen. Keine Cloudflare-Nameserverumstellung ohne Mail-DNS-Migrationsprüfung.
- PR #458 ist **nur die Dokumentationskorrektur**. Er ersetzt weder die unabhängige GitHub-Codefreigabe noch das rechtliche bzw. technische Go-Live-Gate.
