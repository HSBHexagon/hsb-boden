# PROJECT_TRUTH — HSB-Boden / HEXAFLOOR

> Single Source of Truth für den Projektstand. Stand: 2026-06-17.
> Unklare Punkte sind als `unklar / zu prüfen` markiert. Keine Vermutung als Wahrheit.

## 1. Kanonischer Repo-Pfad
`/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden`

Belegt durch: Registry `~/KI-System/08_System/config/canonical-projects.json` und `~/KI-System/08_System/scripts/assert_canonical_project_path.sh hsb-boden`.
Die alte `_MERGED_20260613`-Angabe ist seit der 2026-06-15-Registry-Umstellung nicht mehr Schreibwahrheit.

## 2. Ausgeschlossene falsche Pfade
- `/Users/joelcherinodiaz/KI-System/01_Wahrheitsquelle/_MERGED_20260613/AI-Memory-Hub/projects/hsb-boden` — alte Merge-/Import-Quelle, NICHT kanonisch.
- `/Users/joelcherinodiaz/Projects/hsb-boden` — älterer Klon (HEAD `359ffc2`, 2026-06-12), NICHT kanonisch.
- `/Users/joelcherinodiaz/AI-Memory-Hub/projects/hsb-boden` — fehlt.
- `/Users/joelcherinodiaz/KI-System-Backup-*` — Backups, keine Wahrheit.
- `~/KI-System/06_Archiv/Backups/HSB_FINAL_BACKUP/hsb-boden` — Backup.
- `brain/07_imported/.../hsb-boden` — Rohimport, keine Wahrheit.
- `brain/03_projects/hexafloor` — leerer Platzhalter.

## 3. Aktueller Branch
`agent/hexafloor-codex-superpower-audit` für den Auditlauf. Vorheriger Arbeitsstand: `main...origin/main [ahead 7, behind 1]`.

## 4. Aktueller Commit
- Aktueller HEAD beim Auditstart: `652702e24131c9ca8e368a2c418ff6b32008ba7f` — `chore(hsb): point checkpoint at current head for clean recovery`
- Letzte verifizierte Review-Baseline: `3308d91` — `docs(hsb): add project truth and execution playbooks`
- Vorheriger lokaler Flyer-Asset-Commit: `9ac994a` — `chore(marketing): add finalized HSB flyer assets`
- Vorheriger menschlicher Website-Stand: `697cce6` — `feat(hsb): Reparatur-Leistungsseite + P2-SEO-Finalisierung`
- Nachfolgende Doku-Konsistenzkorrektur siehe Handoff/Report; kein selbstreferenzieller zukünftiger Commit-SHA in dieser Datei.

## 5. GitHub Remote
- `https://github.com/cherinojoel-lang/hsb-boden.git`
- Remote-HEAD bei Entscheidung: `f94ac19` (2026-06-14 09:10 UTC, „ci: enable Jules auto-merge policy + Dependabot automation #43") — reiner Automations-Commit.
- Beziehung: Die lokale Review-Baseline `3308d91` liegt nach dem Flyer-Asset-Commit `9ac994a` und dokumentiert den verifizierten Doku-Stand vor dieser Korrektur. Remote `f94ac19` beschreibt weiterhin nur den Jules/CI/Dependabot-Automationsstand. **Kein Push erfolgt. Kein Deploy erfolgt.**

## 6. Lokaler Arbeitsbaumstatus
- Nur `.astro/data-store.json` (Build-Cache) ist modified und bewusst NICHT committed.
- `.claude/worktrees/` ist untracked und wird in diesem Lauf nicht angefasst.
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
- Lead-Pipeline vorbereiten und Freigabevoraussetzungen dokumentieren: `PUBLIC_LEAD_ENDPOINT` erst nach ausdrücklicher Freigabe setzen, danach kontrollierter Test-Lead.
- n8n-Hosting-Entscheidung (Cloud vs. lokal).

Dieser Schritt ist eine Planung. Keine Live-Aktivierung, kein Endpoint, kein Deploy, kein Push, kein Production-Cutover ohne ausdrückliche Freigabe.

## 15. Offene P1-Aufgaben
- Flyer-/Mail-Konsistenz gegen aktuelle Website prüfen.
- Finale Rechtstext-Abnahme (Impressum/DSGVO) durch Inhaber.
- Repo-Sync-Strategie: Verhältnis `_MERGED`-Repo ↔ GitHub (Push-Freigabe) klären.

## 16. Offene P2-Aufgaben
- Search Console vorbereiten.
- GA4/GTM vorbereiten.
- Cookie-/Consent-Prüfung finalisieren.
- Sitemap/robots/canonical prüfen.
- Structured Data prüfen.
- Cloudflare Preview validieren.
- Core Web Vitals prüfen.
- Go-live-Checkliste vollständig machen.

Diese Schritte sind Vorbereitung ohne Live-Cutover. Keine Live-Aktivierung, kein Endpoint, kein Deploy, kein Push, kein Production-Cutover ohne ausdrückliche Freigabe.

## 17. Offene P3-Aufgaben
- `hsb-boden.de` Cutover.
- Production Route / Custom Domain aktivieren.
- Cloudflare Production Deployment.
- Tracking produktiv aktivieren.
- Live-Formular aktivieren.
- n8n produktiv anbinden.
- Push/Deploy/Go-live.

Diese Schritte sind reine Live-/Production-Schritte und bleiben bis zur ausdrücklichen Freigabe blockiert.

## 18. Offene menschliche Entscheidungen
- Push-Freigabe für lokale Commits bleibt offen.
- `02_Projects/active/hsb-boden` ist der kanonische Arbeitsort; alte `_MERGED_20260613`-Pfade bleiben ausgeschlossen.
- n8n-Hosting, SMTP-Anbieter, Go-Live-Zeitpunkt.

## 22. Gemini-Status
- Gemini Account 1/2 bleiben als ergänzende Research-/Gegenprüfungsrollen dokumentiert.
- Gemini CLI und Gemini Code Assist sind wegen Nutzerbeobachtung langsam/nicht zuverlässig und wegen Googles angekündigtem Stopp für Individuals/Google AI Pro/Ultra ab 2026-06-18 nicht mehr operativer kritischer Pfad.
- Antigravity ist nur Migrationshinweis, kein eingeführter Projektbestandteil.

## 19. Nächster sicherer Schritt
Codex-Review dieser Inventur + Plan-Dateien; danach P0 (Lead-Pipeline) nach Freigabe. Keine Website-Code-Änderung, kein Push/Deploy ohne Freigabe.

## 20. Doku-Konsistenzkorrektur
Doku-Konsistenzkorrektur wird im anschließenden Commit + Report dokumentiert.

## 21. Codex-Review-Bereitschaft
Bereit: Inventur + Plan-Dokumente liegen vor, Website-Code unverändert, Guardrails aktiv.
