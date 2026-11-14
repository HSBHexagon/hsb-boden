# Loop-Kontrakt: Entwurfs-Verifikation

Setzt `2026-11-04-prepare-drafts-kette.md` fort. Plan: `docs/superpowers/plans/2026-11-05-entwuerfe-verifikation.md`.

## Ziel
Jeder Entwurf beider .com-Postfächer ist nachweislich identisch mit einem frischen Rendering aus dem CRM oder aus einem benannten Grund zurückgehalten; kein Mangel ist ungeklärt.

## Abschlusskriterien (messbar, maschinell prüfbar)
- [ ] `gh run watch <audit-id> --exit-status` auf `main`, Modus `audit`, endet mit Exit 0.
- [ ] Dasselbe Log zeigt `"verdict": "PERFECT"`: für beide Postfächer `ok > 0`, `defects` leer, `eligible_without_draft` gleich 0, `ok + held == scanned`.
- [ ] `held` enthält nur `ALREADY_CONTACTED`, `INELIGIBLE`, `HUMAN_REVIEW`, `HUMAN_EDITED`, jeweils mit Zahl im Endbericht.
- [ ] `send-preview` mit 5: `DRY_RUN_COMPLETED`, `selected` 5 für JOEL und 5 für JORDI.
- [ ] `customer_emails_sent` ist in jedem Lauf 0.
- [ ] `python3 -m pytest apps/sales-os/tests -q` ohne Fehler, `python3 scripts/verify_ssot.py` mit Exit 0.

## Nicht-Ziele
Kein Kundenversand. Keine Erhöhung von `REPARATUR_COPY_REV`, keine Text- oder Gestaltungsänderung. Keine Änderung an Sperren. Keine Umverteilung zwischen den Postfächern. Keine Rechtsthemen. Keine Website-Änderung. Das Audit bewertet nur; was es nicht auflösen kann, wird benannt, nicht passend gemacht.

## Limits
- Iterationen: höchstens 4 Zyklen aus Audit und Reparatur. Danach Stopp und Bericht.
- Zeit: höchstens 8 Stunden ab dem ersten Audit.
- Kosten: GitHub-Actions-Minuten; je Zyklus höchstens ein `prepare-drafts`. Modellkosten per `/cost` nach jedem Zyklus prüfen.
- Kontext: bei mehr als 70 % Füllstand verdichten.
- Takt: kein festes Intervall. Wecksignal ist das Ende von `gh run watch`, kein Abfragen im Minutentakt.

## Stop-on-drift
Abbrechen und melden, sobald eines zutrifft:
- Zwei Audits in Folge ohne Änderung bei `ok` oder `defects`.
- `ok` sinkt, ohne dass Sperren dies erklären.
- `customer_emails_sent` ist ungleich 0.
- Ein anderer Lauf schreibt parallel in die Postfächer.
- Die Sperre lässt sich nicht regulär lösen (`STALE_LOCK_*`).
- Eine Reparatur würde ein Nicht-Ziel berühren.
- Ein zuvor grüner Test wird rot und ist nicht in derselben Iteration erklärt.
- Ein Schutz-Hook blockt.
- `DEEP_DEFECT_CAP_EXCEEDED` oder mehr als 50 Tiefenmängel je Postfach: zuerst den Prüfer untersuchen, nichts erneuern.

## Isolation
Worktree: ja, `.worktrees/entwuerfe-verifikation`. Branch: `fix/entwuerfe-verifikation`, ab `origin/main`.
Sandbox: nein. Postfachzugriff läuft nur in GitHub Actions, das Log enthält nur Zahlen.

## Verifikation
Frischer Reviewer: `code-reviewer-lite` auf dem Diff, weil Codex an seiner Nutzungsgrenze ist.
Abschlussprüfung: `validation-auditor` gleicht die Endzahlen mit dem Log ab.

## Protokoll
<!-- Je Iteration eine Zeile: Lauf, Kriterium, Zahl vorher → nachher. -->
