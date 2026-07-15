# PUBLIC_LEAD_ENDPOINT_SPEC — HSB-Boden

> P0A/P0B-Spezifikation. Sicherheitsrevision: 2026-07-15. Der aktuelle Endpoint-Code
> liegt als Cloudflare Pages Function unter `functions/api/lead.ts`; Live-Cutover und
> externe Owner-Gates sind nicht durch dieses Dokument erledigt.

## 1. Zweck
Serverseitiger Annahmepunkt für Website-Formular-Leads, der validierte Daten an den konfigurierten Lead-Webhook weiterreicht. Frontend hält keine Secrets.

## 2. Zielroute
- Implementiert: `POST /api/lead` (Astro/Cloudflare Worker, serverseitig).
- Frontend-Fallback: Wenn `PUBLIC_LEAD_FORM_ENABLED` nicht `"true"` ist, wird nichts versendet und das Formular zeigt Telefon/E-Mail.

## 3. Erlaubte Methoden

| Methode | Erlaubt | Verhalten |
|---------|---------|-----------|
| POST | ja | Lead annehmen |
| GET/PUT/DELETE | nein | 405 Method Not Allowed |
| OPTIONS | ja | CORS-Preflight (nur eigene Origin) |

## 4. Request-Felder

| Feld | Typ | Pflicht | Validierung |
|------|-----|---------|-------------|
| firstName | string | ja | 2–80 Zeichen |
| lastName | string | ja | 2–80 Zeichen |
| company | string | ja | 2–120 Zeichen |
| email | string | ja | RFC-konform |
| phone | string | ja | mind. 5 Zeichen, lokale Schreibweisen erlaubt |
| industry | string | ja | erlaubte Formularwerte aus `LeadForm.tsx` |
| projectType | string | ja | `neubau`, `sanierung`, `bewertung` |
| areaSize | string | nein | Freitext, max. 80 Zeichen |
| liveOperation | string | ja | `ja`, `nein`, `unklar` |
| loads | string[] | ja | mindestens 1 Eintrag aus `loadOptions` |
| message | string | ja | 10–2000 Zeichen |
| privacyConsent | boolean | ja | muss `true` sein |
| source | string | ja | aktuell `website` |
| legalBasis | string | ja | aktuell `inquiry` |
| access_key | string | nein | nur falls externer Provider ihn erwartet; kein echtes Secret im Browser |
| utm_source/medium/campaign | string | nein | max 100 Zeichen |
| honeypot | string | nein | muss leer sein (Spam) |
| timestamp | number | nein | optional; serverseitig gegengeprüft, wenn vorhanden |

## 5. Validierungsregeln
- Schema-Validierung serverseitig (z. B. `zod`, bereits Projekt-Dependency).
- Trim + Längenlimits + Typprüfung.
- `privacyConsent === true` zwingend, sonst Ablehnung.
- Unbekannte Felder verwerfen (allowlist).
- `source` und `legalBasis` werden serverseitig normalisiert, nicht aus dem Browser vertraut.

## 6. Spam-/Rate-Limit-Anforderungen

| Maßnahme | Anforderung |
|----------|-------------|
| Honeypot | gefülltes Feld → stilles Verwerfen |
| Rate Limit | pro IP: max. 5 POSTs / 10 min; pro E-Mail: max. 2 POSTs / 30 min |
| Min-Submit-Zeit | Formular-Render→Submit > Schwellwert |
| Origin-Check | nur eigene Domain/Preview-Origin |
| Payload-Limit | max. 16 KB JSON |

## 7. Consent-/Datenschutzfelder (technisch)
- `privacyConsent` (boolean, Pflicht).
- `consent_text_version` (string, optional) zur Nachweisführung.
- Speicherung minimaler personenbezogener Daten; Zweckbindung Lead-Kontakt.

## 8. Weiterleitung an den Lead-Webhook
> Revidiert 2026-06-22: n8n entfällt (Abo-Kosten). Ziel ist jetzt eine kostenlose Google-Apps-Script-Web-App, siehe `N8N_HOSTING_DECISION.md` §9b und `GOOGLE_SHEETS_CRM_SETUP.md`.
- Bevorzugter Modus: `LEAD_WEBHOOK_CONFIG` enthält URL und Token atomar. Die Pages
  Function sendet `{version:1, authToken, lead}` und akzeptiert nur eine JSON-Antwort
  mit `{ok:true}`.
- Übergangsmodus: Nur wenn `LEAD_WEBHOOK_CONFIG` vollständig fehlt, wird
  `LEAD_WEBHOOK_URL` mit dem bisherigen Lead-JSON verwendet. Eine vorhandene, aber
  ungültige neue Config fällt niemals auf Legacy zurück.
- Beide Ziel-URLs müssen HTTPS, Host `script.google.com`, den kanonischen
  `/macros/s/.../exec`-Pfad und weder Query noch Fragment erfüllen.
- Ziel: Google Apps Script Web App, gebunden an das CRM-Light-Sheet (`doPost(e)`).
- Payload: validierte, normalisierte Felder mit den Namen aus Abschnitt 4.
- Timeout: 6 Sekunden. Retry: keine automatische Mehrfachsendung aus dem Browser; serverseitig höchstens 1 Retry oder Queue in P0B.

## 9. Fehlerfälle

| Fall | Antwort |
|------|---------|
| Validierung fehlgeschlagen | 400 + Feldfehler (ohne interne Details) |
| Methode unzulässig | 405 + `Allow: POST, OPTIONS` |
| Rate Limit | 429 |
| Webhook nicht erreichbar | 502 + keine Erfolgsmeldung; Persistenz/Queue nur nach P0B-Entscheidung |
| interner Fehler | 500 (generisch) |

## 10. Logging ohne Secrets
- Loggen: Zeitstempel, Ergebnis, Fehlercode, anonymisierte/teilmaskierte Felder.
- Nicht loggen: Webhook-URL, Tokens, vollständige PII im Klartext.

## 11. Teststrategie
- Unit: Schema-Validierung (gültig/ungültig, `privacyConsent` fehlt, Honeypot gefüllt).
- Integration: Mock-Webhook (kein Live-Endpoint), getrennt für Legacy- und Auth-Modus.
- Negativtests: 400/405/429 sowie ungültige Config, unsicherer Host, schwacher Token,
  fehlender/negativer Acknowledge und Upstream-Ausfall.
- E2E erst in P0B nach Freigabe (Mock vor Live).

## 12. Freigabe-Gate vor echter Implementierung
Implementierung erst nach Freigabe in `P0B_USER_APPROVAL_REQUEST.md`.

## 13. Klare Grenze
- Keine Live-Aktivierung ohne Freigabe.
- Kein Endpoint-Code in P0A.
- Kein Webhook-Livebetrieb in P0A.

## 14. Nächster Entscheidungspunkt
Der externe Cutover folgt `docs/crm/WEBHOOK_AUTH_CUTOVER.md`. Ohne verifiziertes
serverseitiges Binding bleibt `PUBLIC_LEAD_FORM_ENABLED` auf `false`; Production-Secret,
Redeploy und E2E bleiben getrennte Freigabe-Gates.
