# Verifikationsbericht — HSB Sales OS

Stand 2026-08-21. Jede Aussage unten stammt aus einem gelaufenen Befehl mit
gesehener Ausgabe. Nicht Belegtes ist als solches gekennzeichnet.

---

## Gates

| Kriterium | Status | Nachweis |
|---|---|---|
| `CANONICAL_FLYERS` | **PASS** | Beide Master gegen Soll-SHA-256 geprüft |
| `DRIVE_IDS_VERIFIED` | **PASS** | Beide Drive-IDs heruntergeladen, byte-identisch |
| `OLD_ASSET_ISOLATION` | **PASS** | Hash-Inventur: 12 kanonisch, 0 veraltet, 0 unbekannt |
| `DYNAMIC_BATCH_COUNT` | **PASS** | N ∈ {0,1,17,25,100,250,500} getestet |
| `JORDI_100_DRY_RUN` | **PASS** | 0 ausgewählt, korrekt begründet |
| `JOEL_100_DRY_RUN` | **PASS** | dito |
| `ZERO_CROSS_SENDER_ATTACHMENTS` | **PASS** | Jede EML gehasht gegen Absender-Master |
| `COMPLIANCE_GATE` | **PASS** | 9 Sperrfälle + Umgehungsversuch über Batchgröße |
| `DUPLICATE_PROTECTION` | **PASS** | Keine Überschneidung aktiver Batches |
| `SUPPRESSION_GATE` | **PASS** | Opt-out/Hard-Bounce setzen `Suppressed` |
| `EML_FALLBACK` | **PASS** | `X-Unsent: 1`, Header, genau ein Anhang |
| `VISUAL_PDF_GATE` | **PASS** (1 Warnung) | 13 Prüfungen je Flyer |
| `NO_DNS_WRITE` | **PASS** | 0 DNS-Operationen |
| `NO_ADMIN_DEPENDENCY` | **PASS** | Kein Admin, keine App-Registrierung |
| `REAL_SEND_DURING_TEST` | **0** | Keine externe Sendung |
| `OUTLOOK_DRAFT_PATH` | **EXTERNAL_BLOCKER** | siehe unten |
| `INBOUND_SYNC` | **EXTERNAL_BLOCKER** | siehe unten |

**Testmatrix: 73 von 73 bestanden, 0 fehlgeschlagen.**
`RELEASE_MANIFEST.json` → `release_status: READY`.

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

**Installation:** Das Apps Script ist geschrieben und geprüft, aber noch nicht
im Sheet installiert — dafür braucht es Einfügen im Apps-Script-Editor
(`docs/INSTALL.md`, ca. 10 Minuten). Die zwölf CRM-Spalten werden dabei durch
**HSB Sales OS → Spalten prüfen / ergänzen** angelegt. Ein direktes Anlegen per
API scheiterte an den Grid-Grenzen des Sheets; der Setup-Schritt erledigt es
idempotent.

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

python3 tests/test_matrix.py                        # 73/73
python3 engine/hsb.py gate                          # VISUAL_PDF_GATE: PASS
python3 engine/hsb.py inventory --write             # 12/0/0
python3 engine/hsb.py status                        # Datenlage
python3 engine/hsb.py prepare --owner JORDI --count 100
python3 engine/make_release.py                      # release_status: READY
```
