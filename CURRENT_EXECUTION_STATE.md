# CURRENT_EXECUTION_STATE.md

Stand: 2026-06-20
Projekt: HEXAFLOOR / HSB-Boden
Phase: **PRÄSENTATIONS- UND VERSANDVORBEREITUNG**

## 1. Aktuelle Phase: kontrollierte Vorbereitung
Der aktuelle Repo-Stand ist technisch prüfbar und als Präsentationsgrundlage nutzbar. Live-Akquise, n8n, SMTP, CRM-Light, Push und Deploy bleiben blockiert, bis die zugehörigen Freigaben und externen Systeme real geprüft sind.

## 2. Fertigstellungsgrad
*   **Website-Technik:** lokal verifiziert (`test:run`, `check`, `build` am 2026-06-20 grün); kein Deploy in diesem Lauf.
*   **Content & Referenzen:** im Repo vorhanden; öffentliche Claims/Logos bleiben freigabepflichtig.
*   **Rechtliches:** Texte vorhanden, finale fachliche/rechtliche Abnahme offen.
*   **Lead-System:** Formular und n8n-Workflow vorhanden; Zustellung, Webhook, SMTP und CRM-Light nicht live.
*   **Vertriebs-Assets:** Flyer-PDFs und Mailtexte vorhanden; Leadliste im aktuellen Repo nicht gefunden.

## 3. Offene Aufgaben (Status-Check)

| Bereich | Status | Details |
|---|---|---|
| **Logos/Referenzen sichtbar?** | vorhanden | Website-Daten enthalten freigegebene und anonymisierte Referenzen; finale öffentliche Nutzung bleibt prüfpflichtig. |
| **Präsentation heute?** | ja | Website-Build, Flyer-PDFs und Projektstory sind lokal verwendbar. |
| **Flyer konsistent?** | teilweise | PDF-Dateien vorhanden; Mail-Anhang wurde auf den echten Repo-Dateinamen korrigiert. |
| **Akquise-Mail konsistent?** | vorbereitet | Mailtexte sind nutzbar, aber nur mit manuellem Personalisierungssatz und Freigabe. |
| **Lead-Prozess vollständig?** | nein | `PUBLIC_LEAD_ENDPOINT` leer, n8n inactive, SMTP-Platzhalter, CRM-Light nicht live. |
| **Leadliste vorhanden?** | nicht im Repo | Ältere Docs erwähnen CSV mit 30 Leads; aktueller Arbeitsbaum enthält sie nicht. |

## 4. Nächster kritischer Pfad

1.  **Heute zwingend:** Präsentations- und Versandunterlagen ohne falsche Behauptungen nutzen.
2.  **Heute sinnvoll:** Test-/Seed-Mail manuell vorbereiten, aber keinen Serienversand starten.
3.  **Blocker:** Webhook, SMTP, n8n-Publish, CRM-Light, Empfängerliste und Recht-/Opt-out-Prozess sind nicht live verifiziert.

## 5. Reihenfolge bis zum Versand

1.  **Präsentation:** Lokalen oder bestehenden Preview-Stand zeigen, Flyer `public/HSB-Flyer-Joel-Cherino.pdf` verwenden.
2.  **Versandvorbereitung:** Empfängerliste extern verifizieren, Personalisierungssatz füllen, Seed-Mail senden, Opt-out/Antwortbearbeitung klären.
3.  **Nächster Change-Block:** P0B-Freigabe einholen, dann Endpoint/Rate-Limit/n8n/CRM-Light als eigenen technischen Block umsetzen.
4.  **Nicht heute ohne Freigabe:** Push, Deploy, Production-Cutover, n8n-Livebetrieb, SMTP-Credentials, Serienkampagne.

---
*Dokumentation der Execution Phase beendet. Stoppe wie angewiesen.*
