# TRUTH_MATRIX — 2026-07-15 (Fable-5-Finalisierungspass)

Erstellt: 2026-07-15 ~03:35 CEST · Modell: Claude Code (Fable 5) · Basis: main = `6fa875e` (== origin/main)

Jede Aussage ist gekennzeichnet: VERIFIED (frisch geprüft in dieser Session), HISTORICAL, STALE, CONTRADICTED, NOT_FOUND, OWNER_GATE.

## 1. Repo / Git / GitHub

| Punkt | Status | Evidenz |
|---|---|---|
| main == origin/main auf `6fa875e`, Working Tree clean | VERIFIED | `git status`/`git log` 2026-07-15 |
| PR #79/#80/#81 (Lead-Attribution + Docs + Connector-Patch) gemerged | VERIFIED | Commits ad7ebc3/76fcffe/6fa875e auf main |
| 39 offene PRs (davon Großteil Jules-Bot-Drafts) | VERIFIED | `gh pr list --state open` 2026-07-15 |
| PR #74 (GitHub-Models-PoC) Draft, isoliert, kein Produktionsbestandteil | VERIFIED | PR-Liste; nicht angefasst |
| Tests 147/147, `check` 0 warnings, Build 35 Seiten, `deploy:dry-run` grün | VERIFIED | Frische Läufe 2026-07-15 03:29–03:31 |

## 2. Cloudflare / Live-Website

| Punkt | Status | Evidenz |
|---|---|---|
| https://www.hsb-boden.de/ HTTP 200 via Cloudflare Pages | VERIFIED | curl 2026-07-15 |
| Apex `hsb-boden.de` → **301 auf www** (Apache/All-Inkl), Query-Strings (UTM) bleiben erhalten | VERIFIED, **CONTRADICTED ggü. CHECKPOINT_STATE `blocked_by` („Apex zeigt auf WordPress")** — der Apex-Redirect ist inzwischen gesetzt | curl `/` und mit UTM-Parametern |
| Canonical auf Startseite → `https://www.hsb-boden.de/` | VERIFIED | curl |
| robots.txt nennt `Sitemap: https://www.hsb-boden.de/sitemap.xml` | VERIFIED | curl |
| Preview-Worker `hsb-boden-preview.cherinojoel.workers.dev` liefert weiter HTTP 200 (liegt im ALTEN cherinojoel-CF-Account; die 07-12-Löschung betraf nur den neuen Account) | VERIFIED | curl |
| Nicht-existente Pfade (z. B. Tippfehler `HSB-Flyer-Jordie-Post.pdf`) liefern HTTP 200 + text/html (Soft-404-Verhalten) | VERIFIED | curl -I |

## 3. Google Search Console (Entscheidung beider Properties)

Zugriff: Chrome-Session `info@hsb-boden.de` (authuser=1). VERIFIED 2026-07-15.

| Property | Klassifikation | Zustand |
|---|---|---|
| `https://www.hsb-boden.de/` | **AKTIVE PRODUKTIONS- UND SEO-WAHRHEIT** | 29 indexiert / 5 nicht indexiert (3× „Gecrawlt – zurzeit nicht indexiert", 2× „Gefunden – zurzeit nicht indexiert" — normale Google-Zustände, keine Fehler, keine noindex-Probleme). Sitemap `/sitemap.xml` eingereicht 09.07., zuletzt gelesen 12.07., Status Erfolgreich, 33 Seiten. HTTPS 29/0. Breadcrumbs 18 gültig / 0 ungültig. |
| `hsb-boden-preview.cherinojoel.workers.dev` | **HISTORISCH — behalten als Referenz, keine SEO-Arbeit mehr dagegen** | Genau 1 indexierte Seite, 0 nicht indexiert, 1 Klick gesamt. Keine dritte Property erzeugen. Nicht löschen ohne Owner-Entscheid. |

Empfehlung Preview: behalten als historische Ansicht; optional (Owner) den alten Preview-Worker im cherinojoel-CF-Account stilllegen oder mit `X-Robots-Tag: noindex` versehen, damit der 1-Seiten-Indexrest ausläuft.

**Fehlkonfiguration (Owner-Aktion):** GA4 (Property p543244027) ist mit der **Preview**-GSC-Property verknüpft (Kopplung 09.07.), nicht mit der Production-Property. → In GA4-Admin die Search-Console-Verknüpfung auf `https://www.hsb-boden.de/` umstellen.

## 4. Analytics

| Punkt | Status |
|---|---|
| GA4 erreichbar (info@-Login), Datenfluss aktiv | VERIFIED |
| 7-Tage-Traffic überwiegend (direct)/(none) aus den USA → Bot-/Crawler-Rauschen, kein realer Kundentraffic | VERIFIED (Interpretation: INFERRED) |
| 0 Key Events konfiguriert (Lead-Submit nicht als Schlüsselereignis) | VERIFIED → Owner-Empfehlung: `generate_lead`/Danke-Seite als Key Event markieren |
| Lead-Attribution (sessionStorage `hsb-attribution-v1`) live auf www | HISTORICAL (live-verifiziert 2026-07-14), Code auf main VERIFIED |

## 5. Google-Zugänge (MCP) — zentraler Befund

Alle 4 MCP-Profile (cherinojoel, cherinodiaz, hsb-boden, info) wurden 2026-07-15 ~01:08–01:15 neu authentifiziert, validieren aber **alle gegen denselben Google-Account `cherinodiaz@outlook.com`**.

Folgen:
- CRM-Sheets („HSB CRM Light", MASTER/JOEL/JORDI-Kaltakquise) liegen im Konto `cherinojoel@gmail.com` → Direktzugriff per ID liefert **403** → **OWNER_GATE CRM**.
- Der frühere Befund „info@-Profil tot / 403-Testnutzer" ist STALE (Token existiert), aber das Profil zeigt auf den falschen Account.
- GSC/GA4 sind nur über die Chrome-Session (authuser=1 = info@hsb-boden.de) erreichbar, nicht über MCP.

**Genau ein manueller Schritt für dieses Gate:** `npx @dguido/google-workspace-mcp auth` für Profil `cherinojoel` ausführen und dabei im Browser **cherinojoel@gmail.com** wählen (analog optional Profil `info` → info@hsb-boden.de). Danach sind CRM-Prüfung + Apps-Script-Spaltenmapping maschinell möglich.

## 6. CRM / Apps Script / Attribution (W4)

| Punkt | Status |
|---|---|
| Website→Webhook→CRM-Funnel Ende-zu-Ende | HISTORICAL (belegt 2026-07-12, Testzeile gelöscht) |
| Attribution-Felder im Payload (utm_term/utm_content/referrer/landing_page/form_path/attribution_channel) | VERIFIED (Code auf main + 147 Tests) |
| Apps-Script-Spaltenmapping für Attributionsfelder | OWNER_GATE (Sheet 403; Patch liegt paste-fertig in `docs/crm/ATTRIBUTION_CONNECTOR_PATCH.md`) |
| Kontrollierter Live-Lead-Test in dieser Session | BEWUSST NICHT durchgeführt: ohne Sheet-Zugriff könnte die Testzeile nicht wieder gelöscht werden |
| MASTER-Sheet-Kennzahlen (6424 Leads, Tier A 1612 / B 4812, Versandfreigabe 0, Opt-in/out unknown) | HISTORICAL (2026-07-12) + lokal VERIFIED via Export-CSV (siehe unten) |

## 7. MASTER / JOEL / JORDI-Inventur (W5) — lokal VERIFIED

Quelle: `data/lead-import/output/` (Stand 2026-07-08, deckungsgleich mit Sheet-Befund vom 07-12):

| Datei | Zeilen (ohne Header) |
|---|---|
| HSB_CRM_Leads_ALL_MASTER_2026-07-08.csv | 6424 |
| HSB_CRM_Leads_ALL_Joel_2026-07-08.csv | 3212 |
| HSB_CRM_Leads_ALL_Jordi_2026-07-08.csv | 3212 |
| Joel_2500 / Jordi_2500 (Versandtranchen) | je 2500 |

Konsistenz VERIFIED: Joel ∪ Jordi == MASTER, Überlappung 0. Verteilungen: Verantwortlicher 3212/3212, Tier A 1612 / B 4812, Status 100% `neu`, Versandfreigabe 100% `no`, Opt-in/Opt-out 100% `unknown`, Kampagne `HSB-Outreach-2026-07`, Flyer-Anhang konsistent je Owner (`HSB-Flyer-Joel-Cherino.pdf` / `HSB-Flyer-Jordi-Post.pdf`).

29-Spalten-Header inkl. Status, Nächste Aktion, Follow-up-Datum, Opt-in/Opt-out, Versandfreigabe, Verantwortlicher, Flyer-Anhang, Notizen — beantwortet die operativen Fragen („Welche Leads gehören mir? Was ist überfällig? …") pro Zeile.

Schreibweise: **Jordi Post** ist kanonisch (Flyer-Datei, CSV, Live-URL). „Jordie" kommt nur noch in Alt-Dateinamen vor (`docs/handoff/JOEL_JORDIE_OPERATOR_RUNBOOK.md`) — Inhalt nutzt „JORDI".

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

## 10. Doku-Drift (zu korrigieren in diesem PR bzw. Folge-PR)

1. `CHECKPOINT_STATE.json` `blocked_by`: Apex-WordPress-Eintrag ist überholt (301 aktiv) → aktualisiert in diesem Branch.
2. `docs/handoff/JOEL_JORDIE_OPERATOR_RUNBOOK.md` Trigger A referenziert gelöschte Workers-Architektur (`wrangler deployments list --name hsb-boden`) → Pages-Pfad.
3. `CHECKPOINT_STATE.json` referenziert `docs/handoff/JOEL_JORDI_OPERATOR_RUNBOOK.md` (falscher Dateiname, real `JOEL_JORDIE_...`).
4. Notion-Task CNAME/Apex stale.
5. MASTER_EXECUTION_RULES.md §5/§6 (P0B-Phase) ist HISTORICAL gegenüber realem Projektstand (Website live, Formular live); PROJECT_TRUTH/CHECKPOINT gelten als aktueller.

## 11. Verbleibende echte Owner-Gates (konsolidiert)

| Gate | Genau ein manueller Schritt |
|---|---|
| CRM/Apps-Script (Attribution-Mapping) | MCP-Profil `cherinojoel` auf cherinojoel@gmail.com re-authen — oder `docs/crm/ATTRIBUTION_CONNECTOR_PATCH.md` selbst einspielen |
| GA4↔GSC-Verknüpfung | In GA4-Admin Search-Console-Link von Preview- auf www-Property umstellen |
| GBP-Verifizierung | Physische Postkarten-Verifizierung durch Joel |
| Kaltakquise-Versand | PHASE_7_COMPLIANCE_GATE.md mit Owner durchgehen (Rechtsgrundlage, Opt-out, Batch-Freigabe) + M365-DKIM für j-cherino@ aktivieren |
| Cloudflare-Altlasten | Doppelte CF-Zone im cherinojoel-Account löschen; alten Preview-Worker stilllegen/noindex; CF-API-Token rotieren (stand 07-02 kurz im Chat) |
| Service-Account-Key | `hsb-boden-5389a664a3a5.json` in ~/Desktop + ~/Downloads rotieren/verschieben |
