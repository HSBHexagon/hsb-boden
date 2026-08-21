# Installation — einmalig, ca. 10 Minuten

Die Oberfläche läuft als Apps Script direkt im Google Sheet. Kein Server,
keine Domain, kein Admin, keine App-Registrierung.

---

## 1. Apps Script anlegen

1. Sheet öffnen:
   <https://docs.google.com/spreadsheets/d/1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg/edit>
2. Menü **Erweiterungen → Apps Script**
3. Die vorhandene Datei `Code.gs` leeren

## 2. Dateien einfügen

Aus `apps_script/` je eine Datei im Editor anlegen und den Inhalt einfügen:

| Im Editor anlegen | Typ | Quelle |
|---|---|---|
| `Config` | Script | `apps_script/Config.gs` |
| `Engine` | Script | `apps_script/Engine.gs` |
| `Actions` | Script | `apps_script/Actions.gs` |
| `Code` | Script | `apps_script/Code.gs` |
| `Sidebar` | **HTML** | `apps_script/Sidebar.html` |

> `Sidebar` muss als **HTML-Datei** angelegt werden (Plus-Symbol → HTML),
> nicht als Script.

Speichern.

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
