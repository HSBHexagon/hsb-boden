# CURRENT_HANDOFF — 2026-10-13 (HSB Sales OS `.com` Live-Audit und CRM-Sent-Abgleich)

- **Datum:** 2026-10-13 (Live-Nachkontrolle)
- **Betreiber:** Joel Cherino Diaz
- **Status:** `.com`-IMAP/SMTP + Drafts technisch geprüft; **100 externe Sent-Nachrichten vom 12.10. im Jordie-Postfach**, am 13.10. mit CRM synchronisiert. Einzelzustellung/weitere Freigabe offen.
- **Git:** Dokumentationsänderungen in bestehendem PR #458, nicht automatisch produktiv gemergt.
- **Monorepo:** `HSBHexagon/hsb-boden` (Kanonischer Pfad: `~/KI-System/02_Projects/active/hsb-boden`)

---

## 1. Was wurde live verifiziert & ausgeführt (2026-10-12)

1. **.COM Akquise-Shield Mailboxen (All-Inkl KASServer `w0221a9f.kasserver.com`):**
   - **Joel Cherino Diaz (`j-cherino@hsb-boden.com`):** 102 Entwürfe im IMAP-Ordner `Entw&APw-rfe` (IMAP OK, SMTP OK).
   - **Jordie Post (`j-post@hsb-boden.com`):** 52 Entwürfe im IMAP-Ordner `Entw&APw-rfe` (IMAP OK, SMTP OK).
   - Beide Postfächer erfüllen die Vorgabe ($\ge 50$ fertige Entwürfe).
2. **Google Sheet SSOT (`ALL_LEADS`):**
   - Historisch 50 Leads für Jordie als `drafted` synchronisiert.
   - **13.10. Korrektur:** 100 externe Empfänger/MIME-Message-IDs aus Jordies `Sent`-Ordner eindeutig zu den bestehenden CRM-Zeilen gematcht. 100 Zeilen `Send_Status=sent`, `Batch_Status=SENT_COM_2026`, originaler UTC-Sendezeitpunkt und Absender `j-post@hsb-boden.com`. Alle 300 Google-Sheets-Schreiboperationen beantwortet; keine unerwarteten Änderungen anderer Leads in den betroffenen Spalten.
3. **E-Mail Payloads & Compliance:**
   - 154 Entwürfe: alle mit genau einem PDF, `.com`-From, `.de`-Reply-To, `X-Unsent=1`. Joel 102/102 mit 247437-Byte-PDF, Jordie 51/52 mit 246960-Byte-PDF und **ein alter interner Testdraft** mit 1,5-MB-PDF. Keine unbelegte Vollkommenheitsbehauptung.
   - Absender und Signaturen strikt mit **Jordie Post** (mit -ie, § 35a GmbHG).
   - Header `Reply-To: ...@hsb-boden.de` aktiv (Antworten gehen direkt in Microsoft 365 Exchange).
4. **Cloudflare & Web-Routing:**
   - **Fehler 13.10.:** HTTPS-Zertifikat für `hsb-boden.com` passt nicht zum Origin (`*.kasserver.com`). Der Redirect nach `www.hsb-boden.de` ist nur bei abgeschalteter TLS-Prüfung nachvollziehbar; Cloudflare-Zone ist `pending`, Nameserver autoritativ bei All-Inkl. Mail-MX/NS vor einer Korrektur schützen.
5. **Testversand an Betreiber:**
   - Test-Mails an `cherinodiaz@outlook.com` erfolgreich per SMTP zugestellt (0 Bounces, 0 Fehler).

---

## 2. Revidierte, am 13.10.2026 überprüfte Invarianten

- **Ist:** 100 externe Nachrichten vom 12.10. sind in Jordies All-Inkl-Gesendet-Ordner und haben eindeutige CRM-Message-ID-Zuordnung. `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` ist widerlegt. Ein nachgewiesener `Sent`-Eintrag ist kein Beleg der Einzelzustellung.
- **Soll:** keine automatische Neuversendung ohne überprüfte dokumentierte Einzelfreigabe, Opt-out-/Deduplikationsabgleich und Senderfreigabe. Während des Live-Audits wurden **keine** Mails oder Entwürfe erstellt.
- ✅ Geschäftsführer: `Jordie Post` (mit `-ie`, niemals `Jordi`) — § 35a GmbHG
- ✅ Kanonische Vektor-Flyer: 241 KB (`HSB-Flyer-Joel-Cherino_FINAL.pdf` / `HSB-Flyer-Jordie-Post_FINAL.pdf`)
- ✅ Archivierte Repos: `HSBHexagon/hsb-sales-os` ist archiviert und darf niemals referenziert werden!

---

## 3. Anweisung an nachfolgende KI-Modelle (Claude, Gemini, Cursor, Codex, Jules)

1. Lies zuerst `PROJECT_TRUTH.md` (Monorepo SSOT).
2. Lies `CURRENT_STATE.md` (Live-Taskboard).
3. Beachte: Joel 102 Drafts (100 extern), Jordie 52 (50 extern), alle 154 weiter vorhanden. Vor neuen Batches bestehende 100 externe Jordie-Sent-Nachrichten vom 12.10. berücksichtigen.
4. Google Cloud Run `hsb-com-draft-worker` existiert, aber dessen Scheduler ist PAUSED und Cloud Write deaktiviert. Mac LaunchAgent (`com_sheet_dispatcher.py --apply`) prüft die vorhandene BATCHES-Queue alle 120 Sekunden. Keine doppelten schreibenden Worker. TinyFish ist kein produktiver Versanddienst.
5. Nach Codeänderungen: vorhandene Tests und Repo-Wahrheit prüfen; `scripts/verify_ssot.py` nur ausführen, **wenn diese Datei im jeweiligen Checkout tatsächlich existiert**. Verifikationsergebnis und Datum angeben, nicht historische 798/798 als neuen Lauf ausgeben.

## 4. Abschlussprüfung 13.10.2026

- **Postfachinventar:** Joel IMAP/SMTP OK, 102 Drafts, 3 Sent, 2 Inbox; Jordie IMAP/SMTP OK, 52 Drafts, 104 Sent, 0 Inbox.
- **Unterscheidung:** 150 externe Drafts, 4 interne Tests; kein externer Draft-Empfänger zugleich im Sent-Ordner; vier Tests nicht löschen. 100 externe Sent am 12.10. wurden dem CRM zugeordnet (keine erneute Sendung durch den Abgleich).
- **CRM-Beleg:** `COM_ROLLOUT_GATE!A90:F98` im unveränderten originalen 6.424-Leads-Sheet, `ENTWURF_STEUERUNG!A3` aktualisiert. Historische Gate-Zeilen unverändert.
- **Noch kein uneingeschränktes Go-Live:** leere individuelle `Legal_Evidence`-Felder (externe anwaltliche Unterlagen nicht verneint), HTTPS/TLS `.com` defekt, DKIM/DMARC-Härtung und Einzelzustellung offen. Weder neuen Versand noch Draft-Massenanlage auslösen.
