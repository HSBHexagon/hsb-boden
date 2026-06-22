# Codex-Handoff-Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Den uncommitteten Codex-Arbeitsstand im Repo `hsb-boden` (services.ts-Refactor + diverse Doku-Dateien) per Multi-Agent-Audit prüfen, bestätigte Probleme fixen, verifizieren und in getrennten Commits ablegen — ohne Push, Deploy oder P0B-Freigabe.

**Architecture:** Ein einzelner `Workflow`-Lauf (2 Audit-Agenten parallel + adversarial Verify pro Fund, pipeline statt Barrier) liefert ein strukturiertes Fund-Objekt zurück. Alle Fixes, die Verifikation (`npm run test:run`/`check`/`build`) und die Commits führt die Haupt-Session (ich) direkt aus — keine weiteren Subagenten, kein Push/Deploy.

**Tech Stack:** Astro/TypeScript-Repo (`hsb-boden`), `Workflow`-Tool für die Audit-Agenten, Bash/git/npm für Fixes und Verifikation.

## Global Constraints

- Kein `git add .` — immer exakte Pfade stagen (`CLAUDE.md`).
- `.astro/data-store.json` nie committen (vorbestehender Cache).
- Kein Push, kein Deploy, keine P0B-Freigabe-Checkboxen in diesem Plan.
- Secrets/Credentials-Funde werden nie automatisch verändert — Stop, Bericht an Nutzer, kein Commit.
- Max. 1 Fix-und-Reverify-Zyklus pro bestätigtem Fund.
- Tests/Check/Build müssen grün sein, bevor irgendetwas committed wird.

---

### Task 1: Audit-Workflow ausführen (Refactor-Parität + Docs-Konsistenz)

**Files:**
- Keine Datei-Änderungen — reiner Lese-Audit über `git diff`, `src/data/services.ts`, `src/data/services/*.ts` und die uncommitteten Doku-Dateien.

**Interfaces:**
- Produces: ein Ergebnisobjekt `{ refactorFindings: Finding[], docsFindings: Finding[] }` mit `Finding = { file: string, description: string, severity: "secret" | "contradiction" | "placeholder" | "false_claim" | "content_loss", confirmed: boolean }`. Task 2 und Task 3 lesen ausschließlich `confirmed === true`-Einträge.

- [ ] **Step 1: Workflow-Script mit den 2 Audit-Agenten + adversarial Verify ausführen**

Rufe das `Workflow`-Tool mit folgendem Script auf:

```javascript
export const meta = {
  name: 'codex-handoff-audit',
  description: 'Audit services.ts refactor parity and uncommitted docs consistency, adversarially verified',
  phases: [
    { title: 'Audit' },
    { title: 'Verify' },
  ],
}

const REFACTOR_SCHEMA = {
  type: 'object',
  properties: {
    parityOk: { type: 'boolean' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          service: { type: 'string' },
          field: { type: 'string' },
          issue: { type: 'string' },
        },
        required: ['service', 'field', 'issue'],
      },
    },
  },
  required: ['parityOk', 'findings'],
}

const DOCS_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          file: { type: 'string' },
          issue: { type: 'string' },
          severity: { type: 'string', enum: ['secret', 'contradiction', 'placeholder', 'false_claim'] },
        },
        required: ['file', 'issue', 'severity'],
      },
    },
  },
  required: ['findings'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    confirmed: { type: 'boolean' },
    reasoning: { type: 'string' },
  },
  required: ['confirmed', 'reasoning'],
}

phase('Audit')
const [refactorResult, docsResult] = await parallel([
  () => agent(
    `Repo: hsb-boden (Astro/TypeScript). Vergleiche den gelöschten Inline-Inhalt von src/data/services.ts ` +
    `(siehe "git diff src/data/services.ts" — die Minus-Zeilen sind die alten 9 Service-Objekte) mit dem ` +
    `Inhalt der neuen Dateien unter src/data/services/*.ts (aktuell untracked, lies sie direkt). ` +
    `Prüfe für jeden der 9 Slugs (industrieboden-saeureschutz, keramische-industrieboeden, pu-beton-industrieboden, ` +
    `epoxidharz-bodenbeschichtung, entwaesserung-industrieboden, whg-abdichtung-industrieboden, ` +
    `bodensanierung-laufender-betrieb, dehnungsfugen-rammschutz-industrieboden, boden-reparatur-instandsetzung) ` +
    `ob ALLE Felder (title, seoTitle, description, h1, primaryKeyword, secondaryKeywords, problem, applications, ` +
    `technicalRequirements, systemSolution, benefits, decisionCriteria, relatedIndustries, relatedReferences, ` +
    `relatedArticles, faqs, ctaLabel, ctaTarget) 1:1 unverändert übernommen wurden. Melde jede Abweichung, ` +
    `auch kleinste Textänderungen oder fehlende Felder, als Finding. Wenn alles exakt identisch ist, ` +
    `setze parityOk=true und findings=[].`,
    { label: 'refactor-parity-check', phase: 'Audit', schema: REFACTOR_SCHEMA }
  ),
  () => agent(
    `Repo: hsb-boden. Führe "git diff -- CHECKPOINT_STATE.json SESSION_LOG.md CURRENT_EXECUTION_STATE.md ` +
    `ACQUISITION_SYSTEM_PLAN.md PUBLIC_LEAD_ENDPOINT_SPEC.md AGENTS.md CLAUDE.md AI_EXECUTION_PLAYBOOK.md ` +
    `AI_SYSTEM_ROLES.md PROJECT_TRUTH.md marketing/flyer/akquise-email.md marketing/flyer/akquise-email-varianten.md ` +
    `marketing/flyer/validation.md" aus und lies zusätzlich die untracked Dateien PROJECT_AUDIT.md, ` +
    `docs/ops/*, docs/brain/*, src/OPTIMIZATION.md. Melde als Finding mit severity: ` +
    `"secret" wenn API-Keys/Tokens/Passwörter/Credentials im Klartext stehen; ` +
    `"contradiction" wenn ein Inhalt der CANONICAL_STATE.md oder active_state.json unter ` +
    `~/KI-System/ObsidianVault/brain/ widerspricht (z.B. falscher Repo-Pfad, falsche Branch-Angabe); ` +
    `"placeholder" bei TBD/TODO/Lorem-Ipsum-artigen Lücken; ` +
    `"false_claim" wenn behauptet wird, etwas sei gepusht/deployed/live, obwohl "git status" und ` +
    `"git log" das nicht zeigen. Wenn nichts gefunden wird, findings=[].`,
    { label: 'docs-consistency-check', phase: 'Audit', schema: DOCS_SCHEMA }
  ),
])

phase('Verify')
const allRaw = [
  ...refactorResult.findings.map(f => ({ kind: 'refactor', ...f, severity: 'content_loss' })),
  ...docsResult.findings.map(f => ({ kind: 'docs', ...f })),
]

const verified = await parallel(allRaw.map(f => () =>
  agent(
    `Ein Audit-Agent hat folgenden Fund gemeldet: ${JSON.stringify(f)}. ` +
    `Versuche aktiv, diesen Fund zu widerlegen — prüfe die genannte Datei/den genannten Service selbst nach ` +
    `(git diff, Dateiinhalt lesen). Ist es ein echtes Problem oder ein Fehlalarm (z.B. Secret ist nur ein ` +
    `Platzhalter-String wie "your-api-key-here", oder die "Abweichung" ist nur Whitespace)? ` +
    `Setze confirmed=true nur wenn es ein echtes, handlungsrelevantes Problem ist.`,
    { label: `verify:${f.kind}:${f.file || f.service}`, phase: 'Verify', schema: VERDICT_SCHEMA }
  ).then(v => ({ ...f, confirmed: v.confirmed, reasoning: v.reasoning }))
))

const refactorFindings = verified.filter(f => f.kind === 'refactor')
const docsFindings = verified.filter(f => f.kind === 'docs')

return { parityOk: refactorResult.parityOk, refactorFindings, docsFindings }
```

- [ ] **Step 2: Ergebnis sichern**

Notiere das zurückgegebene Objekt `{ parityOk, refactorFindings, docsFindings }` für Task 2 und Task 3. Filtere in beiden Folge-Tasks ausschließlich auf `confirmed === true`.

- [ ] **Step 3: Secret-Stop-Check**

Wenn irgendein Finding mit `severity === "secret"` und `confirmed === true` existiert: **sofort stoppen**, keine weiteren Tasks ausführen, Befund unverändert an den Nutzer melden. Sonst weiter mit Task 2.

---

### Task 2: Bestätigte Refactor-Findings fixen (services.ts-Parität)

**Files:**
- Modify: `src/data/services/*.ts` (je nach Finding die betroffene Datei)
- Test: `npm run test:run` (Vitest-Suite, vorhandene Tests decken Service-Lookups ab)

**Interfaces:**
- Consumes: `refactorFindings` aus Task 1 (`confirmed === true`-Einträge mit `service`, `field`, `issue`).
- Produces: `src/data/services.ts` + `src/data/services/*.ts` in einem Zustand, der `npm run check` und `npm run build` grün durchläuft.

- [ ] **Step 1: Findings durchgehen**

Wenn `refactorFindings` (gefiltert auf `confirmed === true`) leer ist: Task überspringen, direkt zu Task 3.

- [ ] **Step 2: Für jedes bestätigte Finding den exakten Diff lesen**

```bash
git diff src/data/services.ts | grep -A 30 "<service-slug>"
```

Vergleiche mit der entsprechenden Datei unter `src/data/services/`, identifiziere das fehlende/abweichende Feld.

- [ ] **Step 3: Fix anwenden**

Per `Edit`-Tool die betroffene Datei in `src/data/services/` korrigieren, sodass der Inhalt wieder exakt dem ursprünglichen Inline-Objekt entspricht (Quelle: `git diff src/data/services.ts`, Minus-Zeilen).

- [ ] **Step 4: Verifizieren**

```bash
npm run check && npm run test:run
```

Erwartet: 0 Fehler/Warnungen, alle Tests PASS. Bei Fehlschlag: einmal nachbessern (Step 3 wiederholen), dann bei erneutem Fehlschlag stoppen und an Nutzer melden statt weiter zu versuchen.

---

### Task 3: Bestätigte Docs-Findings fixen

**Files:**
- Modify: je nach Finding eine oder mehrere der unter Task 1 geprüften Doku-Dateien.

**Interfaces:**
- Consumes: `docsFindings` aus Task 1 (`confirmed === true`, `severity !== "secret"` — Secrets wurden bereits in Task 1 Step 3 gestoppt).
- Produces: konsistente Doku-Dateien ohne Platzhalter/Widersprüche/Falschbehauptungen.

- [ ] **Step 1: Findings durchgehen**

Wenn `docsFindings` (gefiltert auf `confirmed === true`) leer ist: Task überspringen, direkt zu Task 4.

- [ ] **Step 2: Pro Finding die betroffene Stelle lesen**

```bash
git diff -- "<file>"
```

- [ ] **Step 3: Fix anwenden**

Per `Edit`-Tool: bei `contradiction` den Text an die echte `CANONICAL_STATE.md`/`active_state.json` anpassen; bei `placeholder` den Platzhalter durch den tatsächlichen Wert ersetzen oder die Zeile entfernen, falls kein echter Wert existiert; bei `false_claim` die Behauptung auf den tatsächlichen Git-Status korrigieren (z.B. "geplant" statt "deployed").

- [ ] **Step 4: Verifizieren**

```bash
npm run check
```

Erwartet: 0 Fehler. (Doku-Dateien beeinflussen keine Tests/Build, daher reicht hier `check` als Rauchtest für evtl. betroffene `.astro`/`.ts`-Dateien — `services.ts`-bezogene Findings werden bereits in Task 2 mit `test:run` abgedeckt.)

---

### Task 4: Finale Verifikation, Commits, Advisor-Review, Report

**Files:**
- Keine neuen Dateien — Abschluss-Task.

**Interfaces:**
- Consumes: Ergebnisse aus Task 2 und Task 3 (welche Dateien geändert wurden, ob Fixes nötig waren).
- Produces: 1–3 Git-Commits, finaler Bericht an den Nutzer.

- [ ] **Step 1: Volle Verifikation**

```bash
npm run test:run && npm run check && npm run build
```

Erwartet: alle drei PASS. Bei Fehlschlag: stoppen, kein Commit, Bericht an Nutzer mit der genauen Fehlermeldung.

- [ ] **Step 2: Commit 1 — services.ts-Refactor**

```bash
git add src/data/services.ts src/data/services/
git status --short
```

Prüfen, dass nur die erwarteten Dateien gestaged sind (kein `.astro/data-store.json`, keine fremden Dateien).

```bash
git commit -m "$(cat <<'EOF'
refactor(hsb): split services.ts into per-service modules

9 Service-Objekte aus der monolithischen services.ts in
src/data/services/*.ts ausgelagert. Audit (2 Agenten + adversarial
Verify) bestätigt 1:1-Inhaltsparität für alle Felder.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 3: Commit 2 — Doku-Fixes (nur falls Task 3 etwas geändert hat)**

Wenn Task 3 Dateien geändert hat:

```bash
git add <jede betroffene Datei einzeln, exakte Pfade>
git commit -m "$(cat <<'EOF'
fix(docs): correct audit findings from codex handoff review

Behebt <severity>-Funde aus dem Multi-Agent-Audit: <kurze Liste der
betroffenen Dateien/Probleme>.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

Wenn Task 3 nichts geändert hat: diesen Schritt überspringen.

- [ ] **Step 4: Commit 3 — restliche, geprüfte Codex-Doku ohne Beanstandung**

Für alle übrigen, von Task 1 geprüften und nicht beanstandeten Dateien (`CHECKPOINT_STATE.json`, `SESSION_LOG.md`, `CURRENT_EXECUTION_STATE.md`, `ACQUISITION_SYSTEM_PLAN.md`, `PUBLIC_LEAD_ENDPOINT_SPEC.md`, `AGENTS.md`, `CLAUDE.md`, `AI_EXECUTION_PLAYBOOK.md`, `AI_SYSTEM_ROLES.md`, `PROJECT_TRUTH.md`, `marketing/flyer/*.md`):

```bash
git add CHECKPOINT_STATE.json SESSION_LOG.md CURRENT_EXECUTION_STATE.md ACQUISITION_SYSTEM_PLAN.md PUBLIC_LEAD_ENDPOINT_SPEC.md AGENTS.md CLAUDE.md AI_EXECUTION_PLAYBOOK.md AI_SYSTEM_ROLES.md PROJECT_TRUTH.md marketing/flyer/akquise-email.md marketing/flyer/akquise-email-varianten.md marketing/flyer/validation.md
git commit -m "$(cat <<'EOF'
docs(hsb): commit codex presentation/versand prep updates

Audit (Multi-Agent, adversarial verified) fand keine Secrets,
Widersprüche oder Falschbehauptungen in diesen Codex-Aktualisierungen.
Inhalt: Mail-Anhang-Korrektur, PUBLIC_LEAD_ENDPOINT_SPEC an reale
Formularfelder angepasst, Truth-Konsolidierung Registry-Pfad.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 5: Advisor-Gegencheck**

Vor dem finalen Report einmalig `advisor()` aufrufen (Top-Level-Tool der Haupt-Session, nicht Teil des Workflow-Scripts) als Gegencheck auf den gesamten Batch (Audit-Ergebnis, Fixes, Commits).

- [ ] **Step 6: Bericht an Nutzer**

Zusammenfassen: wie viele Findings pro Kategorie, wie viele bestätigt, was gefixt wurde, welche 1–3 Commits entstanden sind (mit Hashes), und explizit was bewusst NICHT angefasst wurde (Push, Deploy, P0B-Checkboxen, `.astro/data-store.json`, untracked Planungsdateien außerhalb des geprüften Sets wie `.agents/`, `.codex/`, falls vorhanden — diese ggf. separat erwähnen, da sie nicht Teil des Audits waren).

---

## Out of Scope (siehe Spec)

- P0B-technische Umsetzung, Push, Deploy, Production-Cutover.
- `.astro/data-store.json`.
- `05_Secrets`-Bereich außerhalb dieses Repos.
- Untracked Dateien `.agents/`, `.claude/worktrees/`, `.codex/` — diese sind Tooling-Artefakte, nicht Teil des Doku-Audits in Task 1; falls sie versehentlich Secrets enthalten, gilt dieselbe Stop-Regel, aber sie wurden in diesem Plan nicht explizit in den Audit-Scope aufgenommen, da sie keine inhaltlichen Projekt-Doku sind.
