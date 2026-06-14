# P0B_TEST_PLAN — HSB-Boden

> Stand: 2026-06-14. Planung. Ausführung erst in P0B nach Freigabe. Build/Push/Deploy separat freizugeben.

## 1. Preflight
- Guard: `assert_canonical_project_path.sh hsb-boden`.
- `git status` sauber bis auf erlaubte Dateien.
- Website-Code-Diff-Ausgangswert dokumentieren.

## 2. Unit-/Validierungstests
- Schema gültig/ungültig (Pflichtfelder, `privacyConsent` muss true).
- Feldlängen, Typen, allowlist unbekannter Felder.
- Honeypot gefüllt → verworfen.

## 3. Integrationstest n8n Webhook
- Mock-n8n-Endpoint: Payload-Mapping prüfen gegen `ops/n8n/hsb-boden-lead-intake.json`.
- Fehler-/Timeout-Verhalten.

## 4. Google Sheets Append Test
- Testzeile (`Lead-ID = TEST-*`) appenden (Mock, dann nach Freigabe live).
- Spaltenzuordnung gegen `CRM_LIGHT_SCHEMA.md`.
- Dublettenlogik.
- Testzeile danach kontrolliert markieren/entfernen.

## 5. Testlead (End-to-End)
- Form → Endpoint → n8n → Sheet, nur nach ausdrücklicher Freigabe.

## 6. Negative Tests
- 400 (Validierung), 405 (Methode), 429 (Rate Limit), 502 (n8n nicht erreichbar).

## 7. Abschlussprüfung
- `npm run test:run`, `npm run check`.
- Website-Code-Diff dokumentieren.

## 8. Build
- `npm run build` nur nach Freigabe.

## 9. Push/Deploy
- Separat freizugeben; standardmäßig blockiert.
