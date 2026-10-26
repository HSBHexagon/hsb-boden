# GitHub-Ökosystem Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die GitHub-Automatisierung von `HSBHexagon/hsb-boden` deckt alle Manifeste ab, schützt kritische Pfade und hat keine toten Konfigurationen.

**Architecture:** Zuerst Lücken schließen, die ohne Website-Code lösbar sind (`.github/`, `scripts/`), dann Owner-Entscheidungen bündeln (CI-Landschaft, Settings, Apps). Jede Lücke bekommt einen reproduzierbaren Prüfbefehl, der vor der Korrektur rot ist.

**Tech Stack:** GitHub Actions, Dependabot, CODEOWNERS, Python 3 (`scripts/`), PyYAML.

**Spec:** Keine Spezifikation vorhanden. Grundlage ist der Abschnitt „Ist-Zustand“ unten (Stand 2026-10-26, Belege mit Pfad).

## Global Constraints

- Keine Website-Code-Änderung ohne Freigabe: `src/`, `public/`, `components/`, `layouts/`, `styles/`, `astro.config.*`, `wrangler.toml`, `package.json`, Lockfiles. Dieser Plan berührt sie nicht.
- Kein `git add .`, nur exakte Pfade; `.astro/data-store.json` nie committen; kein Push und kein Production-Deploy ohne Freigabe; keine Secrets.
- `PROJECT_TRUTH.md`: „Keine produktive Website-Veröffentlichung durch diesen Auftrag.“
- Vor jedem Commit: `python3 scripts/verify_ssot.py` mit Exit 0.
- Einstellungen im GitHub-UI (Rulesets, Apps, Security-Settings) führt der Konto-Inhaber aus. Der Plan listet sie als **Owner-Aktion** mit Begründung.
- `~/KI-System` existiert im Cloud-Container nicht; `handoff.sh` und `CURRENT_HANDOFF.md` aus `CLAUDE.md` kann nur der Owner lokal ausführen.

## Ist-Zustand (Belege)

| Befund | Beleg |
|---|---|
| `dependabot.yml` kennt nur `directory: "/"` für `npm` und `github-actions`; im Repo-Root liegt kein `package.json`. Manifeste liegen in `apps/website`, `marketing/flyer`, `apps/sales-os/requirements.txt`. | `.github/dependabot.yml:3-4,17-18`; `find . -name package.json` |
| Laut Referenz braucht Dependabot den Ort der Manifeste, sonst entstehen keine Version-Update-PRs [G1]. Die sichtbaren PRs („bump zod in /apps/website“) stammen von Branch `dependabot/npm_and_yarn/apps/website/multi-…` mit Footer „automated security fix PRs“, also alarmgesteuerte Security-Updates, nicht der Zeitplan. | PR #472; Suche: 48 Dependabot-PRs insgesamt |
| PR #472 hebt `zod` von 3.25.76 auf 4.6.7 (Major); `package.json` nennt `^3.24.4`. Status „behind“. | PR #472, `apps/website/package.json` |
| Kein `CODEOWNERS`. | `ls .github/CODEOWNERS` |
| Derselbe `actions/checkout`-SHA trägt 6× den Kommentar `# v7.0.1` und 2× `# v4`. `git ls-remote --tags` bestätigt für den SHA `v7` und `v7.0.1`, also sind die `# v4`-Kommentare falsch; `ci.yml:23` nennt zusätzlich „actions/checkout@v4 pinned on 2026-06-26“. | `.github/workflows/ci.yml:23-24`, Befehl in Task 4 |
| `ai-pr-review.yml` filtert auf `src/**`, `public/**`, `functions/**`; die Website liegt unter `apps/website/`. Geprüft: diese Pfade treffen 0 getrackte Dateien, `apps/website/src/**` trifft 109. | `.github/workflows/ai-pr-review.yml:6-16` |
| `jules-auto-merge.yml` nutzt `pull_request_target` (label-gesteuert, setzt Freigabe bei `synchronize` zurück). Rest der Datei wurde noch nicht geprüft. | `.github/workflows/jules-auto-merge.yml:1-70` |
| CircleCI (PR #485) dupliziert `ci.yml`; `quality.yml` enthält `check`/`build`/`test:run` ebenfalls. | PR #485, `.github/workflows/quality.yml:29-47` |

## Quellen (abgerufen 2026-10-26)

- [G1] Dependabot options reference: https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference. `directory`/`directories`; `cooldown` nur für Version-Updates, Standard 3 Tage; `open-pull-requests-limit` Standard 5, Security-Updates separat 10. Gelesen wurden die ersten 100.000 von 182.383 Zeichen; der `pip`-Ecosystem-Name stand dort nicht und ist im Task zu prüfen.
- [G2] Secure use reference: https://docs.github.com/en/actions/reference/security/secure-use. SHA-Pinning, `pull_request_target` meiden und keinen untrusted Code auschecken, minimale `GITHUB_TOKEN`-Rechte, Scorecard/CodeQL für Actions.
- [G3] About code owners: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners. Ort der Datei, Schreibrecht der Owner, „Require review from Code Owners“.

## Review Focus

- Nach der Korrektur entstehen schlagartig PRs aus drei Ökosystemen: `open-pull-requests-limit` und `cooldown` müssen das abfangen.
- Ein Security-Update mit Major-Sprung (`zod` 3→4) darf nie automatisch gemergt werden: `dependabot-auto-merge.yml` lässt nur patch/minor zu; das bleibt so.
- Code-Owner-Pflicht mit nur einem Owner blockiert dessen eigene PRs (Annahme: ein Autor kann den eigenen PR nicht freigeben; im Ruleset gegenprüfen, bevor es aktiviert wird).
- Der korrigierte Pfadfilter lässt die AI-Review bei jedem Website-PR laufen: Kosten und verwendete Secrets prüfen, Fork-PRs bekommen keine Secrets.
- Falsche Versions-Kommentare bei gepinnten SHAs täuschen Reviewer; der SHA ist maßgeblich, nicht der Kommentar.

---

### Task 1: Dependabot-Abdeckung herstellen

**Files:**
- Create: `scripts/verify_dependabot_coverage.py`
- Modify: `.github/dependabot.yml`
- Modify: `.github/workflows/quality.yml` (ein Schritt nach `verify_ssot.py`)

**Interfaces:**
- Produces: `main() -> int` in `scripts/verify_dependabot_coverage.py`; Exit 0, wenn jedes getrackte Manifest (`package.json`, `requirements*.txt`, `.github/workflows/*.yml`) durch einen `updates`-Eintrag desselben Ecosystems abgedeckt ist; sonst Exit 1 und eine Zeile je Lücke (`ecosystem directory`).

- [ ] **Step 1: Skript schreiben** (`git ls-files` für Manifeste, `yaml.safe_load` für `dependabot.yml`, Abgleich über `directory` und `directories`). PyYAML steht nicht in `apps/sales-os/requirements.txt` (geprüft); der Workflow-Schritt in `quality.yml` installiert es per `pip install pyyaml`, die Abhängigkeitsdateien bleiben unverändert.
- [ ] **Step 2: Rot beweisen.** Run: `python3 scripts/verify_dependabot_coverage.py`. Expected: Exit 1 mit Zeilen für `npm /apps/website`, `npm /marketing/flyer`, `pip /apps/sales-os`.
- [ ] **Step 3: `dependabot.yml` ändern.** `npm` mit `directories: ["/apps/website", "/marketing/flyer"]`, `pip` mit `directory: "/apps/sales-os"` (Ecosystem-String in [G1] bestätigen), `github-actions` bleibt `"/"`. Je Eintrag `cooldown: default-days: 7` explizit setzen (Standard ist 3 Tage, [G1]); Gruppen und Limit 5 beibehalten. `marketing/flyer` nur aufnehmen, wenn der Owner bestätigt, dass das Verzeichnis gepflegt wird.
- [ ] **Step 4: Grün beweisen.** Run: `python3 scripts/verify_dependabot_coverage.py`. Expected: Exit 0.
- [ ] **Step 5: Commit.** `git add .github/dependabot.yml scripts/verify_dependabot_coverage.py .github/workflows/quality.yml` und `git commit -m "chore(ci): Dependabot deckt alle Manifeste ab"`.
- [ ] **Step 6: Owner-Aktion nach dem Merge.** Im Repo unter Insights → Dependency graph → Dependabot prüfen, dass drei Einträge ohne Fehler laufen.

### Task 2: Offene Dependabot-PRs triagieren

**Files:**
- Create: `docs/audits/DEPENDABOT_TRIAGE_2026-10-26.md`

**Interfaces:**
- Consumes: PRs #464, #470, #471, #472, #474.
- Produces: Tabelle mit Spalten PR, Paket, alt→neu, Art (Security/Version), SemVer-Stufe, Prüfergebnis, Empfehlung.

- [ ] **Step 1: Je PR in einem Wegwerf-Worktree prüfen:** `npm ci && npm run check && npm run test:run && npm run build` in `apps/website`. Expected: Exit 0 oder dokumentierter Fehler.
- [ ] **Step 2: `zod`-Major (#472) gesondert bewerten.** `grep -rn "from \"zod\"" apps/website/src apps/website/functions` und die API-Änderungen von v3→v4 gegen die gefundenen Aufrufe halten; Ergebnis in die Tabelle.
- [ ] **Step 3: Empfehlung je PR eintragen** (mergen / nachziehen lassen / ablehnen). Gemerged wird nichts ohne Owner-Freigabe.
- [ ] **Step 4: Commit.** `git add docs/audits/DEPENDABOT_TRIAGE_2026-10-26.md`, Nachricht `docs(audit): Dependabot-Triage 2026-10-26`.

### Task 3: CODEOWNERS für kritische Pfade

**Files:**
- Create: `.github/CODEOWNERS`

**Interfaces:**
- Produces: Owner-Zuordnung für `/.github/`, `/apps/website/functions/`, `/apps/website/public/_headers`, `/apps/sales-os/config/` (alle auf den Owner-Login `HSBHexagon`; weitere Personen trägt der Owner nach, sie brauchen Schreibrecht [G3]).

- [ ] **Step 1: Datei schreiben** (Muster plus Owner je Zeile, gitignore-Syntax, letzte passende Zeile gewinnt [G3]).
- [ ] **Step 2: Syntax prüfen.** Nach dem Push zeigt die Datei im GitHub-UI keine Fehlerzeilen; ungültige Zeilen werden stillschweigend übersprungen [G3], daher dort nachsehen.
- [ ] **Step 3: Wirkung prüfen.** Test-PR, der nur `.github/dependabot.yml` ändert. Expected: `HSBHexagon` erscheint automatisch als angeforderter Reviewer.
- [ ] **Step 4: Owner-Entscheidung** zu „Require review from Code Owners“ im Ruleset „Protect Main“: erst aktivieren, wenn ein zweiter Reviewer existiert (siehe Review Focus).
- [ ] **Step 5: Commit.** `git add .github/CODEOWNERS`, Nachricht `chore(github): CODEOWNERS für kritische Pfade`.

### Task 4: Workflow-Hygiene

**Files:**
- Modify: `.github/workflows/ai-pr-review.yml` (Pfadfilter)
- Modify: `.github/workflows/ci.yml`, `security.yml`, weitere mit Versionskommentar (nur Kommentare)
- Read: `.github/workflows/jules-auto-merge.yml` (Rest ab Zeile 70)

**Interfaces:**
- Produces: Pfadfilter, die auf getrackte Dateien passen; ein einheitlicher Versionskommentar je SHA.

- [ ] **Step 1: Pfadfilter rot beweisen.** Run: `git ls-files ':(glob)src/**' ':(glob)functions/**' | wc -l`. Expected: `0`.
- [ ] **Step 2: Filter auf `apps/website/**` und `apps/sales-os/**` umstellen**, bestehende Workflow-Pfade behalten. Run: `git ls-files ':(glob)apps/website/src/**' | wc -l`. Expected: größer als 0.
- [ ] **Step 3: SHA-Kommentare rot beweisen.** Run: `grep -rhn "checkout@3d3c42e" .github/workflows | grep -o "# v[0-9.]*" | sort -u`. Expected vorher: zwei Zeilen (`# v4`, `# v7.0.1`).
- [ ] **Step 4: Kommentare korrigieren.** Die beiden `# v4` auf `# v7.0.1` setzen (der SHA gehört laut `git ls-remote --tags https://github.com/actions/checkout` zu `v7.0.1`) und den Satz „actions/checkout@v4 pinned on 2026-06-26“ in `ci.yml:23` entsprechend anpassen. Dieselbe Prüfung für `setup-node` und `upload`-Actions wiederholen. Expected: der Befehl aus Step 3 liefert genau eine Zeile.
- [ ] **Step 5 (lesend): `jules-auto-merge.yml` ab Zeile 70 prüfen.** Erwartung nach [G2]: kein `actions/checkout` mit `ref` auf den PR-Head in einem `pull_request_target`-Job; Untrusted-Eingaben nur über `env`. Fund oder „unauffällig“ im Commit-Text festhalten.
- [ ] **Step 6: Commit.** `git add .github/workflows/ai-pr-review.yml .github/workflows/ci.yml .github/workflows/security.yml`, Nachricht `chore(ci): Pfadfilter und Versionskommentare korrigieren`.

### Task 5: CI-Landschaft, Settings und Apps (Owner-Entscheidungen)

**Files:**
- Create: `docs/audits/GITHUB_ECOSYSTEM_DECISIONS_2026-10-26.md`

**Interfaces:**
- Produces: Entscheidungsliste mit je Punkt Empfehlung, Begründung, Owner-Antwort (offen).

- [ ] **Step 1: CI-Duplikate aufnehmen.** CircleCI (PR #485) neben `ci.yml` und `quality.yml`; vor jeder Entfernung die Namen der Required Checks im Ruleset „Protect Main“ ablesen (CircleCI ist laut Plan vom 2026-10-26 kein Required Check). Empfehlung: Entweder CircleCI behalten (informativ) oder im CircleCI-Dashboard trennen; `ci.yml` erst entfernen, wenn kein Ruleset darauf verweist.
- [ ] **Step 2: Settings-Checkliste für den Owner:** Dependabot alerts und security updates an, Secret-scanning push protection an, Code scanning default setup inklusive Actions an (die Checks „Analyze (actions)“ laufen bereits).
- [ ] **Step 3: Apps-Inventur.** Installierte GitHub-Apps und Bots aus den PR-Checks ableiten (CodeRabbit, Cloudflare Pages, Claude, Copilot, Jules) und je App festhalten: Zweck, Schreibrechte, behalten oder entfernen. Optional bewerten: OpenSSF-Scorecard-Workflow (in [G2] genannt).
- [ ] **Step 4: Commit.** `git add docs/audits/GITHUB_ECOSYSTEM_DECISIONS_2026-10-26.md`, Nachricht `docs(audit): GitHub-Ökosystem-Entscheidungen`.
