# Codex-Handoff-Audit — Design

Stand: 2026-06-22. Einmaliger Abschluss-Lauf für den aktuellen `hsb-boden`-Arbeitsstand.

## Ziel

Den von Codex hinterlassenen, teils uncommitteten Arbeitsstand (services.ts-Refactor + diverse Doku-Dateien) prüfen, Lücken/Fehler finden, beheben und committen — code-fertig und dokumentiert. Kein Push, kein Deploy, keine P0B-Freigabe; diese drei bleiben explizit außerhalb des Workflows und sind Nutzerentscheidungen.

## Ausgangslage

- `src/data/services.ts`: 9 Service-Objekte wurden in `src/data/services/*.ts` ausgelagert und per Import zusammengeführt (562→18 Zeilen). Noch nicht committed, neue Dateien noch untracked.
- Uncommittete Doku-Diffs: `CHECKPOINT_STATE.json`, `SESSION_LOG.md`, `CURRENT_EXECUTION_STATE.md`, `ACQUISITION_SYSTEM_PLAN.md`, `PUBLIC_LEAD_ENDPOINT_SPEC.md`, `AGENTS.md`, `CLAUDE.md`, `AI_EXECUTION_PLAYBOOK.md`, `AI_SYSTEM_ROLES.md`, `PROJECT_TRUTH.md`, `marketing/flyer/*.md`.
- Neue untracked Dateien: `PROJECT_AUDIT.md`, `docs/ops/*`, `docs/brain/*`, `src/OPTIMIZATION.md`, `.agents/`, `.codex/`.
- Bekannter offener Punkt aus `CHECKPOINT_STATE.json`: "decide whether existing service modularization should be committed".

## Architektur / Phasenplan

**Phase 1 — Audit (parallel, 2 Agenten):**
- *Agent A — Refactor-Check:* vergleicht `git diff src/data/services.ts` (gelöschter Inline-Inhalt) mit dem Inhalt der neuen Dateien unter `src/data/services/`. Prüft 1:1-Inhaltsparität: alle 9 Slugs, alle Felder (faqs, relatedReferences, relatedArticles, ctaTarget etc.) vollständig und unverändert übernommen. Meldet jede Abweichung als Fund.
- *Agent B — Docs-Konsistenz-Check:* liest alle uncommitteten Doc-Diffs + neue untracked Planungsdateien. Meldet als Fund: Secrets/Credentials/Tokens im Klartext, Widersprüche zu `~/KI-System/.../CANONICAL_STATE.md` bzw. `active_state.json`, Platzhalter/TBD-Text, Behauptungen über Push/Deploy/Live-Zustände, die laut Git-Status nicht zutreffen.

**Phase 2 — Adversarial Verify (pro Fund, pipeline statt Barrier):**
- Jeder Fund aus Phase 1 geht sofort (nicht erst nach Abschluss des gesamten Audits) an einen zweiten Agenten, der gezielt versucht den Fund zu widerlegen ("ist das wirklich ein Problem oder ein Fehlalarm?"). Nur bestätigte Funde gehen in Phase 3.

**Phase 3 — Fix (durch mich, nicht durch weitere Agenten):**
- Ich wende Fixes für bestätigte, nicht-sicherheitsrelevante Funde direkt per Edit an (max. 1 Fix-Versuch pro Fund).
- Sicherheitsrelevante Funde (Secrets/Credentials) werden **nicht automatisch verändert** — Workflow stoppt, Bericht an Nutzer, kein Commit.

**Phase 4 — Verify (deterministisch, kein Agent):**
- `npm run test:run`, `npm run check`, `npm run build` direkt per Bash. Nur bei grünem Ergebnis geht es weiter zu Commit.
- Wird nach einem Fix nicht grün: Workflow stoppt, Bericht statt Commit.

**Phase 5 — Commit + Advisor + Report:**
- Getrennte Commits, exakte Pfade (kein `git add .`):
  1. `services.ts`-Refactor (alte Datei + neue `services/`-Dateien zusammen)
  2. Doku-Fixes (falls Phase 3 etwas geändert hat)
  3. Unveränderte, aber geprüfte Doku-Updates von Codex (falls Audit keine Probleme fand)
- Vor dem finalen Report: einmaliger `advisor()`-Aufruf als Gegencheck auf den gesamten Batch.
- Report an Nutzer: was geprüft, was gefunden, was gefixt, was committed, was bewusst nicht angefasst wurde (Push/Deploy/P0B/Secrets-Bereich).

## Tools / MCPs

- `Workflow`-Tool für die Agenten (Phase 1 + 2) — kein externes MCP nötig, reine lokale Repo-Arbeit.
- `Bash` direkt für `git`/`npm` (Phase 4) — deterministische Schritte ohne LLM-Overhead.
- `advisor()` (Top-Level-Tool, nicht im Workflow-Script verfügbar) — einmal vor dem Report.
- Kein Cloudflare-/GitHub-MCP, da kein Push/Deploy.

## Stop-Bedingungen

- Secrets/Credentials-Funde stoppen immer vor jedem Commit.
- Max. 1 Fix-und-Reverify-Zyklus pro Fund (kein endloses Nachbessern).
- Test/Check/Build müssen grün sein, sonst kein Commit.
- Push, Deploy, P0B-Freigabe-Checkboxen werden vom Workflow nicht berührt.

## Out of Scope

- P0B-technische Umsetzung (Endpoint/n8n/CRM-Light).
- Push, Deploy, Production-Cutover.
- `.astro/data-store.json` (vorbestehender Cache, nie committen).
- Inhaltliche Entscheidung über `05_Secrets`-Bereich außerhalb dieses Repos.
