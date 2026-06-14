# PUBLIC_LEAD_ENDPOINT_SPEC — HSB-Boden

> P0A-Spezifikation. Stand: 2026-06-14. Nur Spezifikation. Kein Endpoint-Code, kein Webhook-Livebetrieb, keine Live-Aktivierung in P0A.

## 1. Zweck
Serverseitiger Annahmepunkt für Website-Formular-Leads, der validierte Daten an den n8n-Webhook weiterreicht. Frontend hält keine Secrets.

## 2. Mögliche Route
- `POST /api/lead` (Astro/Cloudflare Worker, serverseitig).
- Endgültige Route in P0B festzulegen.

## 3. Erlaubte Methoden

| Methode | Erlaubt | Verhalten |
|---------|---------|-----------|
| POST | ja | Lead annehmen |
| GET/PUT/DELETE | nein | 405 Method Not Allowed |
| OPTIONS | ja | CORS-Preflight (nur eigene Origin) |

## 4. Request-Felder

| Feld | Typ | Pflicht | Validierung |
|------|-----|---------|-------------|
| name | string | ja | 2–100 Zeichen |
| company | string | ja | 2–120 Zeichen |
| email | string | bedingt | RFC-konform; E-Mail ODER phone Pflicht |
| phone | string | bedingt | E.164/locale; E-Mail ODER phone Pflicht |
| message | string | nein | max 2000 Zeichen |
| consent | boolean | ja | muss `true` sein |
| utm_source/medium/campaign | string | nein | max 100 Zeichen |
| honeypot | string | nein | muss leer sein (Spam) |
| timestamp | number | ja | serverseitig gegengeprüft |

## 5. Validierungsregeln
- Schema-Validierung serverseitig (z. B. `zod`, bereits Projekt-Dependency).
- Trim + Längenlimits + Typprüfung.
- `consent === true` zwingend, sonst Ablehnung.
- Unbekannte Felder verwerfen (allowlist).

## 6. Spam-/Rate-Limit-Anforderungen

| Maßnahme | Anforderung |
|----------|-------------|
| Honeypot | gefülltes Feld → stilles Verwerfen |
| Rate Limit | pro IP, z. B. ≤ 5 / 10 min (Wert in P0B) |
| Min-Submit-Zeit | Formular-Render→Submit > Schwellwert |
| Origin-Check | nur eigene Domain/Preview-Origin |

## 7. Consent-/Datenschutzfelder (technisch)
- `consent` (boolean, Pflicht).
- `consent_text_version` (string, optional) zur Nachweisführung.
- Speicherung minimaler personenbezogener Daten; Zweckbindung Lead-Kontakt.

## 8. Weiterleitung an n8n Webhook
- Server ruft n8n-Webhook serverseitig auf (URL als Secret/Env, nicht im Frontend).
- Payload: validierte, normalisierte Felder.
- Timeout + Retry-Strategie in P0B.

## 9. Fehlerfälle

| Fall | Antwort |
|------|---------|
| Validierung fehlgeschlagen | 400 + Feldfehler (ohne interne Details) |
| Methode unzulässig | 405 |
| Rate Limit | 429 |
| n8n nicht erreichbar | 502 + Lead serverseitig persistieren/queuen (P0B) |
| interner Fehler | 500 (generisch) |

## 10. Logging ohne Secrets
- Loggen: Zeitstempel, Ergebnis, Fehlercode, anonymisierte/teilmaskierte Felder.
- Nicht loggen: Webhook-URL, Tokens, vollständige PII im Klartext.

## 11. Teststrategie
- Unit: Schema-Validierung (gültig/ungültig, consent fehlt, honeypot gefüllt).
- Integration: Mock-n8n-Webhook (kein Live-Endpoint).
- Negativtests: 400/405/429.
- E2E erst in P0B nach Freigabe (Mock vor Live).

## 12. Freigabe-Gate vor echter Implementierung
Implementierung erst nach Freigabe in `P0_IMPLEMENTATION_APPROVAL_CHECKLIST.md`.

## 13. Klare Grenze
- Keine Live-Aktivierung ohne Freigabe.
- Kein Endpoint-Code in P0A.
- Kein Webhook-Livebetrieb in P0A.

## 14. Nächster Entscheidungspunkt
Freigabe Route + Rate-Limit-Werte + n8n-Webhook-Ziel → P0B-Implementierung.
