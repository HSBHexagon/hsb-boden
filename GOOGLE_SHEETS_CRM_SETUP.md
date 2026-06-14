# GOOGLE_SHEETS_CRM_SETUP — HSB-Boden

> P0A-Setup-Spezifikation. Stand: 2026-06-14. Keine echten Credentials im Repo, keine Live-Aktivierung ohne Freigabe.

## 1. Sheet-Struktur
Eine Google-Sheets-Datei „HSB-CRM-Light" mit mehreren Tabs. Felder gemäß `CRM_LIGHT_SCHEMA.md`.

## 2. Tabs

| Tab | Zweck | Schlüssel |
|-----|-------|-----------|
| Leads | Stammdaten je Lead | Lead-ID |
| Aktivitäten | Kontakt-/Follow-up-Historie | Aktivitäts-ID + Lead-ID |
| Kampagnen | Kampagnen/Quellen + UTM | Kampagnen-ID |
| Follow-ups | offene Wiedervorlagen | Lead-ID + Follow-up-Datum |
| Statuswerte | erlaubte Status-/Enum-Werte | Statusname |

## 3. Spalten (Tab „Leads")
Gemäß `CRM_LIGHT_SCHEMA.md`: Lead-ID, Firma, Standort, Region, Branche, Tier, Ansprechpartner, Rolle, E-Mail, Telefon, Website, Quelle, Kampagne, Score, Status, Nächste Aktion, Follow-up-Datum, Interesse, Projektart, Fläche geschätzt, Belastungsart, Sanierungsfenster, Notizen, Opt-out-Status, Letzter Kontakt, Verantwortlicher.

## 4. Service Account vs OAuth

| Variante | Einsatz | Empfehlung |
|----------|---------|------------|
| Service Account | interner Sheets-Zugriff (n8n) | bevorzugt für CRM-Light |
| OAuth Client | Nutzerkontext (Gmail/Calendar) | nur bei Bedarf |

Details: `GOOGLE_API_SETUP.md`.

## 5. Testdaten
- 2–3 markierte Test-Leads (`Lead-ID = TEST-*`, `Opt-out = nein`, fiktive Firma).
- Keine echten personenbezogenen Daten in P0A.

## 6. Dublettenprüfung
- Vor Append: Schlüssel (Firma normalisiert + E-Mail/Domain) gegen Tab „Leads" prüfen.
- Treffer → Aktivität anhängen statt neuer Zeile.

## 7. n8n-Schreibtest
- Mock/Testlauf: eine Test-Zeile via n8n appenden.
- Verifizieren: korrekte Spaltenzuordnung, Dublettenlogik.
- Testzeile danach kontrolliert markieren/entfernen.
- Nur nach Freigabe gegen echtes Sheet; vorher Mock.

## 8. Keine echten Credentials im Repo
- Service-Account-/OAuth-Keys nie committen; Ablage extern (Secrets/n8n).

## 9. Live-Gate
Keine Live-Anbindung an ein produktives CRM-Sheet ohne ausdrückliche Freigabe.

## 10. Abnahmekriterien (P0A-Review)
- Tab- und Spaltenstruktur vollständig und konsistent zu `CRM_LIGHT_SCHEMA.md`.
- Dublettenlogik definiert.
- Credential-Variante entschieden bzw. als offen markiert.
- Testdatenkonzept ohne echte PII.
