# n8n Workflow: hsb-boden-lead-intake

## Zweck

Dieser Workflow verarbeitet Projektanfragen vom `hsb-boden` Kontaktformular.

## Struktur

Webhook POST `/hsb-boden-lead-intake`
→ Lead validieren und normalisieren
→ IF Lead gültig?
→ false: JSON 400 `invalid_payload`
→ true: E-Mail senden
→ Lead archivieren
→ JSON 200 `received`

## Import

1. In n8n öffnen.
2. Workflow importieren: `ops/n8n/hsb-boden-lead-intake.json`
3. E-Mail-Credentials im Node `Lead per E-Mail senden` setzen.
4. Platzhalter-Empfänger ersetzen: `LEAD_RECIPIENT_EMAIL_TO_SET_IN_N8N@example.invalid`
5. Optional Absender ersetzen: `noreply@example.invalid`

## Production

1. Workflow aktivieren.
2. Production Webhook URL kopieren.
3. In Cloudflare Pages als `PUBLIC_LEAD_ENDPOINT` setzen.
4. Neu deployen.
5. End-to-End-Test über echtes Formular durchführen.

## Hinweise

- Docker ist für die JSON-Erstellung nicht nötig.
- Eine laufende n8n-Instanz ist für Import, Test und Production nötig.
- Keine OpenAI-Node: Lead-Daten enthalten personenbezogene Daten; für die erste produktive Zustellung ist keine KI-Klassifikation nötig.
- `PUBLIC_LEAD_ACCESS_KEY` ist kein echtes Secret, weil `PUBLIC_*` Werte im Browser sichtbar sind.
