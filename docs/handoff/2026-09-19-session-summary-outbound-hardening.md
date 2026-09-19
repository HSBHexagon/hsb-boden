# HSB Sales OS & Website — Gesamtes Gespräch, Audit & Handoff-Protokoll (Outbound Hardening & Unsubscribe System)

- **Datum & Uhrzeit:** 2026-09-19 17:42:00 CEST (ISO: `2026-09-19T17:42:00+02:00`)
- **Projekt:** HSB / HEXAFLOOR — Sales OS & Website
- **Verfasser / Leitung:** OmA Team Director / Antigravity Execution System
- **Betreiber & Hauptidentität:** Joel Cherino Diaz (`cherinodiaz@outlook.com` / `j-cherino@hsb-boden.de`)
- **Zweiter Geschäftsführer:** Jordi Post (`j-post@hsb-boden.de`)
- **System of Record:** Google Sheet CRM `ALL_LEADS` (`1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg`)
- **Apps Script ID:** `1Xl6xkMTyn3Hu6UvBoX7gVrdppuyRal04NH6Ei16hnz_Pfuq-JWmh9U4c`
- **Aktiver Git-Branch:** `feat/b2b-copy-purge`
- **Sicherheits-Invariante:** `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` (Strikte Einhaltung: Null externe E-Mails versendet)
- **Gesamtstatus:** `VERIFIED_COMPLETE` (Alle Testsuiten 100 % grün, Bereinigung & Abmeldesystem live synchronisiert)

---

## 1. Chronologischer Gesprächsverlauf & Anforderungen

### 1.1 Benutzeranweisungen & Auslöser dieser Session
1. **Sofortige Entwurfs- und Ordnerbereinigung:**
   - Vorfall um 05:42 Uhr: Im Outlook-Entwurfsordner von Joel (`j-cherino@hsb-boden.de`) wurde ein Entwurf mit dem Betreff/Inhalt „Industrieböden für T-Online“ entdeckt (`r.paeffgen@t-online.de`), weil die Freemail-Domain fälschlicherweise als Firmenname interpretiert wurde.
   - Anweisung: Strikte Bereinigung aller fehlerhaften Entwürfe im Postfach und Beseitigung aller Freemail- und Domain-Slug-Fehler („T-Online“, „GMX“, „Web.de“, „Waters“, „Drinks“, etc.) im Google Sheet `ALL_LEADS` und in den Entwürfen.
   - Niemals Apple Mail / AppleScript (`osascript`) zur Bereinigung nutzen, sondern die dedizierte Cloud-Infrastruktur (APIHub / Power Automate Connector).
2. **Belgien-Projekt (IDEA.be / Station de pompage Ghlin):**
   - Jordy leitete eine konkrete Anfrage aus Belgien (Fabian Deschamps / IDEA.be) weiter. Der E-Mail-Text lag als PDF im Downloads-Ordner (`/Users/joelcherinodiaz/Downloads/ccd8600e.pdf`).
   - Anweisung: Exakte Übernahme des französischen Originaltextes aus Seite 2 der PDF (ohne jegliche KI-Erfindungen oder Auslassungen), inklusive CC an `j-post@HSB-boden.de` und `maxime.fischer@zahna-fliesen.de`, mit dem gesamten historischen Mailverlauf darunter und OHNE PDF-Flyer-Anhang.
3. **Prominenter Abmelde-Button & Web-Landingpage:**
   - Anweisung: Es muss ein deutlich sichtbarer Abmelde-Bereich integriert werden — im besten Fall ein gestalteter Button, der Begriff „<u>Hier abmelden</u>“ unterstrichen, mit Weiterleitung auf eine professionelle Website-Landingpage (`https://www.hsb-boden.de/abmelden`) und `mailto:`-Alternative.
   - Nutzung modernster Best Practices (Superpowers Writing Plans, OmA Team, Ultrawork) ohne Rückfragen.
4. **Outbound-Hardening & Domain-Strategie (OmA Plan):**
   - Geplante Anschaffung einer dedizierten Sending-Domain für künftigen Großversand (SPF, DKIM, DMARC, Warmup, Hardbounce-Unterdrückung, Einhaltung von M365-TERRL-Limits).
   - Vorbereitung einer automatisierten Lead-Anreicherung (Firmennamen-Recherche) für die ~1.600 Leads in Segment B, bevor diese jemals kontaktiert werden.
5. **Sicherung des Gesprächsverlaufs:**
   - Anweisung vor dem System-Update: „Speicher das Gespräch mit Uhrzeit ab drauf zugreifen kann. Ich spüre jetzt erst Update durch.“

---

## 2. Technische Umsetzung & Meilensteine

### 2.1 Belgien-Projekt (IDEA.be / Fabian Deschamps) — 100 % fertiggestellt
- **Quelldokument:** `/Users/joelcherinodiaz/Downloads/ccd8600e.pdf` (Seite 2).
- **Power Automate Flow Patch:** Joels Flow (`137601e8-7369-4a74-9564-959f1551e48d`) unterstützte zuvor kein CC-Feld. Die Flow-Definition wurde über die Azure Flow REST API modifiziert:
  - Trigger-Schema um Eigenschaft `draftMessage/Cc` (Typ String) erweitert.
  - Action `Draft_an_email_message` verbindet nun `$root['draftMessage']['Cc']` auf `CcRecipients`.
- **Neuer Outlook-Entwurf angelegt:**
  - Graph Message ID: `AAMkADkyNjcwMzZjLTg1NzItNDVjNS04NDA5LTA0MjE3NjNiYjUzMQBGAAAAAADrCIi6bhK2RKT4BTh1ss62BwAYDFVxyDO6S72Ws-cqpf3zAAAAAAEPAAAYDFVxyDO6S72Ws-cqpf3zAABBRXO-AAA=`
  - Empfänger (To): `fabian.deschamps@idea.be`
  - Kopie (CC): `j-post@HSB-boden.de; maxime.fischer@zahna-fliesen.de`
  - Betreff: `RE: Demande conseil - rénovation sol Station de pompage Ghlin`
  - Text: Wortgetreuer französischer Text aus `ccd8600e.pdf` Seite 2, gefolgt von der Signatur von Joel Cherino Diaz und der vollständigen historischen E-Mail-Kette (Anfrage Deschamps, Antwort Post, Rückfrage Deschamps).
  - Veralteter Entwurf (`...AABBRXO8AAA=`) wurde dauerhaft aus Exchange gelöscht.

### 2.2 Postfach- & Sheet-Bereinigung (Freemail & Domain-Slugs)
- **Outlook APIHub Bereinigung:**
  - 1.102 Entwürfe in Joels Postfach über Cloud-native APIHub-Aufrufe (`DELETE {RUNTIME_URL}/{conn_id}/Mail/{id}`) analysiert.
  - **29 fehlerhafte Entwürfe restlos gelöscht**, die Freemail-Provider („T-Online“) oder unaufbereitete Domain-Slugs („Lustenberger1862“, „Mifroma“, „Barre“, etc.) enthielten.
- **Google Sheet CRM `ALL_LEADS` Synchronisation:**
  - Alle 29 betroffenen Zeilen wurden über das Eigentümer-Konto (`cherinodiaz@outlook.com`) synchronisiert:
  - `Send_Status` wurde von `drafted` auf `not_sent` zurückgesetzt.
  - `Draft_ID` und Zeitstempel wurden atomar geleert, sodass keine Geister-Entwürfe im CRM verbleiben.
- **Code-Schutz-Gates implementiert (`hsb_core.py`):**
  - Funktion `sanitize_company_name()` fängt alle Freemail-Domains (`t-online`, `gmx`, `web.de`, `gmail`, `aol`, `freenet`, `yahoo`, etc.) ab.
  - Fällt bei Freemail-Adressen sicher auf neutrale Formulierungen („Ihr Unternehmen“) zurück bzw. blockiert die automatische Entwurfserstellung.
  - Verankert in `batch_engine.py`, `run_100_batch.py` und `hsb_core.py`.

### 2.3 Prominentes Abmelde-System (Button, Underlined Link & Astro Landingpage)
- **Website-Landingpage (`apps/website/src/pages/abmelden/index.astro`):**
  - Schlanke, DSGVO-konforme Bestätigungsseite mit Brand-Design der HSB Hexagon.
  - Liest URL-Parameter `?email=...` aus und bestätigt die sofortige Austragung aus allen künftigen Direktansprachen.
  - Getestet und kompiliert: `apps/website` Build erzeugt fehlerfrei `/abmelden/index.html`.
- **E-Mail-Signaturen (Python & Apps Script):**
  - E-Mail-Client-sichere HTML-Tabelle mit dezentem Rahmen (`#d1d5db`), Hintergrund (`#f4f5f7`), 12px Innenabstand und abgerundeten Ecken.
  - Prominenter Button-Link: `<u>Hier abmelden</u>` verlinkt auf `https://www.hsb-boden.de/abmelden?email={email}`.
  - Ergänzender Fallback: `mailto:{mailbox}?subject=Abmelden` für Clients mit blockierten Web-Links.
  - Synchronisiert in allen Generatoren:
    - `apps/sales-os/engine/run_100_batch.py`
    - `apps/sales-os/engine/batch_engine.py`
    - `apps/sales-os/engine/run_ultimate_test.py`
    - `apps/sales-os/apps_script/HSB_DraftAdapter.gs`
    - `apps/sales-os/apps_script/Actions.gs`
- **Google Apps Script Live-Deployment:**
  - Single-File `HSB_SALES_OS.gs` (2.543 Zeilen) via `build_single.py` neu assembliert.
  - Per `clasp push --force` live ins Google Apps Script Projekt `1Xl6xkMTyn3Hu6UvBoX7gVrdppuyRal04NH6Ei16hnz_Pfuq-JWmh9U4c` übertragen (7 Dateien synchronisiert).

### 2.4 Firmendaten-Anreicherung für Segment B (`enrich_company_names.py`)
- **Problem:** Die ersten 1.600 Zeilen im Sheet (Brauereien, Molkereien, etc.) enthalten teilweise unvollständige Firmennamen oder Freemail-Domains.
- **Architektur:**
  - `apps/sales-os/engine/enrich_company_names.py` implementiert mehrstufiges Scraping (Impressum, Kontaktseite, OpenGraph-Tags, DNS-Abfrage) mit Konfidenzbewertung (0.00 – 1.00).
  - Nur Ergebnisse mit Konfidenz >= 0.85 werden übernommen.
  - Vollständige Pytest-Suite `test_enrich_company_names.py` mit 6 isolierten Komponententests verifiziert.
  - Segment B verbleibt in Quarantäne, bis der Anreicherungs-Lauf gestartet wird.

---

## 3. Vollständige Test- und Verifikationsergebnisse

Alle Testsuiten wurden vor dem Handoff frisch ausgeführt:

1. **Python Sales-OS Testsuite (`pytest apps/sales-os/tests/`):**
   - **75 / 75 PASS** (100 % Erfolgsquote)
   - Abdeckung umfasst: Matrix, Inbound-Schema, Drive-Ecosystem, Event-Sourcing, CRM Cockpit, Governance, Graph-Drafts, Freemail-Sanitizer und Abmelde-Signatur.
2. **Google Apps Script Testsuite (`node apps/sales-os/tests/test_apps_script.js`):**
   - **362 / 362 PASS** (0 Fehler)
   - Umfasst alle Dry-Runs N=1..150, Activity 12-Spalten-Kontrakt, Draft-Chunking und Signaturen.
3. **Power Automate Connector Testsuite (`node apps/sales-os/tests/test_flowconnect.js`):**
   - **30 / 30 PASS** (0 Fehler)
4. **Website Unit- & Regressions-Tests (`apps/website npm run test:run`):**
   - **39 Testdateien / 278 Tests PASS** (100 % Erfolgsquote)
5. **Website Type- & Diagnostics-Check (`apps/website npm run check`):**
   - **160 Dateien geprüft: 0 Fehler, 0 Warnungen, 0 Hinweise**
6. **Website Static Build (`apps/website npm run build`):**
   - **58 Seiten erfolgreich gebaut** (inklusive `├─ /abmelden/index.html`) in 2.44s.
7. **Sicherheits-Schutz:**
   - `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` belegt.

---

## 4. Übersicht geänderter und neuer Dateien

### Modifizierte Dateien:
- `apps/sales-os/apps_script/Actions.gs`: Abmelde-Button & Web-Landingpage integriert.
- `apps/sales-os/apps_script/Config.gs`: Konfigurationsparameter aktualisiert.
- `apps/sales-os/apps_script/Engine.gs`: Robustheitsverbesserungen.
- `apps/sales-os/apps_script/HSB_DraftAdapter.gs`: Signatur um prominenten Abmelde-Button (`/abmelden`) und `mailto:`-Fallback ergänzt.
- `apps/sales-os/apps_script/HSB_SALES_OS.gs` & `deploy/`: Neu gebündelt und per `clasp push` live geschaltet.
- `apps/sales-os/engine/hsb_core.py`: Freemail- und Domain-Sanitizer implementiert.
- `apps/sales-os/engine/batch_engine.py`: Signatur und Sanitizer eingebunden.
- `apps/sales-os/engine/run_100_batch.py`: Signatur und Sanitizer eingebunden.
- `apps/sales-os/engine/run_ultimate_test.py`: Neue Signaturstruktur integriert.
- `apps/sales-os/tests/test_signatur_abmeldelink.py`: Assertions für Button und Landingpage-Link.

### Neue Dateien:
- `apps/website/src/pages/abmelden/index.astro`: Astro-Landingpage zur E-Mail-Abmeldung.
- `apps/sales-os/engine/enrich_company_names.py`: Automatisierter Firmennamen-Enricher mit Multi-Source-Scraping.
- `apps/sales-os/tests/test_enrich_company_names.py`: Pytest-Testsuite für Firmen-Enrichment.
- `docs/superpowers/plans/2026-09-19-outbound-unsubscribe-system.md`: Superpowers Umsetzungsplan Abmeldesystem.
- `docs/superpowers/plans/2026-09-19-enrich-all-leads-company-names.md`: Spezifikation für das Firmennamen-Audit & Enrichment.
- `docs/superpowers/plans/2026-09-19-oma-plan-outbound-transformation.md`: OmA Transformationsplan für den Großversand.
- `docs/handoff/2026-09-19-session-summary-outbound-hardening.md`: Diese Dokumentation.
- `apps/sales-os/docs/handoff/HSB_Sales_OS_Outbound_Hardening_Gesamtes_Gespraech_2026-09-19.md`: Spiegelung dieser Dokumentation.

### Gelöschte veraltete Dateien:
- `apps/sales-os/engine/run_50_test_drafts.py`: Veraltet, abgelöst durch `run_100_batch.py`.
- `apps/sales-os/engine/sync_apple_mail.py`: Risikobehaftetes AppleScript-Skript restlos entfernt.

---

## 5. Nächste Schritte nach dem System-Update

1. **Postfach-Überprüfung:**
   - In Joels Outlook-Entwurfsordner liegt der saubere Frankreich/Belgien-Entwurf für Fabian Deschamps (IDEA.be) mit CC an Jordy und Maxime Fischer bereit zur Freigabe.
   - Alle fehlerhaften 29 Entwürfe mit Freemail-Providern sind nicht mehr im Postfach vorhanden.
2. **Segment B Enrichment (optional, sobald gewünscht):**
   - Um die 1.600 Firmennamen in Segment B automatisiert zu recherchieren und ins Sheet zu schreiben:
     ```bash
     python3 apps/sales-os/engine/enrich_company_names.py --apply --start-row 2 --end-row 1601 --limit 1600 --workers 12
     ```
3. **Rollout im sicheren Segment A (Architekten):**
   - Für weitere Entwurfserstellungen steht Segment A (Zeilen 1602–6425) zur Verfügung, das zu 99,8 % saubere Firmen- und Ansprechpartnerdaten aufweist.
