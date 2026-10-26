# CURRENT_STATE — HSB Sales OS

Stand: 26.10.2026. Go-live: **NICHT VERSANDBEREIT**.

- Master vollständig bilanziert: 6.424 Leads, 3.212 Joel / 3.212 Jordie. Jede Zeile in ALL_LEADS!BN:BR mit Auditstatus, Gründen und Draft-UIDs; alle 6.424 Zeilen zurückgelesen.
- Joel: 3.080 Entwürfe, davon 3.078 eindeutige CRM-Kundenentwürfe und zwei interne Tests. Jordie: 2.538 / 2.536 / zwei Tests; fünf Kundenentwürfe liegen beim falschen Mitarbeiter.
- Versandfähig: 0 / 0. Hinterlegte Empfängernachweise fehlen bei allen Leads. Historische Varianten und sonstige Einzelmängel bleiben gehalten; Originale sind gesichert und unverändert.
- .de-Forensik: 1.274 Vorgänge, 702 Empfänger. Alle 488 zugehörigen CRM-Leads stehen auf sent; 214 Empfänger liegen außerhalb des Masters und bleiben in der Forensik.
- Zusätzlich 295 bestätigte .com-Versandstatus samt Datum, Message-ID und Sender_Account ins CRM übernommen; insgesamt 1.069 bereits kontaktierte Leads. Wiederholung erzeugt null Sent-Updates.
- 259 Kundenentwürfe überschneiden sich mit dokumentierter Kontaktaufnahme; keine Kunden-Empfängerdubletten zwischen den Entwurfsordnern.
- .com-Inbound: zuletzt 91 Nachrichten. Zwei zuvor fehlende Bounce-Ereignisse und 40 unvollständige Bounce-Sperren mit CRM-Readback nachgetragen. Negative Reclassifizierung ist auch nach unterbrochenem Event-Append wiederanlaufsicher.
- Alle sechs IMAP-Ordner per UID-Satz und UIDVALIDITY erneut abgeglichen; eine neue Inbox-Nachricht archiviert. Keine Entwürfe erzeugt, verändert oder gelöscht.
- Beide .com-Postfächer per IMAP und SMTP authentifiziert. Kundenversand in diesem Lauf: 0.
- PR #469 normal in main übernommen (d80c9bb9). GitHub-Actions-Sent-/Inbound-Sync auf main erfolgreich: Run 40338208174. Stündlich Minute 17, maximal 20 Minuten, keine parallelen Cloud-Läufe; Kunden-SMTP ausdrücklich deaktiviert.
- Start über sales-os-safety.yml / workflow_dispatch / mode=inbound-sync. Kundensenden bleibt ein separat zu aktivierender, begrenzter CLI-Schritt mit globalem Lock, Journal und Readbacks; 35/Postfach/Tag, keine Freigabe für 100/Stunde.
- Abmeldeseite produktiv fehlerhaft: bestätigt ohne Speicherung eine Abmeldung. Korrektur im Code und Preview per HTTP geprüft; neue Abmeldung per Mail an überwachte .com-Inbox. Öffentliche Seite ist bis zur gesonderten geprüften Veröffentlichung nicht abgenommen. Audit erkennt dies als OPTOUT_PAGE_NOT_FUNCTIONAL.
- Jordies historische .de-M365-Verbindung: HTTP 403 / ACCESS_BLOCKED. Outlook-Mac-Sichtbarkeit nicht unabhängig verifiziert. Browser-Rendering blockiert durch Host-Zugriffsrichtlinie.
- 176 Python-Tests bestanden, ein Live-Test separat durch reale Authentifizierung abgedeckt. 337 Website-Tests, Astro ohne Fehler/Warnungen, 58 Seiten gebaut, Wrangler-Dry-Run bestanden. CodeQL und weitere relevante CI in PR #469 erfolgreich.

Maschinenlesbarer Nachweis: docs/audits/SALES_OS_VERIFICATION_2026-10-26.json. Einzelgründe und exakte Lead-IDs stehen im CRM; private Originalbelege unter ~/KI-System/07_Logs/hsb-sales-os-20261026/.
