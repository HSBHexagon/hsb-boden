# CRM/Outreach-Finalisierung — 2026-08-11

> Ergänzt `CRM_DATENQUELLE_WAHRHEIT.md` (dort die laufend korrigierte
> Kern-Wahrheit). Dieses Dokument ist der einmalige Abschlussbericht des
> Finalisierungslaufs vom 2026-08-11. PII-frei — nur Pfade, Counts, Status.

## 1. Quelle und Methode

Ausgangsfehler behoben: eine frühere Session hatte die Spalten der CSV-Dateien
naiv per `;`-Split ausgezählt, ohne die mehrzeiligen Anführungszeichen-Felder
(`Beziehung / Kontaktgrund`, `Notizen`) zu berücksichtigen — das verschob alle
Folgespalten und erzeugte falsche `Versandfreigabe`-Werte. Dieser Lauf nutzt
`python3 csv.DictReader` (Trennzeichen `;`, UTF-8-BOM, quote-bewusst) und
`openpyxl` für die `.xlsx`-Datei. Beide bereits lokal vorhanden, keine neue
Dependency installiert.

## 2. Reale Zahlen (verifiziert, nicht übernommen)

| Kennzahl | Wert |
|---|---|
| `TOTAL_LEADS` | 6.424 (`HSB_CRM_Leads_ALL_MASTER_2026-07-08.csv`) |
| `JOEL_LEADS` | 3.212 |
| `JORDI_LEADS` | 3.212 |
| `OWNER_OVERLAP` | 0 (Joel ∩ Jordi = ∅, Joel ∪ Jordi = ALL_MASTER exakt) |
| `DUPLICATE_RECORDS` (E-Mail, exakt) | 0 |
| `INVALID_EMAIL_RECORDS` (Syntax) | 0 |
| `EMPTY_EMAIL_RECORDS` | 0 |
| `OPT_OUT_RECORDS` | 0 bestätigt (alle `Opt-out-Status=unknown`, keine aktive Abmeldung erfasst) |
| `TIER_A` / `TIER_B` | 1.612 / 4.812 |
| `READY_CANDIDATES` (technisch, s. u.) | 6.424 |

Die erwarteten Zahlen aus dem Masterauftrag (6.424/3.212/3.212/0) sind damit
**bestätigt**, nicht blind übernommen — Beweisführung siehe oben.

### Versandfreigabe — Korrektur ggü. vorherigem Chat-Turn

`Versandfreigabe = no` für **alle** 6.424 Zeilen (0 × `yes`, 0 × `unknown`).
`PROJECT_TRUTH.md` §5 hatte dies korrekt; `CRM_DATENQUELLE_WAHRHEIT.md` hatte
durch den o. g. Parsing-Fehler `unknown` behauptet — dort jetzt korrigiert.
**`Versandfreigabe` bleibt unverändert auf `no` stehen** (nicht auf `unknown`
"geglättet", wie es ein wörtliches Lesen des externen Masterauftrags nahegelegt
hätte — bestehender Wert hat Vorrang vor der Auftrags-Annahme).

### Zusatzfund: `MASTER_5000`-Welle ist veraltet

712 der 2.500 Zeilen in `HSB_CRM_Leads_Jordi_2500_2026-07-08.csv` sind im
aktuellen `ALL_MASTER` Joel statt Jordi zugeordnet — zwischen der 5.000er- und
der 6.424er-Exportwelle fand eine Owner-Neuzuordnung statt. Für den Versand
zählt ausschließlich die 6.424er-Welle (`ALL_MASTER`/`ALL_Joel`/`ALL_Jordi`).

### Zusatzfund: `RESERVE`-Datei ist keine zusätzliche Quelle

`HSB_CRM_Leads_RESERVE_2026-07-08.xlsx` (1.424 Zeilen) überlappt zu 100 % mit
`ALL_MASTER` — es handelt sich um bereits im 6.424er-Bestand enthaltene
Zeilen, die (noch) keinem Operator zugewiesen sind (`Verantwortlicher`
leer), keine separate zusätzliche Lead-Quelle. Klärung von Frage 2 in
`CRM_DATENQUELLE_WAHRHEIT.md`.

## 3. Datenqualitäts-Gates

| Gate | Ergebnis |
|---|---|
| `LEAD_COUNT_GATE` | PASS (6.424 = 3.212 + 3.212) |
| `OWNER_SPLIT_GATE` | PASS (exakt 50/50, 0 Lücken) |
| `OWNER_OVERLAP_GATE` | PASS (0 Überschneidung) |
| `DATA_INTEGRITY_GATE` | PASS (0 Duplikate, 0 leere/ungültige E-Mails) |
| `PII_GIT_GATE` | PASS — `data/lead-import/` bleibt per `.gitignore` Zeile 21 ausgeschlossen; `git status --short` zeigt keine neue xlsx/csv im Tree |

## 4. Finale Exportdateien — erzeugt 2026-08-11

Pfad: `data/lead-import/output/final_2026-08-11/` (gitignored, per
`git check-ignore -v` verifiziert, `.gitignore` Zeile 21). Alle Dateien sind
Arbeitskopien mit 15 angehängten, tool-neutralen Spalten
(`Segment, Kampagne_ID, Email_Template_ID, Flyer_ID, Flyer_URL, Landing_URL,
UTM_Source, UTM_Medium, UTM_Campaign, UTM_Content, Batch_ID, Send_Status,
Send_Datum, Bounce_Status, Reply_Status`) — **bewusst leer**, außer
`Send_Status=not_sent` (belegte Tatsache: `EMAILS_SENT=0`). Keine UTM-/
Kampagnenwerte erfunden, da Sieger-Tool und Landing-URLs noch nicht final
gewählt sind.

| Datei | Zeilen | Zweck |
|---|---|---|
| `HSB_CRM_MASTER_2026-08-11.xlsx` | 14 Tabs | Vollständiger Master mit README, ALL_LEADS/JOEL/JORDI (je 6.424/3.212/3.212), READY_CANDIDATES (6.424), 4 leere Review-Sheets (0 Funde, verifiziert), OWNER_CONFLICT_REVIEW (2 reale Funde aus Abschnitt 2), FLYER_MAPPING (2 reale Flyer, je 3.212 Leads), CAMPAIGN/EMAIL_TEMPLATE/BATCH-Scaffolds (leer, `AWAITING_*`-Status statt erfundener Werte) |
| `HSB_OUTREACH_READY_2026-08-11.{xlsx,csv}` | 6.424 | Tool-neutraler Gesamtexport |
| `HSB_OUTREACH_JOEL_2026-08-11.{xlsx,csv}` | 3.212 | Joel-Export |
| `HSB_OUTREACH_JORDI_2026-08-11.{xlsx,csv}` | 3.212 | Jordi-Export |
| `HSB_PROPOSED_INITIAL_BATCH_2026-08-11.xlsx` | 50 (25+25) | Vorschlag, technisch bereit — Joel: 25× Tier A (alle verfügbaren); Jordi: 25× Tier B (Jordi hat 0 Tier-A-Leads, real so vorgefunden) |

**Flyer-Zuordnung real verifiziert:** `public/HSB-Flyer-Joel-Cherino.pdf`
(3.212× für Joel) und `public/HSB-Flyer-Jordi-Post.pdf` (3.212× für Jordi)
existieren beide im Repo (254 KB / 253 KB) — Flyer-Zuordnung ist bereits
vollständig und korrekt, keine Änderung nötig.

**Export-Readback (§37) durchgeführt:** Dateigrößen > 0, Sheet-/Zeilenzahlen
gegen Quelle geprüft (6.425 inkl. Header überall konsistent), `Versandfreigabe`
in allen Zeilen weiterhin `no` (0 × verändert), `Send_Status` überall
`not_sent`, CSV UTF-8 ohne Indexspalte, Header-Spaltenzahl 44 (29 original +
15 neu) konsistent zwischen xlsx und csv. `EXPORT_READBACK_GATE=PASS`.

`PII_GIT_GATE=PASS`: `git check-ignore -v` bestätigt alle neuen Dateien unter
`.gitignore` Zeile 21; `git status --short` zeigt keine neue xlsx/csv im
Tree.

`TOOL_NEUTRAL_EXPORT_STATUS = READY` (Kern-Schema vollständig befüllt,
Kampagnen-/UTM-Spalten strukturell vorhanden aber erst nach Tool-/Landing-URL-
Wahl befüllbar, Abschnitt 6/7).

## 5. Flyer und Mail-Template — bereits vorhanden

- `Flyer-Anhang`-Spalte in jeder Lead-Zeile bereits gesetzt (Beispiel-Pattern
  aus Stichprobe: `public/HSB-Flyer-Joel-Cherino.pdf`), pro Owner
  unterschiedlich — kein neues Flyer-Mapping nötig, es existiert bereits
  zeilenweise.
- Ein eigenständiges Akquise-Mail-Template als separate Datei wurde in diesem
  Lauf nicht lokalisiert (kein `docs/email/EMAIL_TEMPLATE*.md` mit Volltext
  gefunden) — offener Punkt, kein Fund ≠ „existiert nicht", nur nicht in den
  durchsuchten Pfaden (`docs/email/`, `docs/crm/`, `docs/launch/`) auffindbar.
  **Nicht neu geschrieben**, um keine konkurrierende Version zu erzeugen —
  Owner-Nachfrage empfohlen, wo der finale Text liegt (evtl. außerhalb des
  Repos, z. B. im Versandtool selbst vorbereitet).

## 6. Versandtool-Recherche (offizielle Quellen, 2026-08-11)

| Tool | Modell | Kosten (Einstieg) | Passung für 6.424 Leads |
|---|---|---|---|
| **Smartlead** | Eigene Infrastruktur/SmartSenders optional, unbegrenzte Mailboxen+Warmup je Plan | Base $39/Mon. (2.000 aktive Lead-Credits, 6.000 Mails/Monat); Pro $94/Mon. (150.000 Mails/Monat ≈ 5.000/Tag) | **Pro-Plan nötig** für den vollen 6.424er-Bestand in sinnvoller Zeit — Base reicht nur für Teilbatches. Unabhängig vom M365-DKIM-Problem, da eigene Sende-Infrastruktur/Domains verwendet werden (kein Versand über die bestehende `@hsb-boden.de`-M365-Mailbox nötig). |
| **Mailmeteor** | Sendet über verbundenes Gmail/Outlook-Postfach (OAuth) | Free: 50/Tag, 500/Monat; Starter ab $4/Mon.: 250/Tag, 5.000/Monat; Premium: 1.000/Tag, 30.000/Monat | **Ungeeignet als alleinige Lösung**: erbt die M365-DKIM-Lücke von `hsb-boden.de` 1:1, da über die bestehende Mailbox versendet wird (siehe vorheriger Chat-Turn — dort korrekt benannt). Für 6.424 Leads selbst im Premium-Plan zu langsam (30.000/Monat wäre zwar ausreichend Volumen, löst aber nicht das DKIM-Problem). |
| **Instantly** | Unbegrenzte Postfächer/Warmup je Plan, eigene Sende-Infrastruktur möglich | Growth $47/Mon.: 1.000 Kontakte, 5.000 Mails/Monat | Ähnlich Smartlead technisch geeignet (eigene Domains/Mailboxen, kein M365-Bezug nötig), aber Growth-Plan-Volumen zu klein für 6.424 auf einmal — höherer Plan nötig, konkrete Zahl in dieser Recherche nicht abschließend beziffert. |
| **GMass** (zusätzliches Tool) | Sendet über Gmail/Workspace | Kein echter Dauer-Free-Plan (nur 7-Tage-Trial mit 50/24h); danach kostenpflichtig | Nicht passend: Gmail-basiert, hsb-boden nutzt M365/Outlook — würde ein zusätzliches Gmail-Konto erfordern, das nicht Teil der bestehenden Infrastruktur ist. |

### `BEST_FREE_TOOL` — ehrliches Ergebnis

Es gibt **keine echte kostenlose Lösung, die für 6.424 Leads geeignet ist.**
Mailmeteor Free (50/Tag, 500/Monat) ist der einzige echte Dauer-Free-Plan unter
den geprüften Tools, würde für den vollen Bestand aber >12 Monate benötigen und
löst das DKIM-Problem nicht. `FREE_TOOL_FULL_DATASET_CAPABLE = false`. Klar
benannt statt künstlich als „kostenlos machbar" dargestellt (Vorgabe
Masterauftrag §20).

### `FINAL_TOOL_RECOMMENDATION`

`BEST_OVERALL_TOOL = Smartlead (Pro-Plan)` — einzige Option, die (a) das
DKIM-Problem technisch umgeht (eigene Sende-Infrastruktur statt M365-Mailbox),
(b) das nötige Volumen abdeckt, (c) Joel/Jordi als getrennte Absender-Pools
unterstützt (Multi-Sender-Feature, in dieser Recherche nicht tiefenprüft —
offener Punkt für eine Owner-nahe Testkonto-Prüfung vor Kauf).
`BEST_SCALE_TOOL = Smartlead`. `BEST_LOW_COST_TOOL = Instantly` (wenn ein
kleineres Startvolumen akzeptabel ist). Keine Kaufentscheidung in diesem Lauf
getroffen — `PAID_ACCOUNTS_CREATED=0`.

## 7. Versanddomain-Architektur — Korrektur ggü. vorherigem Chat-Turn

**Live-DNS-Prüfung 2026-08-11** (`dig NS/SOA/MX/TXT hsb-boden.de`):

```
NS   hsb-boden.de → ns5.kasserver.com, ns6.kasserver.com   (All-Inkl/Kasserver)
SOA  www.hsb-boden.de → hsb-boden.pages.dev (CNAME-Ziel, per Kasserver-DNS gesetzt)
MX   hsb-boden.de → hsbboden-de0i.mail.protection.outlook.com (M365 live)
TXT  hsb-boden.de → "v=spf1 include:spf.protection.outlook.com -all"  (SPF hard-fail, korrekt für M365)
TXT  _dmarc → "v=DMARC1; p=none;"  (nur Monitoring, kein rua)
TXT  selector1/2._domainkey → kein Record  (DKIM weiterhin nicht aktiv, bestätigt)
```

**Wichtigste Korrektur:** Die autoritative DNS-Zone für `hsb-boden.de` liegt
bei **All-Inkl/Kasserver**, nicht bei Cloudflare — Cloudflare-Zone bleibt laut
`PROJECT_TRUTH.md` §4 `pending` (kein NS-Cutover erfolgt). Meine Empfehlung im
vorherigen Chat-Turn, DNS-Records „im Cloudflare-Dashboard" einzutragen, war
falsch für die Hauptdomain. Für eine neue Sending-Subdomain
(z. B. `mail.hsb-boden.de`) müssen die vom gewählten Versandtool gelieferten
DNS-Records **im All-Inkl/Kasserver-Kundenmenü** eingetragen werden, nicht in
Cloudflare — unabhängig davon, ob ein Cloudflare-API-Token Schreibrechte hätte.
Das bestehende `-all`-SPF auf der Hauptdomain (hard fail) ist ein zusätzlicher
Grund, zwingend eine **separate Domain oder Subdomain** für Outreach zu nutzen:
jede Mail „im Namen von" `hsb-boden.de`, die nicht über M365 läuft, würde vom
eigenen SPF-Record der Hauptdomain abgelehnt.

`CLOUDFLARE_ACCESS_AVAILABLE = true (Dashboard, laut vorherigen Sessions)`,
`CLOUDFLARE_DNS_READ_ACCESS` in dieser Sitzung = **nur über öffentliches
`dig`, kein authentifizierter Cloudflare-API-/MCP-Zugriff in dieser Session
geprüft** (kein Cloudflare-MCP/-CLI in diesem Environment geladen).
`CLOUDFLARE_DNS_WRITE_CAPABILITY = irrelevant für hsb-boden.de` (Zone nicht
autoritativ). `CAN_CREATE_SENDING_SUBDOMAIN` und
`CAN_CREATE_REQUIRED_DNS_RECORDS` hängen stattdessen vom **All-Inkl/Kasserver
Kundenzugang** ab — wer dort Adminrechte hat, wurde in dieser Sitzung nicht
geprüft (gleiche offene Frage wie beim M365-Tenant-Admin, aber ein
**anderes** System).

`RECOMMENDED_SENDING_DOMAIN_MODEL = Outreach-Subdomain unter der bestehenden
Kasserver-verwalteten Zone` (z. B. `mail.hsb-boden.de` oder
`kampagne.hsb-boden.de`), sofern Kasserver-Zugang besteht. Alternativ: separate
Secondary-Domain, falls Kasserver-Zugang ebenfalls fehlt — dann register-seitig
unabhängig vom hsb-boden.de-Konto.

`DNS_CHANGES_EXECUTED = 0`. Kein Change in dieser Sitzung ausgeführt.

## 8. M365-Einordnung

`M365_ADMIN_REQUIRED_FOR_RECOMMENDED_OUTREACH_ARCHITECTURE = false` — sofern
Smartlead/Instantly mit eigener Sende-Infrastruktur (eigene Domains/Mailboxen)
gewählt wird, ist kein M365-Tenant-Admin-Zugriff nötig. Der M365-DKIM-Pfad
bleibt weiterhin relevant für die **reguläre Unternehmensmail** (`@hsb-boden.de`
Postfächer, z. B. `j.cherino@hsb-boden.de`), aber nicht mehr für den
6.424er-Massenversand, wenn die empfohlene Architektur umgesetzt wird.

## 9. Warm-up/Ramp-up — nur Plan, nicht gestartet

Aktuelle Smartlead-Dokumentation (offizielle Pricing-Seite, s. o.) bewirbt
„unlimited warmup" in jedem Plan, nennt aber in den durchsuchten Quellen keine
konkrete Tagesanzahl/Dauer — eine belastbare Zahl erfordert die
Produktdokumentation nach Kontoerstellung (nicht in dieser Sitzung möglich,
da kein Konto angelegt wurde). Bisherige interne Empfehlung (20-30/Tag,
1-2 Wochen) bleibt als **vorläufiger Platzhalter** bestehen, bis
Tool-Dokumentation nach Account-Erstellung sie bestätigt oder ersetzt.
`WARMUP_STARTED = false`.

## 10. Abschlussstatus

```
CRM_FINALIZATION_STATUS = data_verified_and_corrected_tool_researched_dns_authority_corrected_awaiting_owner_decisions
TOTAL_LEADS=6424 / JOEL=3212 / JORDI=3212 / OVERLAP=0
LEAD_COUNT_GATE=PASS / OWNER_SPLIT_GATE=PASS / OWNER_OVERLAP_GATE=PASS
DATA_INTEGRITY_GATE=PASS / PII_GIT_GATE=PASS
BEST_OVERALL_TOOL=Smartlead (Pro-Plan empfohlen, ungetestet)
BEST_FREE_TOOL=Mailmeteor Free (nicht bestandstauglich, ehrlich benannt)
RECOMMENDED_SENDING_DOMAIN_MODEL=Outreach-Subdomain unter Kasserver-Zone (DNS-Autorität korrigiert von Cloudflare auf All-Inkl/Kasserver)
M365_ADMIN_REQUIRED_FOR_RECOMMENDED_OUTREACH_ARCHITECTURE=false
VERSANDFREIGABE_STATUS=no (unveraendert, nicht auf unknown geglaettet)
EMAILS_SENT=0 / WARMUP_STARTED=false / DNS_CHANGES_EXECUTED=0 / PAID_ACCOUNTS_CREATED=0 / DOMAINS_PURCHASED=0
PERSONAL_DATA_COMMITTED=false
```

## 11. Operationalisierungslauf — Fortsetzung 2026-08-11 (Nachmittag)

Fortsetzung desselben Tages: Live-Verifikation der offenen Content-/URL-Werte,
Excel-Usability-Politur, Desktop-Arbeitspaket. CRM-Daten selbst wurden **nicht**
neu gebaut (No-Regression) — nur die bereits bestehenden Exportdateien um
belegte Werte ergänzt und neu geschrieben (gleicher Inhalt, zusätzliche
Formatierung + befüllte Felder).

### 11a. Landing-URL — live verifiziert

`FINAL_LANDING_URL = https://www.hsb-boden.de/kontakt/` — `curl -I`: HTTP 200,
Kontaktformular vorhanden. Apex-Redirect-Test mit echtem UTM-String
(`?utm_source=email&utm_medium=outreach&utm_campaign=kaltakquise-2026-q3&utm_content=joel-flyer`)
zeigt: `https://hsb-boden.de/kontakt/?...` → HTTP 301 →
`https://www.hsb-boden.de/kontakt/?...` mit **vollständig erhaltenen
Query-Parametern**. `LANDING_URL_GATE=PASS`, `LANDING_URL_UTM_GATE=PASS`.

### 11b. Flyer-URLs — live verifiziert

Beide Produktions-URLs live geprüft (`curl -I`): HTTP 200,
`content-type: application/pdf`, keine Preview-Domain.
- `FINAL_FLYER_URL_JOEL = https://www.hsb-boden.de/HSB-Flyer-Joel-Cherino.pdf`
- `FINAL_FLYER_URL_JORDI = https://www.hsb-boden.de/HSB-Flyer-Jordi-Post.pdf`

`FLYER_URL_GATE=PASS`.

### 11c. UTM-Matrix — korrigiert, nicht neu erfunden

`docs/assets/UTM_QR_DOWNLOAD_MATRIX.md` bestand bereits mit der kanonischen
Konvention (`utm_campaign=kaltakquise-2026-q3`, `utm_content=joel-flyer` /
`jordi-flyer`). Einziger Fix: Basis-URL von `https://hsb-boden.de` (Apex,
Status "awaiting-dns") auf `https://www.hsb-boden.de` (Live-Realität)
korrigiert — der Status "awaiting-dns" war seit dem Pages-Cutover überholt
und wurde ersetzt durch "verified-live-2026-08-11". `UTM_MAPPING_STATUS=VERIFIED`.

### 11d. Mail-Templates — bestehende Vorlagen mit stabilen IDs versehen

`docs/email/EMAIL_DELIVERABILITY_AND_TEMPLATE_READINESS.md` enthielt bereits
4 vollständige Templates (Subject + Body + Signatur, real, nicht Platzhalter).
Vergebene IDs: `EMAIL_TEMPLATE_JOEL_PRIMARY`, `EMAIL_TEMPLATE_JORDI_PRIMARY`,
`EMAIL_TEMPLATE_FOLLOWUP_14D`, `EMAIL_TEMPLATE_WEBFORM_FOLLOWUP`. Flyer-Link im
Dokument von Apex- auf www-URL korrigiert. Kein neuer Text geschrieben.
**Ehrlicher Befund:** Templates 2–4 nutzen aktuell Anhang+Telefon als CTA,
keinen klickbaren Landing-Link im Fließtext — bewusst nicht in dieser Sitzung
geändert (bestehende, freigegebene Formulierung). `EMAIL_TEMPLATE_STATUS=VERIFIED`.

### 11e. Exporte aktualisiert und erneut Readback

Alle vier bestehenden Exportdateien (`HSB_CRM_MASTER`, `HSB_OUTREACH_READY`,
`HSB_OUTREACH_JOEL`, `HSB_OUTREACH_JORDI`, `HSB_PROPOSED_INITIAL_BATCH`) mit
den oben verifizierten Werten befüllt: `Landing_URL` (alle Zeilen),
`Flyer_URL`/`Flyer_ID`/`Email_Template_ID`/`UTM_Content` (owner-abhängig
Joel/Jordi), `UTM_Source`/`UTM_Medium`/`UTM_Campaign`/`Kampagne_ID` (alle
Zeilen). `Segment` und `Batch_ID` bleiben bewusst leer (kein belegter Wert).
**Erneuter Readback:** `Versandfreigabe=no` weiterhin bei allen 6.424 Zeilen
unverändert, `Send_Status=not_sent` überall, Zeilenzahlen identisch zu vorher
(6.424/3.212/3.212/6.424/50). `EXPORT_READBACK_GATE=PASS`, `PII_GIT_GATE=PASS`.

### 11f. Excel-Usability

`HSB_CRM_MASTER` und alle Einzeldateien: erste Zeile eingefroren, AutoFilter
gesetzt, Header hervorgehoben, Spaltenbreiten an Inhalt angepasst,
Telefonnummern als Text formatiert (führende Nullen erhalten), lange
Freitextfelder mit Wrap Text. README-Tab an erster Stelle mit vollständiger
Tab-Erklärung, Versandfreigabe-/Send_Status-Bedeutung, Datei-Zuordnung
Joel/Jordi/Import — ohne PII-Duplizierung. Neu ergänzt: `DASHBOARD`-Tab
(aggregierte Kennzahlen) und `ACTIVITIES`-Tab (leeres Aktivitäten-Log-Template,
Lead_ID-verknüpft) für die tägliche Arbeit. Keine Makros, keine ActiveX, keine
externen Workbook-Links, keine absoluten lokalen Pfade.

### 11g. CRM-Betriebsmodell — Microsoft Lists/SharePoint nicht prüfbar

Kein Microsoft-Graph-/SharePoint-Connector in dieser Umgebung verfügbar
(`ToolSearch` ergebnislos, kein MCP/CLI mit M365-Auth). `MICROSOFT_LISTS_AVAILABLE`,
`SHAREPOINT_AVAILABLE`, `EXTRA_LICENSE_REQUIRED` = **NOT_VERIFIED_NO_CONNECTOR_IN_THIS_ENVIRONMENT**
— nicht geraten. Gemäß der eigenen Fallback-Logik des Auftrags sofort auf
Option B umgestellt:

`CRM_OPERATION_MODE = EXCEL_COAUTHORING` (empfohlen als Ausgangspunkt) —
`HSB_CRM_MASTER_2026-08-11.xlsx` auf OneDrive/SharePoint legen (bereits
vorhandene M365-Lizenz, keine Zusatzkosten), Joel + Jordi Edit-Zugriff, AutoSave.
Owner-Aktion: tatsächlich prüfen, ob Microsoft Lists im Tenant ohne
Zusatzkosten verfügbar ist (Browser-Login nötig, in dieser Sitzung nicht
durchgeführt) — bei Verfügbarkeit späterer Umstieg möglich, aber kein Blocker
für den heutigen Arbeitsbeginn.

### 11h. Desktop-Arbeitspaket — erstellt und QA-geprüft

Pfad: `data/lead-import/output/final_2026-08-11/HSB_OUTREACH_DESKTOP_PACKAGE_2026-08-11/`
(gitignored) + `HSB_OUTREACH_DESKTOP_PACKAGE_2026-08-11.zip` (7,3 MB) im
selben Ordner. Struktur: `01_CRM_MASTER … 08_DOKUMENTATION` +
`START_HIER.html`/`.txt`, `VERSAND_START_HIER.html`,
`THUNDERBIRD_MAIL_MERGE_SETUP.html`/`.txt`, `JOEL_TAGESABLAUF.txt`,
`JORDI_TAGESABLAUF.txt`.

QA-Ergebnis:
- `unzip -t`: keine Fehler, ZIP-Integrität PASS
- 18 relative Links in allen HTML-Dateien geprüft — alle Ziele existieren, 0 fehlend
- 0 externe `href`/`src` (kein Internet nötig) — `OFFLINE_NAVIGATION_GATE=PASS`
- xlsx-Readback aus entpacktem ZIP: 16 Sheets, Zeilenzahlen identisch (6.424/3.212/3.212/50)
- Beide PDFs im Paket als valide PDF (`file`-Check) bestätigt
- Keine `.git`, `.env`, `.local-secrets`, `.DS_Store` im ZIP
- `DESKTOP_PACKAGE_GATE=PASS`, `PACKAGE_INTEGRITY_GATE=PASS`

**Nebenfund:** Eine temporäre Test-Entpackung wurde im Scratchpad
(`/private/tmp/...`) angelegt und **nicht** automatisch gelöscht — der
`rm`-Hook verlangt Einzelfreigabe. Betrifft nur eine Kopie außerhalb des
Projekts, keine Datenintegrität betroffen.

### 11i. Thunderbird/Free-Send — eingeordnet, nicht gestartet

`BEST_FREE_SEND_TOOL=THUNDERBIRD_MAIL_MERGE` (offiziell für XLSX/CSV,
Merge-Variablen, Anhänge, Start/Stop/Pause, Send-Later/Outbox). Klar
dokumentiert: `FREE_BULK_SENDING_SOLVED=false` — Thunderbird ist Client, keine
Bulk-Infrastruktur, löst nicht das grundsätzliche Volumenproblem für 6.424
Leads über eine reguläre M365-Mailbox (Microsoft empfiehlt Exchange Online
nicht für kommerziellen Massenversand). Kein Warm-up gestartet, keine
synthetische Testmail versendet (`SYNTHETIC_MAIL_MERGE_GATE=NOT_EXECUTED` —
Vorbereitung dokumentiert, tatsächlicher Test bewusst nicht in dieser Sitzung
durchgeführt, da Thunderbird/Add-on-Installation ein Owner-System-Eingriff ist).

## 12. Owner-Aktionen erforderlich

1. Entscheidung: Smartlead-Testkonto anlegen (kostenpflichtig ab $39/Mon.,
   Pro-Plan $94/Mon. für vollen Bestand) oder Instantly als Alternative prüfen.
2. Klären: Wer hat Adminzugang zum All-Inkl/Kasserver-Kundenmenü für
   `hsb-boden.de` (separate Frage von M365-Tenant-Admin)?
3. Entscheidung zu `Versandfreigabe` (weiterhin `no`) — pauschal oder
   gestaffelt nach Tier freigeben.
4. Bestätigen oder liefern: finaler Akquise-Mail-Volltext (in dieser Sitzung
   nicht lokalisiert).
5. Nach Tool-Wahl: konkreten DNS-Change-Plan mit echten Provider-Records neu
   erzeugen (aktuell nur Architektur-Empfehlung, keine Records, da Tool noch
   nicht gewählt).
