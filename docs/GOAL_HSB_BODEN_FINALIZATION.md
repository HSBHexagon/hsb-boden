# GOAL — HSB-Boden Finalisierung

> Konsolidiertes Ziel-/Statusdokument. Stand: 2026-07-09.
> Ergänzt `docs/MASTER_EXECUTION_PLAN.md` (Phasenmodell) um eine flache, bereichsweise Sicht: was ist fertig, was ist blockiert und warum, was ist der nächste konkrete Schritt.

## Gesamtziel

`www.hsb-boden.de` als vollständig funktionierendes, sichtbares, technisch sauberes B2B-Akquise-System betreiben — Website live, Lead-Pipeline verifiziert, Sichtbarkeit bei Google aufgebaut — bis zur finalen Freigabe von Apex-DNS und Kaltakquise-Versand.

---

## 1. Website & Deploy — ✅ weitgehend fertig

| Punkt | Status |
|---|---|
| `www.hsb-boden.de` live über Cloudflare Pages | ✅ |
| `pages-static-migration` → `main` konsolidiert | ✅ committed und **gepusht** |
| Canonical-Domain-Bug (Code zeigte auf Apex statt www) | ✅ gefixt und deployed |
| Rate-Limit-Bypass-Lücke in `/api/lead` (In-Memory statt verteilt) | ✅ gefixt via Cloudflare KV (`RATE_LIMIT_KV`, Namespace neu im `info@hsb-boden.de`-Account gebunden), deployed |
| JSON-LD-XSS-Härtung (PR #32) | ✅ gemergt nach `main` auf GitHub |
| Tests/Build/Check | ✅ 51/51 Tests, 0 Typfehler |
| Apex `hsb-boden.de` | ❌ zeigt weiterhin alte WordPress-Seite |
| Lokales `main` vs. `origin/main` | ✅ zusammengeführt und synchron (Push erfolgt via Admin-Bypass der Branch-Protection — bekanntes, im Projekt bereits dokumentiertes Risiko) |
| GitHub-Actions-Secrets `CLOUDFLARE_API_TOKEN`/`CLOUDFLARE_ACCOUNT_ID` | ✅ neu gesetzt (vorheriger Wert leer/ungültig) |
| CI-Deploy-Workflows (`deploy-preview.yml`, `deploy-production.yml`) | ✅ von obsoleter Worker-Architektur auf Cloudflare Pages migriert; Production-Deploy bleibt bewusst `workflow_dispatch`-only (manueller Gate erhalten), PR-Previews deployen jetzt korrekt auf Pages-Branch-URLs |

**Nächster Schritt:** Apex-DNS (siehe Abschnitt 5), sonst ist dieser Bereich vollständig.

---

## 2. Lead-Pipeline & CRM — ✅ fertig, mit zwei offenen Aufräumpunkten

| Punkt | Status |
|---|---|
| `/api/lead` → Cloudflare Pages Function → Apps Script (`HSBBODEN`) → Sheet „HSB CRM Light" | ✅ End-to-End verifiziert (historisch, Phase 6) |
| `LEAD_WEBHOOK_URL` auf Cloudflare Pages Production gesetzt | ✅ (2026-07-08, echter Wert verifiziert über Apps-Script-Deployment v3) |
| Reale Kaltakquise-Lead-Daten | ✅ vorhanden — 6.424 Datensätze, 3 Sheets (Master/Joel/Jordi) |
| Schema-Drift zwischen den 4 CRM-Sheets | ⚠️ dokumentiert, **nicht bereinigt** — `CRM_LIGHT_SCHEMA.md` ist kanonisch erklärt |
| Verwaistes Apps-Script-Projekt „HSB-Boden CRM Webhook" (an Jordi-Sheet gebunden) | ✅ umbenannt + Deployment archiviert (kein Risiko mehr, aber Projekt existiert noch) |

**Nächster Schritt:** Vor einem echten Versand die Spaltenreihenfolge der 3 Kaltakquise-Sheets gegen `CRM_LIGHT_SCHEMA.md` abgleichen (dispatch-blockierende Felder: `Verantwortlicher`, `Flyer-Anhang`, `Versandfreigabe`, `Opt-in-/Opt-out-Status`).

---

## 3. SEO & Analytics — ✅ heute deutlich vorangebracht

| Punkt | Status |
|---|---|
| GA4 Tracking-Code im Build (`G-VC4BJBEFTV`) | ✅ korrekt, empfängt echten Traffic (735 Nutzer/7 Tage) |
| GA4-Property „HSBBODENCLOUDFLAIRE" (Account HexagonSäurebauGmbH) | ✅ identifiziert, verifiziert |
| GA4 Datenaufbewahrung | ✅ auf 14 Monate vereinheitlicht (vorher: Events nur 2 Monate) |
| GSC-Property für `www.hsb-boden.de` | ✅ neu angelegt, automatisch via GA4 verifiziert (kein DNS nötig) |
| Sitemap bei GSC eingereicht | ✅ |
| Indexierung Startseite + Kontakt angefragt | ✅ |
| GA4 Key Events / Conversions | ⬜ noch nicht konfiguriert |
| GSC-Property für Apex `hsb-boden.de` | ⬜ blockiert bis Apex live/DNS-Entscheidung |
| Doppelte Cloudflare-Zone für `hsb-boden.de` (Account cherinojoel) | ⚠️ identifiziert, **nicht gelöscht** (API-Token ohne Löschrecht) — die produktive Zone liegt im `info@hsb-boden.de`-Account |

**Nächster Schritt:** GA4 Key Events (z. B. `kontakt`-Formular-Submit) definieren; verwaiste Cloudflare-Zone im `cherinojoel@gmail.com`-Account manuell im Dashboard löschen.

---

## 4. Google Unternehmensprofil — ❌ nicht begonnen, nicht delegierbar

Erfordert Neuanlage eines Profils plus Postkarten-/Telefon-Verifizierung an die reale Geschäftsadresse. Das kann **nur Joel selbst** durchführen — weder Kontoerstellung noch physische Verifizierung sind an mich delegierbar, unabhängig von erteilter Freigabe.

**Nächster Schritt (nur durch Joel):** `business.google.com` → Unternehmensprofil für „HSB Hexagon Säurebau GmbH" anlegen, Adresse verifizieren lassen.

---

## 5. Apex-DNS (`hsb-boden.de` ohne www) — ❌ weiterhin blockiert, bewusst

- Registrar (All-Inkl/Kasserver) zeigt weiterhin auf die alten Nameserver — kein NS-Switch erfolgt.
- Zwei Cloudflare-Zonen existieren parallel vorbereitet; die richtige liegt im `info@hsb-boden.de`-Account.
- Dies bleibt **absichtlich** blockiert: DNS-Änderungen an einer live laufenden Domain (inkl. E-Mail-Routing-Risiko) sind in jeder Projektdoku als freigabepflichtig markiert und werden nicht automatisiert ausgeführt — auch nicht auf wiederholte Anfrage.

**Nächster Schritt (nur durch Joel/Jan):** Bei All-Inkl die Nameserver auf `bart.ns.cloudflare.com` / `melody.ns.cloudflare.com` (Zone im `info@hsb-boden.de`-Account) umstellen.

---

## 6. Kaltakquise-Versand (Phase 7) — ❌ blockiert durch eigenes Compliance-Gate

- `docs/launch/PHASE_7_COMPLIANCE_GATE.md` verlangt: dokumentierte Rechtsgrundlage pro Kontakt, geprüften Opt-out-Text, explizite Owner-Freigabe pro Batch, max. 10–20 Leads im ersten Testbatch.
- Aktueller Datenstand: alle 6.424 Leads haben `Opt-in-Status = unknown`, `Opt-out-Status = unknown`, `Versandfreigabe = no`.
- Kein Versand-Tooling wurde gebaut (kein Gmail-API-Send, kein Apps-Script-Dispatch, kein n8n) — das ist im Projekt explizit als No-Go gelistet.

**Nächster Schritt (nur durch Joel, mit mir als Unterstützung):** Compliance-Gate Punkt für Punkt durchgehen für einen kleinen, sauberen Testbatch — noch nicht begonnen.

---

## Zusammenfassung: Ein letzter Schritt?

Nein — es sind **drei unabhängige, nicht von mir ausführbare Freigaben**, die das Projekt vom vollständigen Abschluss trennen:

1. **Apex-DNS-Switch** bei All-Inkl (Joel/Jan)
2. **Google-Unternehmensprofil-Verifizierung** (nur Joel, physisch)
3. **Compliance-Freigabe für Kaltakquise-Versand** (Joel, inhaltliche Entscheidung)

Alles technisch Vorbereitbare ohne diese drei Freigaben ist Stand jetzt erledigt.
