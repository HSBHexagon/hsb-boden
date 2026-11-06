# Ausführungsplan für die Entwurfsumstellung

## Ziel
Die offenen, nach den bestehenden Regeln zulässigen Entwürfe beider `.com`-Postfächer auf die aktuelle Reparatur-Fassung bringen. Der Lauf aktualisiert Entwürfe und deren CRM-Zuordnung. Versandfähigkeit wird separat geprüft.

## Bevorzugter Weg über Desktop Commander und Antigravity

Der [Rapid-Draft-Plan vom 26.09.](../../superpowers/plans/2026-09-26-hsb-com-rapid-draft-engine.md) und der [Antigravity-Systemleitfaden](../../ANTIGRAVITY_SYSTEM_GUIDE.md) dokumentieren die direkte All-Inkl-IMAP-Verbindung und gebündelte CRM-Updates. `ComMailboxClient.create_drafts_batch` verwendet eine Verbindung pro Batch. `run_mass_draft_rollout.py` bündelt den Sheets-Schreibvorgang je Tranche. Die dort genannte Größenordnung von 0,3 Sekunden beschreibt das Anlegen eines Entwurfs per IMAP. Für den Austausch bestehender Entwürfe einschließlich Archivierung und CRM-Readback gilt ein eigener Messwert.

- [ ] Über Desktop Commander am Mac das kanonische HSB-Repository öffnen. Aktuellen Commit, Zugriff auf beide All-Inkl-Postfächer und Zugriff auf `ALL_LEADS` prüfen. Die vorhandenen Zugangsdaten bleiben in der eingerichteten Laufzeit.
- [ ] Vor jedem Schreibstart den Status der GitHub-Läufe und die gemeinsame IMAP-Sperre prüfen. Der lokale Lauf übernimmt erst, wenn der Cloud-Lauf beendet ist und keine unklare Versandbuchung oder fremde Sperre offensteht. Die geplante GitHub-Kette als alternativen Ausführungsweg behandeln und den geplanten Start bei lokaler Übernahme berücksichtigen.
- [ ] Die aktuelle Reparaturvorlage mit eingebettetem HSB-Logo als echten Pilotentwurf je Postfach speichern, über IMAP zurücklesen und in Outlook öffnen. Anrede, Betreff, Layout, Signatur, Abmeldehinweis und den einzigen Kampagnenlink `/reparatur/` prüfen. Erst danach auf weitere Kundenentwürfe ausweiten.
- [ ] Den Bestand zuerst per IMAP-Kopfzeilen und CRM-Zuordnung erfassen. Nach der Dublettenbereinigung die betroffenen UID-Sätze und Ordnerstände prüfen. Bei unverändertem Stand und ohne Archivierungen kann die erste Bestandsaufnahme weiterverwendet werden. Bei abweichender UIDVALIDITY oder ungeklärten Änderungen den betroffenen Ordner neu abgleichen. Vollständige MIME-Daten der zur Änderung ausgewählten Originale vor dem Austausch sichern.
- [ ] Die vorhandene Reparatur-Engine für den Austausch nutzen. Pro Postfach die IMAP-Verbindung für eine Tranche wiederverwenden. Die bestehende Lead-ID-Bindung für gebündelte CRM-Aktualisierungen und gebündeltes Rücklesen verwenden. Ersatz und Archiv weiterhin einzeln über Message-ID, UID und Hash belegen. `Draft_ID`, `Email_Template_ID` und `Drafted_At` erst nach bestätigtem Postfachstand aktualisieren. Fortschritt erst nach CRM-Readback zählen.
- [ ] Den lokalen Wiederanlauf mit dauerhaftem Audit und Journal prüfen. Einen Abbruch zwischen IMAP-Austausch und CRM-Readback nachstellen. Die Wiederaufnahme muss den vorhandenen Ersatz erkennen, das Original im Archiv verifizieren und die fehlende CRM-Buchung nachholen. Mehrdeutige Zuordnung stoppt die Tranche.
- [ ] In einer ersten Tranche von 20 zulässigen Bestandsentwürfen Inventur, IMAP-Austausch und CRM-Zugriffe getrennt messen. Erst nach erfolgreichem Wiederanlauf und vollständigem Readback in Tranchen bis 100 fortsetzen. Fortschritt je Postfach und verbleibende Sperrgründe protokollieren.

## Abschlusskriterien (messbar)
- [ ] Beide Postfächer haben keine offenen, zulässigen Kandidaten mehr. Gesperrte oder mehrdeutige Fälle sind separat bilanziert.
- [ ] Abschlussabgleich bestätigt die aktuelle Fassung aller bearbeiteten Entwürfe und deren CRM-Zuordnung. Die Originale liegen im Archiv.
- [ ] `customer_emails_sent` ist in jedem Lauf 0.
- [ ] `python -m pytest apps/sales-os/tests/ -q` und `python scripts/verify_ssot.py` grün.

## Grenzen der Entwurfsumstellung
Der Modus bleibt `prepare-drafts`. Kunden-SMTP ist deaktiviert. Opt-outs, Bounces, Kontaktsperren und Versandfreigaben bleiben wirksam. Eine vorhandene Sperre wird nach den Regeln von `release_stale_lock` behandelt.

## GitHub Actions als Ausweichweg

Die bestehende GitHub-Kette bleibt verfügbar, wenn der lokale Weg ausfällt. Vor einem Wechsel den letzten bestätigten CRM-Stand, offene Journaleinträge, Archivbestand und aktive Sperren abgleichen. Der bestehende GitHub-Workflow behält seine Laufgrenzen.

- Iterationen: höchstens 8 Folgeläufe (`chain` < 8); danach endet die Kette. Eine Verlängerung entscheidet der Inhaber.
- Zeit: je Lauf Budget 190 min, Job-Abbruch 240 min, also höchstens rund 32 Stunden.
- Kosten: GitHub-Actions-Minuten, keine Modellkosten.

## Stop-on-drift (im Workflow verankert)
- Ein Fehler in einem Schritt: `set -e`, kein Folgelauf.
- Ein Lauf ohne CRM-Fortschritt (`crm_updated` gesamt 0): kein Folgelauf.
- Eine Tranche ohne Fortschritt: dieses Postfach endet in diesem Lauf.
- Sperre unklar (`STALE_LOCK_*`): Lauf scheitert, kein Folgelauf.
- Abbrechen des laufenden Laufs stoppt die Kette.

## Isolation
Lokal und in GitHub gilt `HSB_CUSTOMER_SEND_ENABLED=no`. Eine gemeinsame IMAP-Sperre schützt beide Postfächer. Die lokale Ausführung bewahrt Audits und Journale außerhalb des Repositories auf.

## Verifikation
Frischer Reviewer: Codex-Review auf dem PR. Abschlussprüfung: CRM-Zählung und Audit-Zahlen aus dem letzten Lauf.

## Protokoll
- 04.11.2026: Kontrakt angelegt. Start der Kette: einmaliger Cron `55 1 5 11 *`, nach Ende von Lauf `41919946078`.
- 04.11.2026: Plan um den von Antigravity dokumentierten lokalen IMAP- und CRM-Batchweg ergänzt. Desktop Commander erreichte den Mac und das kanonische Repository. Die Laufzeit der schnelleren Austauschvariante ist noch zu messen.
