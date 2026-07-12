# Architecture Review — n8n-HSB-Boden-Design

Review-Gegenstand: `2026-07-09-n8n-hsb-boden-automation-design.md`. Diese Review ändert die Spec nicht, sie bewertet sie.

## Kurzfazit

Keine grundsätzlichen Architekturprobleme. Ein echter technischer Risikopunkt (Apps-Script-Webhook-Call, siehe ROT), ein Overengineering-Verdacht (Postgres-Backend, siehe GELB) und eine strukturelle Redundanz (Boundary-Regel dreifach formuliert, siehe GELB). Ansonsten rollout-bereit.

## GRÜN — sofort wiederverwendbar (projektunabhängig, unverändert übernehmbar)

- **Instanztrennung nach Vertrauenszone.** Kein geteilter Port/Volume/Credential-Store zwischen n8n-Instanzen unterschiedlicher Zonen. Das ist die eigentliche Kernidee der Spec und trägt ohne Anpassung auf jedes künftige Projekt.
- **Dreiteilung Laufzeit/Workflow-Exporte/Secrets** (`04_Developer/n8n-<projekt>/` · `<projekt>/ops/n8n/` · `05_Secrets/<projekt>/`). Klar, minimal, folgt bereits bestehenden Konventionen im System (`n8n-ki-os`). Direkt kopierbar.
- **Hybrid-Migrationsmuster**: bestehender, geprüfter öffentlicher Eingang bleibt unverändert, n8n hängt sich non-blocking als zusätzlicher Konsument an. Das ist die risikoärmste Migrationsstrategie überhaupt und gilt für jedes Projekt mit bereits produktivem Eingang.
- **Self-hosted-n8n-Sicherheits-Checkliste** (Encryption-Key, korrekte Host-Variablen von Anfang an, Access-Policy pro Pfad statt pauschal, kein `:latest`-Tag, Executions-Pruning, Error-Workflow). Bis auf die Subdomain-Namen zu 100 % generisch. Das ist die Liste mit dem höchsten Wiederverwendungswert der ganzen Spec.
- **Compliance-Grundregel** "Automation darf Daten lesen/anreichern, aber nie an den Kontakt selbst senden, solange kein Gate besteht". Formuliert unabhängig von HSB — trägt unverändert zu Schuldenmanagement (Gläubiger-/Gerichtskommunikation) und Mecklenburgische.
- **Rollout-Sequenz-Muster**: lokal ohne Tunnel → Tunnel nur für Editor testen → Credentials anlegen → gegen Testdaten bauen → Erweiterung des bestehenden Eingangs non-blocking → Cutover nur nach expliziter Freigabe. Als Ablaufskelett unabhängig vom Inhalt wiederverwendbar.

## GELB — projektabhängig, später zu abstrahieren

- **Boundary-Regel-Konzept (drei Zonen: privat / business-bootstrap / business-canonical) ist GRÜN als Muster, aber die konkrete Account-Zuordnung ist GELB und dreht sich bei Schuldenmanagement/Mecklenburgische um**: Dort wird `cherinodiaz@outlook.com` der *erlaubte* Account, `cherinojoel@gmail.com` der *ausgeschlossene*. Die Spec regelt aktuell nur die HSB-Richtung. Bei einer künftigen Abstraktion muss die Zuordnung Account↔Zone parametrisiert werden, nicht die Regel selbst.
- **Vier-Pipelines-Archetyp** (intake-getriggerte Anreicherung, Cron-Reminder, Cron-Tagesreport, intake-getriggerte Benachrichtigung) ist als *Form* auf jedes CRM-artige Projekt übertragbar — auch auf Schuldenmanagement (Fristen-Reminder, Fallstatus-Report) oder Mecklenburgische. Die konkreten Feldnamen, Dedupe-Keys und Sheet-Referenzen (`CRM_LIGHT_SCHEMA.md`) sind aber vollständig HSB-spezifisch und müssten pro Projekt neu spezifiziert werden.
- **Postgres statt SQLite als n8n-Backend** — verdient eine bewusste Entscheidung, keine automatische Übernahme aus dem `n8n-ki-os`-Muster. Die Spec selbst zitiert `N8N_HOSTING_DECISION.md`, die HSB-Boden ausdrücklich als "niedrigvolumiges B2B-Lead-Formular" einstuft. Für dieses Volumen ist n8n's eingebautes SQLite-Backend vermutlich ausreichend und spart einen zweiten Container, Healthchecks, und den separaten `pg_dump`-Backup-Cron. Postgres lohnt sich, sobald Concurrency/Wachstum absehbar ist — das ist bei HSB aktuell nicht belegt. Empfehlung: SQLite als Default vormerken, Postgres nur bei belegtem Bedarf nachziehen (spart Betriebskomplexität, ohne die Instanztrennung anzutasten).
- **Drei Ebenen Zugriffsschutz** (Cloudflare Access auf Editor, WAF-Rate-Limit auf Webhook, n8n-eigener Login) sind einzeln sinnvoll (unterschiedliche Bedrohungsflächen), aber nicht als Blaupause 1:1 auf jedes Projekt übertragbar — bei geringerem Schutzbedarf (rein interne Automation ohne öffentlichen Webhook) wäre das teilweise Overkill. Pro Projekt neu abwägen, nicht pauschal kopieren.

## ROT — HSB-spezifisch oder vor Implementierung noch offen

- **Technisches Risiko, nicht in der Spec adressiert: Apps Script `UrlFetchApp` ist nicht fire-and-forget.** Die Spec beschreibt den n8n-Webhook-Call aus Apps Script als "fire-and-forget (Fehler dort blockieren den Sheet-Write nicht)". Google Apps Script hat aber keinen echten asynchronen HTTP-Call — `UrlFetchApp.fetch()` blockiert die Skriptausführung, bis n8n antwortet oder ein Timeout eintritt. Das heißt: Ist die n8n-Instanz langsam, offline oder hinter einer Access-Policy, die den Call verzögert, verlangsamt sich die sichtbare Formular-Bestätigung auf der Website spürbar, statt "nebenbei" zu laufen. Muss vor Implementierung geklärt werden: entweder mit `muteHttpExceptions: true` + sehr kurzem, bewusst gewähltem Timeout arbeiten und Fehler explizit abfangen, oder den Call so bauen, dass Apps Script den Sheet-Write zuerst abschließt und den n8n-Call erst danach absetzt (aktuelle Sheet-Write-Reihenfolge in der Spec nicht spezifiziert).
- **Google-Workspace-Identitätstrennung nicht real** (alle drei Profile zeigen auf `cherinojoel@gmail.com`) — bereits in der Spec als ROT vermerkt, hier nur bestätigt: blockiert eine belastbare Business/Private-Trennung auf Account-Ebene, nicht nur auf Ordner-/Workflow-Ebene.
- **Cloudflare-Zonen-Doppellung** für `hsb-boden.de` — Voraussetzung für Rollout-Schritt 2, unverändert offen.
- **Cloudflare-Zero-Trust-Verfügbarkeit ungeprüft**: Die Spec setzt Access-Policies voraus, aber es ist nicht verifiziert, ob der Ziel-Account (aktuell `cherinojoel@gmail.com`, später eine echte HSB-Adresse) einen Zero-Trust-Plan mit Access aktiviert hat. Sollte vor Rollout-Schritt 2 kurz geprüft werden (Free-Tier deckt i. d. R. bis 50 Nutzer ab, aber Aktivierung ist nicht automatisch).
- **Redundante Formulierung der Boundary-Regel**: Die Kernaussage "kein `cherinodiaz@outlook.com` in HSB-Flows, keine privaten Daten in HSB, keine HSB-Daten privat" steht in der Spec an drei Stellen fast wortgleich (Identity-Regeln, Compliance-Grenzen, implizit im ausgeschlossenen Scope). Inhaltlich kein Fehler, aber unnötige Redundanz — bei einer späteren Foundation-Extraktion sollte das auf eine einzige kanonische Boundary-Sektion konsolidiert werden, auf die alle anderen Abschnitte nur verweisen.
- **CRM_LIGHT_SCHEMA-Feldnamen, Dedupe-Keys, `PHASE_7_COMPLIANCE_GATE`** — vollständig HSB-spezifisch, keine Wiederverwendung ohne Neuspezifikation möglich.
- **`n8n-ki-os` (Instanz A) Konsolidierungsfrage** — unverändert offen, nicht Teil dieser Spec.

## Unverändert übernehmbare Teile (explizite Antwort auf die Frage)

Ohne jede Anpassung auf ein neues Projekt übertragbar: die Sicherheits-Checkliste (bis auf Domainnamen), das Hybrid-Migrationsmuster als Prinzip, die Dreiteilung Laufzeit/Exporte/Secrets, die Compliance-Grundregel "lesen ja, senden nein ohne Gate", und die Rollout-Sequenz als Ablaufskelett.

## Empfehlung

Keine grundsätzliche Überarbeitung der Spec nötig. Vor dem Rollout-Start zwei kleine Klärungen sinnvoll (beide ohne Scope-Erweiterung lösbar):

1. SQLite statt Postgres als Startpunkt für die HSB-Instanz festlegen (oder bewusst Postgres bestätigen, falls ein konkreter Grund dafür besteht, der in dieser Review nicht sichtbar war).
2. Reihenfolge/Timeout-Verhalten des Apps-Script→n8n-Webhook-Calls klären, bevor Rollout-Schritt 5 (Apps-Script-Erweiterung) gebaut wird.

Beides sind Detailentscheidungen für die Implementierung, keine Architekturänderungen — die Spec selbst bleibt wie sie ist.
