# PROJECT_TRUTH — HSB-Boden / HEXAFLOOR

> Single Source of Truth für den Projektstand. Stand: 2026-06-14.
> Unklare Punkte sind als `unklar / zu prüfen` markiert. Keine Vermutung als Wahrheit.

## 1. Kanonischer Repo-Pfad
`/Users/joelcherinodiaz/KI-System/01_Wahrheitsquelle/_MERGED_20260613/AI-Memory-Hub/projects/hsb-boden`

Belegt durch: letzte Claude-Code-Session `754c6082` (2026-06-13) + lokales git log + GitHub-Remote-Lineage.
Registry: `~/KI-System/08_System/config/canonical-projects.json`.

## 2. Ausgeschlossene falsche Pfade
- `/Users/joelcherinodiaz/Projects/hsb-boden` — älterer Klon (HEAD `359ffc2`, 2026-06-12), NICHT kanonisch.
- `/Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden` — fehlt.
- `/Users/joelcherinodiaz/KI-System-Backup-*` — Backups, keine Wahrheit.
- `~/KI-System/06_Archiv/Backups/HSB_FINAL_BACKUP/hsb-boden` — Backup.
- `brain/07_imported/.../hsb-boden` — Rohimport, keine Wahrheit.
- `brain/03_projects/hexafloor` — leerer Platzhalter.

## 3. Aktueller Branch
`main`

## 4. Aktueller Commit
- Lokaler HEAD: `9ac994a` — „chore(marketing): add finalized HSB flyer assets" (2026-06-14 12:26)
- Vorheriger Menschen-HEAD: `697cce6` — „feat(hsb): Reparatur-Leistungsseite + P2-SEO-Finalisierung" (2026-06-13 21:19 UTC)

## 5. GitHub Remote
- `https://github.com/cherinojoel-lang/hsb-boden.git`
- Remote-HEAD bei Entscheidung: `f94ac19` (2026-06-14 09:10 UTC, „ci: enable Jules auto-merge policy + Dependabot automation #43") — reiner Automations-Commit.
- Beziehung: lokaler Stand ist ggü. stale origin-Tracking 1 Commit voraus (Doku-/Asset-Commit), Remote enthält zusätzlich den Jules-CI-Commit. **Kein Push erfolgt.**

## 6. Lokaler Arbeitsbaumstatus
- Nur `.astro/data-store.json` (Build-Cache) ist modified und bewusst NICHT committed.
- Website-Code-Diff = 0.

## 7. Website-Stand
- Stack: Astro + `@astrojs/cloudflare` + React + Tailwind + Radix UI, `zod`, `react-hook-form`.
- Mehrsprachig: de (default), en, fr, nl, pl, tr.
- Seiten: index, leistungen (+[slug]), branchen (+[slug]), wissen (+[slug]), referenzen, kontakt, karriere, impressum, datenschutz, danke-projektanfrage.
- SEO-Routen dynamisch: `src/pages/sitemap.xml.ts`, `src/pages/robots.txt.ts`.
- Laut bestehender Docs (2026-06-11): Build ✅ (65 Seiten), Lighthouse 100/100 Desktop / ~99 Mobile, Mobile-UX-Blocker behoben. **Nach diesen Docs kamen weitere Commits** (697cce6 Reparatur-Leistungsseite + P2-SEO) → exakter aktueller Prozentstand `unklar / zu prüfen` (Re-Build/Re-Audit ausstehend).

## 8. Cloudflare-Stand
- `wrangler.toml`: Preview-Worker `hsb-boden-preview`, Production-Worker `hsb-boden`, Assets aus `./dist`, `nodejs_compat`, Observability aktiv.
- Production-Deploy laut AGENTS.md/Deploy-Gate **blockiert**, bis Lead-Pipeline live und WordPress bewusst umgezogen ist.
- Custom-Domain-/Route-Stand (`hsb-boden.de`): `unklar / zu prüfen`.

## 9. SEO-Stand
- robots.txt + sitemap.xml als dynamische Routen vorhanden.
- JSON-LD, OG-Images, responsive Hero laut Docs implementiert.
- Google Search Console / GA4 / GTM / Consent: `unklar / zu prüfen` → siehe `SEO_GO_LIVE_CHECKLIST.md`.

## 10. Flyer-/Asset-Stand
- Committet (9ac994a): `public/HSB-Flyer-Geschaeftsfuehrer.pdf`, `public/HSB-Flyer-Joel-Cherino.pdf`, `public/HSB-Flyer-Jordie-Post.pdf`, `marketing/flyer/final/HSB-Flyer-Joel-Cherino.pdf`, `marketing/flyer/final/HSB-Flyer-Jordie-Post.pdf`; alter `marketing/flyer/HSB-Industrieboden-Flyer.pdf` als Rename ersetzt.
- Flyer-↔-Website-Konsistenz (Namen/Logos/Referenzen): laut Docs `OFFEN`.

## 11. Akquise-Mail-/Outreach-Stand
- Lead-Liste `hsb_lead_list_2026_06_11.csv` (30 qualifizierte Leads) laut Docs vorhanden.
- Outreach noch nicht gestartet. Mail-Templates an neue Website-Struktur anpassen = `OFFEN`.
- Rolle Outlook-Mail (`cherinodiaz@outlook.com`): Versandkanal → siehe `ACQUISITION_SYSTEM_PLAN.md`.

## 12. CRM-/Lead-Control-Stand
- Noch kein aktives CRM. Start als Google-Sheets-CRM-Light geplant → siehe `CRM_LIGHT_SCHEMA.md`.

## 13. n8n-/Automation-Stand
- Workflow `ops/n8n/hsb-boden-lead-intake.json` laut Docs fertig.
- Webhook (`PUBLIC_LEAD_ENDPOINT`) + SMTP **inaktiv** (BLOCKER). n8n-Hosting-Entscheidung offen → siehe `N8N_AUTOMATION_PLAN.md`.

## 14. Offene P0-Aufgaben
- Lead-Pipeline aktivieren: `PUBLIC_LEAD_ENDPOINT` setzen + Test-Lead.
- n8n-Hosting-Entscheidung (Cloud vs. lokal).

## 15. Offene P1-Aufgaben
- Flyer-/Mail-Konsistenz gegen aktuelle Website prüfen.
- Finale Rechtstext-Abnahme (Impressum/DSGVO) durch Inhaber.
- Repo-Sync-Strategie: Verhältnis `_MERGED`-Repo ↔ GitHub (Push-Freigabe) klären.

## 16. Offene P2/P3-Aufgaben
- Re-Build + Re-Audit (Lighthouse/SEO) nach 697cce6.
- Production-Cutover-Plan WordPress → Cloudflare.
- GA4/GTM/Consent-Finalisierung.

## 17. Offene menschliche Entscheidungen
- Push-Freigabe für lokale Commits (`9ac994a` + Doku-Commit).
- Soll `_MERGED_20260613` der dauerhafte kanonische Ort sein oder relokiert werden (nur mit Freigabe)?
- n8n-Hosting, SMTP-Anbieter, Go-Live-Zeitpunkt.

## 18. Nächster sicherer Schritt
Codex-Review dieser Inventur + Plan-Dateien; danach P0 (Lead-Pipeline) nach Freigabe. Keine Website-Code-Änderung, kein Push/Deploy ohne Freigabe.

## 19. Codex-Review-Bereitschaft
Bereit: Inventur + Plan-Dokumente liegen vor, Website-Code unverändert, Guardrails aktiv.
