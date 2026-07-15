# GOAL — HSB-Boden Finalisierung

> Konsolidiertes Ziel-/Statusdokument. Stand: 2026-07-15, 12:06 CEST.
> Ergänzt `docs/MASTER_EXECUTION_PLAN.md` (Phasenmodell) um eine flache, bereichsweise Sicht: was ist fertig, was ist blockiert und warum, was ist der nächste konkrete Schritt.

## Gesamtziel

`www.hsb-boden.de` als funktionierendes, sichtbares und technisch sauberes
B2B-Akquise-System betreiben: Website live, Lead-Pipeline abgesichert,
Google-Sichtbarkeit messbar und Outreach kontrolliert freigabefaehig. Ein voller
NS-Cutover ist optional und kein globales Abschlusskriterium.

---

## 1. Website & Deploy — ✅ produktiv, Kernfehler behoben

| Punkt | Status |
|---|---|
| `www.hsb-boden.de` live über Cloudflare Pages | ✅ |
| `pages-static-migration` → `main` konsolidiert | ✅ committed und **gepusht** |
| Canonical-Domain-Bug (Code zeigte auf Apex statt www) | ✅ gefixt und deployed |
| Rate-Limit-Bypass-Lücke in `/api/lead` (In-Memory statt verteilt) | ✅ gefixt via Cloudflare KV (`RATE_LIMIT_KV`, Namespace neu im `info@hsb-boden.de`-Account gebunden), deployed |
| JSON-LD-XSS-Härtung (PR #32) | ✅ gemergt nach `main` auf GitHub |
| Tests/Build/Check im Production-Run `29404977846` | ✅ Astro Check ohne Findings, 83 Tests, 36 Seiten |
| Apex `hsb-boden.de` | ✅ 301 auf `www`, Query-Parameter bleiben erhalten |
| Lokales Root-`main` vs. `origin/main` | ⚠️ getrackte Dateien unveraendert, sechs Commits hinter `origin/main`; ungetracktes `.local-secrets/` aus laufender Fable-Sitzung nicht geoeffnet/veraendert; Reconciliation-Worktree basiert auf aktuellem `origin/main` |
| GitHub-Actions-Secrets `CLOUDFLARE_API_TOKEN`/`CLOUDFLARE_ACCOUNT_ID` | ✅ neu gesetzt (vorheriger Wert leer/ungültig) |
| CI-Deploy-Workflows (`deploy-preview.yml`, `deploy-production.yml`) | ✅ von obsoleter Worker-Architektur auf Cloudflare Pages migriert; Production-Deploy bleibt bewusst `workflow_dispatch`-only (manueller Gate erhalten), PR-Previews deployen jetzt korrekt auf Pages-Branch-URLs |
| Unbekannte Pfade | ✅ echter HTTP 404, `no-store`, `noindex` |
| `GET /api/lead` | ✅ HTTP 405 ohne Lead-Erzeugung; `Allow: POST` fehlt als kleiner Vertrags-Follow-up |

**Nächster Schritt:** Kein unrelatierter Production-Deploy. Der einzige
vorgesehene Deploy ist der review- und owner-gesteuerte, dual-kompatible
P0-Webhook-Sicherheitscutover; danach nur gezielte Follow-ups ueber reviewbare
PRs.

---

## 2. Lead-Pipeline & CRM — ⚠️ technisch live, Security-Gate offen

| Punkt | Status |
|---|---|
| `/api/lead` → Cloudflare Pages Function → Apps Script → Sheet „HSB CRM Light" | ✅ 2026-07-15 operator-verifiziert: UTM-Testlead zugestellt, sechs Attributionsfelder korrekt, Testzeile gelöscht; Auth-Sicherheit separat offen |
| `LEAD_WEBHOOK_URL` auf Cloudflare Pages Production gesetzt | ⚠️ HISTORICAL/COMPROMISED: Legacy-Wert aktiv, darf nicht als genehmigte Sicherheitskonfiguration gelten |
| Reale Kaltakquise-Lead-Daten | ✅ vorhanden — 6.424 Datensätze, 3 Sheets (Master/Joel/Jordi) |
| Schema-Drift zwischen den 4 CRM-Sheets | ⚠️ dokumentiert, **nicht bereinigt** — `CRM_LIGHT_SCHEMA.md` ist kanonisch erklärt |
| Weiteres historisches Apps-Script-Deployment | ⚠️ Redigiert, aber bis zur nachgewiesenen Invalidation nicht als risikofrei behandeln |
| Zwei Apps-Script-Endpunkte im oeffentlichen Git-Verlauf | ❌ P0: anonym erreichbar; neuen authentifizierten Pfad ohne Ausfall aufbauen/testen, URL umstellen und alte Deployments zuletzt invalidieren |

**Nächster Schritt:** Neuen Apps-Script-Pfad und eine dual-kompatible Pages
Function vorbereiten. Das einzelne JSON-Secret `LEAD_WEBHOOK_CONFIG` kapselt URL
und Token: zuerst nur Preview negativ/E2E testen, dann Production mit genau
diesem einen Secret konfigurieren und denselben geprueften Commit ueber den
manuellen Production-Workflow erneut deployen. Erst dieses Deployment bindet
URL+Token. Danach einen loeschbaren synthetischen Testlead pruefen,
Legacy-Secret entfernen und alte Deployments zuletzt invalidieren. Kein
Outreach-Versand.

---

## 3. SEO & Analytics — ⚠️ technische Basis aktiv, Conversion-Beweis offen

| Punkt | Status |
|---|---|
| GA4 Tracking-Code im Build | ✅ produktiv vorhanden |
| GA4-Property „HSBBODENCLOUDFLAIRE" (Account HexagonSäurebauGmbH) | ✅ identifiziert, verifiziert |
| GA4 Datenaufbewahrung | ✅ auf 14 Monate vereinheitlicht (vorher: Events nur 2 Monate) |
| GSC-Property für `www.hsb-boden.de` | ✅ Production-Property vorhanden; aktueller Backend-Link von PR #89 operator-verifiziert, im Repo-Audit nicht unabhaengig reproduziert |
| Sitemap bei GSC eingereicht | ✅ |
| Indexierung Startseite + Kontakt angefragt | ✅ |
| GA4 `gtag('event', ...)`-Pfad | ✅ durch PR #87 produktiv; PR #90 belegt den lokalen Aufrufpfad |
| GA4 Netzwerkempfang/DebugView/Key Event | ⬜ nicht end-to-end belegt |
| Doppelte Cloudflare-Zone für `hsb-boden.de` (Account cherinojoel) | ⚠️ identifiziert, **nicht gelöscht** (API-Token ohne Löschrecht) — die produktive Zone liegt im `info@hsb-boden.de`-Account |

**Nächster Schritt:** Basic-vs.-Advanced-Consent explizit entscheiden,
kanonischen Eventnamen festlegen, Delivery vor Navigation absichern und den
Empfang in Network/DebugView verifizieren. PR #86 nicht unveraendert mergen.

---

## 4. Google Unternehmensprofil — ❌ nicht begonnen, nicht delegierbar

Erfordert Neuanlage eines Profils plus Postkarten-/Telefon-Verifizierung an die reale Geschäftsadresse. Das kann **nur Joel selbst** durchführen — weder Kontoerstellung noch physische Verifizierung sind an mich delegierbar, unabhängig von erteilter Freigabe.

**Nächster Schritt (nur durch Joel):** `business.google.com` → Unternehmensprofil für „HSB Hexagon Säurebau GmbH" anlegen, Adresse verifizieren lassen.

---

## 5. Apex-DNS (`hsb-boden.de` ohne www) — ✅ funktional, voller NS-Cutover optional

- Registrar (All-Inkl/Kasserver) nutzt weiterhin die bisherigen Nameserver — kein voller NS-Switch erfolgt.
- Zwei Cloudflare-Zonen existieren parallel vorbereitet; die richtige liegt im `info@hsb-boden.de`-Account.
- Der funktionale Website-Zielzustand ist durch den query-erhaltenden 301 auf
  `www` erreicht. Ein voller NS-Cutover ist keine Website-Completion-
  Voraussetzung und bleibt wegen E-Mail-Routing-Risiken separat freigabepflichtig.

**Nächster Schritt (optional, nur Joel/Jan):** Vor einer Nameserver-Aenderung
einen frischen Pages-/Mail-DNS-Plan erstellen und alle MX/SPF/DKIM/DMARC-
Eintraege sichern. Das historische Worker-Cutover-Runbook nicht ausfuehren.

---

## 6. Kaltakquise-Versand (Phase 7) — ❌ blockiert durch eigenes Compliance-Gate

- `docs/launch/PHASE_7_COMPLIANCE_GATE.md` verlangt: dokumentierte Rechtsgrundlage pro Kontakt, geprüften Opt-out-Text, explizite Owner-Freigabe pro Batch, max. 10–20 Leads im ersten Testbatch.
- Aktueller Datenstand: alle 6.424 Leads haben `Opt-in-Status = unknown`, `Opt-out-Status = unknown`, `Versandfreigabe = no`.
- Kein Versand-Tooling wurde gebaut (kein Gmail-API-Send, kein Apps-Script-Dispatch, kein n8n) — das ist im Projekt explizit als No-Go gelistet.

**Nächster Schritt (nur durch Joel, mit mir als Unterstützung):** Compliance-Gate Punkt für Punkt durchgehen für einen kleinen, sauberen Testbatch — noch nicht begonnen.

---

## Zusammenfassung: Was trennt das System vom belastbaren Abschluss?

Die Website selbst ist produktiv und technisch stabil. Offen sind getrennte,
nicht zu vermischende Gates:

1. **P0 Webhook-Sicherheit:** neuen authentifizierten Pfad ohne Ausfall bauen,
   testen und umstellen; exponierte Deployments erst danach invalidieren.
2. **Google/CRM:** Mapping und loeschbarer Testlead sind operator-verifiziert;
   korrektes Owner-Profil nur fuer weitere API-/Admin-Arbeit re-authentifizieren.
3. **GA4:** Consent-Vertrag, Conversion-Event, Delivery und Key Event belegen.
4. **Google-Unternehmensprofil:** physische Owner-Verifizierung.
5. **Kaltakquise:** Rechtsgrundlage, Opt-out, M365-DKIM und Batch-Freigabe.
6. **Cloudflare-Altlasten/Credentials:** getrennt bereinigen und rotieren;
   voller NS-Cutover nur optional mit Mail-DNS-Sicherheitsplan.
7. **PR #74/Codex Cloud:** PoC deaktiviert lassen; Review-Umgebung und echte
   Gateway-Inferenz fehlen.

Ein globaler „alles fertig“-Claim ist deshalb noch nicht belastbar.
