# Loop-Kontrakt: Website-Finalisierung 2026-08-11

## Ziel
Ein evidenzbasierter, frisch verifizierter Release-Candidate-Commit auf
`chore/website-final-audit`, mit exakter Blockerliste für alles, was nicht
owner-unabhängig lösbar ist. Kein Production-Deploy, kein Push, kein Merge.

## Abschlusskriterien
- [x] `npm run test:run` frisch grün — 178/178, 23 Dateien
- [x] `npm run check` frisch grün — 0 Fehler/0 Warnungen/6 vorbestehende Hints
- [x] `npm run build` frisch grün, Exit 0 — 50 Seiten
- [x] `npm run deploy:dry-run` frisch grün (Pages Functions Build) — Wrangler-Compile OK
- [x] `npm run check:sitemap` frisch grün — 49 URLs konsistent
- [x] JobPosting-Struktur: eine Seite = eine Stelle, kein Multi-Array-Markup — verifiziert in dist/
- [x] LogoCloud-Dedup verifiziert (generisch, kein Namens-Sonderfall) — bereits Commit 341a2f6
- [x] Legal/Privacy-Runtime-Abgleich dokumentiert (Hoster, TMG/TTDSG) — All-Inkl→Cloudflare, TMG→DDG, TTDSG→TDDDG
- [x] Frischer unabhängiger Reviewer ohne verbleibenden P0/P1-Gap — 1 P1 gefunden (verfrühte Fertig-Behauptung in PROJECT_TRUTH.md) und behoben, danach 0 P0/P1

## Nicht-Ziele
CRM, Akquise, n8n, Plattformwechsel, Architektur-Refactoring, neue Dependencies,
PR #59 (3D/KAGETEC), Production-Deploy, DNS, Secrets, echter Versand.

## Limits
- Iterationen: 1 Durchgang (Edits gebündelt, dann eine Vollverifikation)
- Zeit: 180 Minuten Hard Limit (User-Vorgabe)
- Kontext: Subagents für breite Audits, Hauptkontext für P0/P1-Gegenprüfung

## Stop-on-drift
- do_not_do (`no_hsb_changes`, `no_website_changes`) wird durch diese
  In-Session-Owner-Mission explizit für die enumerierten Fixes überschrieben —
  Abweichung wird im Abschlussbericht vermerkt, nicht verschwiegen.
- Erfundene Fakten (Gehalt, Zertifikate, Kundennamen) sind ausgeschlossen.
- Wenn ein Kriterium sich als nicht owner-unabhängig prüfbar erweist: NOT READY
  mit Blocker benennen, nicht weiterarbeiten als wäre es gelöst.

## Isolation
Branch: `chore/website-final-audit` (bereits vorhanden, 2 Commits vor origin/main)
Worktree: nein (bestehender Branch, working tree clean)

## Verifikation
Frischer Reviewer: general-purpose-Subagent ohne Implementierungskontext
Abschlusspruefung: die vier Gate-Kommandos oben, frisch ausgeführt
