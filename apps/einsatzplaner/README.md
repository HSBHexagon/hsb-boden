# HEXAFLOOR Einsatzplanung

Vorhandene Benutzeroberfläche und Core aus `HEXAFLOOR_Einsatzplaner_KOSTENLOS.html`, Version 2, weiterverwendet. Eigenständiger Worker im HSB-Unternehmenskonto; keinerlei Änderungen an Website, Sales OS oder Vertriebs-CRM.

- URL: https://hexafloor-planer.hsb-boden.workers.dev/
- Cloudflare-Konto: `01dc37803d1c687b4f9d6249ec89f700` (`info@hsb-boden.de`).
- Datenbank: `hexafloor-einsatzplanung`, `4798da4e-9a20-4a74-abaa-ad58f6e26e5d`, EU-Jurisdiktion.
- Access: `hsb-hexagon.cloudflareaccess.com`, Anwendung `3d1482b5-3a3c-48d9-ad3f-575ff18f4288`, E-Mail-Einmalcode.
- Eingerichtet: `j-cherino@hsb-boden.de` und `j-post@hsb-boden.de`; zunächst Administratoren. Nur Administratoren können die Rolle des anderen Kontos ändern. Der letzte Administrator bleibt serverseitig geschützt.

## Entwicklung und Prüfung

Node 24. `npm ci`, `npm test`, `npm run check`, `npm run build`, `npm run deploy:dry-run`. Build muss vor einem manuellen Deployment laufen. Keine automatische Bereitstellung; eigener Quality-Workflow. `wrangler.jsonc` enthält keine Passwörter. Der Worker prüft jede Access-JWT-Signatur, Issuer, Audience und Ablaufzeit zusätzlich selbst.

Normale Schreibaufrufe: `POST /api/command`, `If-Match: "<revision>"`, JSON `{command:{type,...}}`, gleicher Origin. Befehle: worker, project, assign, unassign, absence, need, extend, crew. Server prüft und führt sie aus. Unzulässige oder veraltete Änderungen schreiben keine Daten. HTTP409 verlangt Neuladen und erneute Prüfung. Ganze Datenimporte, Wiederherstellungen, Audit- und Benutzerverwaltung sind Administratoren vorbehalten.

Stabile Projekt-ID und eindeutige Projektnummer; Fremdschlüssel verbinden Mitarbeiter, Projekte, Einsätze und Abwesenheiten. Keine späteren Fachmodule implementiert. Personen- und Projektdaten bleiben ausschließlich in der geschützten Datenbank, niemals in GitHub. Tests verwenden ausdrücklich MOCK_DATA.

## Sicherung und Wiederherstellung

Jede erfolgreiche Planänderung sichert den vorherigen Zustand in derselben D1-Transaktion. Die letzten 30 Stände bleiben erhalten. Unter Projekte & Team → Sicherung & Daten → Automatische Sicherungen kann ein Administrator einen Stand wiederherstellen. Vorher entsteht wiederum eine Sicherung. JSON-Export für eine geschützte Sicherung außerhalb des Cloudflare-Kontos vorhanden; diese zusätzliche Sicherung erfolgt durch den Administrator. Keine automatische externe Sicherung behauptet.

Serverseitiger Audit enthält Akteur, Zeitpunkt, Revision, SHA-256 und konkreten Änderungsbefehl. Abwesenheitsarten und interne Notizen erscheinen ausschließlich in berechtigten Ansichten bzw. Sicherungen, nie als eigene Felder im WhatsApp-Export. WhatsApp wird nicht automatisch kontaktiert.

## Nachweisstand 21.10.2026

Lokal: 34 Tests bestanden (inklusive SQLite-Transaktionen, getrennter DOM-Sitzungen, Rechte, Ausfälle/Ersatz, Samstag, Verlängerung, Wiederherstellung). Website unverändert:335 Tests, Typprüfung, Build und Deployment-Trockenlauf bestanden. Sales-OS-Suite:95 bestanden; sechs Tests aus `test_com_mailbox_manager.py` scheitern an hier fehlenden KASServer-Zugangsdaten. Kein Zugriff auf Mailserver und kein Versand erfolgt.

Live: Worker bereitgestellt, EU-D1-Schema und zwei Administratorrollen zurückgelesen; unauthentifizierter URL-Aufruf führt per HTTP302 zum Access-Login. Noch keine produktiven Unternehmensdaten importiert. Angemeldeter Browserablauf, zwei echte angemeldete Browsersitzungen, reale gleichzeitige API-Änderungen und 390px-Darstellung der angemeldeten App sind noch nicht bestätigt. Browser Use scheiterte auf Desktop und bei 390px an ERR_QUIC_PROTOCOL_ERROR; außerdem scheiterte der lokale Browserdownload. DOM-Tests sind kein Ersatz für mobile Darstellungstests.

Keine Tarif-Upgrades oder neuen kostenpflichtigen Abonnements aktiviert. Kostenlose Workers-/D1-Funktionen eingesetzt. Verbindliche Abrechnungsbestätigung bleibt offen: Die OAuth-Verbindung darf das Billing-API nicht lesen (HTTP403). Im Free-Tarif gelten Kontingente; keine automatische kostenpflichtige Erweiterung implementiert.
