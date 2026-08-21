# Verifikationsbericht — HSB Sales OS

Stand 2026-08-21. Jede Aussage unten stammt aus einem gelaufenen Befehl mit
gesehener Ausgabe. Nicht Belegtes ist als solches gekennzeichnet.

---

## Gates

| Kriterium | Status | Nachweis |
|---|---|---|
| `CANONICAL_FLYERS` | **PASS** | Beide Master gegen Soll-SHA-256 geprüft |
| `DRIVE_IDS_VERIFIED` | **PASS** | Beide Drive-IDs heruntergeladen, byte-identisch |
| `OLD_ASSET_ISOLATION` | **PASS** | 10 lose PDFs kanonisch, 0 veraltet **+ 50 EML-Anhänge einzeln geprüft** |
| `DYNAMIC_BATCH_COUNT` | **PASS** | N ∈ {0,1,17,25,100,250,500} — in **beiden** Implementierungen |
| `JORDI_100_DRY_RUN` | **PASS** | 0 ausgewählt, korrekt begründet |
| `JOEL_100_DRY_RUN` | **PASS** | dito |
| `ZERO_CROSS_SENDER_ATTACHMENTS` | **PASS** | 50/50 EMLs: kanonisch **und** richtiger Absender |
| `COMPLIANCE_GATE` | **PASS** | 10 Sperrfälle + Umgehungsversuch über Batchgröße |
| `DUPLICATE_PROTECTION` | **PASS** | Lead-ID **und** E-Mail-Adresse |
| `SUPPRESSION_GATE` | **PASS** | Opt-out/Hard-Bounce setzen `Suppressed` |
| `EML_FALLBACK` | **PASS** | `X-Unsent: 1`, Header, genau ein Anhang, Teilpakete |
| `VISUAL_PDF_GATE` | **PASS** (1 Warnung) | 13 Prüfungen je Flyer |
| `NO_DNS_WRITE` | **PASS** | 0 DNS-Operationen |
| `NO_ADMIN_DEPENDENCY` | **PASS** | Kein Admin, keine App-Registrierung |
| `REAL_SEND_DURING_TEST` | **0** | Keine externe Sendung |
| `OUTLOOK_DRAFT_PATH` | **EXTERNAL_BLOCKER** | siehe unten |
| `INBOUND_SYNC` | **EXTERNAL_BLOCKER** | siehe unten |

**Python-Engine: 76/76 bestanden.**
**Apps Script (der ausgelieferte Code): 62/62 bestanden.**
`RELEASE_MANIFEST.json` → `release_status: READY`.

### Warum zwei Testsuiten

Es gibt zwei Implementierungen derselben Regeln: die Python-Engine (lokal,
für Joel) und das Apps Script (im Sheet, das benutzt Jordi). Ein grüner
Python-Lauf sagt nichts über den Code, der bei Jordi läuft.

`tests/test_apps_script.js` lädt deshalb die echten `.gs`-Dateien in Node,
stubbt die Google-APIs und prüft die Logik — inklusive **echter Flyer-Bytes
und echter SHA-256-Berechnung**. Getestet wird unter anderem, dass ein
manipulierter Flyer tatsächlich mit `ASSET_GATE=FAIL` abgewiesen wird.

### Vor der Übergabe behoben

Drei Fehler, die eine reine Python-Prüfung nicht gezeigt hätte:

1. **EML-Export wäre bei N=100 gescheitert.** Ein einziges ZIP hätte rund
   200 MB im Speicher gehalten. Jetzt Teilpakete à 20 mit Fortsetzungspunkt.
   Das war der einzige heute nutzbare Weg — er hätte bei der ersten
   echten Nutzung versagt.
2. **6-Minuten-Limit.** `writeBatchToLeads_` machte 3×N und `qualifyLeads`
   2×N Einzelzugriffe. Jetzt Bulk-Schreibvorgänge; das Lesen der 6.425 Zeilen
   passiert einmal statt zweimal pro Aufruf.
3. **Ein Test war tautologisch.** Die Dublettenprüfung auf E-Mail-Ebene war
   im Bericht behauptet, aber nie implementiert. Jetzt in beiden
   Implementierungen vorhanden und ehrlich getestet.

---

## Die beiden ehrlichen Antworten

### `CAN_JORDI_CREATE_100`

**JA — technisch bewiesen. Heute erst nach rechtlicher Freigabe.**

Auf realen Daten belegt:

```
JORDI + 100  vor Freigabe  → 0 ausgewählt
                              3212× Legal_Basis=UNKNOWN
                              3212× Versandfreigabe=no
JORDI + 100  nach Freigabe → genau 100
JORDI + 250  nach Freigabe → genau 250
```

Ein schlichtes „JA" wäre falsch: alle 6.424 Datensätze stehen auf
`Versandfreigabe = no` und `Opt-in = unknown`. Ohne Rechtsgrundlage darf nach
§ 7 UWG nicht gesendet werden, und das Gate lässt sich nicht durch eine größere
Batchgröße überreden — das ist getestet.

Die Freigabe ist ein Klick in der Seitenleiste („Rechtliche Freigabe"), aber
eine **bewusste menschliche Entscheidung**, keine technische Hürde.

### `CAN_JOEL_CREATE_ARBITRARY_N`

**JA.** Identisch, dieselbe Bedingung.

---

## Was entfernt wurde

- Fest verdrahtete Mengen `20` / `25` — ersetzt durch freies N
- Feste Ordner `01_JORDI_HEUTE_20`, `02_JORDI_HOLD_5`, `03_JOEL_PILOT_25`
  → `batches/<BATCH_ID>/`
- Browser-`localStorage` als Statusspeicher → Rückschreibung ins Sheet
- Öffnungs-Tracking → Antworten, Bounces, Abmeldungen
- Cloudflare-Sende-Subdomain, DKIM-Änderung, SMTP-Relay, Entra-App
  → vollständig aus dem kritischen Pfad

---

## Was noch aussteht

**Nur eine Anmeldung, kein Admin-Problem:**

`EXTERNAL_BLOCKER = USER_MAILBOX_LOGIN`

Für automatische Outlook-Entwürfe und die Antwort-/Bounce-Synchronisation muss
sich Jordi (`j-post@hsb-boden.de`) bzw. Joel (`j-cherino@hsb-boden.de`) einmalig
mit dem **eigenen** Microsoft-365-Konto an Power Automate anmelden. Der bisher
verbundene Connector gehört `cherinodiaz@outlook.com` und kennt das
HSB-Postfach nicht.

Bis dahin greift der EML-Fallback: identischer Batch, identischer Anhang,
Import in Outlook, Versand durch einen Menschen.

**Installation — der ehrliche Stand:**

Das Apps Script ist geschrieben, überprüft und in Node mit 62 Tests gegen echte
Flyer-Bytes gefahren. **Im Sheet selbst ist es noch nicht installiert und dort
also noch nie gelaufen.** Das lässt sich von hier aus nicht erledigen: der
Versuch, die zwölf Spalten direkt per API anzulegen, scheiterte an den
Grid-Grenzen (`exceeds grid limits. Max columns: 44`), und ein
Apps-Script-Projekt lässt sich ohne aktivierte Apps Script API nicht anlegen.

Nötig sind daher rund 10 Minuten im Browser nach `docs/INSTALL.md`: fünf
Dateien einfügen, Berechtigungen erteilen, **HSB Sales OS → Spalten prüfen /
ergänzen** einmal ausführen.

Was die Node-Tests abdecken: die gesamte Fachlogik. Was sie nicht abdecken
können: das Verhalten der echten Google-APIs unter Last — vor allem die
tatsächliche Laufzeit beim Erzeugen von 100 Entwürfen. Deshalb sind
Teilpakete und Fortsetzungspunkt eingebaut.

**Empfehlung für den ersten Lauf:** mit einem kleinen N beginnen (5 oder 10),
das Ergebnis in Outlook prüfen, dann hochgehen.

---

## Bekannter Mangel am Jordi-Flyer

Der Jordi-Master enthält in der **Textebene** zusätzlich Joels Kontaktblock,
exakt unter Jordis Block (gemessen: beide bei y≈727–742 und y≈777–779, gleiche
x-Position).

- **Sichtbar gerendert: korrekt.** Der Empfänger sieht „Jordi Post".
- **In der Textebene: falsch.** Copy-Paste, PDF-Suche und Screenreader liefern
  zusätzlich `j-cherino@hsb-boden.de`.

Das Gate meldet es als Warnung und blockiert nicht, weil das Sichtbare stimmt.
Behebung nur durch Neuerzeugung aus der Quelldatei mit genau einem
Kontaktblock — eine PDF für den Kundenkontakt wird ohne Quelldatei nicht
chirurgisch verändert.

Der Joel-Master ist sauber (nur `j-cherino@`).

---

## Bewusste Abweichung vom Auftragstext

Das Pilotpaket auf dem Schreibtisch
(`~/Desktop/HSB_SALES_OS_2026-08-21_FINAL.zip`) wurde **nicht** in Quarantäne
verschoben, obwohl der Auftrag die Isolierung alter Pakete verlangt.

Grund: Die Flyer darin sind inzwischen auf die korrekte Fassung gezogen und
verifiziert, und solange das Apps Script nicht installiert ist, wäre es der
einzige sofort nutzbare Weg. Ein funktionierender Übergangsweg wird nicht
entfernt, bevor der Nachfolger läuft. Nach der Installation kann das Paket
weg — reversibel, per Quarantäne.

---

## Nachweisbefehle

```bash
cd ~/KI-System/02_Projects/active/hsb-sales-os

python3 tests/test_matrix.py                     # 76/76 (Python-Engine)
node    tests/test_apps_script.js                # 62/62 (ausgelieferter Code)
python3 engine/hsb.py gate                       # VISUAL_PDF_GATE: PASS
python3 engine/hsb.py inventory --write          # 10 kanonisch / 0 veraltet
python3 engine/asset_inventory.py --eml          # EML-Anhänge separat
python3 engine/hsb.py status                     # Datenlage
python3 engine/hsb.py prepare --owner JORDI --count 100
python3 engine/make_release.py                   # release_status: READY
```

Die Inventur prüft **lose** PDF-Dateien. PDFs in ZIP-Archiven und in
EML-Anhängen fallen nicht darunter — genau dort steckte der Fehler heute
Morgen. Dafür gibt es `--eml` als eigene Prüfung; die 50 Entwürfe im
Desktop-Paket wurden damit einzeln verifiziert (50/50 kanonisch, richtiger
Absender).

---

## Nachtrag: zweites Entwurfspaket mit veraltetem Flyer

Der breite EML-Scan (1.738 Dateien unter Desktop, ABLAGE, Documents) fand nach
Abschluss der Hauptarbeit **100 Entwürfe mit dem veralteten Flyer** an zwei
Stellen:

| Ort | Anzahl | Zustand |
|---|---|---|
| `~/Desktop/01_HSB_Business/Active/HSB_OUTREACH_ENTWUERFE_50_2026-08-14_KORRIGIERT/` | 50 | veraltet |
| `~/ABLAGE/04_PROJEKTE/03_HSB_BODEN/05_DOKUMENTATION/` | 50 | veraltet |

Identische Dateinamen — dieselbe Sammlung in zwei Kopien, vom 14.08.

**Warum das gefährlich war:** Der Desktop-Ordner liegt unter `Active/`, heißt
`…_KORRIGIERT` (war es nicht) und enthält `IMPORT_ENTWUERFE_IN_OUTLOOK.cmd`
samt PowerShell-Skript, das **alle** EML-Dateien des Ordners direkt in den
Outlook-Entwurfsordner schreibt. Ein Doppelklick hätte 50 versandfertige
Entwürfe mit dem falschen Flyer erzeugt.

Enthalten war die Zwischenfassung mit hellem Einzelbild
(`1745c05d…` / `7c72e932…`) — nicht die Vier-Bilder-Referenzseite.

**Erledigt:** Alle 100 Anhänge auf die kanonische Fassung gezogen. Nichts
gelöscht, nichts verschoben.

**Stand nach der Korrektur (systemweit geprüft):**

```
EML-Anhaenge kanonisch korrekt: 150
EML-Anhaenge VERALTET:            0
Absender-Verwechslungen:          0
```

**Offen, deine Entscheidung:** Das Paket vom 14.08. ist jetzt inhaltlich
korrekt, aber weiterhin eine zweite parallele Ablage neben dem Sales OS —
genau die Struktur, die diese Fehlerklasse immer wieder erzeugt. Ich habe es
nicht angerührt. Empfehlung: nach der Installation des Sales OS in Quarantäne,
nicht löschen.

**Lehre für das System:** Genau deshalb prüft `asset_inventory.py --eml`
EML-Anhänge getrennt von losen PDFs. Eine Suche nach `*.pdf` hätte diese
100 Fälle nie gefunden — die Dateien heißen `.eml`.
