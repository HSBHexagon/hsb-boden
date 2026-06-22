# Claude-Code-Automatisierung für hsb-boden — Design

Stand: 2026-06-22. Erweitert das bestehende `.claude/`-Setup (heute: `block-secrets.sh`-Hook, `seo-content-reviewer`-Subagent, `hsb-digital-flyer-design-review`-Skill) um die Bausteine, die fehlen, um bereits dokumentierte Projektregeln technisch durchzusetzen statt sie nur als Doku-Disziplin zu behandeln.

## Ziel

Bestehende, in `CLAUDE.md`/`AGENTS.md` dokumentierte Regeln (kein `git add .`, `.astro/data-store.json` nie committen, kein Deploy/Website-Code-Change ohne Freigabe) technisch erzwingen statt nur zu hoffen, dass jede Session sie einhält. Zusätzlich: schnelles Feedback (Typecheck, Tests) direkt nach Edits, statt erst im CI; gezielte Unterstützung für den aktuell aktiv entwickelten Lead-Endpoint-Pfad.

## Explizit ausgeschlossener Scope

- KI-System-weite Multi-Agent-Governance (Claude/Codex/Gemini, `ai-state`, Brain-Struktur) — bewusste Nutzerentscheidung, eigenes Folgeprojekt.
- Permission-Tuning (`fewer-permission-prompts`), zusätzliche Status-/Stop-Hooks, weitere MCP-Server außer `context7` — Scope-Creep über das hinaus, was hier konkret fehlt.
- Push, Deploy, Production-Cutover, P0B-Freigabe — bleiben wie bisher Nutzerentscheidungen, kein Hook automatisiert sie weg.

## Architektur

### A — Guardrail-Hooks (`.claude/hooks/`, registriert in `.claude/settings.json`)

Alle Hooks folgen dem bestehenden Muster von `block-secrets.sh`: Bash, lesen das Event-JSON von stdin, extrahieren Felder per `sed` (kein `jq`-Zwang), `exit 2` + stderr-Meldung blockt den Tool-Call, `exit 0` lässt ihn durch.

1. **`block-git-add-all.sh`** (`PreToolUse`, Matcher `Bash`): liest `tool_input.command`; blockt, wenn der Befehl `git add .`, `git add -A` oder `git add --all` enthält (Regex-Match auf den Command-String). Meldung verweist auf die Pflicht, exakte Pfade zu stagen.
2. **`block-data-store-commit.sh`** (`PreToolUse`, Matcher `Bash`): blockt `git add`/`git commit`-Befehle, deren Command-String `.astro/data-store.json` referenziert.
3. **`guard-deploy-files.sh`** (`PreToolUse`, Matcher `Edit|Write|MultiEdit`): blockt Edits an `wrangler.toml` immer; blockt Edits an `package.json` nur, wenn der neue Inhalt eine Änderung an den Scripts `deploy`/`deploy:production` enthält (Diff-Heuristik: alter vs. neuer Scriptblock unterscheiden sich). Der Hook sieht nur `tool_input` (Dateipfad, neuer Inhalt) — kein Zugriff auf den Chat-Verlauf, also kein "Bestätigung im Prompt"-Mechanismus. Blockiert immer; Meldung verweist auf die Freigabepflicht aus `CLAUDE.md` und darauf, die Datei bei tatsächlicher Freigabe außerhalb von Claude (oder nach explizitem Hook-Bypass durch den Nutzer) zu bearbeiten.
4. **`typecheck-on-edit.sh`** (`PostToolUse`, Matcher `Edit|Write|MultiEdit`): wenn `file_path` auf `.ts`, `.tsx` oder `.astro` endet, `npm run check` ausführen (ist bereits `astro check --js-only`, günstig). Bei Fehler: Ausgabe an stderr, aber **kein Block** (PostToolUse kann den bereits erfolgten Edit nicht zurückrollen) — reines Sofort-Feedback.
5. **`run-related-test-on-edit.sh`** (`PostToolUse`, Matcher `Edit|Write|MultiEdit`): wenn `file_path` unter `src/` liegt und eine Datei `tests/<basename-ohne-ext>.test.ts` existiert, genau diese Testdatei per `vitest run <pfad>` ausführen. Kein Treffer → `exit 0`, keine Aktion.

### B — MCP

6. **`context7`** in `.mcp.json` (projektweit, ins Repo eingecheckt) registrieren — aktuelle Doku für Astro 6, `@astrojs/cloudflare`, Radix UI. Direkter Bezug: Astro-6-Bump hat laut `CURRENT_HANDOFF.md` bereits eine offene Peer-Dependency-Inkompatibilität mit `@astrojs/tailwind` ausgelöst.

### C — Skills (`.claude/skills/`)

7. **`lead-endpoint-check`**: liest `src/pages/api/lead.ts`, `src/lib/leadSchema.ts` und `tests/lead-endpoint*.test.ts`, prüft Konsistenz zwischen Schema-Feldern, Rate-Limit-Konstanten (`IP_LIMIT`, `EMAIL_LIMIT`), CORS-`ALLOWED_ORIGINS` und den tatsächlichen Testfällen. Meldet Lücken (z. B. ein Schema-Feld ohne zugehörigen Validierungstest). Read-only, beide aufrufbar (Claude + User).
8. **`deploy-gate-check`**: führt das in `CLAUDE.md` dokumentierte Deploy-Gate sequenziell aus: `npm run test:run` → `npm run check` → `npm run build` → `npm run deploy:dry-run`. Bricht bei erstem Fehler ab und meldet, welcher Schritt scheiterte. `disable-model-invocation: true` (nur User-getriggert), da das Ergebnis eine Vorstufe zu einer freigabepflichtigen Aktion ist.

### D — Subagents (`.claude/agents/`)

9. **`test-writer`**: wird bei Änderungen an `src/lib/leadSchema.ts` oder `src/pages/api/lead.ts` proaktiv genutzt. Schlägt zusätzliche Vitest-Fälle vor (Rate-Limit-Grenzwerte, ungültige Payloads, CORS-Origin-Edge-Cases), schreibt sie aber nicht automatisch — Vorschlag, keine Auto-Anwendung.
10. **`dependency-drift-reviewer`**: wird proaktiv genutzt, wenn `package.json` geändert wird. Prüft Peer-Dependency-Constraints der geänderten Pakete gegen die in `package-lock.json` tatsächlich installierten Versionen, meldet Inkompatibilitäten (das hätte die aktuelle Astro-6/`@astrojs/tailwind`-Lücke früher sichtbar gemacht). Read-only, kein Auto-Fix.

## Datenfluss / Wirkungsweise

```
Edit/Write-Tool-Call
  → PreToolUse: guard-deploy-files.sh (kann blocken)
  → [Tool führt aus]
  → PostToolUse: typecheck-on-edit.sh, run-related-test-on-edit.sh (nur Feedback, kein Block)

Bash-Tool-Call (git ...)
  → PreToolUse: block-git-add-all.sh, block-data-store-commit.sh (kann blocken)
  → [Tool führt aus]
```

Skills und Subagents laufen unabhängig davon nur auf expliziten Aufruf bzw. proaktive Erkennung — keine Interaktion mit den Hooks.

## Fehlerbehandlung

- Alle Hooks: kein erkanntes `file_path`/`command` im Event-JSON → `exit 0` (nicht blockieren, fail-open wie `block-secrets.sh`).
- `typecheck-on-edit.sh` / `run-related-test-on-edit.sh`: laufen mit Timeout (analog CI), schlagen sie fehl, wird das nur gemeldet, nicht blockiert — PostToolUse kann ohnehin nicht zurückrollen.
- `guard-deploy-files.sh`: bei unklarer Diff-Heuristik (z. B. `package.json` nicht parsebar) im Zweifel blocken, nicht durchlassen (sicherer Default, analog Secret-Hook).

## Testing

- Jeder neue Hook bekommt einen manuellen Smoke-Test (Tool-Call mit bekanntem Blockier-/Durchlass-Fall, Exit-Code + stderr prüfen) — keine eigene Test-Suite für Bash-Hooks, Repo hat dafür kein Pattern.
- Skills (`lead-endpoint-check`, `deploy-gate-check`): manueller Lauf gegen den aktuellen Repo-Stand, Ergebnis muss mit `npm run test:run`/`check`/`build`-Realität übereinstimmen.
- Subagents: kein automatisierter Test: Verifikation erfolgt durch eine reale Beispieländerung (z. B. testweise ein Schema-Feld ändern) und Prüfung, ob der Subagent das erkennt.

## Out of Scope

- Push, Deploy, Production-Cutover, P0B-Freigabe-Checkbox.
- KI-System-weite Governance/Multi-Agent-Setup.
- `.mcp.json`-Server außer `context7`.
- Permission-/Settings-Tuning über das hinaus, was zur Hook-Registrierung nötig ist.
