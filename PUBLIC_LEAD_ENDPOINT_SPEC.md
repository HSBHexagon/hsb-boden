# PUBLIC_LEAD_ENDPOINT_SPEC — HSB-Boden

> Öffentliche technische Spezifikation für den Website-Lead-Endpoint. Stand:
> 2026-10-02. Der Endpoint-Code liegt als Cloudflare Pages Function unter
> `apps/website/functions/api/lead.ts`. Diese Spezifikation beschreibt den
> aktuellen Codevertrag; Live-Zustellung und externe Owner-Gates werden separat
> in `docs/MASTER_EXECUTION_PLAN.md` und `docs/crm/WEBHOOK_AUTH_CUTOVER.md`
> geführt.

## 1. Zweck
Serverseitiger Annahmepunkt für Website-Formular-Leads. Er validiert und normalisiert die zulässigen Felder, erzwingt Herkunfts-/Zweckkonstanten, begrenzt Missbrauch und leitet ausschließlich an einen erlaubten Google-Apps-Script-Webhook weiter. Im Frontend liegen keine Webhook-Secrets.

## 2. Zielroute
- Implementiert: `POST /api/lead` als Cloudflare Pages Function.
- Das sichtbare Online-Formular wird nur gebaut, wenn `PUBLIC_LEAD_FORM_ENABLED="true"` gesetzt ist.
- Ist das Build-Flag nicht aktiv, zeigt die Kontaktseite Telefon/E-Mail statt eines wirkungslosen Formulars.
- Die Laufzeit-Zustellung benötigt zusätzlich eine gültige Webhook-Bindung; das Build-Flag allein beweist keine Zustellbarkeit.

## 3. Erlaubte Methoden

| Methode | Erlaubt | Verhalten |
|---------|---------|-----------|
| POST | ja | Lead validieren und weiterleiten |
| GET/PUT/DELETE | nein | 405 Method Not Allowed |
| OPTIONS | ja | CORS-Preflight |

## 4. Request-Felder

| Feld | Typ | Pflicht | Serverseitiger Vertrag |
|------|-----|---------|-------------------------|
| firstName | string | ja | trim, 2–80 Zeichen |
| lastName | string | nein | trim, max. 80; Standard `""` |
| company | string | ja | trim, 2–120 Zeichen |
| email | string | ja | trim, gültige E-Mail, max. 254 Zeichen |
| phone | string | nein | trim, leer oder mind. 5, max. 64 Zeichen; Standard `""` |
| industry | string | nein | trim, max. 120 Zeichen; Standard `""` |
| projectType | string | nein | `neubau`, `sanierung`, `bewertung`; Standard `bewertung` |
| areaSize | string | nein | trim, max. 80 Zeichen |
| liveOperation | string | nein | `ja`, `nein`, `unklar`; Standard `unklar` |
| loads | string[] | nein | Werte ausschließlich aus `loadOptions`; Standard `[]` |
| message | string | ja | trim, 10–2000 Zeichen |
| privacyConsent | boolean | ja | muss `true` sein |
| source | string | ja | muss exakt `website` sein |
| legalBasis | string | ja | muss exakt `inquiry` sein |
| access_key | string | nein | trim; Kompatibilitätsfeld, kein Browser-Secret |
| utm_source / utm_medium / utm_campaign / utm_term / utm_content | unbekannter JSON-Typ | nein | Nicht-Strings werden verworfen; Strings normalisiert und auf 100 Zeichen begrenzt |
| referrer | unbekannter JSON-Typ | nein | nur externe HTTP(S)-Origin; Pfad/Query/Fragment werden entfernt; Same-Origin wird verworfen |
| landing_page / form_path | unbekannter JSON-Typ | nein | nur normalisierte interne Pfade ohne Query/Hash |
| attribution_channel | unbekannter JSON-Typ | nein | Clientwert wird nicht vertraut; aus bereinigter Attribution als `campaign`, `referral` oder `direct` neu abgeleitet |
| honeypot | string | nein | muss leer sein |
| timestamp | number | nein | optionales Kompatibilitätsfeld; aktuell keine Zeit-Schwellenprüfung |

## 5. Validierungs- und Vertrauensregeln
- Schema-Validierung erfolgt serverseitig mit Zod.
- `privacyConsent === true` ist zwingend.
- `source` und `legalBasis` sind feste Literale (`website` / `inquiry`) und können nicht durch direkte POSTs umetikettiert werden.
- Unbekannte Felder werden durch das Zod-Objektschema aus dem weitergeleiteten Payload entfernt.
- Attributionswerte werden an der Server-Vertrauensgrenze erneut bereinigt. Formelpräfixe/unerlaubte Zeichen werden entfernt, Referrer auf die Origin reduziert und interne Pfade normalisiert.
- `attribution_channel` wird aus den bereinigten Attributionswerten neu berechnet, wenn Attribution vorhanden ist.

## 6. Missbrauchs- und Transportgrenzen

| Maßnahme | Aktuelles Verhalten |
|----------|----------------------|
| Origin-Check | nur `https://hsb-boden.de`, `https://www.hsb-boden.de` und HTTPS-Previews desselben `*.hsb-boden.pages.dev`-Projekts |
| Payload-Limit | max. 16 KiB; darüber 413 |
| JSON-Tiefe | max. 32 Verschachtelungsebenen |
| Honeypot | gefüllt → Schema-Ablehnung 400; kein Upstream-Request |
| Rate Limit IP | max. 5 POSTs / 10 min |
| Rate Limit E-Mail | max. 2 POSTs / 30 min |
| Rate-Limit-Store | `RATE_LIMIT_KV` ist fail-closed erforderlich; fehlendes Binding → 500 |
| Webhook-Timeout | 6 Sekunden; kein Browser-Retry |

Eine Min-Submit-Zeit wird aktuell **nicht** erzwungen und ist deshalb kein Bestandteil dieses Vertrags.

## 7. Datenschutz-/Consent-Bezug
- `privacyConsent` ist als technische Bestätigung des Formularhinweises zwingend.
- Statistik-/Analytics-Einwilligung ist **keine** Voraussetzung für die Anfrage.
- Attributionsfelder werden im Browser nur bei Statistikfreigabe angereichert und serverseitig erneut minimiert.
- Ein `consent_text_version`-Feld ist aktuell nicht Teil des implementierten Endpoint-Vertrags.

## 8. Weiterleitung an den Lead-Webhook
- **Bevorzugter Modus:** `LEAD_WEBHOOK_CONFIG` enthält atomar `{"url","token"}` als Secret. Die Pages Function sendet `{version:1, authToken, lead}` und akzeptiert nur eine JSON-Antwort mit exakt `{ok:true}`.
- **Übergangsmodus:** Nur wenn `LEAD_WEBHOOK_CONFIG` vollständig fehlt, darf `LEAD_WEBHOOK_URL` den Legacy-Payload ohne Auth-Envelope erhalten. Eine vorhandene, aber ungültige neue Config fällt niemals auf Legacy zurück.
- Ziel-URLs müssen HTTPS, Host `script.google.com`, den kanonischen `/macros/s/.../exec`-Pfad sowie leere Query/Fragmentteile haben.
- Tokens müssen 32–512 Zeichen lang, frei von Steuerzeichen und ohne führende/abschließende Leerzeichen sein.
- Kein Webhook-Token gehört in Browsercode, Git oder Dokumentation.

## 9. Fehlerfälle

| Fall | Antwort |
|------|---------|
| Origin fehlt/unzulässig | 403 |
| Payload zu groß | 413 |
| ungültiges JSON / Body | 400 |
| Schema-Validierung fehlgeschlagen | 400 |
| Methode unzulässig | 405 + `Allow: POST, OPTIONS` |
| Rate Limit | 429 |
| Rate-Limit-Binding fehlt | 500 generisch |
| Webhook-Konfiguration ungültig / Webhook nicht erreichbar / keine gültige Bestätigung im Auth-Modus | 502 |
| Erfolg | 200 + `{"ok":true}` |

Fehlerantworten geben keine Webhook-URL, Tokens, Stacktraces oder interne Anbieter-Details aus.

## 10. Logging ohne Secrets
- Erfolgs-/Fehlerlogs enthalten Zeitstempel, Ergebnis und generischen Fehlercode.
- Webhook-URL, Tokens und vollständige Lead-PII werden nicht geloggt.

## 11. Teststrategie
- Schema: vollständiger und minimaler gültiger Payload, Pflichtfelder, Literale, Defaults, Honeypot und Attribution.
- Endpoint: Methoden, Origins, Payload-Limit, JSON-Tiefe, KV-Fail-Closed, IP-/E-Mail-Rate-Limits.
- Webhook: Legacy- und Auth-Modus, ungültige Config, URL-Allowlist, Tokenregeln, Timeout/Upstreamfehler sowie strikte `{ok:true}`-Bestätigung.
- Frontend: Erfolg erst nach bestätigter Endpoint-Antwort; Fehler behält Eingaben und meldet keinen erfolgreichen Lead.
- Echte Produktionszustellung nur als kontrollierter synthetischer Test mit eindeutigem Testziel und nachgewiesenem Cleanup.

## 12. Deployment-Gates
Die Implementierung ist vorhanden. Für einen belastbaren Livebetrieb müssen getrennt erfüllt sein:
1. geprüfter Code/CI-Stand,
2. `PUBLIC_LEAD_FORM_ENABLED="true"` im freigegebenen Produktions-Build,
3. `RATE_LIMIT_KV` im Production-Environment,
4. bevorzugt ein gültiges verschlüsseltes `LEAD_WEBHOOK_CONFIG` statt des Legacy-Fallbacks,
5. kompatibler serverseitiger Apps-Script-Empfänger für den Auth-Envelope,
6. genau ein markierter End-to-End-Test mit anschließendem Cleanup.

## 13. Klare Grenze
- Das Vorhandensein des Endpoint-Codes ist kein Nachweis erfolgreicher CRM-Zustellung.
- Keine Produktions-Secrets in Git, Chat oder Drive dokumentieren.
- Der Legacy-Modus ist nur eine Übergangskompatibilität und kein Zielzustand.
- Externe Kampagnen-/Prospektversände sind von diesem Endpoint-Vertrag getrennt.

## 14. Nächster Cutover
Der authentifizierte Produktions-Cutover folgt `docs/crm/WEBHOOK_AUTH_CUTOVER.md`. Nach erfolgreicher Auth-Verifikation und Cleanup wird der Legacy-Fallback entfernt beziehungsweise nicht mehr konfiguriert.
