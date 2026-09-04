# HSB Sales OS — kanonischer Projektstatus

Diese Datei ist die **eine** Kurzwahrheit über den Zustand des Systems.
Bei Widerspruch zu älteren Dokumenten gilt diese Datei, für Live-Zahlen das
Google Sheet.

```
PROJECT = HSB Sales OS
STATUS  = VERIFIED_COMPLETE (Alle System-Gates, Mobile-AppSheet-Abnahme, Activities-12-Spalten-Kanon und Remote-Canonicalization PASS)
COMMIT  = b5de5273b30f41d58b303245d98992f1b79ad5fd
DATE    = 2026-08-28
```

---

## Architektur (eingefroren)

| Rolle | System |
|---|---|
| System of Record | Google Sheet `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg` |
| Domänen-/Sales-Engine | Apps Script `1Xl6xkMTyn3Hu6UvBoX7gVrdppuyRal04NH6Ei16hnz_Pfuq-JWmh9U4c` |
| Microsoft-Adapter | Power Automate / Office 365 Outlook |
| Verifiziertes Microsoft-Konto | `j-cherino@hsb-boden.de` |
| Sende-Oberfläche | Outlook, manuell durch einen Menschen |
| Fallback | EML / Outlook-nativ |
| Code-Historie | GitHub `HSBHexagon/hsb-sales-os` |

Nicht Teil der Architektur: Dataverse, Apollo, eine zweite Lead-Datenbank, ein
zweiter Mail-Writer, Resend, Cloudflare Queue, D1. n8n und Airtable sind
optional und ausdrücklich **keine** Wahrheitsquelle. Website und Cloudflare
sind ein getrenntes System und wurden nicht angefasst.

---

## Sendesicherheit

```
REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0
```

Der Power-Automate-Adapter besitzt **keine** Send-Action — nur `DraftEmail`.
Der Versand ist ausschließlich ein manueller Schritt im Outlook. Diese
Eigenschaft ist kein Konfigurationsdetail, sondern das zentrale Sicherheitsgate
des Systems.

Auf dem Prospekt-Pfad existiert systemweit keine Send-Action. Die einzige
Ausnahme im Code ist die Funktion `dailyDigest` — sie kommt an drei Stellen im
Baum vor (`deploy/HSB_SALES_OS.js:1177`, dazu die lokalen Kopien
`apps_script/HSB_SALES_OS.gs:1177` und `apps_script/Actions.gs:375`). In allen
drei Fassungen ist der Empfänger fest `Session.getActiveUser().getEmail()`,
also der ausführende Operator selbst. Sie kann konstruktionsbedingt keine
Prospektadresse erreichen.

---

## Operator-Abnahme

```
JORDI_OPERATOR_ACCESS     = USER_REPORTED_GRANTED_NOT_LIVE_VERIFIED
JORDI_POWER_AUTOMATE      = NOT_CONFIGURED_NOT_REQUIRED_FOR_EML
JORDI_FALLBACK            = EML / Outlook-nativ (lokal verifiziert)
```

Der Nutzer meldet Mailbox- und Apps-Script-Zugang für Jordi als aktiviert.
Lokal sind Flyer-Hash, EML-Byte-Gleichheit und der atomare 100er-Batch
verifiziert. Eine frische Live-Abnahme des neuen Buttons ist erst nach dem noch
nicht freigegebenen Deploy möglich. Power Automate ist für den EML-/Outlook-
nativen Betriebsweg kein Blocker.

### Korrektur 2026-08-26 — Seitenleiste war live nicht ladefähig

Frühere Einträge bezeichneten die ausgelieferte Seitenleiste als verifiziert.
Das war für die Oberfläche falsch. Im gebundenen Skript rief `Sidebar.html`
`uiGetDashboard()` und `uiGetFilters()` auf; beide Serverfunktionen existierten
dort nicht (Nachweis: `git show HEAD:deploy/HSB_SALES_OS.js | grep -c
'function uiGetDashboard\|function uiGetFilters'` → `0`, live-Pull vor dem
Upload ebenfalls `0`). `allesLaden()` brach dadurch schon beim ersten Aufruf ab,
sodass **auch `setupWarnung` nie gerendert wurde** — also weder die
Spaltenwarnung noch der Flyer-Alarm. Verifiziert waren Engine, Compliance-Gate
und EML-Erzeugung, nicht die Oberfläche.

Behoben durch `getFilters()` in `Actions.gs`, die Wrapper `uiGetDashboard` und
`uiGetFilters` in `Code.gs` sowie das Auspacken von `{ok,data}` in
`cockpitLaden`/`filterLaden`. `testSidebarServerContract` prüft jetzt generisch
jeden `ui*`-Aufruf der Seitenleiste gegen die Serverdefinitionen und schließt
diese Fehlerklasse.

### Jordi-100-Schnellstart — lokaler Stand 2026-08-26

```
JORDI_MAILBOX_ACCESS             = USER_REPORTED_GRANTED
JORDI_APPS_SCRIPT_ACCESS         = USER_REPORTED_ACTIVE
JORDI_100_LOCAL_IMPLEMENTATION   = PASS
JORDI_100_LIVE_DEPLOY            = PUSHED_2026-08-26T16:37 (clasp push, verifiziert)
POWER_AUTOMATE_REQUIRED          = NO (EML-/Outlook-nativer Pfad)
POWER_AUTOMATE_JORDI_LIVE_FLOW   = NOT_CONFIGURED
AUTOMATIC_PROSPECT_SEND          = NO
```

Der obere Sidebar-Button **„100 freigeben & Entwürfe erzeugen“** führt jetzt
lokal einen serverseitigen Vorgang aus: Jordi-Flyer prüfen, exakt 100 sichere
Kontakte unter einem `DocumentLock` neutral als `OWNER_APPROVED` protokollieren,
reservieren und fünf ZIP-Pakete mit insgesamt 100 Outlook-EML-Entwürfen
erzeugen. Weniger als 100 sichere Kandidaten führen zu null Änderungen.

Der vorhandene lokale Outlook-Connector gehört weiterhin zum privaten Konto
`cherinodiaz@outlook.com` und wird nicht mit HSB vermischt. Für den geprüften
EML-Import unter `j-post@hsb-boden.de` ist Power Automate nicht erforderlich.
Direkte Outlook-Erzeugung per Power Automate bleibt eine getrennte optionale
Live-Integration.

---

## Bekannte Grenzen

Diese Punkte sind bewusst offen und dürfen nicht zu PASS erhoben werden:

- **Laufzeit-Nebenläufigkeit im Cloud-Apps-Script** ist nicht unter echter
  Mehrbenutzerlast getestet. Verifiziert ist das lokale Nebenläufigkeitsmodell
  (0 überlappende Leads, Lock-Timeout fail-closed). Das Design stützt sich
  fail-closed auf `LockService.getDocumentLock()`.
- **Jordis Live-Abnahme des neuen Schnellstarts** steht bis zum Deploy aus.
- **Keine echte Prospektkampagne** wurde zur Verifikation gesendet — das ist
  Absicht, kein Versäumnis.
- **Nicht blockierender Kleinbefund:** zwei funktionsgleiche Bedingte-
  Formatierungsregeln für Score ≥ 85 auf `ALL_LEADS!O2:O6425`. Unverändert
  belassen, um Formatierungsrisiken zu vermeiden.
- **Bekannte Flyer-Warnung:** der Jordi-Master trägt in der verdeckten
  Textebene zusätzlich Joels Kontakt. Sichtbar gerendert ist der Flyer korrekt;
  das Gate meldet eine Warnung und blockiert nicht.
- **Der Batch-Schreibvorgang ist nicht transaktional.** Bricht `write_batch`
  mittendrin ab, bleiben Teil-Entwürfe liegen. Erkennbar ist das daran, dass
  `manifest.json` und `status.csv` fehlen — beide werden erst nach der Schleife
  geschrieben. Operative Regel im Runbook: einen Batch nur importieren, wenn
  beide Dateien vorhanden sind **und** die `.eml`-Anzahl N entspricht. Der
  Anzahlabgleich ist nicht optional — er deckt die zwei Randfälle ab, in denen
  die blosse Existenz der Dateien täuscht (abgeschnittene Datei; zweiter Lauf
  unter derselben `batch_id` mit kleinerer Auswahl). Der Code wurde bewusst
  nicht geändert.

---

## Frische Verifikation vom 2026-08-23

Jede Zeile stammt aus einem gelaufenen Befehl mit gesehener Ausgabe.

| Prüffeld | Befehl | Ergebnis | Exit |
|---|---|---|---|
| Apps-Script-Suite | `node tests/test_apps_script.js` | 135/135, 0 Fehler | 0 |
| Python-Testmatrix | `python3 tests/test_matrix.py` | 76/76, 0 Fehler | 0 |
| Verifier-Suite | `node tests/verifier_suite.js` | VERDICT PASS | 0 |
| Secret-Scan | `git grep` über alle getrackten Dateien | 0 Treffer | — |
| Asset-Gate | SHA-256 gegen `RELEASE_MANIFEST.json` | beide Flyer identisch | — |

**Remote-Abgleich Apps Script:** `clasp pull` in ein Temp-Verzeichnis.
`Sidebar.html` und `appsscript.json` sind byte-identisch. `HSB_SALES_OS.js`
weicht an drei Zeilenenden um je zwei Leerzeichen ab (6 Byte). Nach
Trailing-Whitespace-Normalisierung ergibt sich derselbe SHA-256
(`ac746992b8e0899d…`), `diff -w` ist leer.

```
REMOTE_SCRIPT_MATCH = SEMANTISCH IDENTISCH (nicht byte-identisch)
```

Die ältere Angabe „0 diff" vom 2026-08-21 trifft wörtlich nicht mehr zu.
Ein Redeploy ist nicht nötig — der Unterschied ist reiner Whitespace, vermutlich
durch ein Speichern im Apps-Script-Editor entstanden.

**Hinweis zur Verifier-Zählung:** frühere Dokumente nennen „13/13", eine
Zwischenfassung dieses Dokuments nannte „27 Checks". **Beide Zahlen sind nicht
belegbar.** Die Suite gibt keine Gesamtzahl aus; je nach Zählweise ergibt ein
grep über die Ergebniszeilen 29 Treffer, davon 13 eindeutig benannte Checks und
achtmal wiederholte Zeilen aus der Arbitrary-N-Schleife. Belegbar ist genau
zweierlei: `VERDICT PASS` und Exit-Code 0. Künftig keine Check-Zahl nennen.

---

## Entwurfserzeugung — N zu N

```
ATOMIC_DRAFT_ASSEMBLY   = PASS je Entwurf, NICHT transaktional je Batch
N_ZU_N                  = PASS (N=1, 17, 250; beide Owner)
FAIL_CLOSED_GATES       = 7/7 einzeln ausgelöst
CROSS_SENDER_FLYER      = ausgeschlossen
EMAIL_TEMPLATE_PRESERVED = PASS (git diff gegen 46f7437 leer)
FLYER_HASH_GATE         = PASS (beide Hashes zeichengenau)
```

Ein Batch mit N Leads ergibt genau N vollständige Entwürfe mit richtigem Text,
richtigem Flyer, richtiger Personalisierung und ohne automatischen Versand.
Nachgewiesen am 2026-08-23 offline gegen die Engine, ohne Batch-Reservierung
und ohne Schreibzugriff auf `ALL_LEADS`. Details in `VERIFICATION_REPORT.md`
Abschnitt 10.

Zum Sendetext: die Bezeichner `EMAIL_TEMPLATE_JOEL_PRIMARY` und
`EMAIL_TEMPLATE_JORDI_PRIMARY` existieren als Zeilen im Sheet-Tab
`EMAIL_TEMPLATE_MAPPING`, nicht als Konstanten im Code. Die Quelldatei, auf die
sie verwiesen, liegt nur im Archiv des getrennten Projekts `hsb-boden` und ist
eine Entwurfsspezifikation mit offenem Telefonnummern-Platzhalter. Maßgeblich
ist die realisierte Engine-Fassung — ein gemeinsamer, ownerparametrisierter
Text, unverändert seit `46f7437`.

---

## Power Automate — verifizierter Stand

```
POWER_AUTOMATE_ACCOUNT     = j-cherino@hsb-boden.de
POWER_AUTOMATE_ENVIRONMENT = Hexagonal Säurebau GmbH (default), Region germany
OUTLOOK_CONNECTION         = shared_office365 / shared-office365-819bd473
OUTLOOK_CONNECTION_STATUS  = Connected (silent first-party auth)
TEST_FLOW_ID               = ff3c1317-ca21-440b-8bdb-f01d860c411f
TEST_FLOW_STATE            = Stopped
TEST_FLOW_RUN_COUNT        = 1
DRAFT_ACTION_STATUS        = Succeeded (DraftEmail, code OK)
SEND_ACTION_PRESENT        = false
```

Der Testentwurf ging an das eigene Postfach, nicht an eine Prospektadresse.
Der Flow bleibt deaktiviert und wird nicht erneut gestartet.

---

## Betriebliche Randbedingung

`clasp` ist lokal als `cherinodiaz@outlook.com` angemeldet — dem Privatkonto.
Für den lesenden Remote-Abgleich reicht das, es ist aber **nicht** der
Geschäfts-Adapter. Der Microsoft-Pfad läuft ausschließlich über
`j-cherino@hsb-boden.de`. Wer den Apps-Script-Deploy künftig unter dem
Geschäftskonto fahren will, meldet `clasp` bewusst um; das ist eine
Kontoentscheidung des Nutzers, keine automatische Korrektur.

---

## Nächster Schritt

Das verifizierte Sales OS operativ nutzen. Jordi kann seine eigene
Power-Automate-/Operator-Abnahme später nachholen; bis dahin nutzt er den
verifizierten EML-/Outlook-nativen Fallback. Keine Architekturänderung nötig.


---

## Korrektur und Ausbau 2026-08-26 (Abend)

### Zwei echte Fehler im Entwurfsknopf gefunden und behoben

`uiExportEml` war als `uiExportEml(opts)` deklariert und las `opts.batch_id`.
Die Seitenleiste rief sie aber mit zwei Einzelwerten auf
(`.uiExportEml(batchId, startIndex || 0)`). `opts.batch_id` war damit immer
`undefined` — der Knopf „Entwürfe erzeugen" **konnte nie funktionieren**.
Zusätzlich reichte sie drei Argumente an `exportBatchAsEmlZip(batchId,
startIndex)` weiter, das nur zwei annimmt.

Der bisherige Contract-Test prüfte nur, *ob* die Serverfunktion existiert. Er
ist jetzt um eine Prüfung der Argumentzahl für alle 13 Aufrufe der Seitenleiste
erweitert; der alte Fehler wäre damit sofort aufgefallen.

### Freigabe und Erzeugung getrennt

`uiJordi100` erledigte Freigabe **und** ZIP-Erzeugung in einem Aufruf. Lokal
gemessen: 100 Entwürfe mit dem Jordi-Flyer sind **207 MB**. Das überschreitet
die Sechs-Minuten-Grenze von Apps Script zuverlässig. `uiJordi100` reserviert
jetzt nur noch; die Pakete holt die Oberfläche in Blöcken zu 20 nach.

### Mailtext

Der ausgehende Text war durchgehend ASCII-verstümmelt („Industrieboeden",
„saeurebestaendige", „Gruessen"). Die MIME-Kodierung war bereits korrekt
(`charset="UTF-8"`, Base64, RFC 2047 im Betreff), der Text ist jetzt
orthografisch korrekt.

Neu ist eine geschäftsübliche Anrede: „Frau Franziska Koch" → „Frau Koch".
Gekürzt wird nur bei eindeutiger Zerlegung; bei Namenszusätzen in der Mitte
(„Wrocklage-aus der Fünten") bleibt der Name vollständig. Über alle 6.424
realen Kontakte gilt die Zusicherung: die Anrede ist immer die Anredeform plus
ein zusammenhängendes Namensende — geprüft im Test.

### Blatt VERSAND

Die Datei hatte 29 Tabellenblätter. Neu ist **VERSAND** an Position 2: eine
Live-Ansicht per `QUERY` über `ALL_LEADS`, eine Zeile pro reserviertem Kontakt.
Kein Blatt wurde gelöscht.

### Entwurfserzeugung mit Selbstprüfung

`engine/make_drafts.py` erzeugt die Entwürfe lokal und liest **jede** Datei
zurück (Empfänger, Anrede, Firma im Betreff, Anhang-SHA-256, genau ein Anhang).
Für Batch `HSB-20260826-JORDI-0002`: `PRUEFUNG=PASS`, 100/100.

### X-Unsent ist kein verlässlicher Weg mehr

Recherche-Befund: `X-Unsent: 1` wird von Outlook für Mac ignoriert und im neuen
Outlook für Windows nicht mehr zuverlässig ausgewertet. Der dokumentierte Weg
ist `POST /me/messages` mit Base64-MIME. `engine/graph_drafts.py`
implementiert genau das — ohne jede Send-Aktion im Code. (Auth-Fluss seit
2026-08-27 delegiert statt Anwendungsberechtigung, siehe Nachtrag unten.)

```
APPS_SCRIPT_TESTS = 203/203
PYTHON_TESTS      = 91/91
VERIFIER_SUITE    = PASS
REAL_EXTERNAL_SEND_COUNT = 0
DEPLOY            = clasp push 2026-08-26 18:43, live zurueckgelesen
```

### Offener Punkt: zwei Batches halten 119 Kontakte

`HSB-20260826-JORDI-0001` (94, Shortfall 6) und `HSB-20260826-JORDI-0003` (25)
stammen vom 26.08. gegen 16:06/16:12, also aus dem alten Ablauf vor der
Reparatur. Beide sind `PREPARED`, keiner wurde freigegeben oder versendet.
Zusammen reservieren sie 119 Kontakte und verkleinern damit den Pool für den
nächsten 100er-Batch.

Bewusst nicht aufgeräumt: das Zurücksetzen von `Batch_ID` löscht die Zuordnung
von Nutzerdaten, und es ist von hier aus nicht erkennbar, ob zu 0001 bereits
Entwürfe im Umlauf sind. Entscheidung liegt beim Nutzer.

### Was live verifiziert ist und was nicht

| Pfad | Stand |
|---|---|
| Freigabe/Reservierung (`uiJordi100`) | deployed, live zurückgelesen, Test grün |
| Erzeugung in Apps Script (`uiExportEml`) | Signatur korrigiert, **nur im Test grün** — nicht live durchlaufen |
| Lokale Erzeugung (`make_drafts.py`) | 100/100 Datei für Datei belegt |
| Postfach-Weg (`graph_drafts.py`) | Code fertig, App-Registrierung weiterhin einmalig nötig — seit 2026-08-27 delegiert ohne Admin-Zustimmung (siehe Nachtrag unten) |

Die 100 Entwürfe, die heute vorliegen, stammen aus dem lokalen Lauf.

---

## Reparatur und Abschlussverifikation 2026-08-27

Fortsetzung der am 26.08. abends begonnenen, unfertig liegen gebliebenen
Aenderung an `exportBatchAsEmlZip` (Chunk-Groesse 20→10, ein Teilpaket pro
Serveraufruf statt einer internen Schleife). Root-Cause-Fixes, TDD und eine
unabhaengige, gegnerisch gefuehrte Review (fremder Subagent, kein eigener
Kontext) wurden bis PASS durchgezogen. Kein Push, kein Deploy.

### Behobene Fehlerklassen

1. **Serverseitig unvollstaendige Umstellung.** `exportBatchAsEmlZip` war
   bereits auf "ein Teilpaket pro Aufruf" umgebaut (Chunk 10 statt 20, wegen
   ca. 70 MB Spitzenspeicherbedarf bei Chunk 20 gegenueber ca. 19,5 MB
   gemessenem Base64-Rohumfang bei Chunk 10), aber die generierte
   Buendeldatei `apps_script/HSB_SALES_OS.gs` war nicht neu gebaut worden und
   zeigte noch den alten Stand. `python3 engine/build_single.py` erneut
   ausgefuehrt; seither bei jeder Aenderung an den vier Quelldateien
   wiederholt. `deploy/` bewusst nicht angeruehrt — dort steht weiterhin
   exakt das, was zuletzt tatsaechlich gepusht wurde.
2. **Fehlender Client-seitiger Nachzieh-Mechanismus.** `Sidebar.html` erwartete
   noch das alte Verhalten: ein manueller "Weiter ab X"-Klick pro Teilpaket —
   bei Chunk 10 waeren das bei N=100 neun Klicks gewesen. `emlExport()` ruft
   sich jetzt bei Erfolg automatisch mit dem naechsten Index erneut auf
   (`CLIENT_SEQUENTIAL_ORCHESTRATION`), zeigt echten Fortschritt
   (Paket X von Y) und sammelt alle Paketlinks statt sie zu ueberschreiben.
   Immer nur ein Serveraufruf gleichzeitig pro Batch, per `exportLaufend`
   auch gegen Doppelklick/Parallelaufruf im selben Tab abgesichert.
3. **Fuenf kritische `google.script.run`-Aufrufe ohne Fehlerbehandlung.**
   `uiEnsureColumns`, `uiQualify`, `uiPrepareBatch`, `uiApproveBatch`,
   `uiSetStatus` setzten teils eine Ladeanzeige oder aendern Zustand, hatten
   aber keinen `.withFailureHandler(...)` — ein Plattformfehler (Timeout,
   Ausnahme ausserhalb des serverseitigen try/catch) liess die Anzeige ohne
   erkennbaren Endzustand stehen. Ergaenzt, ebenso bei `uiGetSetupState`,
   `uiGetBatches`, `uiGetDue`, `uiSearch` (informativ, aber derselbe
   Fehlerklasse). Bei `uiSetStatus` setzt der Fehlerfall zusaetzlich die
   abgedunkelte Zeile zurueck, statt sie dauerhaft halbtransparent stehen zu
   lassen.
4. **Wettlaufsituation ohne Sperre in `exportBatchAsEmlZip`.** Die Pruefung
   "Datei vorhanden?" und das Anlegen der ZIP-Datei waren zwei getrennte,
   ungeschuetzte Schritte — anders als jede andere zustandsaendernde Funktion
   in `Actions.gs`. Zwei echte Parallelaufrufe fuer denselben Batch (zwei
   offene Sidebar-Tabs) haetten beide "nicht vorhanden" sehen und zwei
   gleichnamige ZIPs anlegen koennen. Jetzt im selben `LockService`-Muster
   wie `qualifyLeads`/`prepareBatch`/`processInboundEvent`
   (`tryLock(30000)`, Release im `finally`, `LOCK_TIMEOUT` fail-closed mit
   eigener, auf den Drive-Vorgang zutreffender Fehlermeldung statt der
   falsch uebernommenen Sheet-Formulierung).
5. **Test-Stub war ein Scheingruen.** Der Node-Testharness fuer `DriveApp`
   gab bei `getFoldersByName` immer "nicht gefunden" zurueck; jeder Aufruf
   von `getOrCreateFolder_` legte deshalb einen neuen, leeren Ordner an. Der
   bestehende "Wiederholung legt kein zweites ZIP an"-Test pruefte dadurch
   nie echte Persistenz ueber mehrere Aufruf hinweg. Behoben: Ordner werden
   im Stub jetzt wie in echtem Drive nach Namen persistiert.

### Neue/erweiterte Tests

- Arbitrary-N-Nachweis um **N=25 und N=150** fuer JORDI **und** JOEL
  erweitert (zusaetzlich zu 1/17/100).
- Mitten-in-der-Paketfolge-Fehlschlag + gezielter Retry (nur das
  fehlgeschlagene Teilpaket wird nachgelegt, keine Duplikate).
- Verlorene Erfolgsantwort / Reload-Neustart bei Index 0: bereits erzeugte
  Teilpakete werden wiedererkannt statt neu angelegt.
- Batch-Wiederauffindung nach verlorenem Client-Callback: `prepareBatch`
  committet server-seitig, `getBatches` findet ihn nach simuliertem Reload,
  ein zweiter `prepareBatch`-Aufruf mit derselben Batch-ID legt keinen
  zweiten Datensatz an.
- `LockService`-Timeout jetzt auch fuer `exportBatchAsEmlZip` selbst
  nachgewiesen (fail-closed, danach normaler Ablauf nach Freigabe).
- Statische Sidebar-Vertragspruefung: alle elf kritischen
  `google.script.run`-Aufrufe haben nachweislich einen Fehlerhandler; kein
  manueller Klick fuer den Normalfall der Paketfolge; keine veraltete feste
  Paketgroesse mehr im Text.

### Frische Verifikation vom 2026-08-27

| Prüffeld | Befehl | Ergebnis | Exit |
|---|---|---|---|
| Apps-Script-Suite | `node tests/test_apps_script.js` | 258/258, 0 Fehler | 0 |
| Python-Testmatrix | `python3 tests/test_matrix.py` | 91/91, 0 Fehler | 0 |
| Verifier-Suite | `node tests/verifier_suite.js` | VERDICT PASS | 0 |
| Diff-Hygiene | `git diff --check` | sauber | 0 |
| Secret-Scan | `git grep` ueber alle getrackten Dateien | 0 Treffer | — |
| Send-Audit | `grep` auf Sende-Funktionen | nur `dailyDigest` (Empfaenger = eigener Operator) | — |

Geaenderter Umfang: genau vier Dateien (`apps_script/Actions.gs`,
`apps_script/HSB_SALES_OS.gs` als Buendel-Neubau,
`apps_script/Sidebar.html`, `tests/test_apps_script.js`). `deploy/`
unangetastet. Kein Commit, kein Push, kein clasp-Deploy.
`REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0`.

**Unabhaengige Review:** ein frischer, read-only Subagent ohne eigene
Implementierungs-Vorgeschichte hat den vollstaendigen Diff gegnerisch
geprueft. Erste Runde: zwei CRITICAL-Befunde (fehlende Fehlerbehandlung bei
`freigeben`/`uiApproveBatch` und `status`/`uiSetStatus`), ein begleitender
IMPORTANT-Befund (Test-Allowlist unvollstaendig) und drei MINOR-Befunde.
Alle behoben, zweite Runde: **PASS, keine offenen CRITICAL/IMPORTANT
Befunde.**

### Was weiterhin bewusst offen bleibt

- `JORDI_OPERATOR_ACCEPTANCE` bleibt `DEFERRED` — eine echte Anmeldung von
  Jordi bei Power Automate ist ein externer, durch Software nicht
  aufloesbarer Schritt (`EXTERNAL_BLOCKER = USER_MAILBOX_LOGIN`).
  Der EML-/Outlook-native Fallback bleibt unabhaengig davon voll nutzbar.
- Echte Nebenlaeufigkeit zweier tatsaechlich gleichzeitiger Apps-Script-
  Ausfuehrungen bleibt `UNVERIFIED` im Sinn von "beobachtet" — das Design
  stuetzt sich weiterhin fail-closed auf `LockService.getDocumentLock()`;
  im Node-Stub ist echte Parallelitaet nicht herstellbar, nur die
  Sperrlogik selbst ist getestet.
- Sidebar.html besitzt weiterhin keinen ausfuehrbaren Browser-Test, nur
  statische Text-/Regex-Pruefung gegen die Datei — dokumentiert, kein neuer
  Mangel.

---

## Post-Send-Reconciliation — Nachtrag 2026-08-27

Eng abgegrenzte Nachlieferung zum obigen Stand: Beweis der Reconciliation
nach einem echten Versand (PREPARED != DRAFTED != SENT), ohne die bereits
verifizierten Teile erneut zu pruefen.

### Root Cause

`processInboundEvent` kannte im Dispatch kein `event_type: 'SENT'` (nur
REPLY/POSITIVE_REPLY/NEGATIVE_REPLY/HARD_BOUNCE/SOFT_BOUNCE/OPT_OUT). Ein
echter Sendenachweis wurde als Event protokolliert, aenderte aber nie
`Send_Status`/`Sent_At`/`Batch_Status`. Die `Sent_At`-Spalte im BATCHES-Blatt
war seit Anlage des Sheets vollstaendig tot — nirgends beschrieben.

### Fix (TDD, minimal, bestehende Architektur)

1. **Korrelation nur ueber starke, bewegungsstabile Evidenz.** Fuer
   `event_type === 'SENT'` zaehlt ausschliesslich eine explizite Lead-ID oder
   `Internet_Message_ID` (RFC-5322 Message-ID, Teil des MIME-Inhalts).
   `Outlook_Message_ID`/`Draft_ID` allein zaehlen fuer SENT nicht (Microsoft
   dokumentiert, dass die normale Element-ID sich beim Verschieben
   Drafts → Sent Items aendern kann) und die E-Mail-Adresse allein auch
   nicht (beweist keinen bestimmten Versand). Alles Schwaechere geht
   fail-closed nach `NEEDS_REVIEW`.
2. **Exactly-once zusaetzlich zur bestehenden Event-/Message-ID-Dedup.**
   Ein zweites, technisch anderes Sendesignal (andere Event-/Message-ID,
   z. B. erneuter Automatisierungslauf) fuer einen bereits als `sent`
   markierten Lead erzeugt `ALREADY_SENT_IGNORED` statt einer zweiten
   Statusaenderung/Aktivitaet.
3. **Neue Funktion `stampBatchSentAt_`.** Stempelt `Sent_At` im
   BATCHES-Blatt genau einmal je Batch (erster bestaetigter Sendenachweis).
   Die Status-Spalte des Batches bleibt bewusst unangetastet:
   `activeBatchLeadIds_` behandelt nur `SENT`/`CANCELLED` als
   abgeschlossen — ein verfrueht auf `SENT` gesetzter Batch wuerde seine
   noch nicht bestaetigten Leads faelschlich fuer einen neuen Batch
   freigeben.
4. **Fund der unabhaengigen Review, sofort behoben:** Die bestehende
   generische Dedup-Pruefung verglich `event_id`/`message_id` gegen JEDE
   fruehere `INBOUND_EVENTS`-Zeile unabhaengig von deren Status. Eine
   zunaechst unklare `NEEDS_REVIEW`-Zeile (z. B. weil dem Lead noch keine
   `Internet_Message_ID` zugeordnet war) blockierte dadurch einen spaeter —
   nach Nachtrag der `Internet_Message_ID` — tatsaechlich zuordenbaren
   Sendenachweis dauerhaft als „Duplikat"; der Nachweis ging still
   verloren. Behoben: Die Status-Spalte wird jetzt mitgelesen, nur Zeilen
   mit einem terminalen Status (alles ausser `NEEDS_REVIEW`) zaehlen als
   echtes Duplikat.

### Neue Tests

`testPostSendReconciliation` (tests/test_apps_script.js) deckt ab: echter
Sendenachweis ueber `Internet_Message_ID` setzt `Send_Status=sent` +
`Sent_At` + `Batch_Status=SENT` + Batch-`Sent_At`; Replay derselben
Message-ID = generische Dedup; zweites technisches Sendesignal fuer
bereits gesendeten Lead = `ALREADY_SENT_IGNORED`, null zusaetzliche
Aktivitaeten; reine `Outlook_Message_ID` und reine E-Mail-Adresse reichen
fuer SENT nicht (`NEEDS_REVIEW`); EML-Export impliziert niemals SENT;
Retry nach nachtraeglicher `Internet_Message_ID`-Zuordnung wird korrekt
verarbeitet statt verschluckt.

### Frische Verifikation

| Prüffeld | Befehl | Ergebnis | Exit |
|---|---|---|---|
| Apps-Script-Suite | `node tests/test_apps_script.js` | 276/276, 0 Fehler | 0 |
| Python-Testmatrix | `python3 tests/test_matrix.py` | 91/91, 0 Fehler | 0 |
| Verifier-Suite | `node tests/verifier_suite.js` | VERDICT PASS | 0 |
| Diff-Hygiene | `git diff --check` | sauber | 0 |
| Send-Audit | `grep sendEmail` | nur `dailyDigest` (Empfaenger = eigener Operator) | — |

Geaenderter Umfang gegenueber dem Stand oben: `apps_script/Actions.gs`,
`apps_script/HSB_SALES_OS.gs` (Buendel-Neubau), `tests/test_apps_script.js`
sowie diese Datei. `apps_script/Sidebar.html` unveraendert in dieser
Nachlieferung. `deploy/` unangetastet. HEAD unveraendert bei
`b5f73ab8abe2883db42d07dae4b8d96defd9b28a`. Kein Commit, kein Push, kein
clasp-Deploy. `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0`.

**Unabhaengige Reviews:** `validation-auditor` (read-only) hat alle acht
gepruefte Behauptungen als VERIFIED bestaetigt. `implementation-reviewer`
(read-only, kein Bash-Zugriff, rein per Lesen/Grep) meldete im ersten
Durchlauf FAIL wegen des oben unter Punkt 4 beschriebenen Dedup-Fundes —
behoben, Testfall ergaenzt, Gesamtsuite erneut GREEN. Ein zweiter Punkt des
Reviewers (die Staerke der SENT-Korrelation haengt letztlich davon ab, dass
die externe Automatisierung selbst niemals eine aus einer instabilen ID
abgeleitete Lead-ID einschleust) wurde vom Reviewer selbst ausdruecklich
als „Beleglücke, kein bestaetigter Defekt" eingestuft — das liegt
ausserhalb dieses Repos (kein interner SENT-Event-Erzeuger vorhanden, nur
ein Passthrough fuer ein extern geliefertes Event-Objekt) und ist hier nur
dokumentiert, nicht code-seitig loesbar.

### Was weiterhin bewusst offen bleibt

- Es existiert **keine lebende Power-Automate/Graph-„Sent"-Trigger-
  Integration**, die echte `Internet_Message_ID`-Werte bei einem
  tatsaechlichen Versand an das System liefert. Der Reconciliation-Pfad ist
  software-seitig durchgaengig mit synthetischen Testdaten bewiesen; ein
  echter Live-Trigger aus Outlook/Graph ist nicht konfiguriert. Externer
  Integrationsblocker, kein Softwaredefekt.
- Die Korrektheit der von aussen gelieferten `lead_id`/`message_id`-Werte
  liegt ausserhalb der Kontrolle dieses Repos (siehe Review-Punkt oben).

---

## Graph-Auth-Vereinfachung — Nachtrag 2026-08-27

Frage: Ist die Einrichtung von `engine/graph_drafts.py` ohne Admin-Zugang
moeglich? Antwort: teilweise, und der bisherige Code nutzte unnoetig genau
den Teil, der immer einen Admin braucht.

### Befund

`token_holen()` nutzte den Client-Credentials-Fluss (`grant_type:
client_credentials`, Scope `.default`) — das ist eine *Anwendungsberechtigung*.
Application-Permissions wirken unbeaufsichtigt und tenant-weit; Microsoft
laesst sie deshalb grundsaetzlich nur von einer Person mit einer Entra-
Admin-Rolle freischalten (Global Administrator, Privileged Role
Administrator, Application Administrator, Cloud Application Administrator).
Das ist Sicherheitsdesign, kein Konfigurationsdetail, und war fuer diesen
Berechtigungstyp nicht zu umgehen.

Das Werkzeug braucht aber gar keine tenant-weite Wirkung — jede Person legt
ohnehin nur Entwuerfe im eigenen Postfach an. Dafuer reicht eine *delegierte*
Berechtigung mit Self-Consent der angemeldeten Person selbst.

### Aenderung

`engine/graph_drafts.py`: Client-Credentials-Fluss ersetzt durch einen
delegierten Geraetecode-Fluss (OAuth Device Authorization Grant) mit lokalem
Refresh-Token-Cache (`~/.hsb_graph_token_cache.json`, `chmod 600`):

- Erster Lauf: Werkzeug zeigt Anmelde-URL + Code, Person meldet sich selbst
  im Browser an und stimmt selbst zu (Self-Consent) — keine
  Administratorbeteiligung, sofern der Tenant Nutzerzustimmung fuer
  delegierte Berechtigungen nicht generell gesperrt hat.
- Spaetere Laeufe: stiller Refresh-Versuch mit dem gecachten Token, nur bei
  Fehlschlag erneute interaktive Anmeldung.
- `HSB_GRAPH_CLIENT_SECRET` entfaellt vollstaendig — delegierte Public-
  Client-Registrierungen brauchen kein Geheimnis.
- Alle Graph-Aufrufe laufen jetzt gegen `/me/...` statt `/users/{postfach}/...`;
  `identitaet_pruefen()` (vormals `postfach_pruefen()`) prueft weiterhin
  fail-closed, dass die angemeldete Person zum erwarteten Postfach passt.

Damit lautet die ehrliche Antwort auf die Ausgangsfrage: Die App-
Registrierung selbst kann jede Person mit gewoehnlichem Nutzerkonto anlegen
(Standardeinstellung, kein Admin). Ob die anschliessende Selbstzustimmung
ohne Admin durchgeht, zeigt erst der echte Anmeldeversuch — das ist jetzt
der einzige verbleibende Unsicherheitsfaktor, nicht mehr eine von vornherein
sichere Anforderung an einen Administrator.

### Neue Tests

`tests/test_graph_drafts.py` (neu, 19 Assertionen, kein echter Netzwerk-
zugriff): Cache-leer -> Geraetecode; gueltiges Refresh-Token umgeht die
Geraetecode-Anmeldung (kein Login-Zwang bei jedem Lauf); ungueltiges
Refresh-Token faellt genau einmal auf Geraetecode zurueck; kein
`HSB_GRAPH_CLIENT_SECRET` mehr erforderlich; Polling-Zustandsmaschine
(`authorization_pending` -> Erfolg, `authorization_declined` -> fail-closed
Abbruch ohne Endlosschleife); `identitaet_pruefen` akzeptiert/verweigert
`/me` korrekt; `entwurf_anlegen` ruft nachweislich `/me/messages` auf.

### Verifikation

| Prüffeld | Befehl | Ergebnis |
|---|---|---|
| Neue Auth-Tests | `python3 tests/test_graph_drafts.py` | 19/19 PASS |
| Python-Testmatrix (unveraendert betroffen) | `python3 tests/test_matrix.py` | 91/91 PASS |
| Apps-Script-Suite (nicht betroffen) | `node tests/test_apps_script.js` | 277/277 PASS |
| Verifier-Suite (nicht betroffen) | `node tests/verifier_suite.js` | VERDICT PASS |
| Diff-Hygiene | `git diff --check` | sauber |

Geaenderter Umfang: `engine/graph_drafts.py`, `tests/test_graph_drafts.py`
(neu), `README_OPERATING.md`, diese Datei. Kein Commit, kein Push, kein
clasp-Deploy. `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` (dieses Werkzeug legt
ohnehin nur Entwuerfe an, nie einen Versand).

### Was weiterhin offen bleibt

- Ob der HSB-Tenant Self-Consent fuer delegierte Berechtigungen erlaubt,
  ist von hier aus nicht pruefbar — nur der echte Anmeldeversuch zeigt es.
  Zeigt Entra „Genehmigung durch Administrator erforderlich", ist das ein
  echter, dann konkret benennbarer externer Blocker (wer genau freigeben
  muss), kein Softwaredefekt.
- Die App-Registrierung selbst (Client-ID/Tenant-ID) ist weiterhin einmalig
  in Entra ID anzulegen — das ist Konfiguration, kein Code.

---

## Power Automate — beide Konten live verifiziert, 2026-09-04

Fortsetzung von „Power Automate — verifizierter Stand" oben: statt eines
Testentwurfs ans eigene Postfach jetzt zwei echte Entwürfe an echte
Prospektadressen, für beide Owner-Konten getrennt, mit echten Draft-IDs.

### Zwei Flows statt einem

```
JOEL_FLOW_ID        = 137601e8-7369-4a74-9564-959f1551e48d ("HSB Sales OS Draft Adapter")
JOEL_TRIGGER         = Request/Http (Premium — bei j-cherino vorhanden)
JOEL_CONNECTION      = shared-office365-819bd473 (j-cherino@hsb-boden.de)
JOEL_STATE           = Started

JORDI_FLOW_ID        = 47ee3d7a-626c-4fff-9e16-6d938949e4bd ("HSB Sales OS Draft Adapter (Jordi)")
JORDI_TRIGGER        = Button (Free-Tier — j-post hat KEINE Premium-Lizenz)
JORDI_CONNECTION     = 3d152ea7ddb24e9286fe006cb9f5069b (j-post@hsb-boden.de)
JORDI_STATE          = Started
```

Beide Flows: nur `DraftEmail`, keine Send-Action. `SEND_ACTION_PRESENT = false`
gilt weiterhin für beide.

### Warum zwei verschiedene Flow-Definitionen nötig waren

1. **Connections sind nicht personenübergreifend nutzbar.** Ein Flow, den
   Person A erstellt hat, kann Person B nicht per `update_flow` auf ihre
   eigene Connection umbiegen — `ConnectionAuthorizationFailed`. Jeder Owner
   braucht seinen eigenen, unter der eigenen Identität erstellten Flow.
2. **j-post hat kein Power-Automate-Premium.** Der `Request/Http`-Trigger-
   *Typ selbst* ist premium-pflichtig (nicht nur einzelne Premium-
   Connectoren) — `MissingAdequateQuotaPolicy` beim Aktivieren, Flow bleibt
   `Suspended`/`BillingConsumption`. Fix: Trigger-Kind auf `Button`
   (Free-Tier) statt `Request`/`Http`. Einmal mit einer Premium-Aktion
   angelegte Flow-Instanzen bleiben dauerhaft markiert — Löschen und mit der
   korrigierten Definition neu anlegen war nötig, ein nachträgliches
   `update_flow` genügte nicht.
3. **Kein `Http`-Download-Trick für Jordi möglich.** Der Joel-Flow lädt den
   Flyer serverseitig per generischer `Http`-Aktion von der HSB-Website
   (`Get_Flyer` → `@body('Get_Flyer')?['$content']`) — das ist selbst
   wieder ein Premium-Connector. Für Jordis Flow kommen die Flyer-Bytes
   deshalb direkt Base64-kodiert im Trigger-Body (`attachmentContentBytes`),
   wie ursprünglich bei `graph_drafts.py`.
4. **SAS-Callback-URL ist für `Button`-Trigger gesperrt.** `listCallbackUrl`
   liefert `ListCallbackUrlOperationBlocked`. Für Jordis Flow bleibt nur der
   authentifizierte Logic-Flows-Connector-Endpunkt (siehe unten) — für
   Joels `Request/Http`-Flow funktioniert die SAS-URL dagegen.

### Direkter Aufrufweg (umgeht das MCP-Tool-Limit bei großen Anhängen)

`mcp__plugin_power-automate_flowagent__run_flow` verlangt den Trigger-Body
als Werkzeugparameter — bei ~2 MB Base64-Flyer nicht praktikabel als
einzelner Tool-Aufruf. Reproduzierbarer Weg stattdessen:

```
1. GET  {PPAPI_BASE}/powerautomate/apis/shared_logicflows?api-version=1
   Token-Ressource: https://service.powerapps.com/
   -> properties.primaryRuntimeUrl entnehmen (NICHT Top-Level - Bug in einer
      ersten Skriptfassung, siehe engine/pa_direct_drafts.py Git-Historie)

2. POST {primaryRuntimeUrl}/{flowId}/triggers/manual/run?api-version=2016-11-01
   Token-Ressource: https://apihub.azure.com  (OHNE Trailing-Slash — mit
   Trailing-Slash: "Audience ... is not found in list of allowed audiences")
   Body: das Trigger-Payload-JSON
```

Implementiert und lokal verifiziert in `engine/pa_direct_drafts.py`
(`_runtime_url()`, `entwurf_anlegen()`, `payload_fuer_lead()`). Das Skript
selbst führt noch keine Batch-Schleife gegen das Sheet aus — es stellt die
geprüften Bausteine bereit; eine Schleife über `READY_CANDIDATES` ist
bewusst noch nicht gebaut (siehe „Nächster Schritt" unten).

### Frische Verifikation vom 2026-09-04

| Prüffeld | Befehl/Aufruf | Ergebnis |
|---|---|---|
| Joel-Flow, Testentwurf an echten Lead | `run_flow` (MCP) gegen `137601e8...`, Lead `HSB-20260708-03307` | `status=DRAFTED`, `draftId=AAMkADkyNjcwMzZjLTg1NzItNDVjNS04NDA5LTA0MjE3NjNiYjUzMQBG...` |
| Jordi-Flow, Testentwurf an echten Lead (curl, Logic-Flows-Endpunkt) | Lead `HSB-20260708-03307` | `status=DRAFTED`, `draftId=AAMkADQzMGFmYWE4LTk2YTItNDlkOS05ODgwLWNkNTdhZDdmMTVlNABG...` |
| `engine/pa_direct_drafts.py --pruefen` | `python3 engine/pa_direct_drafts.py --owner JORDI --batch HSB-20260826-JORDI-0002 --pruefen` | Identität + Runtime-URL OK, exit 0 |
| `engine/pa_direct_drafts.py`, echter zweiter Testlead über die Skript-Bausteine | Lead `HSB-20260708-03308` (Hägele + Partner) | `status=DRAFTED`, `draftId=AAMkADQzMGFmYWE4LTk2YTItNDlkOS05ODgwLWNkNTdhZDdmMTVlNABG...` (anderer Suffix) |

Drei von 100 Leads aus Batch `HSB-20260826-JORDI-0002` haben jetzt echte
Entwürfe (die zwei oben plus der allererste Konnektivitätstest an
j-cherinos eigenes Postfach). `Draft_ID`/`Drafted_At` im Sheet sind dafür
noch **nicht** zurückgeschrieben — offener Punkt, siehe unten.

### Bekannter Rest — ungefährlich, aber unaufgeräumt

`e0a2a6ec-cd27-41cf-853e-39fd44d408c0` ("HSB Sales OS Draft Adapter
(Jordi)", Duplikat-Name) ist eine verworfene Zwischenversion: von
j-cherino angelegt, Connection nie korrekt auf j-post verdrahtet, Zustand
`Stopped`. Braucht zum Löschen eine erneute Anmeldung als j-cherino —
bewusst nicht gemacht, weil der Flow inaktiv ist und niemanden stört.
Löschen, sobald ohnehin wieder als j-cherino angemeldet.

### Nächster Schritt

Batch-Schleife über die verbleibenden 97 Leads in `HSB-20260826-JORDI-0002`
bauen (liest `READY_CANDIDATES`, ruft `pa_direct_drafts.entwurf_anlegen()`
je Zeile, schreibt `Draft_ID`/`Drafted_At` zurück) — noch nicht begonnen,
ausdrücklich auf Nutzer-Freigabe wartend (echte Anschreiben an 97 weitere
reale Firmenkontakte). Kein automatischer Versand in keinem Szenario.

---

## Apps-Script-Sidebar zeigt „Berechtigung erforderlich" — Diagnose 2026-09-04

Live-Symptom (Screenshot, Jordi-Tab): Klick auf „100 freigeben & Entwürfe
erzeugen" zeigt eine Fehler-Karte „Für die Ausführung dieser Aktion ist eine
Berechtigung erforderlich".

### Befund 1 — Drift zwischen git und dem live gebundenen Skript

`clasp pull` gegen den echten gebundenen Stand (Script-ID
`1Xl6xkMTyn3Hu6UvBoX7gVrdppuyRal04NH6Ei16hnz_Pfuq-JWmh9U4c`) zeigte eine
Datei, die **nie in git existierte**: `HSB_DraftAdapter.gs.js` (682 Zeilen,
offenbar direkt im Apps-Script-Web-Editor angelegt, nie per `clasp push` aus
diesem Repo ausgerollt, nie zurückgeholt). Jetzt nachträglich gesichert
(Commit `def72ec`), als reiner Fund — **nicht bereinigt**. `HSB_SALES_OS.js`
und `Sidebar.html` sind dagegen live byte-identisch zum lokalen Stand.

Ebenfalls live bereits aktiv, lokal vorher unversioniert: die Manifest-
Erweiterung um `script.external_request` (nötig, weil `HSB_DraftAdapter.gs.js`
`UrlFetchApp.fetch()` gegen eine externe Domain aufruft) und die
Selbsttest-Funktion `HSB_AdapterSelbsttest.gs`.

### Befund 2 — wahrscheinliche Ursache des Fehlers: fehlende Re-Autorisierung

Eine neu hinzugefügte OAuth-Scope (`script.external_request`) verlangt von
**jeder Person**, die das Skript bereits vorher autorisiert hatte, eine
erneute, explizite Zustimmung — Google erzwingt das serverseitig, keine
Code-Änderung umgeht das. Wird eine Server-Funktion aus einer Sidebar/Karte
per `google.script.run` aufgerufen, **kann der Consent-Dialog dort nicht
erscheinen** (iframe-Einschränkung) — die Aktion schlägt statt dessen mit
genau der beobachteten generischen Meldung fehl. Das erklärt das Symptom,
unabhängig vom Code-Bug unten.

**Fix ist keine Code-Änderung, sondern eine einmalige manuelle Aktion pro
betroffener Person** (hier: Jordi): Google Sheet → Erweiterungen → Apps
Script → im Editor irgendeine Funktion direkt über „Ausführen" starten (z. B.
`preflight()`) → im erscheinenden echten Vollbild-Consent-Dialog die neuen
Berechtigungen bestätigen. Danach sollte die Sidebar-Karte wieder
funktionieren, *sofern* der Code-Bug unten ebenfalls behoben ist.

### Befund 3 — echter Code-Bug: Payload passt nicht zu den verifizierten Flows (kritisch)

`HSB_DraftAdapter.gs.js` (`createDraftsForBatch`) baut den Trigger-Payload
so:

```js
var payload = {
  leadId: lead.Lead_ID,
  batchId: batchId,
  to: lead['E-Mail'] || lead.Email,
  subject: rendered.subject,
  bodyHtml: textToHtml_(rendered.body),
  attachments: [flyerAttachment_(owner)]   // <- Array mit {Name, ContentBytes}
};
```

Beide oben verifizierten Flows erwarten aber **flache** Felder, nicht das
Array `attachments`:

- Jordi-Flow (`47ee3d7a-...`, Button/Free-Tier): `attachmentName` +
  `attachmentContentBytes` als eigene Top-Level-Strings.
- Joel-Flow (`137601e8-...`, Request/Http): `flyerUrl` (der Flow lädt den
  Flyer selbst per HTTP-Aktion) + `attachmentName` — `attachmentContentBytes`
  wird dort komplett ignoriert.

Mit dem aktuellen Payload liefe `Draft_an_email_message` in beiden Flows mit
leerem `attachmentName`/`attachmentContentBytes` (bzw. leerem `flyerUrl` bei
Joel) — der Entwurf würde vermutlich ohne Flyer-Anhang erzeugt oder ganz
fehlschlagen. **Noch nicht live gegen einen echten Batch getestet, weil
Befund 2 das ohnehin blockiert** — die Reihenfolge zum Beheben ist also:
zuerst Befund 3 fixen, dann Re-Autorisierung (Befund 2), dann erst
`entwurfTesten()` versuchen.

### Befund 4 — Datei ist komplett doppelt eingefügt (kein Crash, aber Code-Leiche)

`HSB_DraftAdapter.gs.js` enthält denselben Inhalt **zweimal hintereinander**
(Zeilen 1–342 und 343–683 sind identisch — vermutlich ein Copy-Paste-Fehler
im Web-Editor, ganzer Dateiinhalt beim Bearbeiten erneut angehängt statt
ersetzt). `var`- und `function`-Redeklaration ist in Apps Script (V8) kein
Syntaxfehler (letzte Deklaration gewinnt), verursacht also nicht den
beobachteten Fehler — aber es ist tote, verwirrende Doppelung, die vor jeder
weiteren Änderung entfernt gehört.

### Bewusst noch nicht gemacht

- **Keine Korrektur gepusht.** Diese Diagnose ist die Grundlage für eine
  separat vorbereitete Korrekturanweisung (an ChatGPT gerichtet, siehe
  Chat-Verlauf des Sessions oben) — bewusst nicht selbst durchgeführt, auf
  ausdrücklichen Wunsch des Nutzers.
- **Skripteigenschaften nicht verifiziert.** `preflight()` prüft u. a.
  `HSB_ADAPTER_URL_JORDI`, `HSB_ADAPTER_URL_JOEL`, `HSB_ACTIVE_BATCH_ID` —
  ob diese drei Properties tatsächlich gesetzt sind, ist von hier aus nicht
  einsehbar (kein Lesezugriff auf Script Properties ohne Skriptausführung).
  Muss vor Ort geprüft werden (Apps-Script-Editor → Projekteinstellungen →
  Skripteigenschaften) oder durch Ausführen von `preflight()` nach der
  Re-Autorisierung.
