
## 2026-09-17 17:12 — Claude Code: Abmeldung end-to-end belegt
- Trigger-Abgleich laeuft in beiden Konten (j-cherino, j-post); Jordis laufender Batch wurde automatisch auf SENT gesetzt (52 Leads, 15 Bounces).
- Befund: Ereignis-Flut (NEEDS_REVIEW bei jedem Lauf neu) -> Vorfilter (live 15:10).
- Befund: drei "Abmelden"-Antworten von Kollegenadressen der Firmendomain blieben ungesperrt -> Domain-Abmeldung (Merge 45664c8, live 17:06 per clasp push durch Owner).
- Nachweis 17:10 UTC+2: HSB-20260708-03671/-03677/-03218 Opt-out=yes, Suppressed=yes, Versandfreigabe=no, Pipeline Abgemeldet; INBOUND_EVENTS OPT_OUT PROCESSED "Domain-Abmeldung".
- Offen (Owner-Gate): Task 4 Datenregeln (crm_data_hygiene_gate.py --apply), INBOUND_EVENTS-Layout + 284 Duplikate (Plan docs/superpowers/plans/2026-09-17-crm-cockpit-visual.md Task 1), Cockpit-Tabs (Plan Task 2-7), Abmelde-Link (mailto in Signatur -> gleicher Opt-out-Pfad).

---

## 2026-09-19 17:42 CEST — Claude Code / OmA Team Director: Outbound Hardening, Postfach-Bereinigung & Abmeldesystem
- **Bereinigung Postfach & Sheet:** 1.102 Entwürfe in Joels Exchange-Mailbox gescannt; 29 fehlerhafte Entwürfe mit Freemail-Providern („T-Online“) oder unaufbereiteten Domain-Slugs restlos per APIHub (`DELETE Mail/{id}`) gelöscht; 29 Zeilen im Google Sheet `ALL_LEADS` synchron auf `Send_Status = not_sent` zurückgesetzt (`Draft_ID` geleert).
- **Code-Schutz-Gates:** `sanitize_company_name()` in `hsb_core.py` implementiert; fängt Freemail-Domains ab und erzwingt neutrale Fallbacks.
- **Prominentes Abmelde-System:** Email-Safe HTML-Tabelle mit dezentem Rahmen, Button und unterstrichenem Link `<u>Hier abmelden</u>` (`https://www.hsb-boden.de/abmelden`) + `mailto:`-Fallback in allen Python-Engines und Apps-Script synchronisiert; Astro-Landingpage `apps/website/src/pages/abmelden/index.astro` implementiert und gebaut.
- **Apps Script Live-Deploy:** `HSB_SALES_OS.gs` (2.543 Zeilen) neu assembliert und per `clasp push --force` live geschaltet (7 Dateien übertragen).
- **Belgien-Projekt (IDEA.be / Fabian Deschamps):** Flow `137601e8...` per REST API um nativen `Cc`-Support erweitert; Entwurf mit originalem französischen Text aus PDF Seite 2, CC an `j-post@HSB-boden.de` und `maxime.fischer@zahna-fliesen.de` und voller Mailhistorie erstellt; alter Entwurf gelöscht.
- **Lead-Enrichment Segment B:** `apps/sales-os/engine/enrich_company_names.py` (Multi-Source-Scraping, Konfidenz-Scoring) implementiert (Segment B Quarantäne gewahrt).
- **Tests:** Pytest 75/75, Apps Script 362/362, FlowConnect 30/30, Website 278/278, Check 0/0/0, Build 58 Seiten.
- **Sicherheit:** `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0`.
