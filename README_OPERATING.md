# HSB Sales OS — Bedienung

Für Jordi und Joel. Kein Terminal, kein Mac, keine Installation nötig.

---

## Der tägliche Ablauf

**Jordi will heute 100 anschreiben:**

1. Google Sheet öffnen → Menü **HSB Sales OS → Sales OS öffnen**
2. Absender **Jordi Post**, Anzahl **100**
3. **Batch vorbereiten**
4. **Entwürfe als ZIP erzeugen** → ZIP aus Drive herunterladen
5. In Outlook importieren, jeden Entwurf prüfen, senden

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

**So gibst du Leads frei:**

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
- **Vorbereiten ist nicht Senden.** Ein vorbereiteter Batch verschickt nichts.
  Der Versand passiert erst, wenn eine Person die Entwürfe in Outlook prüft und
  abschickt.
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

## Größenhinweis

Jeder Flyer ist rund 1,5 MB. Ein Batch mit 100 Entwürfen erzeugt daher ein ZIP
von etwa 150 MB, bei 250 rund 375 MB. Der Aufbau dauert entsprechend — das ist
normal, nicht hängengeblieben.
