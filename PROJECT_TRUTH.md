# PROJECT_TRUTH — HSB Sales OS

Stand: 04.11.2026. Aktueller Auftrag und frische Messungen ersetzen ältere Abnahmebehauptungen.

- Einziges aktives Repository: `HSBHexagon/hsb-boden`.
- Kanonischer Projektpfad: `~/KI-System/02_Projects/active/hsb-boden`.
- Einziger CRM-Master: `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg`.
- `ALL_LEADS`: 6.424 Datensätze, 3.212 Joel Cherino Diaz / 3.212 Jordie Post.
- `DE_VERSENDUNGEN_FORENSIK`: 1.274 dokumentierte historische Versandvorgänge. Empfänger werden zusätzlich zu Sendestatus, Antworten, Sperren und .com-Gesendet-Ordnern ausgeschlossen.
- Ausgang: `j-cherino@hsb-boden.com` und `j-post@hsb-boden.com`, All-Inkl `w0221a9f.kasserver.com`, IMAPS 993 / SMTPS 465.
- Neue .com-Nachrichten (Owner-Entscheidung 04.11.2026, ersetzt den Online-Flyer-Link): Vorlage „Reparatur zuerst“, kein Anhang, kein Flyer-Link, kein Klick-Token im Sichttext. Einziger Link: `https://www.hsb-boden.de/reparatur/` (302 auf `/leistungen/boden-reparatur-instandsetzung/?utm_source=email&utm_medium=outreach&utm_campaign=reparatur-2026-11`). Auswertung je Kampagne in GA4 (nur mit Einwilligung) und über die UTM-Attribution im Kontaktformular; keine Klickverfolgung einzelner Empfänger. Anrede nur mit belegter Anrede und Nachname, sonst „Sehr geehrte Damen und Herren,“. Keine CRM-Firmen- oder Titelangaben im Fließtext. MIME: multipart/alternative (text/plain + text/html), CRLF. Kein separates Reply-To. Historische Varianten nur nach Einzelabgleich ändern.
- Die `/flyer`-Weiterleitungen aus #466 bleiben aktiv, damit bereits versendete Links nicht ins Leere laufen.
- Bereits kontaktierte Empfänger und Firmendomains (.de-Forensik, .com-Gesendet, CRM-Versandstatus) sowie Opt-outs werden weder neu als Entwurf angelegt noch überschrieben. Doppelte Entwürfe je Empfänger werden nur ins Archiv `Entwürfe-Archiv-v1` verschoben (`hsb_cli.py dedupe-drafts`), nie gelöscht.
- Antworten: .com-IMAP-Sammler mit CRM-Readback. Historische .de-Antworten bleiben relevant. Jordies bestehende M365-Verbindung lieferte beim aktuellen Test HTTP 403 und ist nicht abgenommen.
- `OWNER_APPROVED`, `CONTRACT_APPROVED` und automatisch gesetzte Freigabe-Flags sind keine Empfängernachweise. Draft-Erstellung darf keine Rechtsgrundlage oder Versandfreigabe erzeugen.
- Alle Kunden-SMTP-Einstiege verwenden `outbound_safety.dispatch_verified`. Standard ist deaktiviert; Produktivversand verlangt gesonderte Aktivierung, frische Prüfungen, globalen IMAP-Lock, dauerhaften Versuchsnachweis, Sent-Readback und CRM-Readback.
- Ein Timeout nach möglicher SMTP-Annahme wird nicht automatisch wiederholt. Unklare Versuche und verbleibende Locks blockieren weitere Ausführung.
- 35 Nachrichten pro Postfach und Tag bleiben Obergrenze. 100 pro Stunde sind nicht freigegeben.
- Entwurfsoriginale werden erhalten. Kein Massen-Purge. Vor Reparaturen Original-MIME, UIDVALIDITY, UID, Message-ID und Hash sichern.
- Der Workflow `sales-os-safety.yml` erlaubt Tests, lesende Abnahmen und .com-Inbound-Sync. Owner-Entscheidung 04.11.2026 (geräteunabhängig): zusätzlich `prepare-drafts-preview`/`prepare-drafts` (Dubletten-Archiv und Reparatur-Erneuerung, kein Versand) und `send-preview`/`send` (Tranche 1–35 je Postfach, nur manuell gestartet, Environment `customer-send`). Zeitgesteuert wird nie gesendet. Doppelversand bleibt ausgeschlossen: CRM `SENDING` vor SMTP, IMAP-Sperre bleibt nach Abbruch stehen. Ohne Azure gleicht der GitHub-Versand nur .com-Antworten ab; .de-Antwortende sind über Forensik/CRM gesperrt.
- Die geprüfte Abmeldekorrektur wurde über den vorhandenen manuellen Production-Workflow veröffentlicht (Run 40341382688); öffentlicher HTTP-Readback bestanden. Kein ungeprüfter Website-Deploy.

Die vollständigen Einzelbilanzen stehen im Master unter `ALL_LEADS!BN:BR`. Rohbelege liegen privat unter `~/KI-System/07_Logs/hsb-sales-os-20261026/`. Kundendaten und Zugangsdaten gehören nicht in neue Git-Commits oder öffentliche CI-Artefakte.

Aktuelle ausdrückliche Betreiberbestätigung vom 26.10.2026 zur bereits geklärten §-7-Prüfung: Legal_Review_Status=yes für alle 6.424 Leads, Herkunftsvermerk und UTC-Datum in BS:BU. Die Engine berücksichtigt diesen vollständigen manuellen Review-Vermerk getrennt von Opt-in-Evidenz. Individuelle Sperren einschließlich Legal_Basis=BLOCKED/NO, Opt-outs, Bounces, Sendestatus und Versandfreigabe=no bleiben wirksam.

## Kanonische Assets (von `scripts/verify_ssot.py` geprüft)

Lokale Master, kein Mailanhang. Anhangsname, falls je wieder genutzt: `HSB-HEXAGON-Industrieboeden-Flyer.pdf`.

| Datei | SHA-256 |
| --- | --- |
| `apps/sales-os/assets/canonical/HSB-Flyer-Joel-Cherino_FINAL.pdf` | `6ac5ed1112c88768ac56950faab8802ceaa2817913f35a7b95e73ee79c3431d8` |
| `apps/sales-os/assets/canonical/HSB-Flyer-Jordie-Post_FINAL.pdf` | `a11876f02b54421bcafd9a6b8ec6f62d748e383b26fcadc8bbe834ee7ffbc4ce` |
