# PROJECT_TRUTH — HSB Hexagon Säurebau GmbH &middot; Monorepo SSOT

> **Status:** UNVERRÜCKBARE QUELLE DER WAHRHEIT (SSOT) FÜR ALLE KI-TOOLS  
> **Gültigkeit:** Verbindlich für Claude Code, Gemini CLI (agy), Antigravity, Cursor, Codex und Menschen  
> **Stand:** 2026-09-20 &middot; Monorepo-Konsolidierung: 2026-09-16  
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

1. **`REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` (Hermetische Entwurfs-Governance):**
   - Es werden **ausschließlich Entwürfe** im Postfach erzeugt (`DraftEmail`).
   - Unter keinen Umständen darf ein automatisierter, unautorisierter Versand an externe Kontakte erfolgen.
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

