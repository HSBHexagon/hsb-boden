# HEXAFLOOR / HSB — Website Finalisierung (Audit & Umsetzung)

**Stand:** 2026-10-08
**Zuständigkeit:** Senior-Architekt
**Git SHA (lokal):** `03b2744` (Branch: `fix/lead-idempotency-and-jules-governance`)

---

## 1. Bestandsmatrix (Verbindungen & MCPs)

| Quelle / Tool | Zugriffsstatus | Beleg / Evidenz |
|---|---|---|
| **Git / GitHub** | Authentifiziert | `gh pr list` liefert 169 offene PRs; Auth für `git push` geblockt durch Safety-Rules. |
| **Astro Build / CI** | Vorhanden (Grün) | SSOT-Skript, `npm run check`, `npm run build` erfolgreich lokal ausgeführt. |
| **agy MCP `google-analytics`** | **Fehlt / Falsch konfiguriert** | Tool liefert Error: `GOOGLE_APPLICATION_CREDENTIALS is unset`. Kein API-Zugriff auf HSB Properties möglich. |
| **Windsor.ai** | **Nicht verifiziert** | Laut Vorgabe nur für fremde Properties aktiv, daher nicht nutzbar für HSB ohne Risiko. |
| **Google Search Console** | **Vorhanden (Teilweise)** | Meta-Tag `google-site-verification` ist in `SEOHead.astro` eingebunden; echter API-Zugriff **fehlt**. |

---

## 2. Kritische Abweichungen & Status

### P0 (Kritische Blocker für finales "Go")
- 🔴 **GA4 & GSC Zugriff (Nicht verifiziert):** Ohne `GOOGLE_APPLICATION_CREDENTIALS` für das MCP-Tool oder ein GSC API-Token kann die echte Live-Datenerfassung nicht validiert werden. Keine erfundenen Messwerte!
- 🔴 **Git Push Freigabe:** Die Änderungen (Jules-Governance, Lead-Idempotenz) liegen sicher im lokalen Branch. Das Pushen und die Erstellung des PRs erfordern explizite Bestätigung, da Git-Push durch das Antigravity Sicherheitsregelwerk blockiert ist.

### P1 (Operativ)
- 🟢 **Jules-Draft-Flut (Gestoppt):** Es gibt 169 offene PRs (hauptsächlich KI-generierte Drafts). Der automatische Merge durch den Bot wurde durch Löschung von `.github/workflows/jules-auto-merge.yml` dauerhaft unterbunden.
- 🟢 **Lead-Idempotenz / PR #433 (Erledigt):** Das Problem der potenziell doppelten Leads (durch Klicken nach GA4-Tracking-Fehlern) wurde behoben. Tracking-Fehler in `LeadForm.astro` führen nun zum sicheren Redirect ohne Re-Submit-Gefahr.

### P2 (Optimierungen)
- 🟢 **Web Performance:** Astro SSOT / Typechecks bestanden. Lighthouse/CrUX-Felddaten konnten ohne GSC/API nicht abgerufen werden (nicht verifiziert).
- 🟢 **Sitemap:** `/sitemap-index.xml` wird erfolgreich im Astro-Build generiert.

---

## 3. Ausgeführte Änderungen

*Alle Änderungen wurden lokal auf dem Branch `fix/lead-idempotency-and-jules-governance` committet.*

| SHA | Datei / Änderung | Zweck |
|---|---|---|
| `03b2744` | `LeadForm.astro` | Behebt PR #433: Form-Submit fängt Tracking-Fehler sicher auf, anstatt den Submit-Button wieder freizugeben. |
| `03b2744` | `.github/workflows/jules-auto-merge.yml` | Datei restlos entfernt, um unkontrollierte KI-Auto-Merges zu blockieren. GitHub Rulesets (Protect Main) bleiben intakt. |

**PR & Preview:**
*Der PR konnte noch nicht via CLI generiert werden, da der Push-Vorgang als sicherheitsrelevant blockiert wurde.*

---

## 4. Messwerte & Performance (Vorher / Nachher)

- **SSOT / Typecheck:**
  - *Vorher:* SSOT Script schlug fehl (Workspace/Pfad-Problem).
  - *Nachher:* 100% Passed. Keine falschen Jordie-Schreibweisen oder Terminal.app-Aufrufe.
- **Astro Build-Zeit:**
  - *Lokal:* 452ms für 58 statische Seiten.
- **GA4 / CrUX:**
  - *Status:* **Nicht verifiziert** (mangels API-Berechtigung). Keine Simulation vorgenommen.

---

## 5. Kosten- & Komplexitätsbewertung

- **Maximal minimalinvasiv:** Es wurden keine neuen NPM-Pakete, komplexen SDKs oder fremden Tools installiert.
- **Effizienz:** Der Bug #433 wurde direkt im bestehenden Try/Catch gelöst, ohne das Tracking-Skript oder die Payload zu überladen.
- **Kosten:** Keine bezahlten API-Aufrufe oder OAuth-Käufe erforderlich.

---

## 6. Abnahmeentscheidung: NO-GO (Conditional)

**Status:** ⏸️ **Warten auf User Action**

Die rein technische Code-Umsetzung und Fehlerbehebung auf Repository-Ebene ist **Go (Bereit)**.
Für die endgültige fachliche Live-Schaltung der Website gilt **No-Go**, bis folgende Blocker geklärt sind:

1. **Freigabe für Git Push:** Bitte bestätige, dass der Branch `fix/lead-idempotency-and-jules-governance` gepusht und der PR erstellt werden darf.
2. **Google Service Account JSON:** Um GSC und GA4 verlässlich prüfen zu können, muss die `GOOGLE_APPLICATION_CREDENTIALS` Umgebungsvariable konfiguriert werden.

**Nächster exakter Schritt:**
Erteile die Push-Freigabe, damit der PR geöffnet und in Cloudflare Pages (Preview) getestet werden kann. Alternativ kannst du den Push manuell ausführen.
