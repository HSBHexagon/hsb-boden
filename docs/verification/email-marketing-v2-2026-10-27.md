# E-Mail-Marketing v2 — Entwicklungsnachweis

Stand 27.10.2026. Worktree `feat/email-marketing-v2` nach Transfer fortgesetzt.

Tasks 1–6 lagen mit taskbezogenen Reviews vor (`8d9377f`). Tasks 7–9 im eigenen Codex-Kontext ergänzt: journalisierte Sequenzplanung, Reply-SLA, 10/20/30-Hochlauf, persistente domainweite Pause und erneute Gesundheitsprüfung vor jeder Mail; wiederaufnehmbarer Entwurfsaustausch mit UID MOVE und Readbacks; URL-Prüfung und strengere MX-Prüfung.

## Prüfstand
- Python: kombinierter Lauf 370 bestanden/1 übersprungen, Fokusprüfungen danach grün. Abschließender Lauf/CI noch zu prüfen.
- Website: 359 Tests, Astro 0 Fehler/0 Warnungen, 59 Seiten gebaut, Deployment-Dry-Run bestanden.
- SSOT und `git diff --check` grün.
- Lokaler HTTP-Aufruf `/flyer/`: Landingpage und PDF-Link vorhanden; kein `email=`.
- Browserprüfung versucht: Chrome-Connector verweigert lokalen Host (`Host access is restricted by policy`). Keine visuelle Abnahme behauptet.
- Dry-Run auf Snapshot vom 26.10. mit aktuellen DNS-Abfragen: Joel 5, Jordie 1 Pilotkandidaten, sämtliche Mutationszähler/Kundenversand = 0. Historischer Snapshot, keine aktuelle Gesamtbestandsabnahme. Apply verweigert Snapshots älter als 24 h.

## Sicherheitsverhalten
Neue Message-ID und Ersatz-MIME werden vor APPEND dauerhaft gespeichert. Bei unklarem APPEND-/MOVE-Ausgang kein blindes Wiederholen. Original bleibt im Journal sowie nach MOVE im Archiv; kein EXPUNGE. Ohne MOVE hält der Vorgang an. Frisches CRM wird vor jedem Apply gelesen. Historische Erstkontakte starten keine neue Nachfasssequenz; `sequence-preview` zählt nur. Erst nach SMTP-/Sent-/CRM-Readback wird ein neuer v2-Erstkontakt journalisiert. Automatischer Folgeversand wird nicht aktiviert.

## Grenzen und nächste Aktivierung
Production-Deploy, KV/Secret, CRM-Schreiben und Verschieben echter Entwürfe bleiben im vereinbarten Freigabeschritt. Kundenversand bleibt separat deaktiviert. Für Seed-Tests fehlen bestätigte Zielpostfächer. .de-Collector hatte HTTP 403. Keine .env gelesen oder kopiert und keine Live-Mutation in dieser Fortsetzung.

Die früher genannten 5,9 % (63/1069) sind ein Verhältnis zweier CRM-Zählungen, keine nach Versandzeitraum/Message-ID verifizierte Bounce-Rate. „Reaktionen“ enthielten auch Abwesenheiten: keine belastbare Aussage über positive Antworten oder Umsatz. Health-Guard/Pilot benötigen eine zusammengehörige aktuelle Stichprobe. Scanner-Filter sind Heuristiken, kein sicherer Mensch-Nachweis.

## Gegenprüfung und Korrekturen
Unabhängiger Codex-Review stellte sechs weitere Fehler nach. Korrigiert: CRM-Lead-ID vor und nach dem Schreiben prüfen/Zeile frisch auflösen; Linkabrufe über gehärteten Redirect-/IP-Opener; neue .com-Rückläufer vor jeder Versandfreigabe lesen; vorhandenes Tier Z erhalten; erledigte Journalzeilen vor dem Limit ausfiltern; unbestimmte Abwesenheit entfernt eine alte Fälligkeit. Außerdem schützt der bestehende JOEL-Postfachlock die Upgrade-Operationen, die Pause wird geräteübergreifend im technischen IMAP-Ordner geführt und der Sequenzbeleg teilt sich eine SQLite-Transaktion mit dem finalen Versandstatus.

Aktueller lokaler Teststand nach diesen Korrekturen: 380 bestanden, 1 übersprungen, SSOT und diff-check grün. PR #503: GitHub-Prüfungen erfolgreich, zusätzlicher CircleCI-Status meldet fehlende Projektkonfiguration (Pipeline 134), kein fehlgeschlagener Anwendungstest. CircleCI ist keine erforderliche Main-Prüfung; keine neue Pipeline oder Schutzabsenkung vorgenommen.

## Letzte Absicherungen
- Inbound-Abfrage nutzt UIDs und bricht bei SELECT-/SEARCH-/FETCH-Fehlern oder Änderungen während des Scans ab. Eine ungelesene Inbox gilt nicht als leer.
- Gesundheitsmessung verwendet bereits erfasste Message-IDs als Baseline, niemals den frei gesetzten Date-Header. Verspätete Policy-Bounces werden berücksichtigt. Fehlt der Cursor, bleibt der Versand gehalten.
- Upgrade-Zellschreiben verwendet `batchUpdateByDataFilter` mit `developerMetadataLookup`, keine Zeilennummer. Fehlende/eindeutig falsche Bindungen blockieren vor APPEND/MOVE. Zusätzlich ist der neue Apply-Pfad standardmäßig gehalten, bis ein Sortier-Canary mit einer Testkopie der Sheets-Daten die Bindungen bestätigt (`HSB_CRM_BINDINGS_VERIFIED`). Diese Inbetriebnahme ist offen und braucht den bestehenden Google-Zugang, keinen KAS-Zugang.
- Ein nach dem Snapshot gesetztes Tier Z wird auch beim Live-Read respektiert.

Abschließender lokaler Stand dieser Korrektur: 385 Python-Tests bestanden, 1 übersprungen, SSOT und diff-check grün. Website-Prüfstand bleibt 359 Tests, Build und Dry-Run bestanden. Es wurden keine Produktionsflags gesetzt.
