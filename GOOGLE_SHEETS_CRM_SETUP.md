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

## 4. Zugriffsweg: Google Apps Script Web App (kostenlos)

> Revidiert 2026-06-22: n8n + Service Account verworfen (Abo-Kosten), siehe `N8N_HOSTING_DECISION.md` §9b.

Kein Service Account, kein OAuth-Client nötig. Stattdessen ein an das Sheet
gebundenes Apps Script, das als Web App bereitgestellt wird und unter dem
Konto des Sheet-Eigentümers läuft (Google-Workspace-Gratis-Kontingente):

1. Sheet „HSB-CRM-Light" öffnen → **Erweiterungen → Apps Script**.
2. `Code.gs` mit einer `doPost(e)`-Funktion anlegen, die `e.postData.contents`
   als JSON parst, Pflichtfelder prüft, eine Dublettenprüfung gegen Tab
   „Leads" macht (siehe §6) und per `SpreadsheetApp` eine Zeile anhängt.
   Optional: `MailApp.sendEmail(...)` für die Sofort-Benachrichtigung an
   `info@hsb-boden.de` (ebenfalls kostenlos, im Tagesquota enthalten).
3. **Bereitstellen → Neue Bereitstellung → Web App**, Zugriff: „Jeder mit der
   URL" (oder „Jeder", je nach Apps-Script-Domain-Policy). Die resultierende
   URL (`https://script.google.com/macros/s/…/exec`) ist der Wert für
   `LEAD_WEBHOOK_URL`.
4. Die URL ist kein klassisches Geheimnis (sie kann nur Zeilen anhängen, nicht
   lesen), wird aber dennoch ausschließlich als Server-Secret gehalten, nie im
   Frontend (`PUBLIC_*`-Variablen).

Details zu API-Aktivierung/Scopes: `GOOGLE_API_SETUP.md`.

## 5. Testdaten
- 2–3 markierte Test-Leads (`Lead-ID = TEST-*`, `Opt-out = nein`, fiktive Firma).
- Keine echten personenbezogenen Daten in P0A.

## 6. Dublettenprüfung
- Vor Append: Schlüssel (Firma normalisiert + E-Mail/Domain) gegen Tab „Leads" prüfen.
- Treffer → Aktivität anhängen statt neuer Zeile.

## 7. Schreibtest
- Mock/Testlauf: eine Test-Zeile per `curl` direkt an die Apps-Script-Web-App-URL senden.
- Verifizieren: korrekte Spaltenzuordnung, Dublettenlogik.
- Testzeile danach kontrolliert markieren/entfernen.
- Nur nach Freigabe gegen echtes Sheet; vorher Mock.

## 8. Keine echten Credentials im Repo
- `LEAD_WEBHOOK_URL` nie committen; Ablage extern (`~/KI-System/05_Secrets/` bzw. Cloudflare-Worker-Secret).

## 9. Live-Gate
Keine Live-Anbindung an ein produktives CRM-Sheet ohne ausdrückliche Freigabe.

## 10. Abnahmekriterien (P0A-Review)
- Tab- und Spaltenstruktur vollständig und konsistent zu `CRM_LIGHT_SCHEMA.md`.
- Dublettenlogik definiert.
- Credential-Variante entschieden bzw. als offen markiert.
- Testdatenkonzept ohne echte PII.
