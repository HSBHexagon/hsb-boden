# HSB Sales OS — Architektur

Stand 2026-08-21.

## Prinzip

Ein System of Record, eine Bedienoberfläche, zwei unveränderliche Assets.
Keine zweite parallele Wahrheit.

```
┌──────────────────────────────────────────────────────────┐
│  Google Sheet  —  System of Record                       │
│  1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg            │
│  6.424 Leads · Status · Wiedervorlage · Ereignisse       │
└───────────────┬──────────────────────────────────────────┘
                │ Apps Script (gebunden, läuft im Sheet)
                ▼
┌──────────────────────────────────────────────────────────┐
│  Sales OS Seitenleiste                                   │
│  Absender · Anzahl N · Filter · Batch vorbereiten        │
│  Cockpit · Wiedervorlage · Rechtliche Freigabe           │
└───────┬─────────────────────────────┬────────────────────┘
        │                             │
        ▼                             ▼
┌───────────────────┐      ┌──────────────────────────────┐
│ Asset-Gate        │      │ EML-Fallback                 │
│ Drive-ID → SHA256 │      │ ZIP in Drive → Outlook-Import│
│ fail-closed       │      │ ohne Admin, ohne DNS         │
└───────────────────┘      └──────────────────────────────┘
```

## Rollen

| Baustein | Rolle | Ausdrücklich nicht |
|---|---|---|
| Google Sheet | einzige vollständige Datenbasis | — |
| Apps Script | Oberfläche + Batch-Engine | zweite Datenhaltung |
| Google Drive | Ablage der zwei Flyer-Master | Lead-Daten |
| Outlook | Entwurf und Versand durch Menschen | Autoversand |
| Airtable | höchstens Management-Spiegel | vollständige Datenbank |
| Cloudflare | nur die bestehende Website | Lead-Daten, Mailversand |
| Browser-Speicher | nichts | führender Statusspeicher |

Bewusst **nicht** im kritischen Pfad: eigene Sende-Subdomain, DKIM-Änderung,
SMTP-Relay, Entra-App-Registrierung, Admin-Consent, n8n.

## Die zwei Assets

Auflösung ausschließlich über `sender → Drive-ID → SHA-256`.
Niemals über Dateiname, Datum oder „neueste Datei" — genau diese Auflösung
hat am 2026-08-21 dreimal die falsche Fassung ausgeliefert.

| Absender | Datei | Drive-ID | SHA-256 |
|---|---|---|---|
| Jordi Post | `HSB-Flyer-Jordi-Post_FINAL.pdf` | `1UMX-fi2lJ9bo14KwuClqgfZQWECdE_XV` | `e0aa76c1…2585d`¹ |
| Joel Cherino Diaz | `HSB-Flyer-Joel-Cherino_FINAL.pdf` | `16Kt-eRk1uY0HorZCrEmGt3QfGcRpYadS` | `2bccadac…de5fb`¹ |

¹ Vollständige Werte in `RELEASE_MANIFEST.json`. Beide Drive-IDs wurden gegen
die tatsächlichen Bytes verifiziert, nicht aus einer Textquelle übernommen.

Bei Hash-Abweichung: `ASSET_GATE=FAIL`, Versand blockiert, **keine**
automatische Ersatzauswahl.

## Compliance-Gate

Fail-closed nach § 7 UWG. Sendefähig nur bei **allen** Bedingungen:

```
Legal_Basis ∈ {OPT_IN, EXISTING_CUSTOMER_7_3, OWNER_APPROVED}
Versandfreigabe = yes
Suppressed ≠ yes
Opt_Out ≠ yes
kein Hard Bounce
Send_Status ≠ sent
E-Mail syntaktisch gültig
Owner eindeutig auflösbar
```

`OWNER_APPROVED` ist die neutral protokollierte, ausdrückliche Operator-Aktion
des atomaren Jordi-100-Schnellstarts. Sie behauptet weder Opt-in noch
Bestandskundenstatus. `UNKNOWN` und `BLOCKED` sind nicht sendefähig. Das Gate ist weder über die
Batchgröße noch über die Oberfläche noch über die CLI umgehbar — dafür gibt es
einen eigenen Test (`test_gate_not_bypassable_by_count`).

Der Schnellstart prüft unter einem einzigen `DocumentLock` zuerst alle
unveränderlichen Sperren und das Jordi-Flyer-Gate. Nur wenn exakt 100 sichere,
eindeutige Kandidaten verfügbar sind, werden Freigabe und Reservierung
geschrieben. Bei Shortfall: null Writes, null Batch.

## Batch-Engine

Eingabe `owner + count (+ Filter)` → immutable Batch `HSB-JJJJMMTT-OWNER-NNNN`.

- Deterministische Reihenfolge: Tier A vor B, dann Lead-ID
- Ein Lead nie gleichzeitig in zwei aktiven Batches
- Gleiche Eingabe → gleiche Auswahl (idempotent)
- Leerer Batch ist ein legitimes Ergebnis mit gezählten Ausschlussgründen

## Ereignismodell

`PREPARED → DRAFTED → APPROVED → SENT` und danach `REPLIED`,
`POSITIVE_REPLY`, `NEGATIVE_REPLY`, `AUTO_REPLY`, `HARD_BOUNCE`,
`SOFT_BOUNCE`, `OPT_OUT`, `SUPPRESSED`.

`SENT_NO_BOUNCE` wird **nie** als `DELIVERED` bezeichnet. Ein ausbleibender
Bounce ist kein Zustellnachweis.

Kein Öffnungs-Tracking, kein Zählpixel, keine Tracking-Domain — Apple Mail
Privacy Protection macht Öffnungsraten ohnehin unbrauchbar.

`OPT_OUT` und `HARD_BOUNCE` setzen sofort `Suppressed = yes`.

## Versandrate

Vorbereiten und Senden sind getrennt. Voreinstellung 2 Nachrichten pro Minute.
Microsofts technische Grenze von 30/Minute ist eine Obergrenze, keine Zielrate.

## Warum kein Cloudflare-Versand

Eine frühere Planung sah eine eigene Sende-Subdomain mit SPF/DKIM/DMARC über
Cloudflare vor. Verworfen, weil sie DNS-Schreibrechte und eine neue
Mail-Reputation gebraucht hätte, ohne das eigentliche Problem zu lösen: die
fehlende Nachverfolgung. Der Versand über das bestehende, bereits zugestellte
HSB-Postfach ist der kürzere und rechtlich unauffälligere Weg.

## Bekannte Einschränkung

Der Jordi-Master enthält in der **Textebene** zusätzlich Joels Kontaktblock,
exakt überlagert von Jordis Block. Sichtbar gerendert ist der Flyer korrekt;
Copy-Paste, PDF-Suche und Screenreader liefern jedoch den falschen
Ansprechpartner. Das Gate meldet dies als Warnung, blockiert aber nicht, weil
das Sichtbare stimmt. Behebung nur durch Neuerzeugung aus der Quelldatei mit
genau einem Kontaktblock.
