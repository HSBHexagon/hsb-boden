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

Kein Service Account und kein OAuth-Client nötig. Stattdessen ein an das Sheet
gebundenes, token-authentifiziertes Apps Script, das als Web App unter dem
Konto des Sheet-Eigentümers läuft (Google-Workspace-Kontingente). Der verbindliche
Migrations- und Prüfpfad steht in `docs/crm/WEBHOOK_AUTH_CUTOVER.md`:

1. Sheet „HSB-CRM-Light" öffnen → **Erweiterungen → Apps Script**.
2. `Code.gs` mit einer `doPost(e)`-Funktion anlegen, die zuerst den authentifizierten
   Umschlag gegen `HSB_WEBHOOK_AUTH_TOKEN` aus den Script Properties prüft, danach
   Pflichtfelder validiert, eine Dublettenprüfung gegen Tab
   „Leads" macht (siehe §6) und per `SpreadsheetApp` eine Zeile anhängt.
   Optional: `MailApp.sendEmail(...)` für die Sofort-Benachrichtigung an
   `info@hsb-boden.de` (ebenfalls kostenlos, im Tagesquota enthalten).
3. **Bereitstellen → Neue Bereitstellung → Web App**. Die Plattformfreigabe macht
   den Pfad technisch öffentlich erreichbar; die Anwendungsauthentifizierung muss
   deshalb vor jedem Sheet-Zugriff im Script stattfinden.
4. URL und Token werden gemeinsam als verschlüsseltes Cloudflare-Pages-Secret
   `LEAD_WEBHOOK_CONFIG` gehalten, nie im Frontend oder Repo. Die URL allein ist
   ausdrücklich keine Sicherheitsgrenze.

Details zu API-Aktivierung/Scopes: `GOOGLE_API_SETUP.md`.

## 5. Testdaten
- 2–3 markierte Test-Leads (`Lead-ID = TEST-*`, `Opt-out = nein`, fiktive Firma).
- Keine echten personenbezogenen Daten in P0A.

## 6. Dublettenprüfung
- Vor Append: Schlüssel (Firma normalisiert + E-Mail/Domain) gegen Tab „Leads" prüfen.
- Treffer → Aktivität anhängen statt neuer Zeile.

## 7. Schreibtest
- Mock/Testlauf zuerst gegen die Pages Function im isolierten Preview. Keine direkte
  POST-Anfrage an die Apps-Script-Web-App; der echte Pfad ist `/api/lead`.
- Verifizieren: korrekte Spaltenzuordnung, Dublettenlogik.
- Testzeile danach kontrolliert markieren/entfernen.
- Nur nach Freigabe gegen echtes Sheet; vorher Mock.

## 8. Keine echten Credentials im Repo
- `LEAD_WEBHOOK_CONFIG` und den temporären Legacy-Fallback `LEAD_WEBHOOK_URL` nie
  committen. Echte Werte ausschließlich im vorgesehenen Secret-Tresor beziehungsweise
  als verschlüsselte Cloudflare-Pages-Secrets halten.

## 9. Live-Gate
Keine Live-Anbindung an ein produktives CRM-Sheet ohne ausdrückliche Freigabe.

## 10. Abnahmekriterien (P0A-Review)
- Tab- und Spaltenstruktur vollständig und konsistent zu `CRM_LIGHT_SCHEMA.md`.
- Dublettenlogik definiert.
- Credential-Variante entschieden bzw. als offen markiert.
- Testdatenkonzept ohne echte PII.
