# HEXAFLOOR — technischer Prüfstand 21.10.2026

**Ergebnis: TEILWEISE. Zentral gespeichert und geschützt veröffentlicht. Die geforderte vollständige Browserabnahme ist blockiert.**

Anwendung: https://hsb-monteurplanung.glossy-trail-5737.chatgpt.site

GitHub: https://github.com/HSBHexagon/hsb-boden/pull/463 (Entwurf, nicht gemergt).

Veröffentlichter Stand: Sites-Version 4, Quellcommit `89076b65187acf49d9b295f33b7f9c83eeea0226`, Deployment `appgdep_6ad8e90590448191ba6ac415867d285f`, Status `succeeded` am 21.10.2026 um 18:32 Uhr Europe/Berlin. Kein Produktivwebsite-Deployment.

## Tatsächlich umgesetzt

Vorhandene HTML-Oberfläche und Planungslogik wiederverwendet: Projektstamm mit Nummer, dauerhafter UUID, Kunde/Bezeichnung, Ort, Zeitraum, Personalbedarf, Treffpunkt, Zeit, Qualifikation und interner Notiz; Projekt bearbeiten, archivieren und wieder öffnen; Monteure, Qualifikationen und Kolonnen; Montag bis Samstag; Tagesbedarf; Projektverlängerung; Abwesenheiten; freie geeignete Kandidaten; Vorschläge aus Überbesetzung und bestätigte Umbesetzung; Wochenübersicht; WhatsApp-Text, CSV und Druckansicht; JSON-Sicherung/Wiederherstellung; zentraler Änderungsverlauf.

Serverprüfung verhindert ungültige Datensätze, fehlende Qualifikation, Einsätze bei Abwesenheit und Doppelbelegungen. Ein Datenbank-Unique-Key schützt Mitarbeiter/Tag zusätzlich. CAS-Revision und transaktionale D1-Batches verhindern stilles Überschreiben; fehlerhafte Batches rollen zurück. Projektzeilen werden in-place aktualisiert, damit spätere Dokument-Fremdschlüssel erhalten bleiben.

## Hosting, Daten und Zugriff

Bestehendes Sites-Hosting auf Cloudflare Workers; bestehendes Cloudflare-D1-Binding `DB`. Tabellen: `planning_meta`, `planning_workers`, `planning_projects`, `planning_assignments`, `planning_absences`, `planning_revisions`. Jede erfolgreiche Speicherung erzeugt einen unveränderlichen Revisionsdatensatz mit Zeit, Akteur, serverseitig berechneter Änderungsbeschreibung und vollständigem Snapshot.

Sites-Zugriff von öffentlich auf `custom` umgestellt und zurückgelesen, Policy-Revision 3: ausschließlich bisheriger Eigentümer, keine Gruppen, keine weiteren Besucher. Eigentümerkonto: cherinojoel@gmail.com. Kein Mitarbeitereinladungsversand. Zusätzliche Mitarbeiter sind noch nicht für den Zugriff eingerichtet. Die serverseitige Sites-Zugriffspolitik erzwingt die Mitgliedschaft auf allen Routen; die Site-spezifische Besucher-ID wird für die Änderungshistorie verwendet. Keine Vermischung mit globalen Konto-IDs. Service-Aufrufe mit gültigem privaten Plattform-Credential besitzen Eigentümer-Servicezugriff, keine Browseridentität.

**Einzige operative Quelle:** D1-Datenraum `production`. Testdatenraum `test` im selben D1 ist logisch durch zusammengesetzte Schlüssel und feste API-Endpunkte getrennt; er ist keine separate physische Datenbank. Google Sheet bleibt Referenz, ohne bidirektionale Synchronisierung. `_META!A5:B9` dokumentiert die Anwendung, Quelle und offene Browserabnahme; Rücklesung erfolgt. Bestehende Werte und fachliche Tabellen wurden nicht ersetzt.

## Nachweise

- 22 automatisierte Tests bestanden: ursprüngliche Baseline, wiederverwendete Fachlogik, SQL-Transaktionen auf echter SQLite, Versionskonflikt, Datenraum-Isolation, unveränderte Tage, zukünftige Dokumentverweise, Rücksicherung bei geänderten Projektnummern tatsächlicher Click-Handler im Node-VM-Test sowie korrekter Umgang mit Site-spezifischen Identitäten.
- TypeScript `tsc --noEmit`: Exit 0.
- Sites/Worker-Build: Exit 0.
- `python3 apps/website/scripts/verify_ssot.py`: Exit 0.
- `git diff --check`: Exit 0.
- Unabhängige Codeprüfung: Befunde zur Ladesynchronisierung, Wiederherstellung und datierten Schaltflächen mit Regressionstests korrigiert. Node-VM-Tests sind **keine Browserprüfung**.
- GitHub-Commit `0155ef57bc3d8b52945fcefc46dbb59e09e38ff8`: Security Analysis, Quality Assurance, CI, Deploy Preview und Lighthouse erfolgreich. Diese bestehenden Workflows ersetzen keine anwendungsspezifische Browserabnahme.
- Anfangs gefundene kritische Abhängigkeit `next@16.3.4` auf `16.3.6` aktualisiert; offizieller Hinweis: https://github.com/vercel/next.js/security/advisories/GHSA-vcvr-r3jv-pc5j . Sicherheitsprüfung danach erfolgreich. Keine Behauptung einer ausgenutzten Lücke.

### Live-API gegen echte zentrale D1-Datenquelle

Nur `/api/test-plan` wurde mit synthetischen Datensätzen beschrieben. Produktivdaten wurden nur gelesen.

| Verbindlicher Fall | Tatsächlicher Nachweis | Browserstatus |
|---|---|---|
| 1. Neu anlegen, speichern, erneut öffnen | 4 TEST-Monteure und 2 TEST-Projekte per HTTP gespeichert und in neuem autorisiertem HTTP-Aufruf gelesen | Offen |
| 2. Zwei Projekte besetzen | Unterschiedlicher Bedarf 2/1, 15 Wochenzuweisungen zentral gespeichert | Offen |
| 3. Mittwoch krank | Nur betroffenen Mittwochseinsatz entfernt; Projekt A danach 1 statt 2 besetzt | Offen |
| 4. Freie Ersatzperson | Mittwoch wieder 2 Personen; Fachlogik-Fehlbedarf 0 | Offen |
| 5. Doppelbuchung | API HTTP 400; Revision unverändert; DB-Unique-/Rollback-Test bestanden | Offen |
| 6. Verlängerung/Samstag | Projektende 26.10., Tagesbedarf 24.10. und Samstagseinsatz gespeichert | Offen |
| 7. Andere Einsätze erhalten | Übrige Tageszuweisungen vor/nach Ausfall identisch | Offen |
| 8. WhatsApp | Fachlogik-Test: aktuelle Teams, Ort/Treffpunkt/Zeit enthalten, Abwesenheitsgründe und interne Notiz ausgeschlossen | Clipboard/Druck offen |
| 9. Zweite Sitzung/Gerät | Unabhängige autorisierte Service-Aufrufe lesen dieselben Daten; nach neuem Deployment ebenfalls Revision 5 | Zweite Browsersitzung offen |
| 10. Zugriff/Isolation | Anonym und mit gefälschtem Identitätsheader ohne Credential gesperrt; fehlender Origin bei PUT HTTP 403; Produktivraum bleibt leer | Anderer angemeldeter Benutzer offen |

Ein zunächst falsch formulierter Test versuchte, einen fremden Besucher durch einen gefälschten Header **zusätzlich zu einem gültigen Eigentümer-Service-Credential** zu simulieren. Das blieb berechtigter Servicezugriff und ist kein Fremdbenutzertest. Der korrigierte Test ohne Service-Credential wurde gesperrt. Diese Einschränkung ist nicht als Nachweis eines zweiten angemeldeten Benutzers gewertet.

D1-Nativrücklesung: 2 Projekte und 4 Monteure, jeweils ausschließlich `environment=test`; 5 Testrevisionen mit Snapshot-Feld. Das Werkzeug kürzt längere Snapshot-Zellen in seiner Ausgabe; die vollständige Wiederherstellung ist durch die SQL-Tests nachgewiesen, nicht durch Parsen gekürzter Rücklesungen.

Produktiv-API nach Wiederveröffentlichung: HTTP 200, Revision 0, **0 Mitarbeiter, 0 Projekte, 0 Einsätze, 0 Änderungen**. Test-API: HTTP 200, Revision 5, 4 TEST-Monteure, 2 TEST-Projekte, 16 Einsätze, 5 Änderungen. Kein Demodatensatz produktiv eingebracht.

## Grenzen und externe Hindernisse

1. Cloud-Browser konnte `http://terminal.local:4173/` nicht öffnen; anschließend ausdrückliche URL-Policy-Ablehnung. Kein Umgehen dieser Richtlinie. Desktop-/Tablet-/Mobil-Rendering, Druck/Clipboard und zwei echte autorisierte Browsersitzungen sind nicht abgenommen. Für Fortsetzung ist ein Browserzugang nötig, der die Anwendung erreichen darf.
2. Direkter Cloudflare-Konnektor: `whoami`, `search`, `execute` lieferten MCP -32603 Internal error. Keine fehlende Authentifizierung behauptet. Bestehendes Sites-Hosting/D1 konnte über seine native Integration weiterverwendet werden; kein Wechsel auf Supabase/Vercel.
3. Der konkret benannte Prototyp `HEXAFLOOR_Monteurplanung_BEARBEITBAR.html` wurde in den erreichbaren Quellen nicht gefunden. Der vorhandene weiterentwickelte `HEXAFLOOR_Einsatzplaner_KOSTENLOS.html`, Revision 2, wurde vollständig gelesen und wiederverwendet. Die Mac-Entwicklungsmaschine war offline.
4. Lokaler Website-Teststart scheiterte an fehlendem `vitest`; bestehende Website-CI war erfolgreich. Keine Änderungen unter `apps/website/` oder `apps/sales-os/`. Produktivwebsite nicht deployt; bestehende PR-Preview-Workflows liefen separat.
5. `design-qa` war nicht als eigenständiger Skill verfügbar. Produkt-Audit und Frontend-/Visualisierungs-Test-Skills wurden geladen; eine visuelle Abnahme wird nicht behauptet.

## Betriebskosten und Grenzen

Kein neuer kostenpflichtiger Tarif, keine neue Datenbank-Plattform und kein neues Abonnement aktiviert. Nutzung des bestehenden Sites-Projekts und seines bereits vorhandenen D1-Bindings. Zusätzlicher neu abgeschlossener Monatsvertrag: keiner.

**Der tatsächliche Sites-Kontotarif, dessen Restkontingente und mögliche Plattformlimits sind über die verfügbaren Werkzeuge nicht verifiziert. Daher keine Zusage unbegrenzten oder dauerhaft kostenlosen Betriebs.** Direkte Cloudflare-Free-Grenzen dürfen nicht pauschal dem verwalteten Sites-Tarif gleichgesetzt werden. Offizielle Referenz: https://developers.cloudflare.com/d1/platform/pricing/ (Free: 5 Mio. gelesene Zeilen/Tag, 100.000 geschriebene Zeilen/Tag, 5 GB gesamt; diese Zahlen sind keine bestätigte Tarifzuordnung dieser App).

Anwendungsgrenzen: höchstens 500 Monteure, 1.500 Projekte, maximal 2 Jahre Projektzeitraum und 1.500.000 Byte je Speicheranforderung. Volle Plan-Snapshots je Revision erhöhen Speicherbedarf; kein automatisches Löschen älterer Sicherungen implementiert. Wachstum/Quoten müssen vor breiterem Betrieb geprüft werden. Beim Speicherversagen bleibt der vorherige bestätigte Stand bestehen.

## Zukunftsmodule

Drive-Bautagesberichte HTML `1FtcXbHpNa_tx-xumpNSsDg9YdJDMAptu` und PDF `11WYZYkGSbdkwcAPHY2if1ZkGXZwO1POq` analysiert: Berichtnummer/Datum, Bauvorhaben, Bauführer, Witterung, Arbeitszeiten/Stunden, Tätigkeiten, Behinderungen, Änderungen, Vorkommnisse, Unterschriften und Fotobeschreibungen. Bestehende HTML-Formular-/Fotoseiten-/PDF-Drucklogik kann später übernommen werden; aktuelle browserlokale Speicherung ist kein zentraler Dokumentendienst.

Nicht umgesetzt: zentrale Bautagesberichte/Fotos, Mitarbeiterstunden/Tätigkeiten, Materialbestellungen/-verbrauch, Angebote/Verträge/Nachträge, Schriftverkehr/Chronologie sowie Kosten-/Projektanalysen. Diese Module sollen auf dauerhafte Projekt-IDs verweisen.
