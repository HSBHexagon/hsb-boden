# ATTRIBUTION_CONNECTOR_PATCH — Apps-Script-Mapping für Lead-Attribution

Status: `ready-to-paste` | Stand: 2026-07-13
Gilt für: Apps Script **HSBBODEN** (Script-ID `1_xBbLkV_BddyAPqqPLaRGnZrw_DRY82GYGPcFUPvMZunXMwJOYdgeSzV`, Google-Konto cherinojoel@gmail.com) und Sheet **„HSB CRM Light"** (`1d0zZXXwYGo38ZKf0oUSSJpoZ_WVG545rDalXAdItm80`, Tab `Leads`).

Seit 2026-07-13 sendet der Live-Lead-Endpoint (`/api/lead`, PR #79) sechs zusätzliche
Attributionsfelder im Webhook-JSON. Sie werden vom Connector **ignoriert**, bis dieses
Mapping eingespielt ist. Kein Bruch — nur Datenverlust für Attribution.

## Schritt 1 — Spalten im Sheet ergänzen (einmalig)

Im Tab `Leads` hinter der letzten belegten Spalte (Stand: `AA`) sechs neue
Header-Zellen anfügen, exakt in dieser Reihenfolge (AB1:AG1):

| Spalte | Header |
|--------|--------|
| AB | `utm_term` |
| AC | `utm_content` |
| AD | `referrer` |
| AE | `landing_page` |
| AF | `form_path` |
| AG | `attribution_channel` |

## Schritt 2 — Apps-Script-Patch (paste-ready)

Öffnen: <https://script.google.com> → Projekt HSBBODEN → Datei mit `doPost`.

Dort, wo aus dem geparsten Webhook-Body (`data` / `payload` / `lead` — Name je nach
Bestand) die Zeile für `appendRow(...)` bzw. `setValues(...)` gebaut wird, ans **Ende
des Zeilen-Arrays** anhängen (Reihenfolge = Schritt 1):

```javascript
// --- Lead-Attribution (PR #79, 2026-07-13): sechs neue optionale Felder ---
// Werte sind serverseitig bereits sanitisiert (Allowlist, Origin-only-Referrer,
// Pfade ohne Query). Fehlen sie (Alt-Clients), bleiben die Zellen leer.
var att = function (v) {
  v = (v === undefined || v === null) ? "" : String(v);
  // Defense-in-depth gegen Spreadsheet-Formula-Injection:
  return /^[=+@-]/.test(v) ? "'" + v : v;
};
row.push(
  att(data.utm_term),
  att(data.utm_content),
  att(data.referrer),
  att(data.landing_page),
  att(data.form_path),
  att(data.attribution_channel)
);
```

Hinweise:
- `row` und `data` an die tatsächlichen Variablennamen im Bestandscode anpassen.
- Falls der Bestandscode **headerbasiert** mappt (Objekt→Header-Lookup), genügt es,
  die sechs Keys der Mapping-Liste hinzuzufügen — der `att()`-Guard bleibt empfohlen.
- Bereits gemappte Felder `utm_source`, `utm_medium`, `utm_campaign` NICHT doppeln.
- Danach: neue Version deployen (Bereitstellen → Deployment verwalten → Bearbeiten →
  Version: Neu → Bereitstellen). Die Webhook-URL bleibt unverändert, solange dasselbe
  Deployment aktualisiert wird — **kein** neues Deployment anlegen, sonst ändert sich
  die URL und `LEAD_WEBHOOK_URL` (Cloudflare Pages, Production) müsste nachgezogen werden.

## Schritt 3 — Verifikation (ohne echten Lead)

1. Auf `https://www.hsb-boden.de/kontakt/?utm_source=internal_test&utm_medium=qa&utm_campaign=mapping_check` das Formular mit klar als intern markierten Daten absenden (Nachricht: „INTERNER TEST — bitte löschen").
2. Im Sheet prüfen: AB–AG der neuen Zeile gefüllt (`utm_term`/`utm_content` leer ist ok, `attribution_channel` = `campaign`, `form_path` = `/kontakt/`).
3. Testzeile löschen und Löschung verifizieren.

## Feldreferenz (Quelle: `src/lib/leadSchema.ts` / `src/lib/attribution.ts`)

| Key | Inhalt | Grenzen |
|-----|--------|---------|
| `utm_term`, `utm_content` | zusätzliche UTM-Parameter | ≤ 100 Zeichen, Allowlist |
| `referrer` | externes Origin (nur Schema+Host) | ≤ 200 Zeichen |
| `landing_page` | erste Seite der Session, Pfad ohne Query | ≤ 200 Zeichen |
| `form_path` | Seite des Formular-Submits | ≤ 200 Zeichen |
| `attribution_channel` | `campaign` \| `referral` \| `direct` (serverseitig abgeleitet) | Enum |

Grenze (dokumentiert in `CRM_LIGHT_MAX_READINESS.md`): Attribution ist clientseitig
erhoben und kein Herkunftsnachweis — nur für Reporting, nie für Sicherheits- oder
Abrechnungsentscheidungen.
