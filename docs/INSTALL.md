# Installation

Die Oberfläche läuft als Apps Script direkt im Google Sheet. Kein Server,
keine Domain, kein Admin, keine App-Registrierung.

Zwei Wege — **Weg A ist der kürzere.**

---

## Weg A: automatisch per clasp (empfohlen)

`clasp` ist bereits installiert (`@google/clasp` 3.3.0, offizielles
Google-Paket).

**Zwei einmalige Schritte im Browser — nur du kannst sie machen:**

1. **Apps Script API einschalten**
   <https://script.google.com/home/usersettings> → Schalter
   „Google Apps Script API" auf **AN**

2. **Anmelden**
   ```bash
   clasp login
   ```
   Öffnet den Google-Anmeldedialog. Nimm das Konto, dem das Sheet gehört.

**Danach genügt ein Befehl:**

```bash
cd ~/KI-System/02_Projects/active/hsb-sales-os
./deploy.sh
```

Das Skript bündelt die Quelldateien, legt beim ersten Lauf ein an das Sheet
gebundenes Apps-Script-Projekt an und lädt Code plus Oberfläche hoch. Jeder
weitere Lauf aktualisiert nur.

Anschließend im Browser: Sheet neu laden → Menü **HSB Sales OS** →
**Spalten prüfen / ergänzen** → **Flyer-Pruefung** → **Sales OS öffnen**.

> Warum diese zwei Schritte nicht automatisierbar sind: Beide sind
> OAuth-Vorgänge mit deinen Zugangsdaten. Die gehören dir, nicht dem Agenten.

---

## Weg B: manuell einfügen (ca. 10 Minuten)

Falls du die Apps Script API nicht einschalten willst.

## 1. Apps Script anlegen

1. Sheet öffnen:
   <https://docs.google.com/spreadsheets/d/1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg/edit>
2. Menü **Erweiterungen → Apps Script**
3. Die vorhandene Datei `Code.gs` leeren

## 2. Zwei Dateien einfügen

Nur zwei Einfügevorgänge nötig — die vier Script-Teile sind gebündelt:

| Im Editor | Typ | Quelle |
|---|---|---|
| `Code` (die vorhandene Datei) | Script | `apps_script/HSB_SALES_OS.gs` |
| `Sidebar` | **HTML** | `apps_script/Sidebar.html` |

1. Inhalt von `HSB_SALES_OS.gs` kopieren, in `Code.gs` einfügen (vorher alles
   markieren und ersetzen).
2. Plus-Symbol → **HTML** → Name `Sidebar` (ohne `.html`) → Inhalt von
   `Sidebar.html` einfügen.
3. Speichern (⌘S).

> Der Name muss exakt `Sidebar` lauten und der Typ **HTML** sein — sonst
> findet `HtmlService.createHtmlOutputFromFile('Sidebar')` die Datei nicht.

Die gebündelte Datei ist mit derselben Testsuite geprüft wie die
Einzeldateien (62/62). Wer lieber vier getrennte Dateien pflegt, kann
stattdessen `Config.gs`, `Engine.gs`, `Actions.gs` und `Code.gs` einzeln
anlegen — die Reihenfolge spielt keine Rolle, Apps Script teilt sich einen
gemeinsamen Namensraum.

## 3. Berechtigungen erteilen

1. Im Apps-Script-Editor Funktion `onOpen` wählen → **Ausführen**
2. Google fragt nach Berechtigungen → **Zulassen**
   - Tabellen lesen/schreiben — für das CRM
   - Drive lesen — um den Flyer zu holen und zu prüfen
   - E-Mail senden — nur für die tägliche Erinnerung an dich selbst

Es wird dabei **keine** E-Mail an Interessenten versendet.

## 4. Spalten ergänzen

Sheet neu laden → Menü **HSB Sales OS → Spalten prüfen / ergänzen**

Ergänzt zwölf Spalten (`Legal_Basis`, `Suppressed`, `Batch_Status`,
`Prepared_At`, `Draft_ID`, `Drafted_At`, `Approved_At`, `Outlook_Message_ID`,
`Internet_Message_ID`, `Conversation_ID`, `Last_Reply_At`, `Last_Error`).

Bestehende Spalten werden nicht angefasst. `Legal_Basis` wird fail-closed auf
`UNKNOWN` vorbelegt — bewusst, damit ohne geprüfte Rechtsgrundlage nichts
versendet werden kann.

Der Schritt ist idempotent: mehrfaches Ausführen ändert nichts mehr.

## 5. Flyer-Prüfung

Menü **HSB Sales OS → Flyer-Pruefung (Asset-Gate)**

Erwartet:

```
OK   JORDI: HSB-Flyer-Jordi-Post_FINAL.pdf
OK   JOEL: HSB-Flyer-Joel-Cherino_FINAL.pdf
```

Bei `FAIL` wurde der Flyer in Drive verändert. Dann **nicht senden**, sondern
den Master wiederherstellen.

## 6. Fertig

**HSB Sales OS → Sales OS öffnen** startet die Seitenleiste.

---

## Optional: Zugriff für Jordi

Sheet für `j-post@hsb-boden.de` freigeben (Bearbeiter). Beide Flyer-Dateien in
Drive müssen für ihn mindestens **lesbar** sein, sonst schlägt das Asset-Gate
bei ihm fehl.

Hat Jordi kein Google-Konto, bleibt der Weg: Joel bereitet den Batch vor,
lädt das ZIP herunter und übergibt es.

---

## Optional: lokale Werkzeuge (nur Joel, mit Mac)

```bash
cd ~/KI-System/02_Projects/active/hsb-sales-os/engine

python3 hsb.py status                              # Datenlage
python3 hsb.py gate                                # visuelles PDF-Gate
python3 hsb.py inventory --write                   # Flyer-Inventur per Hash
python3 hsb.py prepare --owner JORDI --count 100   # Trockenlauf
python3 hsb.py prepare --owner JOEL --count 25 --write   # EML erzeugen

cd ../tests && python3 test_matrix.py              # Testmatrix
```

Voraussetzungen: Python 3, `openpyxl`, `Pillow`, `poppler` (`brew install poppler`).

Der lokale Snapshot wird per Google-Workspace-MCP erzeugt
(`export_file`, Format `xlsx`, Ziel `data/`). Das Sheet bleibt System of Record.

---

## Vorab geprüfte Voraussetzungen (2026-08-21)

Diese Punkte sind bereits verifiziert — sie können beim Einbau nicht mehr
schiefgehen:

| Voraussetzung | Ergebnis | Wie geprüft |
|---|---|---|
| Sheet lesbar | **OK** | 6.425 Zeilen, 44 Spalten, 21 Tabs gelesen |
| Sheet schreibbar | **OK** | Testtab angelegt, beschrieben, zurückgelesen, gelöscht |
| Flyer in Drive erreichbar | **OK** | Beide Dateien heruntergeladen |
| Flyer-Bytes korrekt | **OK** | SHA-256 beider Dateien stimmt exakt |
| Konto mit Vollzugriff | **OK** | `cherinojoel` |

Nicht vorab prüfbar, weil es das installierte Skript braucht:

- Laufzeit beim Erzeugen vieler Entwürfe unter echten Google-Kontingenten
- `DriveApp`-Zugriff aus dem Skriptkontext heraus (Berechtigungsdialog)

**Deshalb: erster Lauf mit N = 5.** Wenn fünf Entwürfe sauber im
Outlook-Entwurfsordner landen, ist der Weg bewiesen und die Menge nur noch
eine Zahl im Feld.

## Warum zwei Schritte bei dir bleiben

| Weg | Zustand |
|---|---|
| Sheets-API direkt | Zu. Spaltenanlage scheitert an Rastergrenzen (`Max columns: 44`), und ein Apps-Script-Projekt lässt sich darüber ohnehin nicht anlegen. |
| **clasp** | **Offen** — installiert und vorbereitet. Fehlen nur API-Schalter und `clasp login`. |
| Browser-Automatisierung | Zu, solange die Chrome-Erweiterung nicht verbunden ist. |

Beide verbleibenden Schritte sind OAuth-Vorgänge mit deinen Zugangsdaten.
Die macht der Nutzer selbst — das ist eine feste Regel, keine technische
Einschränkung.
