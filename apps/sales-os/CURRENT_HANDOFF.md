# CURRENT_HANDOFF — 2026-10-12 (HSB Sales OS .COM Shield Live Activation)

- **Datum / Uhrzeit:** 2026-10-12T16:10:00+02:00
- **Betreiber:** Joel Cherino Diaz
- **Status:** .COM OUTBOUND SHIELD LIVE & VERIFIZIERT (`REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0`)
- **Git HEAD:** `main` (clean)
- **Monorepo:** `HSBHexagon/hsb-boden` (Kanonischer Pfad: `~/KI-System/02_Projects/active/hsb-boden`)

---

## 1. Was wurde live verifiziert & ausgeführt (2026-10-12)

1. **.COM Akquise-Shield Mailboxen (All-Inkl KASServer `w0221a9f.kasserver.com`):**
   - **Joel Cherino Diaz (`j-cherino@hsb-boden.com`):** 102 Entwürfe im IMAP-Ordner `Entw&APw-rfe` (IMAP OK, SMTP OK).
   - **Jordie Post (`j-post@hsb-boden.com`):** 52 Entwürfe im IMAP-Ordner `Entw&APw-rfe` (IMAP OK, SMTP OK).
   - Beide Postfächer erfüllen die Vorgabe ($\ge 50$ fertige Entwürfe).
2. **Google Sheet SSOT (`ALL_LEADS`):**
   - 50 Leads für Jordie (`COM-JORDI-20261012`) atomar auf Status `drafted` synchronisiert (300 Zellen aktualisiert).
3. **E-Mail Payloads & Compliance:**
   - Kanonischer Vektor-Flyer (241 KB) bei allen Entwürfen angehängt (`HSB-HEXAGON-Industrieboeden-Flyer.pdf`).
   - Absender und Signaturen strikt mit **Jordie Post** (mit -ie, § 35a GmbHG).
   - Header `Reply-To: ...@hsb-boden.de` aktiv (Antworten gehen direkt in Microsoft 365 Exchange).
4. **Cloudflare & Web-Routing:**
   - `hsb-boden.com` leitet per Cloudflare 301 Redirect sauber auf `https://www.hsb-boden.de/` weiter.
5. **Testversand an Betreiber:**
   - Test-Mails an `cherinodiaz@outlook.com` erfolgreich per SMTP zugestellt (0 Bounces, 0 Fehler).

---

## 2. Invarianten (100% VERIFIZIERT)

- ✅ `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` — Ausschließlich Entwürfe in Outlook
- ✅ Geschäftsführer: `Jordie Post` (mit `-ie`, niemals `Jordi`) — § 35a GmbHG
- ✅ Kanonische Vektor-Flyer: 241 KB (`HSB-Flyer-Joel-Cherino_FINAL.pdf` / `HSB-Flyer-Jordie-Post_FINAL.pdf`)
- ✅ Archivierte Repos: `HSBHexagon/hsb-sales-os` ist archiviert und darf niemals referenziert werden!

---

## 3. Anweisung an nachfolgende KI-Modelle (Claude, Gemini, Cursor, Codex, Jules)

1. Lies zuerst `PROJECT_TRUTH.md` (Monorepo SSOT).
2. Lies `CURRENT_STATE.md` (Live-Taskboard).
3. Beachte: Beide Postfächer sind live mit >50 Entwürfen bestückt und einsatzbereit.
4. Es gibt KEIN Cloud Run / tinyfish.ai Setup; die Monorepo-CLI-Engine ist das einzige kanonische Werkzeug.
5. Vor jedem Commit / Abschluss MUSS `python3 scripts/verify_ssot.py` mit Exit 0 durchlaufen!
