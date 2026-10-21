# HEXAFLOOR Einsatzplanung

Vorhandene Benutzeroberfläche und Core aus `HEXAFLOOR_Einsatzplaner_KOSTENLOS.html`, Version 2, weiterverwendet. Eigenständiger Worker im HSB-Unternehmenskonto; keinerlei Änderungen an Website, Sales OS oder Vertriebs-CRM.

- URL: https://hexafloor-planer.hsb-boden.workers.dev/
- Cloudflare-Konto: `01dc37803d1c687b4f9d6249ec89f700` (`info@hsb-boden.de`).
- Datenbank: `hexafloor-einsatzplanung`, `4798da4e-9a20-4a74-abaa-ad58f6e26e5d`, EU-Jurisdiktion.
- Access: `hsb-hexagon.cloudflareaccess.com`, Anwendung `3d1482b5-3a3c-48d9-ad3f-575ff18f4288`, E-Mail-Einmalcode.
- Eingerichtet: `j-cherino@hsb-boden.de` und `j-post@hsb-boden.de`; zunächst Administratoren. Nur Administratoren können die Rolle des anderen Kontos ändern. Der letzte Administrator bleibt serverseitig geschützt.

## Entwicklung und Prüfung

Node 24. `npm ci`, `npm test`, `npm run check`, `npm run build`, `npm run deploy:dry-run`. Build muss vor einem manuellen Deployment laufen. Keine automatische Bereitstellung; eigener Quality-Workflow. `wrangler.jsonc` enthält keine Passwörter. Der Worker prüft jede Access-JWT-Signatur, Issuer, Audience und Ablaufzeit zusätzlich selbst.

Normale Schreibaufrufe: `POST /api/command`, `If-Match: "<revision>"`, JSON `{command:{type,...}}`, gleicher Origin. Befehle: worker, project, assign, unassign, absence, edit-absence, cancel-absence, need, extend, crew. Server prüft und führt sie aus. Unzulässige oder veraltete Änderungen schreiben keine Daten. HTTP409 verlangt Neuladen und erneute Prüfung. Ganze Datenimporte, Wiederherstellungen, Audit- und Benutzerverwaltung sind Administratoren vorbehalten.

Die einfache Tagesansicht zeigt je Projekt benötigte, eingeteilte und fehlende Monteure. Abwesenheit eintragen aktualisiert die Besetzung ohne Ersatzdialog. Unter Abwesenheit können Einträge korrigiert oder aufgehoben werden; frühere Einsätze werden nur nach erneuter Konfliktprüfung wiederhergestellt. Nicht wiederherstellbare Einsätze werden einzeln angezeigt. Kein WhatsApp-Bereich in der normalen Bedienung, kein automatischer Versand.

Stabile Projekt-ID und eindeutige Projektnummer; Fremdschlüssel verbinden Mitarbeiter, Projekte, Einsätze und Abwesenheiten. Keine späteren Fachmodule implementiert. Personen- und Projektdaten bleiben ausschließlich in der geschützten Datenbank, niemals in GitHub. Tests verwenden ausdrücklich MOCK_DATA.

## Sicherung und Wiederherstellung

Jede erfolgreiche Planänderung sichert den vorherigen Zustand in derselben D1-Transaktion. Die letzten 30 Stände bleiben erhalten. Unter Projekte & Team → Sicherung & Daten → Automatische Sicherungen kann ein Administrator einen Stand wiederherstellen. Vorher entsteht wiederum eine Sicherung. JSON-Export für eine geschützte Sicherung außerhalb des Cloudflare-Kontos vorhanden; diese zusätzliche Sicherung erfolgt durch den Administrator. Keine automatische externe Sicherung behauptet.

Serverseitiger Audit enthält Akteur, Zeitpunkt, Revision, SHA-256 und konkreten Änderungsbefehl. Abwesenheitsarten und interne Notizen erscheinen ausschließlich in berechtigten Ansichten bzw. Sicherungen, nie als eigene Felder im WhatsApp-Export. WhatsApp wird nicht automatisch kontaktiert.

## Nachweisstand 21.10.2026

Lokal: 39 Tests bestanden (inklusive SQLite-Transaktionen, getrennter DOM-Sitzungen, Rechte, Ausfälle, Samstag, Verlängerung, Sicherungen sowie atomarer Abwesenheitskorrektur). Syntaxprüfung, Build und Wrangler-Dry-Run bestanden. Zusätzlich echter Chromium-Lauf mit zwei unabhängigen Browserkontexten gegen die lokalen API-Routen und SQLite: identischer Datenstand, Ausfall 3→2 und Korrektur zurück auf 3, Bearbeiten/Aufheben über die Oberfläche, konkurrierende Schreibaufrufe mit HTTP200/409. Desktop 1280px und Smartphone-Emulation 390px ohne horizontales Überlaufen oder JavaScript-Seitenfehler. Testidentität lokal injiziert: kein Nachweis für echten Cloudflare-Login. Reproduzierbar mit `node test/browser-check.mjs` nach Installation der bestehenden Website-Entwicklungsabhängigkeiten und Playwright Chromium; alternativ `HEXAFLOOR_CHROMIUM_EXECUTABLE` auf vorhandenen Chromium setzen. Optional `HEXAFLOOR_BROWSER_EVIDENCE` für Screenshots. Kein neues Abonnement nötig.

Website bleibt unverändert. Vorheriger Baseline-Befund Sales OS:95 bestanden; sechs Tests aus `test_com_mailbox_manager.py` scheiterten an fehlenden KASServer-Zugangsdaten. Nicht erneut gegen Mailserver ausgeführt; kein Versand erfolgt.

Live, historisch verifiziert: erster Worker bereitgestellt, EU-D1-Schema und zwei Administratorrollen zurückgelesen; unauthentifizierter URL-Aufruf führt zum Access-Login. Noch keine produktiven Unternehmensdaten importiert. Aktueller Blocker: Cloudflare-Connector liefert bei `search` und lesendem `execute` jeweils MCP -32603 Internal error; Veröffentlichung der vereinfachten und korrigierten Version nicht bestätigt. Browser Use erkennt bei 390px die Access-Weiterleitung, scheitert anschließend mit ERR_SOCKS_CONNECTION_FAILED. Echte angemeldete Live-Sitzungen, Live-Konflikte und Live-Wiederherstellung bleiben unverifiziert. Draft-PR #462 / Branch `feat/hexafloor-central-planner`, kein Merge. Nächster Schritt ausschließlich nach Wiederherstellung der Verbindung: getestetes Worker-Bundle veröffentlichen und denselben Ablauf angemeldet live prüfen; keine neue Planung oder Plattformmigration.

Keine Tarif-Upgrades oder neuen kostenpflichtigen Abonnements aktiviert. Kostenlose Workers-/D1-Funktionen eingesetzt. Verbindliche Abrechnungsbestätigung bleibt offen: Die OAuth-Verbindung darf das Billing-API nicht lesen (HTTP403). Im Free-Tarif gelten Kontingente; keine automatische kostenpflichtige Erweiterung implementiert.
