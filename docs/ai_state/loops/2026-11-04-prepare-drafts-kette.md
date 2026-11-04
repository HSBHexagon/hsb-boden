# Loop-Kontrakt: prepare-drafts-Kette

## Ziel
Alle offenen Entwürfe beider Postfächer sind versandfertig, ohne dass ein Mac oder eine Sitzung Folgeläufe anstoßen muss.

## Abschlusskriterien (messbar)
- [ ] Letzter Lauf der Kette: beide Postfächer enden mit `selected: 0` im Log (`Tranche n: 0 erneuert`).
- [ ] Abschluss-Audit (`audit-3`) dieses Laufs: keine Entwürfe mehr mit `OUTDATED_PLANNER_COPY` oder `OUTDATED_REPAIR_COPY`.
- [ ] `customer_emails_sent` ist in jedem Lauf 0.
- [ ] `python -m pytest apps/sales-os/tests/ -q` und `python scripts/verify_ssot.py` grün.

## Nicht-Ziele
Kein Kundenversand. Kein Ändern von Opt-out-, Bounce- oder Kontaktsperren. Keine Änderung an Texten. Kein Lösen fremder Sperren außerhalb von `release_stale_lock`.

## Limits
- Iterationen: höchstens 8 Folgeläufe (`chain` < 8); danach endet die Kette. Eine Verlängerung entscheidet der Inhaber.
- Zeit: je Lauf Budget 190 min, Job-Abbruch 240 min, also höchstens rund 32 Stunden.
- Kosten: GitHub-Actions-Minuten, keine Modellkosten.

## Stop-on-drift (im Workflow verankert)
- Ein Fehler in einem Schritt: `set -e`, kein Folgelauf.
- Ein Lauf ohne CRM-Fortschritt (`crm_updated` gesamt 0): kein Folgelauf.
- Eine Tranche ohne Fortschritt: dieses Postfach endet in diesem Lauf.
- Sperre unklar (`STALE_LOCK_*`): Lauf scheitert, kein Folgelauf.
- Abbrechen des laufenden Laufs stoppt die Kette.

## Isolation
Worktree: nein. Branch: `claude/marketing-strategy-url-bug-ddllet`. Modus `prepare-drafts` ist fest verdrahtet, `HSB_CUSTOMER_SEND_ENABLED=no`.

## Verifikation
Frischer Reviewer: Codex-Review auf dem PR. Abschlussprüfung: CRM-Zählung und Audit-Zahlen aus dem letzten Lauf.

## Protokoll
- 04.11.2026: Kontrakt angelegt. Start der Kette: einmaliger Cron `55 1 5 11 *`, nach Ende von Lauf `41919946078`.
