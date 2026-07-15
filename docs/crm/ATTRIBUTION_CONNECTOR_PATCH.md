# ATTRIBUTION_CONNECTOR_PATCH — Apps-Script-Mapping für Lead-Attribution

Status: `live` | Stand: 2026-07-15
Gilt für: Apps Script **HSBBODEN** (Script-ID `1_xBbLkV_BddyAPqqPLaRGnZrw_DRY82GYGPcFUPvMZunXMwJOYdgeSzV`, Google-Konto cherinojoel@gmail.com) und Sheet **„HSB CRM Light"** (`1d0zZXXwYGo38ZKf0oUSSJpoZ_WVG545rDalXAdItm80`, Tab `Leads`).

Seit 2026-07-13 sendet der Live-Lead-Endpoint (`/api/lead`, PR #79) sechs zusätzliche
Attributionsfelder im Webhook-JSON. Der Patch wurde am 2026-07-15 live eingespielt:
Sheet-Header AB1:AG1 ergänzt, Code.gs um `att()`-Sanitizer + 6 Row-Felder erweitert,
bestehendes Deployment auf Version 4 aktualisiert (Deployment-ID/Webhook-URL unverändert).
Schritt-3-Verifikation mit echtem UTM-Test-Lead bestand: alle 6 Spalten korrekt befüllt,
Testzeile danach gelöscht. Kein Datenverlust mehr für Attribution.

## Schritt 1 — Spalten im Sheet ergänzen (einmalig)

**Zuerst prüfen:** Existieren im Tab `Leads` bereits Header für `utm_source`,
`utm_medium`, `utm_campaign`? (Das Repo-Schema in `CRM_LIGHT_SCHEMA.md` definiert sie
nicht — nur der Endpoint sendet sie seit jeher.)

- **Falls ja:** nur die sechs neuen Header hinter der letzten belegten Spalte anfügen
  (Beispiel bei letzter Spalte `AA` → AB1:AG1): `utm_term`, `utm_content`, `referrer`,
  `landing_page`, `form_path`, `attribution_channel`.
- **Falls nein:** alle **neun** Attribution-Header anfügen, in dieser Reihenfolge:
  `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`, `referrer`,
  `landing_page`, `form_path`, `attribution_channel` — und in Schritt 2 entsprechend
  alle neun `row.push`-Einträge übernehmen (die drei Kern-UTMs zusätzlich vorn).

Die Spaltenreihenfolge im Sheet MUSS der `row.push`-Reihenfolge in Schritt 2 entsprechen.

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
  // Erst Whitespace/Steuerzeichen am Anfang entfernen, DANN Formula-Präfix prüfen —
  // sonst rutscht z. B. "\t=IMPORTXML(...)" am Guard vorbei (Defense-in-depth für
  // direkte POSTs an die Web-App, die /api/lead umgehen):
  v = v.replace(/^[\s\u0000-\u001F]+/, "");
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

1. Auf `https://www.hsb-boden.de/kontakt/?utm_source=internal_test&utm_medium=qa&utm_campaign=mapping_check&utm_term=spalten_check&utm_content=patch_v1` das Formular mit klar als intern markierten Daten absenden (Nachricht: „INTERNER TEST — bitte löschen").
2. Im Sheet prüfen — **alle** sechs neuen Zellen der Zeile müssen exakt stimmen (deckt Vertauschungen/Auslassungen auf): `utm_term` = `spalten_check`, `utm_content` = `patch_v1`, `referrer` leer oder externes Origin, `landing_page` = `/kontakt/`, `form_path` = `/kontakt/`, `attribution_channel` = `campaign`.
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
