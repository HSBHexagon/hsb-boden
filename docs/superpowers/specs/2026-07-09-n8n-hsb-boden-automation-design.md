# n8n-Automation für HSB-Boden — Design

Stand: 2026-07-09. Status: abgeschlossen als Referenzimplementierung (siehe Abschnitt "Status" am Ende).

## Ausgangslage

Am 2026-06-22 wurde n8n für HSB-Boden explizit verworfen (`N8N_HOSTING_DECISION.md` §9b), weil n8n Cloud ein laufendes Abo bedeutet hätte ("die nehmen, die gratis ist und bleibt"). Ersatz war eine kostenlose Google Apps Script Web App, die seither produktiv läuft (`/api/lead` → Apps Script → CRM-Sheet). `CRM_LIGHT_SCHEMA.md` hält fest: *"n8n ist nicht die aktive Lead-Intake-Lösung."*

Am selben Tag (2026-07-09) wurde in einer separaten Session eine **lokale, self-hosted n8n-Instanz** für ein anderes Projekt (Schuldenmanagement/SCMS, `~/KI-System/notion-platform`) vollständig eingerichtet und verifiziert: Outlook-, Google-Drive-, Notion- und OpenAI-Credentials verbunden, Workflow `SCMS-01` lauffähig. Diese Instanz ist self-hosted und kostenlos (Docker, kein Abo) — der ursprüngliche Kosteneinwand gegen n8n bei HSB-Boden entfällt damit grundsätzlich.

**Nutzerentscheidung dieser Session:** Die alte n8n-Ablehnung für HSB-Boden wird revidiert. n8n übernimmt die in `N8N_AUTOMATION_PLAN.md` beschriebenen Pipelines 2–5 (Dedupe/Scoring, Follow-up-Reminder, Tagesreport, Neu-Lead-Benachrichtigung) zusätzlich zum bestehenden Formularpfad, in einer eigenen, von allen bestehenden n8n-Instanzen getrennten Umgebung.

## Ziel

Alle fünf in `N8N_AUTOMATION_PLAN.md` geplanten Pipelines mit einer dedizierten, self-hosted n8n-Instanz für HSB-Boden umsetzen, ohne den bereits geprüften öffentlichen Formularpfad (`/api/lead`, Zod/Rate-Limit/Honeypot/Origin-Check) zu verändern und ohne bestehende n8n-Instanzen (SCMS, KI-OS) anzutasten.

## Explizit ausgeschlossener Scope

- **Kaltakquise-Kampagne (6424 Leads, `PHASE_7_COMPLIANCE_GATE.md`)** — keine Pipeline dieses Designs greift auf diese Leads zu, sendet an sie oder automatisiert irgendeinen Versandschritt. Das Gate bleibt vollständig in Kraft, unabhängig von diesem n8n-Aufbau.
- **Veränderung des bestehenden `/api/lead`-Endpunkts** (Validierung, Rate-Limit, Honeypot, Origin-Check) — bleibt exakt wie es ist.
- **Veränderung der bestehenden n8n-Instanzen** `notion-platform` (SCMS, Port 5678) und `04_Developer/n8n-ki-os` (Docker/Postgres, KI-Task-Capture) — beide bleiben unangetastet, keine gemeinsame Nutzung von Ports, Volumes oder Credential-Stores.
- **Automatisierter Mailversand an Leads** — jede Pipeline in diesem Design benachrichtigt ausschließlich intern (HSB-Boden-Verantwortliche), nie den Lead selbst.
- Migration von Sheets zu Supabase/CRM (im `N8N_AUTOMATION_PLAN.md` als "optional/später" markiert) — nicht Teil dieses Designs.
- **Große KI-System-Reorganisation, neue Top-Level-Ordnerstruktur, allgemeine Foundation-Spec, Account-Migration, Notion-Workspace-Verschiebung** — bewusst nicht Teil dieses Designs (siehe Abschnitt "Identity- und Boundary-Regeln").

## Identity- und Boundary-Regeln

Diese Regeln wurden in dieser Session verbindlich vereinbart. Sie gelten für alle Bestandteile dieses Designs, ohne dass dafür eine Account-Migration, Notion-Umstrukturierung oder KI-System-weite Reorganisation nötig ist.

- **`cherinojoel@gmail.com` ist der vorläufige gewerbliche Bootstrap-Account** für HSB-Boden-Automation (n8n-OAuth-Credentials, sofern keine echte HSB-Boden-Adresse verfügbar ist). Technisch verifiziert (2026-07-09, per `google-workspace-*`-MCP-Statusabfrage): Die drei bestehenden Google-Workspace-Connector-Profile (`hsb-boden`, `cherinojoel`, `cherinodiaz`) sind aktuell **alle** auf denselben Account `cherinojoel@gmail.com` authentifiziert — es besteht noch **keine** echte technische Trennung zwischen den Profil-Labels. Das ist eine bekannte Lücke, kein Zielzustand.
- **`cherinodiaz@outlook.com` bleibt privat/rechtlich** und darf in keinem HSB-Boden-n8n-Workflow als Credential verwendet werden.
- **Eine spätere echte HSB-Boden-Geschäftsidentität** (z. B. `info@hsb-boden.de` / `j-cherino@hsb-boden.de`) ist das Migrationsziel für Produktion, wird in diesem Design aber nur dokumentiert, nicht erzwungen — abhängig von Schritt 3 im Rollout (siehe unten) und einer separaten Freigabe.
- **Keine privaten Daten (Schuldenmanagement, Vollstreckung, Mecklenburgische/FKF, private Rechtsangelegenheiten) in HSB-Boden-n8n-Workflows, keine HSB-Boden-Daten in privaten n8n-Workflows.** Durchgesetzt durch die vollständige Instanztrennung (siehe unten).
- **Secrets:** keine Secrets in Git, Notion, Google Drive, Obsidian, Markdown oder Logs; kein `.env` committen; keine OAuth-Exports mit Tokens speichern; n8n-Credentials bleiben ausschließlich im n8n-Credential-Store.
- **Kein produktiver Versand, kein DNS-/Cloudflare-Cutover, keine Account-Migration** ohne separate, ausdrückliche Freigabe außerhalb dieses Designs.

## Architektur

### Instanztrennung

| Instanz | Zweck | Ort | Port | Status |
|---|---|---|---|---|
| B: SCMS/Schuldenmanagement | Outlook/GDrive/Notion/OpenAI, `SCMS-01`-Workflow | `~/KI-System/notion-platform/workers/local-stub/` | 5678 | läuft, unangetastet |
| A: KI-OS Task-Capture | Obsidian-Brain-Automation | `~/KI-System/04_Developer/n8n-ki-os/` | — | dormant, unangetastet |
| C: HSB-Boden (neu) | Lead-Dedupe/Scoring, Follow-ups, Reports, Benachrichtigung | `~/KI-System/04_Developer/n8n-hsb-boden/` (Laufzeit) + `hsb-boden/ops/n8n/` (Workflow-Exporte, Doku) | 5679 | neu aufzusetzen |

Instanz C teilt keine Ports, Docker-Volumes, Credentials oder Datenverzeichnisse mit A oder B. **[PLATTFORMFÄHIG]** Das Muster "eine Instanz pro Vertrauenszone (privat / business-bootstrap / business-canonical), keine geteilten Ports/Volumes/Credentials" ist unabhängig von HSB-Boden und eignet sich als Vorlage für jede künftige Projekt-Instanz.

### Ordnerstruktur (neu, nur innerhalb der bestehenden KI-System-Struktur)

```
~/KI-System/04_Developer/n8n-hsb-boden/          # Laufzeit: Docker-Compose, Volumes, .env — NICHT in Git
  docker-compose.yml
  n8n_data/
  postgres_data/
  .env

~/KI-System/02_Projects/active/hsb-boden/ops/n8n/   # versionskontrolliert
  workflows/
    01_lead_dedupe_scoring.json
    02_followup_reminder.json
    03_daily_report.json
    04_new_lead_notification.json
  README.md

~/KI-System/05_Secrets/hsb-boden/n8n.env         # Secrets, wie N8N_HOSTING_DECISION.md §5 vorsieht
```

Kein neuer Top-Level-Ordner unter `~/KI-System/`, keine Änderung an der bestehenden, in `CANONICAL_STATE.md` dokumentierten Struktur. **[PLATTFORMFÄHIG]** Die Dreiteilung Laufzeit (`04_Developer/n8n-<projekt>/`) / versionskontrollierte Workflow-Exporte (im jeweiligen Projekt-Repo unter `ops/n8n/`) / Secrets (`05_Secrets/<projekt>/`) ist projektunabhängig und als Namenskonvention für künftige n8n-Instanzen wiederverwendbar.

### Datenfluss (Hybrid)

```
Website-Formular
   → /api/lead (Cloudflare Pages Function, unverändert)
   → Apps Script Web App (unverändert, schreibt Lead-Zeile in CRM-Sheet)
   → zusätzlich: Apps Script ruft n8n-Webhook auf (fire-and-forget; Fehler dort blockieren den Sheet-Write nicht)
        → n8n: Dedupe/Scoring (Pipeline 1) → Sheet-Update (Score/Status-Spalte)
        → n8n: Neu-Lead-Benachrichtigung intern (Pipeline 4)

n8n Cron-Trigger (zeitgesteuert, unabhängig vom Formular):
   → Follow-up-Reminder (Pipeline 2): täglich Sheet nach fälligen Follow-up-Daten scannen → interne Mail/Task
   → Tagesreport (Pipeline 3): tägliche Zusammenfassung neuer/offener Leads → Mail an j-cherino@hsb-boden.de
```

Der Formularpfad bleibt also die alleinige öffentliche Eintrittsstelle; n8n hängt als zusätzlicher, nicht-blockierender Konsument daran und übernimmt separat die zeitgesteuerten Pipelines. **[PLATTFORMFÄHIG]** Das Hybrid-Muster "bestehender, geprüfter öffentlicher Eingang bleibt unverändert; n8n hängt sich non-blocking als zusätzlicher Konsument an, statt den Eingang zu ersetzen" ist die risikoärmste Migrationsstrategie für jedes Projekt mit bereits produktivem, sicherheitsgeprüftem Endpunkt.

## Sicherheits- und Betriebshärtung

Abgeleitet u. a. aus dem Redirect-URI-Bug, der bei der SCMS-Instanz am selben Tag nachträglich gefixt werden musste (`N8N_HOST`/`WEBHOOK_URL` zeigten auf `127.0.0.1` statt auf die tatsächlich erreichbare Adresse) — hier von Anfang an korrekt konfiguriert. **[PLATTFORMFÄHIG]** Die gesamte folgende Liste ist projektunabhängig und sollte für jede künftige self-hosted-n8n-Instanz als Checkliste gelten:

- `N8N_ENCRYPTION_KEY` explizit setzen, in `05_Secrets/hsb-boden/` sichern (sonst sind Credentials nach Neustart/Restore unlesbar).
- `N8N_HOST` / `N8N_EDITOR_BASE_URL` / `WEBHOOK_URL` von Anfang an auf die öffentliche Cloudflare-Tunnel-Domain setzen, nicht auf `127.0.0.1`/`localhost`.
- Öffentliche Erreichbarkeit über **Cloudflare Tunnel** (kostenlos, kein Portforwarding) unter einer HSB-Boden-Subdomain (z. B. `n8n.hsb-boden.de`) — vorausgesetzt die korrekte Cloudflare-Zone liegt im `info@hsb-boden.de`-Account (die im Handoff dokumentierte doppelte Zone im `cherinojoel`-Account ist dafür nicht zu verwenden).
- **Editor-UI hinter Cloudflare-Access-Policy** (nur authentifizierte Nutzer); **nur der Webhook-Pfad** bleibt öffentlich offen — getrennte Access-Regeln pro Pfad im selben Tunnel.
- `N8N_USER_MANAGEMENT_DISABLED` **nicht** auf `true` setzen (im Unterschied zur rein lokalen SCMS-Instanz) — Login/Basic-Auth aktiv, da öffentlich erreichbar.
- Docker-Image-Version pinnen (kein `:latest`), Container non-root, `restart: unless-stopped`, Ressourcen-Limits.
- Postgres-Backup via `pg_dump`-Cron, Ziel außerhalb des Git-Repos.
- `EXECUTIONS_DATA_SAVE_ON_SUCCESS=none`, Fehler-Executions behalten (Debugging), analog zum bestehenden `n8n-ki-os`-Muster.
- Zusätzliche Cloudflare-WAF-Regel (Rate-Limit) auf dem Webhook-Pfad als weitere Schicht vor n8n.
- n8n-Error-Workflow: bei Pipeline-Fehlschlag automatische interne Benachrichtigung, damit ein stiller Ausfall nicht unbemerkt bleibt. **[PLATTFORMFÄHIG]** Ein generischer "Error-Workflow → interne Benachrichtigung"-Baustein ist direkt auf jede künftige n8n-Instanz übertragbar.

### Google/Microsoft-Konten für Credentials

OAuth-Credentials (Google, Microsoft, SMTP) werden vorläufig unter `cherinojoel@gmail.com` angelegt (siehe "Identity- und Boundary-Regeln" oben) — organisatorisch als HSB-Boden-Bootstrap-Credentials gekennzeichnet, technisch aber noch derselbe Account wie die anderen Profile. Migration zu einer echten HSB-Boden-Adresse ist ein späterer, separat freizugebender Schritt. Redirect-URI wird von Beginn an korrekt auf die Tunnel-Domain gesetzt (kein `127.0.0.1`/`localhost`-Fehler wie bei der SCMS-Einrichtung).

## Pipelines

1. **Lead-Dedupe/Scoring** — getriggert vom Apps-Script-Webhook-Call. Dublettenprüfung nach den in `CRM_LIGHT_SCHEMA.md` definierten Keys (E-Mail, Website, Firma+Standort, Firma+Ansprechpartner, Telefon), anschließend Scoring gemäß `ACQUISITION_SYSTEM_PLAN.md`, Ergebnis zurück ins Sheet (Score-/Status-Spalte).
2. **Follow-up-Reminder** — täglicher Cron, scannt Sheet nach `Follow-up-Datum <= heute` und `Status` nicht in `gewonnen/verloren/opt-out`, sendet interne Erinnerung (Mail/Task) an `Verantwortlicher`.
3. **Tagesreport** — täglicher Cron, fasst neue/offene Leads des Tages zusammen, Mail an `j-cherino@hsb-boden.de`.
4. **Neu-Lead-Benachrichtigung** — getriggert vom Apps-Script-Webhook-Call, sofortige interne Benachrichtigung bei neuem Formular-Lead.

Alle vier Pipelines sind rein intern (kein Kontakt zum Lead) und berühren `Versandfreigabe=no`-Zeilen nur lesend (Dedupe/Scoring). **[PLATTFORMFÄHIG]** Die Grundregel "Automation darf CRM-Daten lesen/anreichern, aber niemals an den Kontakt selbst senden, solange kein Compliance-Gate bestanden ist" ist als Muster auf jedes Projekt mit vergleichbarem Compliance-Gate übertragbar.

## Compliance-Grenzen (hart, unverändert)

- Kein Workflow sendet Mail an Leads.
- Die Kaltakquise-Kampagne bleibt vollständig außerhalb — kein Zugriff, kein Trigger, keine Automatisierung.
- `Versandfreigabe=no`-Leads werden von keiner Pipeline aktiv bearbeitet, nur lesend fürs Dedupe/Scoring einbezogen.
- Keine privaten Schulden-/Rechts-/Mecklenburgische-/FKF-Daten in HSB-Boden-Workflows; keine HSB-Boden-Daten in privaten Workflows (siehe "Identity- und Boundary-Regeln").

## Rollout-Schritte

1. Instanz `n8n-hsb-boden` lokal aufsetzen (Docker, Härtung s. o.), zunächst ohne Live-Tunnel.
2. Cloudflare Tunnel + Access-Policy einrichten, gegen `n8n.hsb-boden.de` testen (nur Editor-Zugriff, kein Produktivverkehr) — Voraussetzung: Cloudflare-Zonen-Bereinigung (siehe "Offene Punkte").
3. OAuth-Credentials vorläufig unter `cherinojoel@gmail.com` anlegen (Bootstrap, siehe Identity-Regeln), spätere Migration zu einer echten HSB-Boden-Adresse separat freizugeben.
4. Alle vier Pipelines bauen, gegen eine Test-Sheet-Kopie verifizieren (nicht das Produktions-Sheet).
5. Apps Script um den zusätzlichen n8n-Webhook-Call erweitern (non-blocking), gegen die Test-Instanz verifizieren.
6. Erst nach expliziter Nutzerfreigabe: Umschaltung auf Produktions-Sheet und Live-Tunnel-Traffic.

## Testing

- Pipeline-Unit-Test je Workflow: n8n-eigene "Pin Data"/manuelle Testläufe gegen Testdaten, bevor Cron/Webhook aktiviert wird.
- Dedupe/Scoring gegen bekannte Duplikat-Fälle aus dem bestehenden CRM-Sheet-Schema verifizieren.
- Fehlerpfad testen: Apps-Script-Webhook-Call schlägt fehl → Sheet-Write darf trotzdem durchlaufen (non-blocking bestätigen).
- Tunnel/Access-Policy: Editor-Zugriff ohne Authentifizierung muss abgelehnt werden; Webhook-Pfad muss ohne Authentifizierung erreichbar sein.
- Nach Rollout-Schritt 6: ein einzelner Test-Lead durch den kompletten Live-Pfad verifizieren, bevor die Instanz als produktiv gilt.

## Wiederverwendbare Bausteine (Golden-Path-Kandidaten)

Diese Session hat bewusst **keine** allgemeine Foundation-Spec und **keine** neue KI-System-Ordnerstruktur angelegt. Die folgenden, in diesem Design mit **[PLATTFORMFÄHIG]** markierten Bausteine sind jedoch projektunabhängig und eignen sich als Ausgangspunkt für eine spätere, separat zu brainstormende Enterprise-/Connector-Foundation:

1. Instanztrennung nach Vertrauenszone (kein geteilter Port/Volume/Credential-Store zwischen privaten und geschäftlichen n8n-Instanzen).
2. Dreiteilung Laufzeit/Workflow-Exporte/Secrets über `04_Developer/`, projekteigenes `ops/n8n/`, `05_Secrets/`.
3. Hybrid-Migrationsmuster: bestehender geprüfter Eingang bleibt unverändert, n8n hängt sich non-blocking an.
4. Self-hosted-n8n-Sicherheits-Checkliste (Encryption-Key, korrekte Host-Variablen von Anfang an, Access-Policy pro Pfad, kein `:latest`-Tag, Executions-Pruning, Error-Workflow).
5. Compliance-Grundregel "lesen/anreichern ja, Versand an Kontakte nein, solange kein Gate besteht".

Diese Liste ist eine Kennzeichnung, keine Umsetzung — eine tatsächliche Foundation-Extraktion ist ein eigenes, künftiges Brainstorming/Spec-Vorhaben.

## Offene Punkte (nicht Teil dieses Designs, separat zu klären)

- Ob `n8n-ki-os` (Instanz A) langfristig konsolidiert oder aufgegeben wird — bewusst nicht in diesem Design entschieden.
- Cloudflare-Zonen-Bereinigung (`hsb-boden.de` doppelt registriert, falscher Account) — Voraussetzung für Rollout-Schritt 2, aber eigene, bereits dokumentierte offene Aufgabe.
- Echte technische Trennung der drei Google-Workspace-Connector-Profile (aktuell alle auf `cherinojoel@gmail.com`) — Voraussetzung für eine spätere echte HSB-Boden-Identität, nicht Teil dieses Designs.
- Spätere Extraktion einer allgemeinen n8n-/Connector-Foundation aus den oben gekennzeichneten Bausteinen — eigenes künftiges Vorhaben, hier nur vorbereitet, nicht begonnen.

## Status (Abschluss dieser Session)

**GRÜN — sicher finalisiert:**
- Design vollständig dokumentiert und in `docs/superpowers/specs/2026-07-09-n8n-hsb-boden-automation-design.md` im kanonischen Repo (`~/KI-System/02_Projects/active/hsb-boden`) abgelegt.
- Instanztrennung von den beiden bestehenden n8n-Instanzen (SCMS, KI-OS) technisch definiert, keine der beiden verändert.
- Identity-/Boundary-Regeln festgelegt und mit dem tatsächlich verifizierten technischen Zustand abgeglichen (keine unbelegten Behauptungen übernommen).
- Wiederverwendbare Bausteine gekennzeichnet, ohne vorzeitige Foundation-Extraktion.

**GELB — vorbereitet, nicht produktiv umgesetzt:**
- Ordnerstruktur (`04_Developer/n8n-hsb-boden/`, `ops/n8n/`, `05_Secrets/hsb-boden/`) ist geplant, aber noch nicht angelegt.
- Docker-Compose, Pipelines, Cloudflare Tunnel — noch nicht gebaut.
- Apps-Script-Erweiterung um den n8n-Webhook-Call — noch nicht umgesetzt.

**ROT — blockiert, braucht separate Freigabe/Klärung:**
- Google-Workspace-Identitätstrennung: alle drei Profile zeigen aktuell auf denselben Account (`cherinojoel@gmail.com`) — keine echte Business/Private-Trennung vorhanden.
- Cloudflare-Zonen-Doppellung für `hsb-boden.de` (falscher Account `cherinojoel`) — muss vor Rollout-Schritt 2 manuell im Dashboard bereinigt werden.
- Echte HSB-Boden-Geschäftsadresse für OAuth-Credentials noch nicht final geprüft.
- Notion-Integration-Secret und OpenAI-Key wurden laut heutigem SCMS-Handoff zwischenzeitlich im Chat sichtbar — Rotation-Status für dieses Design nicht relevant (andere Instanz), aber als bekannter offener Punkt aus derselben Session vermerkt.

**Nächster Schritt:** Rollout-Schritt 1 — `n8n-hsb-boden`-Instanz lokal aufsetzen (Docker, Härtung gemäß Abschnitt "Sicherheits- und Betriebshärtung"), ohne Live-Tunnel, ohne Produktions-Credentials.
