# HSB Sales OS — Bedienung

Für Jordi und Joel. Kein Terminal, kein Mac, keine Installation nötig.

---

## Wo du nachsiehst, was rausgegangen ist

Ein Blatt: **VERSAND**. Es steht ganz vorn in der Datei und aktualisiert sich
selbst. Eine Zeile pro vorbereitetem Kontakt, mit Firma, Ansprechpartner,
E-Mail, Verantwortlichem, **Rechtsgrundlage**, **Versandfreigabe**,
Entwurfsdatum, Versanddatum und Antwort. Die beiden fettgedruckten Spalten
sagen dir auf einen Blick, ob ein Kontakt überhaupt angeschrieben werden darf.

Die übrigen Blätter bleiben als Arbeitsstände erhalten, werden im Alltag aber
nicht mehr gebraucht.

Eine Einschränkung, die du kennen musst: **„Versendet am" kann das System nicht
messen.** Gesendet wird von Hand in Outlook, und auf dem Prospekt-Pfad gibt es
systemweit keine Send-Aktion — das ist das zentrale Sicherheitsgate. Die Spalte
ist deshalb eine Bestätigung, die gesetzt wird, kein Messwert.

---

## Der tägliche Ablauf

**Jordi will heute 100 anschreiben:**

1. Google Sheet öffnen → Menü **HSB Sales OS → Seitenleiste öffnen**
2. Absender **Jordi** wählen
3. Oben **100 freigeben & Entwürfe erzeugen** klicken

Der Vorgang läuft in zwei Stufen: zuerst die Freigabe und die Reservierung von
exakt 100 Kontakten — das dauert Sekunden. Danach holt die Seitenleiste die
Entwürfe **automatisch nacheinander** in kleinen Paketen nach, ohne dass du
klicken musst. Diese Trennung ist notwendig: 100 Mails mit je 1,5 MB Anhang
ergeben rund 150 MB, und Apps Script bricht nach sechs Minuten ab. Vorher lief
beides in einem Aufruf, was den Knopf zuverlässig scheitern ließ.

Schlägt ein Teilpaket fehl (z. B. Zeitüberschreitung), stoppt die Seitenleiste
und zeigt **„Vorgang sicher erneut versuchen"** — ein Klick setzt genau ab dem
fehlgeschlagenen Paket fort, nichts wird doppelt angelegt oder übersprungen.

Der Schnellstart arbeitet exakt: Sind nicht mindestens 100 sichere, eindeutige
Jordi-Kontakte verfügbar, verändert er **null** Zeilen und legt keinen Batch an.
Opt-out, Suppression, Hard Bounce, ungültige Adressen, bereits gesendete oder
aktiv reservierte Kontakte sowie falsche Owner/Flyer bleiben gesperrt.

**Joel will 12:** dasselbe, Absender *Joel*, Anzahl **12**.

---

## Wie die Entwürfe ins Postfach kommen

Es gibt zwei Wege. Der zweite ist der belastbare.

### Weg 1 — ZIP-Pakete, ohne jede Einrichtung

Die Pakete herunterladen, entpacken und die `.eml`-Dateien in Outlook **in den
Ordner „Entwürfe" des Postfachs ziehen**.

Wichtig: **nicht doppelklicken.** Die Kopfzeile `X-Unsent: 1`, die Outlook zum
Öffnen als unversendeten Entwurf bewegen soll, wird von Outlook für Mac
ignoriert und im neuen Outlook für Windows nicht mehr zuverlässig ausgewertet.
Ein Doppelklick zeigt die Datei dann als *empfangene* Nachricht — ohne
Sende-Knopf. Das Hineinziehen in den Ordner funktioniert unabhängig davon.

### Weg 2 — direkt ins Postfach (empfohlen)

`engine/graph_drafts.py` legt jeden Entwurf über Microsoft Graph serverseitig
im Ordner „Entwürfe" an. Kein Ziehen, kein Client-Verhalten, kein
`X-Unsent`-Trick — und es funktioniert für jeden Outlook-Client gleich.

Einmalig nötig — **ohne Administrator möglich**: eine App-Registrierung in
Entra ID mit der *delegierten* Berechtigung `Mail.ReadWrite` (nicht
Anwendungsberechtigung — die würde tenant-weit wirken und bräuchte deshalb
zwingend einen Admin). Delegiert heißt: du meldest dich einmalig selbst an
und wirkst danach nur in deinem eigenen Postfach — genau das, was hier
gebraucht wird. Details und die genauen Klick-Schritte stehen im Kopf von
`engine/graph_drafts.py`. Danach:

```sh
export HSB_GRAPH_TENANT_ID=...
export HSB_GRAPH_CLIENT_ID=...

python3 engine/graph_drafts.py --batch HSB-... --pruefen        # nur Prüfung
python3 engine/graph_drafts.py --batch HSB-... --limit 1        # ein Probelauf
python3 engine/graph_drafts.py --batch HSB-...                  # alle
```

Beim ersten Lauf zeigt das Werkzeug eine Internetadresse und einen kurzen
Code — im Browser öffnen, Code eingeben, fertig. Merkt sich danach eine
Anmeldung lokal, damit du dich nicht bei jedem Lauf neu anmelden musst.

Zeigt der Anmeldebildschirm „Genehmigung durch Administrator erforderlich",
hat eure IT die Selbstzustimmung tenant-weit gesperrt — dann bitte kurz
Rücksprache halten, wer die Berechtigung einmalig freigibt.

Das Werkzeug ruft ausschließlich `POST /me/messages` auf, also im Postfach
der gerade angemeldeten Person. Die Graph-Aktion `.../send` kommt im Code
nicht vor.

---

## Entwürfe am Rechner erzeugen

```sh
python3 engine/make_drafts.py --batch HSB-20260826-JORDI-0002
```

Erzeugt eine `.eml` pro Kontakt, **liest jede Datei wieder ein** und vergleicht
Empfänger, Anrede, Firma im Betreff und den SHA-256 des Anhangs gegen die
Sheet-Daten. Bei einer einzigen Abweichung endet der Lauf mit `PRUEFUNG=FAIL`.
Ergebnis liegt unter `~/Desktop/HSB-Entwuerfe/<BATCH>/`.

Das Werkzeug arbeitet auf einem Sheet-Export und hat selbst keinen
Schreibzugriff. Es nennt deshalb am Ende den genauen Bereich, in dem die Spalte
`Drafted_At` auf das Datum zu setzen ist (auch als `sheet_update.json`).
**Ohne diesen Eintrag zeigt VERSAND für die Kontakte weiterhin „kein Entwurf".**

---

## Was das Cockpit zeigt

Pro Absender:

| Kennzahl | Bedeutung |
|---|---|
| sendefähig | Darf rechtlich und technisch angeschrieben werden |
| gesperrt | Darf **nicht** angeschrieben werden — siehe unten |
| gesendet | Tatsächlich versendet |
| Antworten | Rückmeldung eingegangen |
| positiv | Fachlich positive Antwort |
| Bounces | Unzustellbar |
| Abmeldungen | Opt-out — dauerhaft gesperrt |
| Wiedervorlage fällig | Heute oder überfällig |

---

## Warum steht da „0 sendefähig"?

**Das ist kein Fehler.** Aktuell stehen alle 6.424 Datensätze auf
`Versandfreigabe = no` und `Opt-in-Status = unknown`.

Nach § 7 UWG braucht Werbung per E-Mail eine Rechtsgrundlage. Ohne diese darf
die Software nicht senden — und sie lässt sich auch nicht durch eine größere
Batchgröße überreden. Das ist bewusst so gebaut.

**Jordi:** Der obere Schnellstart ist die ausdrückliche Operator-Freigabe. Er
protokolliert neutral `OWNER_APPROVED`, ohne Einwilligung oder
Bestandskundenstatus zu behaupten. Jordi muss keine Grundlage aus einer Liste
auswählen.

**Joel / erweiterter Ablauf:**

1. In der Seitenleiste ganz unten: **Rechtliche Freigabe**
2. Absender wählen, Anzahl eintragen (z. B. 100)
3. Grundlage wählen:
   - **Bestandskunde § 7(3)** — bestehende Geschäftsbeziehung, eng an vier
     Voraussetzungen gebunden
   - **Einwilligung** — ausdrückliche Zustimmung liegt vor
   - **Sperren** — dauerhaft ausschließen
4. **Freigeben**

Danach liefert „Batch vorbereiten" die gewünschte Anzahl.

Diese Entscheidung trifft **eine Person**, nicht die Software. Genau deshalb ist
sie ein eigener, sichtbarer Schritt.

---

## Wiedervorlage

**Heute fällige anzeigen** listet alles, was ansteht. Pro Eintrag:

- **Antwort** — Rückmeldung eingegangen, wird im Cockpit gezählt
- **+7 Tage** — Wiedervorlage verschieben
- **Abmeldung** — dauerhaft sperren, keine weiteren Kontakte

Jede Aktion schreibt sofort ins Sheet zurück. Kein CSV-Export, kein
Zwischenspeicher im Browser.

Optional: **HSB Sales OS → Tägliche Erinnerung einrichten** schickt jeden
Morgen um 7 Uhr eine Übersicht der fälligen Wiedervorlagen per Mail.

---

## Was automatisch gesperrt wird

Nach einer **Abmeldung** oder einem **Hard Bounce** wird der Lead sofort auf
`Suppressed = yes` gesetzt und fällt aus allen künftigen Batches heraus.
Das lässt sich nicht versehentlich rückgängig machen, indem man einen neuen
Batch anfordert.

---

## Grenzen, die bewusst so sind

- **Kein Öffnungs-Tracking.** Apple Mail Privacy Protection macht Öffnungsraten
  unbrauchbar. Gezählt werden Antworten, Bounces und Abmeldungen — also das,
  was wirklich passiert ist.
- **„Gesendet" heißt nicht „im Posteingang angekommen."** Ein ausbleibender
  Bounce ist kein Zustellnachweis.
- **Vorbereiten ist nicht Senden.** Auch der Jordi-Schnellstart verschickt
  nichts. Er erzeugt Outlook-Entwürfe; der Versand passiert erst, wenn eine
  Person sie unter `j-post@hsb-boden.de` prüft und abschickt.
- **Langsam senden.** Nicht 100 Mails in wenigen Sekunden. Microsofts
  technische Obergrenze ist keine Empfehlung für die Geschwindigkeit.

---

## Wenn etwas nicht geht

| Meldung | Bedeutung |
|---|---|
| `ASSET_GATE=FAIL` | Der Flyer in Drive stimmt nicht mit dem hinterlegten Prüfwert überein. **Nicht senden.** Der Flyer wurde verändert oder ersetzt. |
| „0 von N sendefähig" | Rechtliche Freigabe fehlt — siehe oben |
| „Spalten fehlen" | Einmalig **HSB Sales OS → Spalten prüfen / ergänzen** ausführen |
| Batch bleibt leer trotz Freigabe | Filter zu eng gesetzt (Branche/Tier) |

---

## Größe und Teilpakete

Jeder Flyer ist rund 1,5 MB und steckt in jedem Entwurf. 100 Entwürfe sind
also rund 150 MB.

Deshalb entstehen **mehrere ZIP-Dateien statt einer**, je höchstens zehn
Entwürfe ein Paket. Ein einziges großes ZIP würde Google Apps Script
überlasten — das ist keine Bequemlichkeit, sondern eine harte Grenze.

Für dich heißt das: **jedes Paket einzeln in Outlook importieren.** Bei 100
Entwürfen sind das zehn Importe. Die Seitenleiste holt die Pakete beim
Jordi-Schnellstart automatisch nacheinander; du musst nur noch jedes fertige
Paket importieren.

Bricht ein Teilschritt ab (Laufzeitgrenze erreicht oder ein anderer Fehler),
zeigt die Seitenleiste **„Vorgang sicher erneut versuchen"**. Ein Klick setzt
genau ab dem fehlgeschlagenen Paket fort — es geht nichts verloren und nichts
wird doppelt erzeugt.
