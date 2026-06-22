# Claude-Code-Automatisierung (hsb-boden) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bestehende, dokumentierte Projektregeln (kein `git add .`, `.astro/data-store.json` nie committen, kein Deploy-Config-Change ohne Freigabe) technisch über Hooks erzwingen; zusätzlich Sofort-Feedback (Typecheck, Tests), `context7`-MCP, zwei Skills und zwei Subagents für den Lead-Endpoint-Pfad und Dependency-Drift ergänzen.

**Architecture:** 5 Bash-Hooks unter `.claude/hooks/`, registriert in `.claude/settings.json` (PreToolUse blockt, PostToolUse meldet nur). 1 MCP-Server-Eintrag in `.mcp.json`. 2 Skills unter `.claude/skills/`. 2 Subagents unter `.claude/agents/`. Jeder Baustein ist unabhängig von den anderen und einzeln testbar.

**Tech Stack:** Bash (Hooks, POSIX-`sed`, kein `jq`), Claude Code Settings-JSON, Markdown+YAML-Frontmatter (Skills/Agents), npm/vitest (Verifikation).

## Global Constraints

- Hooks lesen das Event-JSON von stdin und extrahieren Felder ausschließlich per `sed` (kein `jq`-Zwang) — exaktes Muster aus dem bestehenden `.claude/hooks/block-secrets.sh`.
- Hook-Exit-Codes: `exit 2` + Meldung auf stderr blockiert den Tool-Call; `exit 0` lässt ihn durch. Kein erkanntes Feld im Payload → `exit 0` (fail-open, wie `block-secrets.sh`).
- Projektregel: niemals `git add .` / `git add -A` / `git add --all`.
- Projektregel: `.astro/data-store.json` nie committen.
- Projektregel: kein Deploy-Config-Change (`wrangler.toml`, `deploy`-Scripts in `package.json`) ohne Freigabe.
- Deploy-Gate-Reihenfolge exakt: `npm run test:run` → `npm run check` → `npm run build` → `npm run deploy:dry-run`.
- Skills ohne `disable-model-invocation`/`user-invocable` im Frontmatter sind für Claude und Nutzer aufrufbar (Default). `disable-model-invocation: true` macht einen Skill nutzer-only.
- Kein `git add .` bei den Commits in diesem Plan — immer exakte Pfade.

---

### Task 1: Hook `block-git-add-all.sh`

**Files:**
- Create: `.claude/hooks/block-git-add-all.sh`
- Modify: `.claude/settings.json`

**Interfaces:**
- Produces: registrierter `PreToolUse`-Hook mit Matcher `Bash`, der den Bash-Tool-Call blockiert, wenn `tool_input.command` `git add .`, `git add -A` oder `git add --all` enthält.

- [ ] **Step 1: Hook-Script schreiben**

```bash
#!/usr/bin/env bash
# PreToolUse-Hook: blockiert "git add ." / "git add -A" / "git add --all".
# Projektregel (CLAUDE.md): nie mit Wildcard stagen, immer exakte Pfade.
set -euo pipefail

payload="$(cat)"
command_str="$(printf '%s' "$payload" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n1)"

if [ -z "$command_str" ]; then
  exit 0
fi

case "$command_str" in
  *"git add ."*|*"git add -A"*|*"git add --all"*)
    echo "BLOCKIERT: 'git add .' / '-A' / '--all' ist nicht erlaubt." >&2
    echo "Regel (CLAUDE.md): immer exakte Pfade stagen, z.B. 'git add src/foo.ts'." >&2
    exit 2
    ;;
esac

exit 0
```

Datei ausführbar machen: `chmod +x .claude/hooks/block-git-add-all.sh`

- [ ] **Step 2: Smoke-Test — Blockier-Fall**

Run:
```bash
echo '{"tool_input":{"command":"git add ."}}' | bash .claude/hooks/block-git-add-all.sh; echo "exit=$?"
```
Expected: stderr-Meldung `BLOCKIERT: 'git add .' ...`, `exit=2`

- [ ] **Step 3: Smoke-Test — Durchlass-Fall**

Run:
```bash
echo '{"tool_input":{"command":"git add src/foo.ts"}}' | bash .claude/hooks/block-git-add-all.sh; echo "exit=$?"
```
Expected: keine Ausgabe, `exit=0`

- [ ] **Step 4: Hook in `.claude/settings.json` registrieren**

Aktueller Inhalt von `.claude/settings.json`:
```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/block-secrets.sh\""
          }
        ]
      }
    ]
  }
}
```

Ersetze den `"PreToolUse": [...]`-Block durch:
```json
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/block-secrets.sh\""
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/block-git-add-all.sh\""
          }
        ]
      }
    ]
```

- [ ] **Step 5: JSON-Validität prüfen**

Run: `python3 -m json.tool .claude/settings.json > /dev/null && echo VALID`
Expected: `VALID`

- [ ] **Step 6: Commit**

```bash
git add .claude/hooks/block-git-add-all.sh .claude/settings.json
git commit -m "feat(hsb-claude): block git add -A/-./--all via PreToolUse hook"
```

---

### Task 2: Hook `block-data-store-commit.sh`

**Files:**
- Create: `.claude/hooks/block-data-store-commit.sh`
- Modify: `.claude/settings.json`

**Interfaces:**
- Consumes: gleicher `Bash`-Matcher wie Task 1 (`PreToolUse`).
- Produces: zweiter Hook im selben Matcher, blockiert jeden Bash-Befehl, dessen `command` den String `data-store.json` enthält.

- [ ] **Step 1: Hook-Script schreiben**

```bash
#!/usr/bin/env bash
# PreToolUse-Hook: blockiert Bash-Befehle, die .astro/data-store.json referenzieren
# (z.B. git add/commit). Cache-Artefakt, darf laut CLAUDE.md nie committed werden.
set -euo pipefail

payload="$(cat)"
command_str="$(printf '%s' "$payload" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n1)"

if [ -z "$command_str" ]; then
  exit 0
fi

case "$command_str" in
  *"data-store.json"*)
    echo "BLOCKIERT: '.astro/data-store.json' darf nie committed werden (Cache-Artefakt)." >&2
    exit 2
    ;;
esac

exit 0
```

Datei ausführbar machen: `chmod +x .claude/hooks/block-data-store-commit.sh`

- [ ] **Step 2: Smoke-Test — Blockier-Fall**

Run:
```bash
echo '{"tool_input":{"command":"git add .astro/data-store.json"}}' | bash .claude/hooks/block-data-store-commit.sh; echo "exit=$?"
```
Expected: stderr-Meldung `BLOCKIERT: '.astro/data-store.json' ...`, `exit=2`

- [ ] **Step 3: Smoke-Test — Durchlass-Fall**

Run:
```bash
echo '{"tool_input":{"command":"git add src/foo.ts"}}' | bash .claude/hooks/block-data-store-commit.sh; echo "exit=$?"
```
Expected: keine Ausgabe, `exit=0`

- [ ] **Step 4: Hook in `.claude/settings.json` registrieren (zweiter Eintrag im `Bash`-Matcher)**

Ersetze:
```json
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/block-git-add-all.sh\""
          }
        ]
      }
    ]
```
durch:
```json
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/block-git-add-all.sh\""
          },
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/block-data-store-commit.sh\""
          }
        ]
      }
    ]
```

- [ ] **Step 5: JSON-Validität prüfen**

Run: `python3 -m json.tool .claude/settings.json > /dev/null && echo VALID`
Expected: `VALID`

- [ ] **Step 6: Commit**

```bash
git add .claude/hooks/block-data-store-commit.sh .claude/settings.json
git commit -m "feat(hsb-claude): block .astro/data-store.json commits via PreToolUse hook"
```

---

### Task 3: Hook `guard-deploy-files.sh`

**Files:**
- Create: `.claude/hooks/guard-deploy-files.sh`
- Modify: `.claude/settings.json`

**Interfaces:**
- Produces: zweiter Hook im `Edit|Write|MultiEdit`-Matcher unter `PreToolUse`, blockiert Edits an `wrangler.toml` immer und an `package.json`, wenn der neue Inhalt (Diff-Heuristik: Substring-Suche im gesamten Event-Payload) `"deploy` enthält.

- [ ] **Step 1: Hook-Script schreiben**

```bash
#!/usr/bin/env bash
# PreToolUse-Hook: blockiert Edits an wrangler.toml (immer) und an package.json,
# wenn die Aenderung ein "deploy"-Script betrifft (Substring-Heuristik im Payload).
# Sieht nur tool_input (Dateipfad, neuer Inhalt) -- kein Zugriff auf Chat-Text,
# daher immer blockieren statt auf eine "Bestaetigung im Prompt" zu warten.
set -euo pipefail

payload="$(cat)"
file_path="$(printf '%s' "$payload" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n1)"

if [ -z "$file_path" ]; then
  exit 0
fi

base="$(basename "$file_path")"

if [ "$base" = "wrangler.toml" ]; then
  echo "BLOCKIERT: '$file_path' ist eine Deploy-Konfigurationsdatei." >&2
  echo "Regel (CLAUDE.md): kein Deploy-Config-Change ohne Freigabe. Bei Freigabe manuell außerhalb von Claude bearbeiten." >&2
  exit 2
fi

if [ "$base" = "package.json" ]; then
  if printf '%s' "$payload" | grep -q '"deploy'; then
    echo "BLOCKIERT: '$file_path' enthält eine Änderung an einem 'deploy'-Script." >&2
    echo "Regel (CLAUDE.md): kein Deploy-Script-Change ohne Freigabe. Bei Freigabe manuell außerhalb von Claude bearbeiten." >&2
    exit 2
  fi
fi

exit 0
```

Datei ausführbar machen: `chmod +x .claude/hooks/guard-deploy-files.sh`

- [ ] **Step 2: Smoke-Test — wrangler.toml blockiert**

Run:
```bash
echo '{"tool_input":{"file_path":"/repo/wrangler.toml","content":"name = \"x\""}}' | bash .claude/hooks/guard-deploy-files.sh; echo "exit=$?"
```
Expected: stderr-Meldung `BLOCKIERT: ... wrangler.toml ...`, `exit=2`

- [ ] **Step 3: Smoke-Test — package.json mit deploy-Script blockiert**

Run:
```bash
echo '{"tool_input":{"file_path":"/repo/package.json","content":"{\"scripts\":{\"deploy\":\"x\"}}"}}' | bash .claude/hooks/guard-deploy-files.sh; echo "exit=$?"
```
Expected: stderr-Meldung `BLOCKIERT: ... 'deploy'-Script ...`, `exit=2`

- [ ] **Step 4: Smoke-Test — Durchlass-Fall (anderes File)**

Run:
```bash
echo '{"tool_input":{"file_path":"/repo/src/lib/leadSchema.ts","content":"export const x = 1;"}}' | bash .claude/hooks/guard-deploy-files.sh; echo "exit=$?"
```
Expected: keine Ausgabe, `exit=0`

- [ ] **Step 5: Hook in `.claude/settings.json` registrieren (zweiter Eintrag im `Edit|Write|MultiEdit`-Matcher)**

Ersetze:
```json
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/block-secrets.sh\""
          }
        ]
      },
```
durch:
```json
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/block-secrets.sh\""
          },
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/guard-deploy-files.sh\""
          }
        ]
      },
```

- [ ] **Step 6: JSON-Validität prüfen**

Run: `python3 -m json.tool .claude/settings.json > /dev/null && echo VALID`
Expected: `VALID`

- [ ] **Step 7: Commit**

```bash
git add .claude/hooks/guard-deploy-files.sh .claude/settings.json
git commit -m "feat(hsb-claude): guard wrangler.toml and deploy scripts via PreToolUse hook"
```

---

### Task 4: Hook `typecheck-on-edit.sh`

**Files:**
- Create: `.claude/hooks/typecheck-on-edit.sh`
- Modify: `.claude/settings.json`

**Interfaces:**
- Produces: neuer `PostToolUse`-Key mit Matcher `Edit|Write|MultiEdit`, führt nach Edits an `.ts`/`.tsx`/`.astro` `npm run check` aus. Reines Feedback, blockiert nicht (Exit immer 0).

- [ ] **Step 1: Hook-Script schreiben**

```bash
#!/usr/bin/env bash
# PostToolUse-Hook: laeuft 'npm run check' nach Edits an .ts/.tsx/.astro.
# Reines Sofort-Feedback, kein Block (PostToolUse kann den Edit nicht zurueckrollen).
set -uo pipefail

payload="$(cat)"
file_path="$(printf '%s' "$payload" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n1)"

if [ -z "$file_path" ]; then
  exit 0
fi

case "$file_path" in
  *.ts|*.tsx|*.astro)
    project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"
    (cd "$project_dir" && npm run check) || echo "TYPECHECK-WARNUNG: 'npm run check' meldet Fehler nach Edit an '$file_path'." >&2
    ;;
esac

exit 0
```

Datei ausführbar machen: `chmod +x .claude/hooks/typecheck-on-edit.sh`

- [ ] **Step 2: Smoke-Test — Treffer löst Check aus**

Run:
```bash
echo '{"tool_input":{"file_path":"src/lib/leadSchema.ts"}}' | bash .claude/hooks/typecheck-on-edit.sh; echo "exit=$?"
```
Expected: `npm run check`-Ausgabe (PASS bei sauberem Repo-Stand), `exit=0`

- [ ] **Step 3: Smoke-Test — kein Treffer, kein Check**

Run:
```bash
echo '{"tool_input":{"file_path":"README.md"}}' | bash .claude/hooks/typecheck-on-edit.sh; echo "exit=$?"
```
Expected: keine `npm run check`-Ausgabe, `exit=0`

- [ ] **Step 4: Hook in `.claude/settings.json` registrieren (neuer `PostToolUse`-Key)**

Ersetze:
```json
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/block-data-store-commit.sh\""
          }
        ]
      }
    ]
  }
}
```
durch:
```json
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/block-data-store-commit.sh\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/typecheck-on-edit.sh\""
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 5: JSON-Validität prüfen**

Run: `python3 -m json.tool .claude/settings.json > /dev/null && echo VALID`
Expected: `VALID`

- [ ] **Step 6: Commit**

```bash
git add .claude/hooks/typecheck-on-edit.sh .claude/settings.json
git commit -m "feat(hsb-claude): run npm run check after ts/tsx/astro edits via PostToolUse hook"
```

---

### Task 5: Hook `run-related-test-on-edit.sh`

**Files:**
- Create: `.claude/hooks/run-related-test-on-edit.sh`
- Modify: `.claude/settings.json`

**Interfaces:**
- Produces: zweiter Hook im `PostToolUse`-`Edit|Write|MultiEdit`-Matcher. Führt bei Edits unter `src/**` die exakt benannte Testdatei `tests/<basename-ohne-ext>.test.ts` aus, falls sie existiert.

- [ ] **Step 1: Hook-Script schreiben**

```bash
#!/usr/bin/env bash
# PostToolUse-Hook: laeuft die exakt benannte Vitest-Datei nach Edits unter src/.
# Reines Sofort-Feedback, kein Block. Kein Namens-Treffer -> keine Aktion.
set -uo pipefail

payload="$(cat)"
file_path="$(printf '%s' "$payload" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n1)"

if [ -z "$file_path" ]; then
  exit 0
fi

case "$file_path" in
  */src/*) ;;
  *) exit 0 ;;
esac

project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"
base="$(basename "$file_path")"
name="${base%.*}"
test_file="$project_dir/tests/${name}.test.ts"

if [ -f "$test_file" ]; then
  (cd "$project_dir" && npx vitest run "$test_file") || echo "TEST-WARNUNG: '$test_file' schlägt nach Edit an '$file_path' fehl." >&2
fi

exit 0
```

Datei ausführbar machen: `chmod +x .claude/hooks/run-related-test-on-edit.sh`

- [ ] **Step 2: Smoke-Test — Namens-Treffer löst Testlauf aus**

Run:
```bash
echo '{"tool_input":{"file_path":"src/lib/schema.ts"}}' | bash .claude/hooks/run-related-test-on-edit.sh; echo "exit=$?"
```
Expected: `vitest`-Ausgabe für `tests/schema.test.ts` (PASS bei sauberem Repo-Stand), `exit=0`

- [ ] **Step 3: Smoke-Test — kein Namens-Treffer, keine Aktion**

Run:
```bash
echo '{"tool_input":{"file_path":"src/lib/leadSchema.ts"}}' | bash .claude/hooks/run-related-test-on-edit.sh; echo "exit=$?"
```
Expected: keine `vitest`-Ausgabe (kein `tests/leadSchema.test.ts` vorhanden), `exit=0`

- [ ] **Step 4: Hook in `.claude/settings.json` registrieren (zweiter Eintrag im `PostToolUse`-Matcher)**

Ersetze:
```json
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/typecheck-on-edit.sh\""
          }
        ]
      }
    ]
```
durch:
```json
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/typecheck-on-edit.sh\""
          },
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/run-related-test-on-edit.sh\""
          }
        ]
      }
    ]
```

- [ ] **Step 5: JSON-Validität prüfen**

Run: `python3 -m json.tool .claude/settings.json > /dev/null && echo VALID`
Expected: `VALID`

- [ ] **Step 6: Commit**

```bash
git add .claude/hooks/run-related-test-on-edit.sh .claude/settings.json
git commit -m "feat(hsb-claude): run related vitest file after src edits via PostToolUse hook"
```

---

### Task 6: MCP `context7`

**Files:**
- Create: `.mcp.json`

**Interfaces:**
- Produces: projektweiter MCP-Server-Eintrag `context7`, im Repo eingecheckt.

- [ ] **Step 1: `.mcp.json` anlegen**

```json
{
  "mcpServers": {
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

- [ ] **Step 2: JSON-Validität prüfen**

Run: `python3 -m json.tool .mcp.json > /dev/null && echo VALID`
Expected: `VALID`

- [ ] **Step 3: Server-Start-Smoke-Test (Netzwerkzugriff nötig)**

Run: `timeout 15 npx -y @upstash/context7-mcp --help`
Expected: Hilfetext oder Server-Startmeldung ohne Fehler (Exit-Code 0 oder Timeout durch laufenden stdio-Server — beides zeigt, dass das Paket auflöst und startet, kein `command not found`/`404`).

- [ ] **Step 4: Commit**

```bash
git add .mcp.json
git commit -m "feat(hsb-claude): register context7 MCP server"
```

---

### Task 7: Skill `lead-endpoint-check`

**Files:**
- Create: `.claude/skills/lead-endpoint-check/SKILL.md`

**Interfaces:**
- Produces: Skill, aufrufbar von Claude und Nutzer (`/lead-endpoint-check`), liest `src/pages/api/lead.ts`, `src/lib/leadSchema.ts`, `tests/lead-endpoint.test.ts`, `tests/lead-endpoint-schema.test.ts`.

- [ ] **Step 1: Skill-Datei schreiben**

```markdown
---
name: lead-endpoint-check
description: Use when reviewing or changing the HSB lead endpoint (src/pages/api/lead.ts, src/lib/leadSchema.ts) to verify schema fields, rate-limit constants, and CORS origins are each covered by tests in tests/lead-endpoint*.test.ts.
---

# Lead-Endpoint-Check (HSB Boden)

Du bist ein read-only Reviewer für den HSB-Lead-Endpoint. Du änderst nichts — du meldest Lücken mit exaktem `datei:zeile`-Bezug.

## Geprüfte Dateien
- `src/pages/api/lead.ts`
- `src/lib/leadSchema.ts`
- `tests/lead-endpoint.test.ts`
- `tests/lead-endpoint-schema.test.ts`

## Arbeitsweise
1. Lies alle vier Dateien vollständig.
2. Liste jedes Feld aus `leadEndpointSchema` (`src/lib/leadSchema.ts`) und prüfe, ob `tests/lead-endpoint-schema.test.ts` einen Validierungstest dafür enthält (gültiger Wert + mindestens ein ungültiger Wert).
3. Prüfe `IP_LIMIT` und `EMAIL_LIMIT` aus `src/pages/api/lead.ts`: existiert in `tests/lead-endpoint.test.ts` ein Test, der das jeweilige Limit tatsächlich auslöst (mehr Requests als `max` innerhalb `windowMs`)?
4. Prüfe `ALLOWED_ORIGINS`: existiert ein Test für einen erlaubten UND einen nicht erlaubten Origin?
5. Melde jede Lücke als eigenen Punkt, jeden bestandenen Check kurz als OK-Zeile.

## Output-Format
```
LEAD-ENDPOINT-CHECK

LÜCKEN:
- <datei:zeile> — <Befund> — <was fehlt konkret>

OK:
- <kurze Liste bestandener Checks>

VERDIKT: PASS | FAIL (FAIL bei ≥1 Lücke)
```
Keine Spekulation — nur das, was in den vier Dateien tatsächlich steht oder fehlt.
```

- [ ] **Step 2: Smoke-Test — Skill lädt ohne Frontmatter-Fehler**

Run: `python3 -c "import yaml,sys; d=open('.claude/skills/lead-endpoint-check/SKILL.md').read().split('---')[1]; yaml.safe_load(d); print('FRONTMATTER_OK')"`
Expected: `FRONTMATTER_OK`

- [ ] **Step 3: Funktionaler Test — Skill gegen aktuellen Repo-Stand aufrufen**

In einer Claude-Code-Session: `/lead-endpoint-check` ausführen.
Expected: Output im oben definierten Format; da `tests/lead-endpoint-schema.test.ts` und `tests/lead-endpoint.test.ts` bereits existieren, sollten die meisten Checks als OK gemeldet werden — keine Exceptions/Absturz, valides `VERDIKT`.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/lead-endpoint-check/SKILL.md
git commit -m "feat(hsb-claude): add lead-endpoint-check skill"
```

---

### Task 8: Skill `deploy-gate-check`

**Files:**
- Create: `.claude/skills/deploy-gate-check/SKILL.md`

**Interfaces:**
- Produces: nutzer-only Skill (`disable-model-invocation: true`), führt `npm run test:run` → `npm run check` → `npm run build` → `npm run deploy:dry-run` sequenziell aus.

- [ ] **Step 1: Skill-Datei schreiben**

```markdown
---
name: deploy-gate-check
description: Run the documented HSB deploy gate (test:run, check, build, deploy:dry-run) sequentially and report which step failed first, if any. User-triggered only.
disable-model-invocation: true
---

# Deploy-Gate-Check (HSB Boden)

Führt das in `CLAUDE.md` dokumentierte Deploy-Gate sequenziell aus. Bricht beim ersten Fehler ab und meldet exakt, welcher Schritt gescheitert ist. Führt selbst keinen Deploy aus.

## Reihenfolge
1. `npm run test:run`
2. `npm run check`
3. `npm run build`
4. `npm run deploy:dry-run`

## Arbeitsweise
Führe die vier Befehle in genau dieser Reihenfolge per Bash aus. Stoppe sofort beim ersten nicht-Null-Exit-Code.

## Output-Format
```
DEPLOY-GATE-CHECK

1. test:run  — PASS/FAIL
2. check     — PASS/FAIL/SKIPPED (vorheriger Schritt fehlgeschlagen)
3. build     — PASS/FAIL/SKIPPED
4. deploy:dry-run — PASS/FAIL/SKIPPED

VERDIKT: ALL PASS | FAILED AT STEP <n>: <Fehlerausgabe gekürzt>
```
Kein echter Deploy, keine Freigabe-Entscheidung — nur das Gate-Ergebnis.
```

- [ ] **Step 2: Smoke-Test — Skill lädt ohne Frontmatter-Fehler**

Run: `python3 -c "import yaml,sys; d=open('.claude/skills/deploy-gate-check/SKILL.md').read().split('---')[1]; yaml.safe_load(d); print('FRONTMATTER_OK')"`
Expected: `FRONTMATTER_OK`

- [ ] **Step 3: Funktionaler Test — Skill gegen aktuellen Repo-Stand aufrufen**

In einer Claude-Code-Session: `/deploy-gate-check` ausführen.
Expected: alle vier Schritte laufen sequenziell, Output im definierten Format, `VERDIKT: ALL PASS` bei sauberem Repo-Stand (entspricht dem in CLAUDE.md dokumentierten Deploy-Gate).

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/deploy-gate-check/SKILL.md
git commit -m "feat(hsb-claude): add deploy-gate-check skill (user-only)"
```

---

### Task 9: Subagent `test-writer`

**Files:**
- Create: `.claude/agents/test-writer.md`

**Interfaces:**
- Produces: Subagent, proaktiv genutzt bei Änderungen an `src/lib/leadSchema.ts` oder `src/pages/api/lead.ts`. Liefert Vitest-Code-Vorschläge, schreibt nichts automatisch.

- [ ] **Step 1: Agent-Datei schreiben**

```markdown
---
name: test-writer
description: MUSS proaktiv genutzt werden nach Änderungen an src/lib/leadSchema.ts oder src/pages/api/lead.ts. Schlägt fehlende Vitest-Fälle (Rate-Limit-Grenzwerte, ungültige Payloads, CORS-Origin-Edge-Cases) vor, ohne sie selbst zu schreiben.
tools: Read, Grep, Glob
---

# Test-Writer (HSB Lead-Endpoint)

Du bist ein read-only Vorschlags-Agent für Vitest-Testfälle rund um den HSB-Lead-Endpoint. Du schreibst keine Dateien — du lieferst vollständigen, einsatzbereiten Testcode als Vorschlag im Chat.

## Kontext
- Endpoint: `src/pages/api/lead.ts` (Rate-Limits `IP_LIMIT`/`EMAIL_LIMIT`, CORS `ALLOWED_ORIGINS`, `MAX_PAYLOAD_BYTES`).
- Schema: `src/lib/leadSchema.ts` (`leadEndpointSchema`).
- Bestehende Tests: `tests/lead-endpoint.test.ts`, `tests/lead-endpoint-schema.test.ts`.

## Arbeitsweise
1. Lies die geänderte Datei und die zugehörigen Tests.
2. Identifiziere Verhalten, das geändert/neu eingeführt wurde, aber noch keinen Test hat: neue Schema-Felder, geänderte Limit-Werte, neue Origins, neue Fehlerpfade.
3. Liefere für jede Lücke einen vollständigen, lauffähigen Vitest-Testfall (kompletter Code, keine Pseudocode-Platzhalter), passend zum bestehenden Test-Setup (`vitest`, `resetLeadRateLimiter()` falls Rate-Limit-Tests).

## Output-Format
```
TEST-WRITER-VORSCHLAG

Lücke: <was fehlt>
Vorschlag:
\`\`\`typescript
<vollständiger Testcode>
\`\`\`
```
Keine Auto-Anwendung. Reine Vorschläge zur Übernahme durch den Nutzer oder Claude.
```

- [ ] **Step 2: Smoke-Test — Frontmatter valide**

Run: `python3 -c "import yaml,sys; d=open('.claude/agents/test-writer.md').read().split('---')[1]; yaml.safe_load(d); print('FRONTMATTER_OK')"`
Expected: `FRONTMATTER_OK`

- [ ] **Step 3: Funktionaler Test**

In einer Claude-Code-Session: testweise ein Feld in `src/lib/leadSchema.ts` lokal ändern (nicht committen), dann den `test-writer`-Subagent für diese Datei aufrufen.
Expected: Subagent erkennt die fehlende Testabdeckung für das geänderte Feld und liefert vollständigen Testcode-Vorschlag — keine Datei wird dabei geschrieben. Änderung danach verwerfen (`git checkout -- src/lib/leadSchema.ts`).

- [ ] **Step 4: Commit**

```bash
git add .claude/agents/test-writer.md
git commit -m "feat(hsb-claude): add test-writer subagent for lead endpoint changes"
```

---

### Task 10: Subagent `dependency-drift-reviewer`

**Files:**
- Create: `.claude/agents/dependency-drift-reviewer.md`

**Interfaces:**
- Produces: Subagent, proaktiv genutzt bei Änderungen an `package.json`. Prüft Peer-Dependency-Kompatibilität gegen `package-lock.json`, meldet Inkompatibilitäten, ändert nichts.

- [ ] **Step 1: Agent-Datei schreiben**

```markdown
---
name: dependency-drift-reviewer
description: MUSS proaktiv genutzt werden nach Änderungen an package.json. Prüft Peer-Dependency-Constraints der geänderten Pakete gegen die in package-lock.json tatsächlich installierten Versionen und meldet Inkompatibilitäten.
tools: Read, Grep, Glob, Bash
---

# Dependency-Drift-Reviewer (HSB Boden)

Du bist ein read-only Reviewer für `package.json`-Änderungen. Du änderst nichts — du meldest Befunde.

## Arbeitsweise
1. Lies `package.json` und identifiziere geänderte/neue Einträge unter `dependencies`/`devDependencies`.
2. Für jedes geänderte Paket: ermittle per `npm info <paket>@<neue-version> peerDependencies` die deklarierten Peer-Dependencies.
3. Vergleiche jede Peer-Dependency-Anforderung gegen die tatsächlich in `package-lock.json` aufgelöste Version (per `Grep` auf den Paketnamen in `package-lock.json` oder `npm ls <peer-paket>`).
4. Melde jede Version außerhalb des deklarierten Peer-Ranges als Befund — mit Paketname, geforderter Range, tatsächlich installierter Version.

## Output-Format
```
DEPENDENCY-DRIFT-REVIEW

Geänderte Pakete: <Liste>

BEFUNDE:
- <paket>: verlangt Peer <paket-name>@<range>, installiert ist <version>

OK: <Pakete ohne Peer-Konflikt>

VERDIKT: PASS | FAIL (FAIL bei ≥1 Befund)
```
Kein Auto-Fix, keine `npm install`-Ausführung — nur Analyse und Bericht.
```

- [ ] **Step 2: Smoke-Test — Frontmatter valide**

Run: `python3 -c "import yaml,sys; d=open('.claude/agents/dependency-drift-reviewer.md').read().split('---')[1]; yaml.safe_load(d); print('FRONTMATTER_OK')"`
Expected: `FRONTMATTER_OK`

- [ ] **Step 3: Funktionaler Test gegen den bekannten Astro-6-Fall**

In einer Claude-Code-Session: den `dependency-drift-reviewer`-Subagent gegen die aktuelle `package.json` aufrufen (kein Edit nötig — der bekannte Astro-6/`@astrojs/tailwind`-Konflikt aus `CURRENT_HANDOFF.md` ist bereits im Repo-Stand vorhanden).
Expected: Subagent meldet die Inkompatibilität zwischen `astro@^6.4.6` und `@astrojs/tailwind`s deklarierter Peer-Range als Befund (oder bestätigt explizit, falls der Konflikt durch einen zwischenzeitlichen Dependency-Bump bereits behoben wurde — in dem Fall `VERDIKT: PASS`).

- [ ] **Step 4: Commit**

```bash
git add .claude/agents/dependency-drift-reviewer.md
git commit -m "feat(hsb-claude): add dependency-drift-reviewer subagent for package.json changes"
```

---

## Abschluss

Nach allen 10 Tasks: `git log --oneline -10` zeigt 10 einzelne, klar benannte Commits. `.claude/settings.json` registriert 5 neue Hooks zusätzlich zum bestehenden `block-secrets.sh`. `.mcp.json` ist neu im Repo. Zwei neue Skills, zwei neue Subagents. Kein Push, kein Deploy — diese Automatisierungen ändern nichts an den bestehenden Freigabe-Anforderungen für Push/Deploy/P0B.
