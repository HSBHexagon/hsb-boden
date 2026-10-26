# PROJECT_TRUTH — HSB Sales OS

Stand: 26.10.2026. Aktueller Auftrag und frische Messungen ersetzen ältere Abnahmebehauptungen.

- Einziges aktives Repository: `HSBHexagon/hsb-boden`.
- Kanonischer Projektpfad: `~/KI-System/02_Projects/active/hsb-boden`.
- Einziger CRM-Master: `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg`.
- `ALL_LEADS`: 6.424 Datensätze, 3.212 Joel Cherino Diaz / 3.212 Jordie Post.
- `DE_VERSENDUNGEN_FORENSIK`: 1.274 dokumentierte historische Versandvorgänge. Empfänger werden zusätzlich zu Sendestatus, Antworten, Sperren und .com-Gesendet-Ordnern ausgeschlossen.
- Ausgang: `j-cherino@hsb-boden.com` und `j-post@hsb-boden.com`, All-Inkl `w0221a9f.kasserver.com`, IMAPS 993 / SMTPS 465.
- Neue .com-Nachrichten: Online-Flyer `https://www.hsb-boden.de/flyer`, kein Standard-PDF-Anhang, kein separates Reply-To. Historische Varianten nur nach Einzelabgleich ändern.
- Antworten: .com-IMAP-Sammler mit CRM-Readback. Historische .de-Antworten bleiben relevant. Jordies bestehende M365-Verbindung lieferte beim aktuellen Test HTTP 403 und ist nicht abgenommen.
- `OWNER_APPROVED`, `CONTRACT_APPROVED` und automatisch gesetzte Freigabe-Flags sind keine Empfängernachweise. Draft-Erstellung darf keine Rechtsgrundlage oder Versandfreigabe erzeugen.
- Alle Kunden-SMTP-Einstiege verwenden `outbound_safety.dispatch_verified`. Standard ist deaktiviert; Produktivversand verlangt gesonderte Aktivierung, frische Prüfungen, globalen IMAP-Lock, dauerhaften Versuchsnachweis, Sent-Readback und CRM-Readback.
- Ein Timeout nach möglicher SMTP-Annahme wird nicht automatisch wiederholt. Unklare Versuche und verbleibende Locks blockieren weitere Ausführung.
- 35 Nachrichten pro Postfach und Tag bleiben Obergrenze. 100 pro Stunde sind nicht freigegeben.
- Entwurfsoriginale werden erhalten. Kein Massen-Purge. Vor Reparaturen Original-MIME, UIDVALIDITY, UID, Message-ID und Hash sichern.
- Der Workflow `sales-os-safety.yml` erlaubt Tests, lesende Abnahmen und .com-Inbound-Sync. Kundenversand ist dort ausdrücklich deaktiviert. Zeitpläne sind erst nach Übernahme in den Default-Branch aktiv.
- Die geprüfte Abmeldekorrektur wurde über den vorhandenen manuellen Production-Workflow veröffentlicht (Run 40341382688); öffentlicher HTTP-Readback bestanden. Kein ungeprüfter Website-Deploy.

Die vollständigen Einzelbilanzen stehen im Master unter `ALL_LEADS!BN:BR`. Rohbelege liegen privat unter `~/KI-System/07_Logs/hsb-sales-os-20261026/`. Kundendaten und Zugangsdaten gehören nicht in neue Git-Commits oder öffentliche CI-Artefakte.

Aktuelle ausdrückliche Betreiberbestätigung vom 26.10.2026 zur bereits geklärten §-7-Prüfung: Legal_Review_Status=yes für alle 6.424 Leads, Herkunftsvermerk und UTC-Datum in BS:BU. Die Engine berücksichtigt diesen vollständigen manuellen Review-Vermerk getrennt von Opt-in-Evidenz. Individuelle Sperren einschließlich Legal_Basis=BLOCKED/NO, Opt-outs, Bounces, Sendestatus und Versandfreigabe=no bleiben wirksam.
