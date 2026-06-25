# PROJECT_TRUTH — HSB-Boden / HEXAFLOOR

> Single Source of Truth für den Projektstand. Stand: 2026-06-26.
> Unklare Punkte sind als `unklar / zu prüfen` markiert. Keine Vermutung als Wahrheit.
>
> **Aktueller Stand in einem Satz (2026-06-26):** Lead-Pipeline ist end-to-end live und verifiziert; Production-Worker `hsb-boden` ist route-los deployed (Prod-Secret gesetzt). Es fehlt **ausschließlich** der externe NS-/DNS-Switch der Domain (Zone `hsb-boden.de` weiterhin `pending`); danach nur noch die zwei Worker-Routes setzen = Seite live. Detail-Verlauf: `CHECKPOINT_STATE.json` + `~/KI-System/ObsidianVault/brain/CURRENT_HANDOFF.md`; Cutover-Schritte: `docs/PHASE_C_CUTOVER_RUNBOOK.md`.

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
`main` ist der produktive Stand; lokal == `origin/main`. Der frühere Auditbranch `agent/hexafloor-codex-superpower-audit` ist seit dem Direkt-Merge in `main` (a016b8c) überholt/stale. Doku-Arbeit dieser Session läuft isoliert im Worktree `worktree-hsb-truth-refresh` (Background-Isolation), Übernahme nach `main` bleibt freigabepflichtig.

## 4. Aktueller Commit
- Aktueller `main`-HEAD: `92bda23` — `docs(hsb): Phase-C Prod-Worker route-los vorgezogen + verifiziert, Runbook + PR-Triage`.
- Wesentliche Code-Meilensteine: `a016b8c` (Merge Foto + services.ts-Refactor + P0B-Lead-Pipeline nach main), `5030504` (Dependency-Migration Astro 6 / Tailwind 4 / @astrojs/cloudflare 13), `6203095` (n8n→Apps-Script-Pivot).
- Historische Baselines: `697cce6` (menschlicher Website-Stand „Reparatur-Leistungsseite + P2-SEO"), `3308d91` (Doku-/Playbook-Baseline), `9ac994a` (Flyer-Assets).

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
- `wrangler.toml`: Preview-Worker `hsb-boden-preview`, Production-Worker `hsb-boden` (`[env.production]`), Assets aus `./dist`, `nodejs_compat`, Observability aktiv. Production-Routes sind in `wrangler.toml` **bewusst auskommentiert** (route-los, kein versehentliches Live-Schalten).
- **WICHTIG (verifizierter Fund 2026-06-23/24):** `wrangler deploy --env production` ist mit dem Astro-6-Cloudflare-Adapter kaputt (`--env` wird still ignoriert, landet auf Preview). Echter Prod-Deploy nur via `wrangler deploy --name hsb-boden --var ENVIRONMENT:production`. Siehe `docs/PHASE_C_CUTOVER_RUNBOOK.md`.
- Prod-Worker `hsb-boden` ist **route-los deployed und live** (verifiziert 2026-06-26: `https://hsb-boden.cherinojoel.workers.dev/` → 200, `/api/lead` GET → 405 Methoden-Guard), Secret `LEAD_WEBHOOK_URL` gesetzt, SESSION-KV `hsb-boden-session` provisioniert. **Keine Worker-Routes gesetzt** → Seite NICHT live, alter WordPress aktiv bis Cutover.
- Zone `hsb-boden.de`: Account `cherinojoel@gmail.com` (`043ec…`), Zone-ID `2aefa04f69a2339b2f9f3f2876d7e35c`, Status **`pending`** (2026-06-26 erneut bestätigt) — NS-/DNS-Switch durch den Domain-Admin steht weiterhin aus. Mail = Outlook (MX/SPF/DMARC/autodiscover — nicht anfassen).

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
- **Aktiv:** Google-Sheet „HSB CRM Light" (`1d0zZXXwYGo38ZKf0oUSSJpoZ_WVG545rDalXAdItm80`, Account `cherinojoel@gmail.com`), 27 Spalten, Status-Feld `neu`. Schema siehe `CRM_LIGHT_SCHEMA.md`. Inhalt aktuell nur Kopfzeile (alle Testzeilen geleert).

## 13. Lead-Intake-/Automation-Stand
- **n8n verworfen** (Nutzervorgabe „die nehmen, die gratis ist und bleibt"; n8n Cloud = Abo). Ersetzt durch eine **kostenlose Google-Apps-Script-Web-App** (Projekt `HSBBODEN`, gebunden an „HSB CRM Light"), die die Worker-Payload auf die 27 Spalten mappt (`doPost`/`doGet`, Telefon als Text → führende Null bleibt erhalten). `ops/n8n/` ist als deprecated markiert.
- **Lead-Endpoint live:** `src/pages/api/lead.ts` (Zod-Validierung, Rate-Limit, Honeypot, Origin-Check, Payload-Größen-Guard) postet an `env.LEAD_WEBHOOK_URL` (= die Apps-Script-Web-App-URL). `ALLOWED_ORIGINS` hart = `hsb-boden.de`/`www`; server-/no-origin-POST passiert. Frontend `LeadForm.tsx` → `POST /api/lead`, Flag `PUBLIC_LEAD_FORM_ENABLED`.
- **End-to-End verifiziert** (zuletzt 2026-06-24 auf dem route-losen Prod-Worker): server-seitiger POST → `{ok:true}` → echte Zeile im Sheet, korrektes 27-Spalten-Mapping, Testzeile geleert.

## 14. P0-Aufgaben — ABGESCHLOSSEN
- Lead-Pipeline implementiert, freigegeben (P0B), live und end-to-end verifiziert (Endpoint + Apps-Script-Webhook + CRM-Sheet).
- Hosting-Entscheidung getroffen: kostenlose Apps-Script-Web-App statt n8n.

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

## 17. Offene P3-Aufgaben (Production-Cutover — das Finale)
Status: Prod-Worker + Prod-Secret bereits live (route-los, verifiziert). Es verbleiben nur die externen/Live-Schritte:
- **BLOCKER (extern):** NS-/DNS-Switch der Domain durch den Domain-Admin (Zone `hsb-boden.de` `pending` → `active`). Steht weiterhin aus.
- Danach: zwei Worker-Routes `hsb-boden.de/*` + `www.hsb-boden.de/*` → script `hsb-boden` auf Zone `2aefa04f69a2339b2f9f3f2876d7e35c` setzen (= Seite live). Schritte 5–6 in `docs/PHASE_C_CUTOVER_RUNBOOK.md`.
- Live-Verify auf `hsb-boden.de` (200 vom Worker; echtes Browser-Formular → Zeile im Sheet).
- Tracking produktiv aktivieren (P2-Vorbereitung).

Diese Schritte sind reine Live-/Production-Schritte und bleiben bis zur ausdrücklichen Freigabe **und** dem erfolgten NS-Switch blockiert. **Wichtig:** Nach NS-Switch greift die Route sofort → Worker muss vorher verifiziert sein (ist er), sonst Seite down statt Fallback.

## 18. Offene menschliche Entscheidungen
- Push-Freigabe für lokale Commits bleibt offen.
- `02_Projects/active/hsb-boden` ist der kanonische Arbeitsort; alte `_MERGED_20260613`-Pfade bleiben ausgeschlossen.
- n8n-Hosting, SMTP-Anbieter, Go-Live-Zeitpunkt.

## 22. Gemini-Status
- Gemini Account 1/2 bleiben als ergänzende Research-/Gegenprüfungsrollen dokumentiert.
- Gemini CLI und Gemini Code Assist sind wegen Nutzerbeobachtung langsam/nicht zuverlässig und wegen Googles angekündigtem Stopp für Individuals/Google AI Pro/Ultra ab 2026-06-18 nicht mehr operativer kritischer Pfad.
- Antigravity ist nur Migrationshinweis, kein eingeführter Projektbestandteil.

## 19. Nächster sicherer Schritt
Warten auf den externen NS-/DNS-Switch (Zone `pending` → `active`). Es gibt aktuell **keine** sichere, nicht-blockierte Implementierungsaufgabe mehr: jeder verbleibende Schritt ist entweder extern blockiert (DNS) oder freigabepflichtig (Routes setzen = Production-Cutover; PR-Triage/Branch-Protection = Phase D). Sobald die Zone `active` ist **und** Freigabe vorliegt → Cutover strikt nach `docs/PHASE_C_CUTOVER_RUNBOOK.md` (Schritte 5–6), Worker vor Routes re-prüfen. Keine Website-Code-Änderung, kein Push/Deploy ohne Freigabe.

## 20. Doku-Konsistenzkorrektur
Doku-Konsistenzkorrektur wird im anschließenden Commit + Report dokumentiert.

## 21. Codex-Review-Bereitschaft
Bereit: Inventur + Plan-Dokumente liegen vor, Website-Code unverändert, Guardrails aktiv.
