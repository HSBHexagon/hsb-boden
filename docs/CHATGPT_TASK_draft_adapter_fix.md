# Arbeitsauftrag für ChatGPT — HSB_DraftAdapter.gs.js reparieren

Kontext: Google-Apps-Script-Datei `HSB_DraftAdapter.gs.js`, gebunden an das
Sheet `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg` (Script-ID
`1Xl6xkMTyn3Hu6UvBoX7gVrdppuyRal04NH6Ei16hnz_Pfuq-JWmh9U4c`). Lokale Kopie
im Repo `hsb-sales-os` unter `deploy/HSB_DraftAdapter.gs.js` (Commit
`def72ec`) — das ist der reale Live-Stand, 1:1 gesichert.

**Nicht verändern:** `deploy/HSB_SALES_OS.js`, `deploy/Sidebar.html`,
`engine/*` — diese sind bereits korrekt und unabhängig verifiziert.

## Aufgabe 1 — Duplikat entfernen (Zeilen 343–683 löschen)

Die Datei enthält ihren gesamten Inhalt zweimal hintereinander (Copy-Paste-
Fehler). Zeilen 1–342 und 343–683 sind identisch. Behalte **nur** die erste
Kopie (Zeilen 1–342), lösche den Rest. Ergebnis: eine Datei mit genau einer
Definition von `preflight`, `createDraftsForBatch`, `entwurfTesten`,
`entwuerfeErzeugen`, `aktivenBatchFinden_`, `writeBackDraft_`,
`writeBackError_`, `flyerPruefen`, `flyerAttachment_`, `adapterUrlFor_`,
`textToHtml_`, `sha256Hex_`.

## Aufgabe 2 — Payload-Schema korrigieren (kritisch, funktionaler Bug)

In `createDraftsForBatch`, aktueller Payload-Aufbau:

```js
var payload = {
  leadId: lead.Lead_ID,
  batchId: batchId,
  to: lead['E-Mail'] || lead.Email,
  subject: rendered.subject,
  bodyHtml: textToHtml_(rendered.body),
  attachments: [flyerAttachment_(owner)]
};
```

Die zwei live verifizierten Power-Automate-Flows (siehe
`PROJECT_STATE.md`, Abschnitt „Power Automate — beide Konten live
verifiziert, 2026-09-04") erwarten **keine** `attachments`-Array, sondern
je nach Owner unterschiedliche flache Felder:

- **JORDI** (`47ee3d7a-...`, Button-Trigger, Free-Tier): erwartet
  `attachmentName` (string) + `attachmentContentBytes` (base64-string) als
  eigene Top-Level-Felder im Trigger-Body.
- **JOEL** (`137601e8-...`, Request/Http-Trigger, Premium): erwartet
  `attachmentName` (string) + `flyerUrl` (string, öffentliche PDF-URL — der
  Flow lädt sie selbst per HTTP-Aktion). `attachmentContentBytes` wird von
  diesem Flow ignoriert.

Korrigiere `createDraftsForBatch` so, dass der Payload owner-abhängig
gebaut wird. Referenzimplementierung (bereits verifiziert, andere Sprache
— Python, `engine/pa_direct_drafts.py`, Funktion `payload_fuer_lead`):

```python
def payload_fuer_lead(owner, lead, batch_id, subject, body_html):
    flyer = FLYERS[owner]
    basis = {
        "leadId": ...,
        "batchId": batch_id,
        "owner": owner,
        "to": ...,
        "subject": subject,
        "bodyHtml": body_html,
        "attachmentName": flyer.filename,
    }
    if FLOWS[owner]["usesFlyerUrl"]:   # nur JOEL
        basis["flyerUrl"] = f"https://www.hsb-boden.de/HSB-Flyer-{website_name}.pdf"
    else:                              # JORDI
        basis["attachmentContentBytes"] = base64.b64encode(flyer.path.read_bytes()).decode()
    return basis
```

Übertrage dieselbe Verzweigung nach Apps Script. Praktischer Hinweis für
JOEL: `flyerAttachment_(owner)` liest den Flyer bereits aus Drive
(`getVerifiedFlyer_`) — für JOEL genügt es, `attachmentName` aus
`flyer.blob.getName()` zu setzen und zusätzlich `flyerUrl` fest zu codieren
(siehe die zwei öffentlichen URLs unten); für JORDI zusätzlich
`attachmentContentBytes = Utilities.base64Encode(blob.getBytes())` setzen,
wie es der bisherige Code für den `attachments`-Array-Eintrag schon tut —
nur eben als eigenes Feld statt in einem Array.

Flyer-URLs, verifiziert gegen Sheet-Tab `FLYER_MAPPING` (HTTP 200 zuletzt
geprüft 2026-08-11):

```
JORDI: https://www.hsb-boden.de/HSB-Flyer-Jordi-Post.pdf
JOEL:  https://www.hsb-boden.de/HSB-Flyer-Joel-Cherino.pdf
```

Owner-Erkennung: `lead.Verantwortlicher` steht im Sheet als Klartext
(„Jordi Post" / „Joel Cherino Diaz"), nicht als `JORDI`/`JOEL`-Schlüssel —
prüfe, ob `owner = lead.Verantwortlicher || lead.Owner` bereits die
richtige Normalisierung liefert oder ob `adapterUrlFor_`s vorhandene
Erkennung (`indexOf('JORDI') >= 0`) auf den Klartext-Wert überhaupt
anschlägt. Falls nicht: dieselbe Normalisierung wie `adapterUrlFor_`
konsistent auch für die neue Payload-Verzweigung verwenden, nicht zweimal
leicht unterschiedlich implementieren.

## Aufgabe 3 — Nach dem Fix: NICHT selbst deployen

Nicht per `clasp push` ausrollen. Ergebnis als Diff/vollständige
korrigierte Datei zurückgeben — der Nutzer prüft und rollt selbst aus.

## Was NICHT Teil dieser Aufgabe ist

- Die Re-Autorisierung der neuen OAuth-Scope (`script.external_request`)
  ist eine manuelle Aktion einer Person im Apps-Script-Editor, kein
  Code-Fix — siehe `PROJECT_STATE.md`, Befund 2. Kein Codeänderungsvorschlag
  dafür nötig.
- Ob `HSB_ADAPTER_URL_JORDI` / `HSB_ADAPTER_URL_JOEL` /
  `HSB_ACTIVE_BATCH_ID` als Script Properties gesetzt sind, ist ungeprüft —
  kein Codefix, sondern eine Konfigurationsprüfung vor Ort.
