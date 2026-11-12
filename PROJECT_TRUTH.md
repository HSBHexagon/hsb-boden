# PROJECT_TRUTH — HSB Sales OS

Stand: 08.11.2026. Kanonische Gesamtwahrheit und verbindlicher SSOT-Standard für alle KI-Systeme und Betreiber.

- Einziges aktives Repository: `HSBHexagon/hsb-boden`.
- Kanonischer Projektpfad: `~/KI-System/02_Projects/active/hsb-boden`.
- Einziger CRM-Master: `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg` (HSB CRM MASTER SSOT – 2026).
- `ALL_LEADS`: 6.424 Datensätze, 3.212 Joel Cherino Diaz / 3.212 Jordie Post.
- `PROJECT_CHRONOLOGY`: Kanonischer Tab im Master-Sheet, lückenlos gepflegt von Seq 1 bis Seq 37 (Stand 08.11.2026).
- `DE_VERSENDUNGEN_FORENSIK`: 1.274 dokumentierte historische Versandvorgänge. Empfänger werden zusätzlich zu Sendestatus, Antworten, Sperren und .com-Gesendet-Ordnern ausgeschlossen.
- Ausgang: `j-cherino@hsb-boden.com` und `j-post@hsb-boden.com`, All-Inkl `w0221a9f.kasserver.com`, IMAPS 993 / SMTPS 465.
- Web & Production: Cloudflare Pages Projekt `hsb-boden` auf Account `01dc37803d1c687b4f9d6249ec89f700` ist entsperrt (`production_deployments_enabled: true`) und live auf `https://www.hsb-boden.de`.
- Analytics: GA4 Property-ID `543244027`, Measurement-ID `G-VC4BJBEFTV` (im Astro-Frontend integriert).
- Neue .com-Nachrichten (Owner-Entscheidung 04.11.2026, bestätigt 08.11.2026): Vorlage „Reparatur zuerst“, kein Anhang, kein Flyer-Link, kein Klick-Token im Sichttext. Einziger Link: `https://www.hsb-boden.de/reparatur/` (302 auf `/leistungen/boden-reparatur-instandsetzung/?utm_source=email&utm_medium=outreach&utm_campaign=reparatur-2026-11`). Auswertung: anonyme Tageszählung aller Klicks (human/bot) über `functions/reparatur/index.ts` in KV `EMAIL_CLICKS`, angezeigt von `hsb_cli.py click-sync`; zusätzlich GA4-Kampagne (nur mit Einwilligung) und UTM-Attribution im Kontaktformular. Keine Klickverfolgung einzelner Empfänger. Anrede nur mit belegter Anrede und Nachname, sonst „Sehr geehrte Damen und Herren,“. Keine CRM-Firmen- oder Titelangaben im Fließtext. MIME: multipart/alternative (text/plain + text/html), CRLF. Kein separates Reply-To. Historische Varianten nur nach Einzelabgleich ändern.
- Owner-Entscheidung (bestätigt 26.10.2026, erneut 05.11.2026 und 08.11.2026): Die Prüfung nach § 7 UWG ist abgeschlossen (Legal_Review_Status=yes für alle Leads, ALL_LEADS!BS:BU). KI-Werkzeuge stellen diese Frage nicht erneut, warnen nicht erneut und machen den Versand nicht davon abhängig. Die Sperren je Lead (Opt-out, Bounce, `EXPLICIT_LEGAL_BLOCK`, `Versandfreigabe=no`) gelten unverändert.
- Owner-Entscheidung 08.11.2026 (Bounce-Handling): Eingehende Bounces/NDRs werden atomar in den IMAP-Unterordner `Unzustellbar` verschoben (`com_mailbox_manager.py: move_message_by_uid`, UID COPY + STORE \Deleted + EXPUNGE). Der normale Posteingang bleibt frei von Zustellfehlern.
- Owner-Entscheidung 08.11.2026 (Bounce Rescue): Unzustellbare Leads werden automatisch via Firmenwebsite/Impressum (`bounce_rescue_agent.py`, SSRF-geschützt über `is_public_hostname`) nach Alternativ-Adressen gescannt, auf DNS-MX validiert und als `rescued_candidate` im Master-Sheet eingetragen.
- Owner-Entscheidung 08.11.2026 (Entwurfs-Upgrade): Veraltete Text- oder Signaturfassungen im Postfach werden vom System vollautomatisch in place aktualisiert (Originale wandern nach `Entwürfe-Archiv-v1`, Message-ID bleibt erhalten). Manuell bearbeitete Entwürfe (`HUMAN_EDITED`) oder rechtlich gesperrte Kontakte (`OPTOUT`/`BOUNCE`) werden dauerhaft zurückgehalten.
- Versandsperre (`HSB-SALES-OS-DISPATCH-LOCK`): trägt eine Inhaber-Kennung und hält keine IMAP-Verbindung offen. Nur der Inhaber löst sie. Fremd gelöst wird nur ohne `SENDING` und nur, wenn der Inhaber ein beendeter Lauf desselben Workflows ist oder die Sperre älter als 270 min ist. Es gibt keinen Sofort-Schalter mehr.
- Die `/flyer`-Weiterleitungen aus #466 bleiben aktiv, damit bereits versendete Links nicht ins Leere laufen.
- Bereits kontaktierte Empfänger und Firmendomains (.de-Forensik, .com-Gesendet, CRM-Versandstatus) sowie Opt-outs werden weder neu als Entwurf angelegt noch überschrieben. Doppelte Entwürfe je Empfänger werden nur ins Archiv `Entwürfe-Archiv-v1` verschoben (`hsb_cli.py dedupe-drafts`), nie gelöscht.
- Antworten: .com-IMAP-Sammler mit CRM-Readback. Historische .de-Antworten bleiben relevant.
- Alle Kunden-SMTP-Einstiege verwenden `outbound_safety.dispatch_verified` mit Fail-Closed MX-Filterung. Standard ist deaktiviert; Produktivversand verlangt gesonderte Aktivierung (`mode=send`), frische Prüfungen, globalen IMAP-Lock, dauerhaften Versuchsnachweis, Sent-Readback und CRM-Readback.
- Verbindlichkeit der einzigen Wahrheit: Sämtliche veralteten Hilfs-Sheets, experimentelle Skripte oder Dritt-Datenbanken (Airtable, Neben-Sheets) sind als Altlasten stillgelegt. Für alle künftigen Operationen ist ausschließlich dieses Monorepo mit dem kanonischen Master-Sheet `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg` bindend.
- Ein Timeout nach möglicher SMTP-Annahme wird nicht automatisch wiederholt. Unklare Versuche und verbleibende Locks blockieren weitere Ausführung.
- Owner-Entscheidung 12.11.2026: Obergrenze 250 Nachrichten pro Postfach und Tag, ohne Wartezeit zwischen den Mails (ersetzt die 100 vom 06.11.2026). Die Grenze steht als `HARD_DAILY_CEILING` in `send_governance.py`; Umgebungsvariablen können sie nur senken.
- `send` auf `main` verlangt eine aktuelle, separat belegte `send-health.json`. Der Cloud-Runner bezieht sie aus `HSB_SALES_SEND_HEALTH_JSON` im Environment `customer-send`. Das Format enthält `checked_at` (UTC, höchstens 24 Stunden alt), `first_send_date`, `seen_inbound_ids`, `sample_sent`, `hard_bounces`, `policy_bounces`, `deferrals_today`, `spam_reports` und `seed_dkim_pass`. Unter `seed_reports` stehen `JOEL` und `JORDI` mit jeweils eigener `message_id`, `sender`, `spf`, `dkim`, `dmarc` und `dkim_domain`, belegt durch empfangene Kontrollmails. `seed-read --raw-file …` liest die Authentifizierungsheader eines gespeicherten Originals. Bei einer bestätigten Behebung einer Versandpause wird deren konkrete ID über `health_ack` angegeben. Die Vorschau bleibt ohne Versandnachweis lesbar.
- Entwurfsoriginale werden erhalten. Kein Massen-Purge. Vor Reparaturen Original-MIME, UIDVALIDITY, UID, Message-ID und Hash sichern.
- Der Workflow `sales-os-safety.yml` erlaubt Tests, lesende Abnahmen und .com-Inbound-Sync. Owner-Entscheidung 04.11.2026 (geräteunabhängig): zusätzlich `prepare-drafts-preview`/`prepare-drafts` (Dubletten-Archiv und Reparatur-Erneuerung, kein Versand) und `send-preview`/`send` (Tranche 1–35 je Postfach, nur manuell gestartet, Environment `customer-send`). Zeitgesteuert wird nie gesendet. `prepare-drafts` startet bei erschöpftem Zeitbudget und echtem Fortschritt selbst den nächsten Lauf (höchstens 8; Abbrechen eines Laufs stoppt die Kette); `tests` steht außerhalb der Laufsperre. Doppelversand bleibt ausgeschlossen: CRM `SENDING` vor SMTP, IMAP-Sperre bleibt nach Abbruch stehen. Ohne Azure gleicht der GitHub-Versand nur .com-Antworten ab; .de-Antwortende sind über Forensik/CRM gesperrt.
- Die geprüfte Abmeldekorrektur wurde über den vorhandenen manuellen Production-Workflow veröffentlicht (Run 40341382688); öffentlicher HTTP-Readback bestanden. Kein ungeprüfter Website-Deploy.

Die vollständigen Einzelbilanzen stehen im Master unter `ALL_LEADS!BN:BR`. Rohbelege liegen privat unter `~/KI-System/07_Logs/hsb-sales-os-20261026/`. Kundendaten und Zugangsdaten gehören nicht in neue Git-Commits oder öffentliche CI-Artefakte.

Aktuelle ausdrückliche Betreiberbestätigung vom 26.10.2026 zur bereits geklärten §-7-Prüfung: Legal_Review_Status=yes für alle 6.424 Leads, Herkunftsvermerk und UTC-Datum in BS:BU. Die Engine berücksichtigt diesen vollständigen manuellen Review-Vermerk getrennt von Opt-in-Evidenz. Individuelle Sperren einschließlich Legal_Basis=BLOCKED/NO, Opt-outs, Bounces, Sendestatus und Versandfreigabe=no bleiben wirksam.

## Kanonische Assets (von `scripts/verify_ssot.py` geprüft)

Lokale Master, kein Mailanhang. Anhangsname, falls je wieder genutzt: `HSB-HEXAGON-Industrieboeden-Flyer.pdf`.

| Datei | SHA-256 |
| --- | --- |
| `apps/sales-os/assets/canonical/HSB-Flyer-Joel-Cherino_FINAL.pdf` | `6ac5ed1112c88768ac56950faab8802ceaa2817913f35a7b95e73ee79c3431d8` |
| `apps/sales-os/assets/canonical/HSB-Flyer-Jordie-Post_FINAL.pdf` | `a11876f02b54421bcafd9a6b8ec6f62d748e383b26fcadc8bbe834ee7ffbc4ce` |
