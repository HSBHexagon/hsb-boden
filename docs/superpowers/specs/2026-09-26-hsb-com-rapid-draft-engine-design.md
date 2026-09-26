# HSB Sales OS — .COM Rapid Draft Engine Design Specification

- **Datum:** 2026-09-26
- **Status:** APPROVED_DRAFT
- **Ziel:** Sofortige, unkomplizierte und ultraschnelle Erstellung von Akquise-Entwürfen direkt im .com-Postfach (KASServer IMAP) mit atomarem Writeback ins Google Sheet 'ALL_LEADS'.
- **Kerninvariante:** REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0 (Reine Draft-Erstellung, menschliche Freigabe vor Absenden).

---

## 1. Problemstellung & Radikal ehrliche Lösung

### Bisheriger Flaschenhals:
- Entwurfserstellung war an Microsoft Power Automate und Azure APIHub gekoppelt.
- Tokens liefen ab, Azure-Rechte machten Probleme, und das System war fest mit der .de-Hauptdomain verdrahtet.

### Die neue .COM-Architektur:
- **E-Mail-Postfächer:** Laufen autark auf All-Inkl (KASServer) unter `@hsb-boden.com`.
- **Direkte IMAP-Injektion:** Anstatt fehleranfälliger Cloud-Flows schreibt die Python-Engine `run_com_batch.py` fertige MIME-Entwürfe (inkl. Flyer & Logo) direkt per IMAP-SSL (Port 993) in den Ordner `Entw&APw-rfe`.
- **Geschwindigkeit:** ~0.3 Sekunden pro Entwurf. 50 Entwürfe in unter 15 Sekunden.
- **Bedienung:** Joel und Jordi sehen die Entwürfe sofort in ihrem Webmail (`webmail.all-inkl.com`) oder in ihrem Outlook. Sie prüfen drüber und klicken auf Senden.
- **Rückkanal:** Eingehende Antworten auf `.com` werden serverseitig automatisch an die normale `.de`-Adresse weitergeleitet.

---

## 2. Komponenten & Datenfluss

```
[Google Sheet: ALL_LEADS]
         │
         │ (1) load_leads_authoritative() -> Filter: Freigabe=yes, Owner=JOEL/JORDI, Drafted_At=leer
         ▼
[run_com_batch.py]
         │
         │ (2) Rendert E-Mail mit kanonischem Flyer & Logo (render_canonical_email)
         │ (3) Baut MIME Multipart mit Message-ID <uuid@hsb-boden.com>
         │
         ▼
[KASServer IMAP: Entw&APw-rfe]  <--- Entwurf liegt in 0.3s im Postfach
         │
         │ (4) write_2d_matrix_bulk()
         ▼
[Google Sheet: ALL_LEADS]      <--- Markiert Drafted_At, Batch_ID, Draft_ID
```

---

## 3. Invarianten & Sicherheitsgates

1. **Kein automatischer Versand:** Die Software ruft NIEMALS `smtp.sendmail()` an externe Prospektadressen auf.
2. **Kanonischer Flyer:** Hash-Prüfung auf Byte-Gleichheit:
   - Jordi: `HSB-Flyer-Jordie-Post_FINAL.pdf` (SHA-256: 08e1149e4fed...)
   - Joel: `HSB-Flyer-Joel-Cherino_FINAL.pdf` (SHA-256: 2bccadacc77b...)
3. **Rechtliche Konformität:**
   - § 35a GmbHG Impressum in der Signatur (Gronau, HRB 21481, Geschäftsführer: Jordie Post).
   - Abmelde-Hinweis in jeder E-Mail.
4. **Isolationsgarantie:**
   - Absender ist ausschließlich `j-cherino@hsb-boden.com` oder `j-post@hsb-boden.com`.
   - Die Domain `hsb-boden.de` taucht in keinem E-Mail-Header auf.

---

## 4. Test- & Abnahmekriterien

1. `test_com_batch_generation_dry_run`: Prüft Lead-Filterung und MIME-Zusammensetzung ohne Netzwerklauf.
2. `test_com_batch_live_injection`: Erzeugt 1 echten Entwurf im Zielpostfach, verifiziert Vorhandensein im IMAP-Ordner und bereinigt diesen wieder.
3. `test_sheet_writeback_mock`: Verifiziert, dass `Drafted_At` und `Batch_ID` exakt für die ausgewählten Zeilen geschrieben werden.
