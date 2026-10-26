# CURRENT_STATE — HSB Sales OS

Stand: 26.10.2026. Go-live: **NICHT VERSANDBEREIT**.

- Live-Master: 6.424 Leads, 3.212 Joel / 3.212 Jordie. Audit je Lead in `ALL_LEADS!BN:BR`, alle 6.424 Einträge zurückgelesen.
- Joel: 3.080 Gesamtentwürfe, davon 3.078 eindeutige CRM-Kundenentwürfe und 2 interne Tests.
- Jordie: 2.538 Gesamtentwürfe, davon 2.536 eindeutige CRM-Kundenentwürfe und 2 interne Tests.
- Versandfähig: 0 / 0. Bei allen Leads fehlen hinterlegte Empfängernachweise; keine Freigaben erfinden.
- Historische .de-Forensik: 1.274 Vorgänge / 702 Empfänger. Alle 488 zugehörigen CRM-Leads stehen bereits als sent; 214 Empfänger liegen außerhalb des Lead-Masters und bleiben in der Forensik.
- 259 vorhandene Kundenentwürfe überschneiden sich mit dokumentierter früherer Kontaktaufnahme. 5 Entwürfe liegen beim falschen Mitarbeiter. Keine Kunden-Dubletten zwischen den Entwurfsordnern.
- Original-MIME und Einzelidentifikatoren sind privat gesichert. Keine Entwürfe neu erzeugt, verändert oder gelöscht.
- .com-Inbound: 90 Nachrichten gelesen, 2 fehlende Bounces mit Sperren und Readback übernommen; Wiederholung erzeugt 0 Ereignisse.
- All-Inkl IMAP und SMTP für beide Konten live authentifiziert. Kundenversand in diesem Lauf: 0.
- Jordies .de-M365-Connector: HTTP 403. Diese historische Antwortquelle bleibt ACCESS_BLOCKED.
- Python: 165 Tests bestanden, 1 separater Live-Test übersprungen; Authentifizierung separat live geprüft. Website: 335 Tests bestanden.
- GitHub-Actions-Leseabnahme erfolgreich: Run 40332225903. PR #469 enthält die Korrekturen; Kunden-SMTP bleibt deaktiviert. Der stündliche Inbound-Zeitplan aktiviert sich erst im Default-Branch.

Maschinenlesbarer Nachweis: `docs/audits/SALES_OS_VERIFICATION_2026-10-26.json`.
