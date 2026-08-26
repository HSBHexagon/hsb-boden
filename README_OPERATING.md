# HSB Sales OS — Bedienung

Für Jordi und Joel. Kein Terminal, kein Mac, keine Installation nötig.

---

## Der tägliche Ablauf

**Jordi will heute 100 anschreiben:**

1. Google Sheet öffnen → Menü **HSB Sales OS → Seitenleiste öffnen**
2. Absender **Jordi** wählen
3. Oben **100 freigeben & Entwürfe erzeugen** klicken
4. Die fünf ZIP-Pakete aus Drive herunterladen
5. In Neues Outlook unter `j-post@hsb-boden.de` in **Entwürfe** importieren
6. Entwürfe prüfen und manuell senden

Der Schnellstart arbeitet exakt: Sind nicht mindestens 100 sichere, eindeutige
Jordi-Kontakte verfügbar, verändert er **null** Zeilen und legt keinen Batch an.
Opt-out, Suppression, Hard Bounce, ungültige Adressen, bereits gesendete oder
aktiv reservierte Kontakte sowie falsche Owner/Flyer bleiben gesperrt.

**Joel will 12:** dasselbe, Absender *Joel*, Anzahl **12**.

Die Anzahl ist frei: 3, 17, 25, 100, 250. Nie wieder ein neuer Programmierauftrag,
nur weil eine andere Menge gebraucht wird.

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

Deshalb entstehen **mehrere ZIP-Dateien statt einer**: je 20 Entwürfe ein
Paket. Ein einziges großes ZIP würde Google Apps Script überlasten — das ist
keine Bequemlichkeit, sondern eine harte Grenze.

Für dich heißt das: **jedes Paket einzeln in Outlook importieren.** Bei 100
Entwürfen sind das fünf Importe.

Erscheint der Hinweis „Noch nicht vollständig", war die Laufzeitgrenze
erreicht. Ein Klick auf **Weiter ab Eintrag …** setzt genau dort fort — es geht
nichts verloren und nichts wird doppelt erzeugt.
