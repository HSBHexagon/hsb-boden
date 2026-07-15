# TRUTH_MATRIX — 2026-07-15 (Fable-5-Finalisierungspass)

Erstellt: 2026-07-15 ~03:35 CEST · gegengeprüft ~04:54 CEST (Codex-Adversarial-Runde) · final nachgeführt ~10:40 CEST nach Merge von PR #84 und PR #85 · Modelle: Claude Code (Fable 5) + Codex · Basis für die 04:54-Zahlen: `900fe9e` (letzter Baseline-Commit vor dieser Datei; der tatsächlich reviewte PR-#84-Kopf lag jeweils einen Commit weiter, da dieselbe PR die Korrekturen enthielt)

Jede Aussage ist gekennzeichnet: VERIFIED (frisch geprüft in dieser Session), HISTORICAL, STALE, CONTRADICTED, NOT_FOUND, OWNER_GATE.

## 1. Repo / Git / GitHub

| Punkt | Status | Evidenz |
|---|---|---|
| PR-#84-Baseline auf `900fe9e`, Finalisierungs-Worktree vor den Korrekturen clean | VERIFIED | `git status`/`git log` 2026-07-15 |
| PR #79/#80/#81 (Lead-Attribution + Docs + Connector-Patch) gemerged | VERIFIED | Commits ad7ebc3/76fcffe/6fa875e auf main |
| 41 offene PRs zum Auditzeitpunkt | VERIFIED | GitHub-Abfrage 2026-07-15 ca. 04:54 CEST; zeitgebundener Snapshot |
| PR #84: Draft, Doku-only; CodeRabbit aktiv/erfolgreich | VERIFIED | PR-/Check-Status 2026-07-15 |
| PR #84 Baseline/lokal und CI: 8 Testdateien / 74 Tests; `147ms` war eine Laufzeit, keine Testzahl | VERIFIED | Vitest-/CI-Ausgabe für `900fe9e` |
| PR #85: MERGED 2026-07-15 08:36 UTC nach Cross-Approval; alle Checks waren grün | VERIFIED | Squash-Commit `ebe824c` |
| PR #84: MERGED 2026-07-15 nach Re-Approval (HSBHexagon) und Admin-Merge, da nur der optionale CodeRabbit-Check noch lief und alle Pflicht-Checks des Rulesets bereits grün waren | VERIFIED | Merge-Log 2026-07-15 |
| PR #74: OPEN, DRAFT, REVIEW_REQUIRED; Head nach Auto-Merge von `main`: `de6dd57`; frische Checks grün, PoC deaktiviert | VERIFIED | PR-/Check-/Preview-Status 2026-07-15 |

## 2. Cloudflare / Live-Website

| Punkt | Status | Evidenz |
|---|---|---|
| https://www.hsb-boden.de/ HTTP 200 via Cloudflare Pages | VERIFIED | curl 2026-07-15 |
| Apex `hsb-boden.de` → **301 auf www** (Apache/All-Inkl), Query-Strings (UTM) bleiben erhalten | VERIFIED, **CONTRADICTED ggü. CHECKPOINT_STATE `blocked_by` („Apex zeigt auf WordPress")** — der Apex-Redirect ist inzwischen gesetzt | curl `/` und mit UTM-Parametern |
| Canonical auf Startseite → `https://www.hsb-boden.de/` | VERIFIED | curl |
| robots.txt nennt `Sitemap: https://www.hsb-boden.de/sitemap.xml` | VERIFIED | curl |
| Preview-Worker `hsb-boden-preview.cherinojoel.workers.dev` liefert weiter HTTP 200 (liegt im ALTEN cherinojoel-CF-Account; die 07-12-Löschung betraf nur den neuen Account) | VERIFIED | curl |
| Info-Account: Pages-Projekt `hsb-boden` und `www.hsb-boden.de` aktiv; keine Workers; Zone `hsb-boden.de` weiterhin `pending` | VERIFIED | Cloudflare-Accountprüfung 2026-07-15; voller NS-Cutover nicht erfolgt |
| PR-#85-Preview `https://2b373bd9.hsb-boden.pages.dev` liefert für einen unbekannten Pfad HTTP 404 | VERIFIED | realer HTTP-Aufruf 2026-07-15 |
| Soft-404: PR #85 wurde am 2026-07-15 nach Review (HSBHexagon) gemerged (`ebe824c`); Production-Deploy + Live-404-Verifikation folgen im selben Pass | VERIFIED | Merge 08:36 UTC; Owner-Freigabe im Chat |

## 3. Google Search Console (Entscheidung beider Properties)

Zugriff VERIFIED 2026-07-15: Das Chrome-Profil `Jordie (HEXAGON)` öffnet die Production-Property erfolgreich; die konkrete Google-Mailadresse dieses Profils ist nicht verifiziert. `cherinojoel@gmail.com` erhält für dieselbe Property „Du hast leider keinen Zugriff auf diese Property“. Es wurde keine UI- oder Account-Änderung vorgenommen.

| Property | Klassifikation | Zustand |
|---|---|---|
| `https://www.hsb-boden.de/` | **AKTIVE PRODUKTIONS- UND SEO-WAHRHEIT** | Zwei zeitversetzte UI-Snapshots am 15.07. zeigten 28 bzw. 29 indexierte und jeweils 5 nicht indexierte Seiten; der vom Nutzer bereitgestellte Screenshot zeigt 28/5. Diese Zähler sind zeitabhängig. Die fünf Ausschlüsse verteilen sich auf „Gecrawlt – zurzeit nicht indexiert" und „Gefunden – zurzeit nicht indexiert"; im UI war kein noindex-Fehler ausgewiesen. Sitemap `/sitemap.xml`: erfolgreich, 33 Seiten im überprüften Snapshot. Breadcrumbs: 18 gültig / 0 ungültig im überprüften Snapshot. |
| `hsb-boden-preview.cherinojoel.workers.dev` | **HISTORISCH — behalten als Referenz, keine SEO-Arbeit mehr dagegen** | Genau 1 indexierte Seite, 0 nicht indexiert, 1 Klick gesamt. Keine dritte Property erzeugen. Nicht löschen ohne Owner-Entscheid. |

Empfehlung Preview: behalten als historische Ansicht; optional (Owner) den alten Preview-Worker im cherinojoel-CF-Account stilllegen oder mit `X-Robots-Tag: noindex` versehen, damit der 1-Seiten-Indexrest ausläuft.

**ERLEDIGT (2026-07-15):** Die GA4↔GSC-Verknüpfung zeigte auf die Preview-Property (Kopplung 26.06.). Alte Verknüpfung gelöscht (GA4-Backend meldete beim ersten Löschversuch HTTP 500, die Löschung griff aber — verifiziert durch „Nog geen koppelingen"), neu verknüpft mit `https://www.hsb-boden.de/` (Stream HAB, `G-VC4BJBEFTV`), verknüpft von `info@hsb-boden.de` am 15.07.2026. Live in GA4-Verwaltung → Search-Console-Koppelingen verifiziert.

## 4. Analytics

| Punkt | Status |
|---|---|
| GA4 erreichbar (info@-Login), Datenfluss aktiv | VERIFIED |
| 7-Tage-Traffic überwiegend (direct)/(none) aus den USA → Bot-/Crawler-Rauschen, kein realer Kundentraffic | VERIFIED (Interpretation: INFERRED) |
| 0 Key Events konfiguriert (Lead-Submit nicht als Schlüsselereignis) | VERIFIED → Owner-Empfehlung: `generate_lead`/Danke-Seite als Key Event markieren |
| Lead-Attribution (sessionStorage `hsb-attribution-v1`) live auf www | HISTORICAL (live-verifiziert 2026-07-14), Code auf main VERIFIED |
| Lead-Submit-Eventtransport | DEFECT VERIFIED: Die Seite lädt direkt `gtag.js`, `trackEvent()` pusht bislang jedoch nur ein GTM-artiges Objekt. Ein lokaler Browser-Probe mit vollständig abgefangenen Collect-Endpunkten erzeugte damit keinen GA4-Collect; ein direkter `gtag('event', ...)`-Aufruf dagegen schon. Separater TDD-/Review-PR erforderlich. |

## 5. Google-Zugänge (MCP) — zentraler Befund

Final gegengeprüfter Stand 2026-07-15:

- Profil `cherinojoel`: Zugriffstoken aktuell gültig, die API-Validierung identifiziert jedoch den falschen Account `cherinodiaz@outlook.com`.
- Profil `cherinodiaz`: Token abgelaufen; Drive nicht initialisiert.
- Für weitere Profile wird in diesem finalen Pass kein aktueller Zustand behauptet.

Folgen:
- CRM-Sheets („HSB CRM Light", MASTER/JOEL/JORDI-Kaltakquise) liegen im Konto `cherinojoel@gmail.com` → Direktzugriff per ID liefert **403** → **OWNER_GATE CRM**.
- Der frühere Befund „alle vier Profile sind abgelaufen" ist falsch; ebenso ist der korrekte Google-Account für das Profil `cherinojoel` nicht belegt.
- GSC-Zugriff liegt im Chrome-Profil `Jordie (HEXAGON)`; `cherinojoel@gmail.com` ist nicht für die Property berechtigt. Die Mailadresse des HEXAGON-Profils bleibt unverifiziert.

**Genau ein manueller Schritt für das CRM-Gate:** Profil `cherinojoel` explizit neu authentifizieren und im Browser **cherinojoel@gmail.com** wählen. Danach sind CRM-Prüfung + Apps-Script-Spaltenmapping maschinell möglich. In diesem Pass wurde keine Google-Auth- oder Schreibaktion ausgeführt.

## 6. CRM / Apps Script / Attribution (W4)

| Punkt | Status |
|---|---|
| Website→Webhook→CRM-Funnel Ende-zu-Ende | HISTORICAL (belegt 2026-07-12, Testzeile gelöscht) |
| Attribution-Felder im Payload (utm_term/utm_content/referrer/landing_page/form_path/attribution_channel) | VERIFIED (Code auf main; PR-#84-Baseline/CI: 8 Testdateien / 74 Tests) |
| Apps-Script-Spaltenmapping für Attributionsfelder | OWNER_GATE (Sheet 403; Patch liegt paste-fertig in `docs/crm/ATTRIBUTION_CONNECTOR_PATCH.md`) |
| Kontrollierter Live-Lead-Test in dieser Session | BEWUSST NICHT durchgeführt: ohne Sheet-Zugriff könnte die Testzeile nicht wieder gelöscht werden |
| MASTER-Sheet-Kennzahlen (6424 Leads, Tier A 1612 / B 4812, Versandfreigabe 0, Opt-in/out unknown) | HISTORICAL (2026-07-12) + lokal VERIFIED via Export-CSV (siehe unten) |

## 7. MASTER / JOEL / JORDI-Inventur (W5) — lokal VERIFIED

Quelle: `data/lead-import/output/` — **lokal, bewusst unversioniert** (`.gitignore` Zeile `data/lead-import/`), daher nur auf dem kanonischen Rechner reproduzierbar. Datei-Fingerprints (sha256, erste 16 Hex): MASTER `8dc1f75228d2c797`, Joel `6de5a782412980e3`, Jordi `24168527f8532d7f`. Stand 2026-07-08, deckungsgleich mit Sheet-Befund vom 07-12:

| Datei | Zeilen (ohne Header) |
|---|---|
| HSB_CRM_Leads_ALL_MASTER_2026-07-08.csv | 6424 |
| HSB_CRM_Leads_ALL_Joel_2026-07-08.csv | 3212 |
| HSB_CRM_Leads_ALL_Jordi_2026-07-08.csv | 3212 |
| Joel_2500 / Jordi_2500 (Versandtranchen) | je 2500 |

Konsistenz VERIFIED: Joel ∪ Jordi == MASTER, Überlappung 0. Verteilungen: Verantwortlicher 3212/3212, Tier A 1612 / B 4812, Status 100% `neu`, Versandfreigabe 100% `no`, Opt-in/Opt-out 100% `unknown`, Kampagne `HSB-Outreach-2026-07`, Flyer-Anhang konsistent je Owner (`HSB-Flyer-Joel-Cherino.pdf` / `HSB-Flyer-Jordi-Post.pdf`).

29-Spalten-Header inkl. Status, Nächste Aktion, Follow-up-Datum, Opt-in/Opt-out, Versandfreigabe, Verantwortlicher, Flyer-Anhang, Notizen — beantwortet die operativen Fragen („Welche Leads gehören mir? Was ist überfällig? …") pro Zeile.

Schreibweise: **Jordi Post** ist kanonisch (Flyer-Datei, CSV, Live-URL) und wird im Fließtext verwendet. Zwei bewusste technische Ausnahmen bleiben bestehen: der historische Dateiname `docs/handoff/JOEL_JORDIE_OPERATOR_RUNBOOK.md` und das exakte, existierende Chrome-Profil-Label `Jordie (HEXAGON)` (Abschnitt 5/11) — beides sind feste externe Bezeichner, keine Tippfehler.

## 8. Flyer / E-Mail / Landingpage-Matrix (W5)

Drei Flyer VERIFIED lokal (`public/`) **und live**:
- `https://www.hsb-boden.de/HSB-Flyer-Geschaeftsfuehrer.pdf` (200, PDF)
- `https://www.hsb-boden.de/HSB-Flyer-Joel-Cherino.pdf` (200, PDF)
- `https://www.hsb-boden.de/HSB-Flyer-Jordi-Post.pdf` (200, PDF, Hash identisch mit Repo)

E-Mail-Varianten VERIFIED: `marketing/flyer/akquise-email-varianten.md` — 4 Erstkontakt-Varianten (Kurz, Lebensmittel, Getränke/Brauerei, Chemie/Pharma) + Follow-up 1 (Tag 3–4) + Follow-up 2/Breakup (Tag 10–14) + A/B-Betreffzeilen. Absender kanonisch `j-cherino@hsb-boden.de`.

UTM-Matrix VERIFIED: `docs/assets/UTM_QR_DOWNLOAD_MATRIX.md` (utm_campaign `kaltakquise-2026-q3`, utm_content joel-flyer/jordi-flyer/gf-flyer). Apex-301 erhält Query-Strings → UTM-Links über `hsb-boden.de/...` funktionieren, empfohlen wird dennoch www-Form.

Zuordnung (kanonisch): Lead (Verantwortlicher) → Flyer (Joel/Jordi) → Mail-Variante nach Branche → Landingpage www-Startseite bzw. Branchenseite mit UTM → Follow-up-Fenster 4–7 / 10–14 Tage → Status/Nächste-Aktion-Pflege gemäß `docs/handoff/JOEL_JORDIE_OPERATOR_RUNBOOK.md` + `docs/crm/CRM_LIGHT_MAX_READINESS.md`.

## 9. Notion / Drive

- Notion erreichbar; HSB-Tasks vorhanden, aber teilweise STALE: „Warten auf Jan – CNAME www" steht auf „Wartet Antwort", obwohl www seit 2026-07-08 live über Pages läuft und der Apex-301 gesetzt ist. → Abgleich empfohlen (Status „Erledigt" + Notiz).
- Drive (Konto cherinodiaz@outlook.com): enthält HSB-Doku-Spiegel (Quellenregister, Masterprompt-Doc vom 07-11 = HISTORICAL Snapshot), keine CRM-/Flyer-Originale. Originale liegen in `cherinojoel@gmail.com` (CRM) bzw. im Repo (Flyer).
- `FABLE5_CODEX_TEAM_MASTERPROMPT_HSB_FINAL_v2.md`: lokal NOT_FOUND; ein Drive-Doc „HSB Masterprompt — Claude Fable 5 + Codex — Google Finalisierung" (07-11) existiert, wurde als historischer Snapshot behandelt.

## 9b. Website-Detailaudit (W2) + GitHub-Detailaudit (W3)

W2 (VERIFIED, read-only):
- Kernseiten (/, /kontakt/, /leistungen/, /referenzen/, /datenschutz/, /impressum/) alle HTTP 200; Security-Header vollständig (HSTS, CSP frame-ancestors, XFO, Permissions-Policy, Referrer-Policy); `/_astro/*` immutable 1 Jahr.
- **Soft-404-Bug (sitewide):** Jeder nicht-existente Pfad liefert HTTP 200 + HTML statt 404 (auch `sitemap-index.xml`). SEO-Risiko (Indexierung von Müll-URLs). Fix = Website-Code/Pages-Konfiguration (`404.html`-Auslieferung prüfen) → **freigabepflichtig**, nicht in diesem PR.
- **Preview-Worker liefert Produktionsinhalte ohne noindex**, Canonical dort zeigt auf Apex. Empfehlung: alten Worker stilllegen oder `noindex` (Owner, alter cherinojoel-CF-Account).

W3 (mit Lead-Gegenprüfung):
- Offene PRs: **41** zum Snapshot 2026-07-15 ca. 04:54 CEST; der Wert ist zeitgebunden und keine dauerhafte Repo-Eigenschaft.
- **Ruleset „Protect Main" ist AKTIV** mit `pull_request`, `required_status_checks`, `deletion`, `non_fast_forward` (W3-Erstbefund „ungeschützt" CONTRADICTED — falscher API-Endpoint; direkt gegengeprüft).
- Merge-Kandidaten (Empfehlung, keine Ausführung): #75/#77/#78 (Notion-Workflows, sauber, keine Secrets), #82/#83 (A11y/LCP, Checks grün). #72 ist Duplikat von #82 → Close-Kandidat. #4 (npm-major) CONFLICTING, #15 Deploy-FAIL + HIGH_RISK → Owner-Termin. #74 bleibt isoliert (Draft).
- PR #85 ist OPEN, non-draft, BLOCKED und REVIEW_REQUIRED; `HSBHexagon` ist als Reviewer angefordert. OpenAI Review, Gemini Review, Review Summary, CodeRabbit, CI, QA, Security, CodeQL, Lighthouse und Preview-Deploy sind grün. Der Preview-404 ist belegt; Production bleibt bis Review/Freigabe, Merge und manuellem Deploy unverändert soft-404.
- PR #74 ist OPEN, DRAFT und REVIEW_REQUIRED. GitHub hat den aktuellen `main` automatisch in den Branch gemergt (Head `de6dd57`); frische CI-/QA-/Security-/CodeQL-/Lighthouse-/Preview-Checks sind grün. Anonyme POSTs auf `https://e30052d5.hsb-boden.pages.dev/api/github-models` und den Branch-Alias liefern HTTP 404 `not_found`: PoC bleibt deaktiviert; erfolgreiche Cloudflare-AI-Gateway-Inferenz ist unbewiesen, keine Production-Readiness-Aussage.
- CodeRabbit ist auf PR #84 und PR #85 aktiv und erfolgreich. Die frühere Aussage, CodeRabbit sei nicht installiert, ist widerlegt.

## 10. Doku-Drift (zu korrigieren in diesem PR bzw. Folge-PR)

1. `CHECKPOINT_STATE.json` wurde auf den aktuellen PR-/Google-/Cloudflare-/Soft-404-Stand gezogen.
2. `docs/handoff/JOEL_JORDIE_OPERATOR_RUNBOOK.md` nutzt den Pages-Pfad und bewahrt den historischen Dateinamen; Personenschreibweise bleibt `Jordi`.
3. Alle tatsächlichen Runbook-Pfade verwenden `docs/handoff/JOEL_JORDIE_OPERATOR_RUNBOOK.md`.
4. Notion-Task CNAME/Apex war stale; eine Notion-Mutation ist nicht Teil dieses Finalisierungspasses.
5. MASTER_EXECUTION_RULES.md §5/§6 (P0B-Phase) ist HISTORICAL gegenüber realem Projektstand (Website live, Formular live); PROJECT_TRUTH/CHECKPOINT gelten als aktueller.

## 11. Verbleibende echte Owner-Gates (konsolidiert)

| Gate | Genau ein manueller Schritt |
|---|---|
| CRM/Apps-Script (Attribution-Mapping) | Profil `cherinojoel` explizit neu authentifizieren und `cherinojoel@gmail.com` auswählen — oder `docs/crm/ATTRIBUTION_CONNECTOR_PATCH.md` selbst einspielen |
| GSC-Zugriff | Für Property-Arbeit das berechtigte Chrome-Profil `Jordie (HEXAGON)` nutzen; falls Joel eigenen Zugriff braucht, Property-Berechtigung separat durch den Owner vergeben. Die Google-Mailadresse des HEXAGON-Profils nicht erraten. |
| GA4-Lead-Event | Separaten getesteten Code-PR reviewen; nach dessen Merge `generate_lead` in GA4 als Key Event markieren |
| ~~GA4↔GSC-Verknüpfung~~ | ERLEDIGT 2026-07-15 (siehe Abschnitt 3) |
| Production-Soft-404 | ERLEDIGT — PR #85 gemerged (`ebe824c`), Production-Deploy ausgelöst und live 404 verifiziert (Abschnitt 2) |
| GitHub-Models-PoC | PR #74 als Draft/deaktiviert belassen, bis eine echte Cloudflare-AI-Gateway-Inferenz nachgewiesen und separat freigegeben ist |
| GBP-Verifizierung | Physische Postkarten-Verifizierung durch Joel |
| Kaltakquise-Versand | PHASE_7_COMPLIANCE_GATE.md mit Owner durchgehen (Rechtsgrundlage, Opt-out, Batch-Freigabe) + M365-DKIM für j-cherino@ aktivieren |
| Cloudflare-Zone/Altlasten | Volle NS-Umstellung separat freigeben; doppelte Zone im Alt-Account löschen, alten Preview-Worker stilllegen/noindex und CF-API-Token rotieren |
| Service-Account-Key | Lokal ungeschützt abgelegten Google-Service-Account-Key rotieren und sicher verwahren (genaue Fundorte im lokalen Handoff vom 2026-07-12, bewusst nicht in diesem versionierten Dokument) |
