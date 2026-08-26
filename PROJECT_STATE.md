# HSB Sales OS — kanonischer Projektstatus

Diese Datei ist die **eine** Kurzwahrheit über den Zustand des Systems.
Bei Widerspruch zu älteren Dokumenten gilt diese Datei, für Live-Zahlen das
Google Sheet.

```
PROJECT = HSB Sales OS
STATUS  = PASS_WITH_DEFERRED_JORDI_OPERATOR_ACCEPTANCE
DATE    = 2026-08-23
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
ist `POST /users/{id}/messages` mit Base64-MIME. `engine/graph_drafts.py`
implementiert genau das — ohne jede Send-Aktion im Code.

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
| Postfach-Weg (`graph_drafts.py`) | Code fertig, ohne App-Registrierung nicht lauffähig |

Die 100 Entwürfe, die heute vorliegen, stammen aus dem lokalen Lauf.
