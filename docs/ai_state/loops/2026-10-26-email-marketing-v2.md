# Loop-Kontrakt: email-marketing-v2

Stand 27.10.2026, ersetzt den Entwurf vom 26.10. Grundlage: Plan `docs/superpowers/plans/2026-10-26-email-marketing-v2.md` inkl. „Korrekturen nach Verifikation“. Freigabe des Nutzers: „gehe alles nochmal durch und verify dann go“.

## Ziel
Tasks 1–9 des Plans sind umgesetzt, per PR in `main` gemerged (Dauerfreigabe nach grüner CI + Codex), und die lesenden Live-Läufe/Dry-Runs liefern Zählungen für die gebündelte Freigabe von Task 10 — ohne Kundenversand, ohne Production-Deploy, ohne Änderung an Kundenentwürfen.

## Abschlusskriterien (messbar)
- [ ] `cd apps/sales-os && PYTHONPATH=. pytest tests -q` → 0 failed; enthält `test_lead_quality.py`, `test_seed_test.py`, `test_fit_score.py`, `test_template_v2.py`, `test_click_sync.py`, `test_sequence.py`, `test_ramp.py`, `test_draft_upgrade.py`, `test_link_health.py`
- [ ] `cd apps/website && npm run test:run` → 0 failed inkl. `tests/abmelden.test.ts`, `tests/click-redirect.test.ts`; `npm run check` 0 errors; `npm run build` Exit 0; `npm run deploy:dry-run` Exit 0
- [ ] `python3 scripts/verify_ssot.py` Exit 0
- [ ] PR nach `main` gemerged, Required Checks grün, Codex `adversarial-review --base origin/main` ohne offene high-Befunde
- [ ] Live, nur lesend: `bounce-report` (Zählungen je Klasse), `blocklist-check 85.13.130.17`, IMAP-`CAPABILITY` beider Postfächer, `upgrade-drafts --cohort pilot` Dry-Run (Zählungen)
- [ ] `customer_emails_sent` = 0 in allen Lauf-Ausgaben

## Nicht-Ziele
- Kein Kundenversand, kein Setzen von `HSB_CUSTOMER_SEND_ENABLED`/`HSB_INTERNAL_TEST_SEND_ENABLED`, kein `dispatch_verified(dry_run=False)`
- Kein `deploy-production.yml`, kein KV/Secret am Production-Projekt, kein `score-leads --apply`, kein `upgrade-drafts --apply`, kein `seed-send` — alles erst nach gebündelter Freigabe
- Nichts mit KAS (DNS, DMARC, Postmaster, CNAME)
- Keine Arbeit an den uncommitteten Dateien im Haupt-Checkout, alten PRs oder Worktrees; `.env` wird nicht kopiert

## Limits
- Iterationen: 14 (eine je Task-Implementierung oder Review-Fix)
- Zeit: 6 Stunden
- Kosten: Kontrolle nach jedem dritten Task
- Kontext: bei > 70 % compacten

## Stop-on-drift
- zwei Iterationen ohne messbaren Fortschritt an einem Kriterium
- eine Änderung berührt ein Nicht-Ziel
- ein vorher grüner Test wird rot und ist nicht in derselben Iteration erklärt
- ein Schutz-Hook blockt
- ein IMAP-Lauf meldet einen unerwarteten Zustand

## Isolation
Worktree: ja, Branch `feat/email-marketing-v2` (`.worktrees/email-marketing-v2`). Sandbox: nein (lesende IMAP/Sheets-Läufe).

## Verifikation
Frischer Reviewer je Task (subagent-driven), vor Merge Codex `adversarial-review --base origin/main`; Abschluss `validation-auditor`.
