# CircleCI-Konfiguration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Der Check „CircleCI Pipeline“ auf Pull Requests im Repo `HSBHexagon/hsb-boden` besteht, statt mit „No configuration was found“ zu scheitern.

**Architecture:** `main` enthält keine `.circleci/config.yml`; die Einrichtung wurde am 2026-10-25 auf dem unge-mergten Branch `origin/circleci-project-setup` (Commit `8382231`, nur ein „Hello, World“-Job) begonnen. Der Plan ersetzt diesen Platzhalter durch eine echte Konfiguration, die dieselben Schritte wie `.github/workflows/ci.yml` ausführt, und liefert sie in einem eigenen PR, getrennt von PR 476 (Atlassian-Datei).

**Tech Stack:** CircleCI 2.1, `cimg/node:22.x`, npm (`apps/website/package-lock.json`), Astro/Vitest-Skripte aus `apps/website/package.json`.

**Spec:** Keine Spezifikation vorhanden. Grundlage sind die Befunde vom 2026-10-26: `ci.yml` (Schritte), Ruleset „Protect Main“ (CircleCI ist **kein** Required Check), Commit `8382231`.

## Global Constraints

- Arbeitsverzeichnis aller Schritte: `apps/website` (dort liegen `package.json` und Lockfile).
- Node 22 (wie `ci.yml`: `node-version: 22`).
- Schritte exakt wie `ci.yml`: `npm ci`, `npm run check`, `npm run test:run`, `npm run build`.
- Keine Secrets in der Konfiguration; keine Deploy-Schritte (Production läuft nur über `deploy-production.yml`).
- `CLAUDE.md`: kein `git add .`, nur exakte Pfade stagen; kein Push ohne Freigabe.
- PR 476 (`chore/atlassian-domain-verification`) bleibt unverändert.

## Review Focus

- Pull Request aus einem Fork oder von Dependabot: Der Job darf ohne Secrets laufen und nicht an fehlenden Umgebungsvariablen scheitern.
- Lockfile nicht passend zu `package.json`: `npm ci` bricht ab, der Check wird rot (erwünscht, wie in `ci.yml`).
- Tests brauchen Browser (Playwright) oder Netzwerk: Der Job darf nur laufen lassen, was `ci.yml` auch ausführt, damit er nicht häufiger rot ist als GitHub Actions.
- Zwei CI-Systeme melden gleichzeitig: Ein roter CircleCI-Check darf den Merge nicht blockieren, weil er nicht in „Protect Main“ steht; das bleibt so.
- Konfigurationsfehler im YAML: Die Datei muss vor dem Push validiert werden, sonst ist der Check wieder „no configuration“-ähnlich rot.

---

### Task 1: CircleCI-Konfiguration für die Website

**Files:**
- Create: `.circleci/config.yml`

**Interfaces:**
- Consumes: Skripte `check`, `test:run`, `build` aus `apps/website/package.json`.
- Produces: Workflow `website` mit Job `build-and-test`; erscheint als Check „CircleCI Pipeline“ am PR.

- [ ] **Step 1: Branch anlegen**

```bash
git fetch origin && git switch -c chore/circleci-config origin/main
```

- [ ] **Step 2: `.circleci/config.yml` schreiben**

Version `2.1`, Job `build-and-test` mit `docker: [{image: cimg/node:22.23}]` (Minor-Tag, existiert laut Docker Hub, neueste Patch-Version 22.23.4) und `resource_class: small` (CircleCI rät, die Ressourcenklasse explizit zu setzen, der Default kann sich ändern). Schritte, jeweils mit `working_directory: ~/project/apps/website` ausgenommen `checkout`:
1. `checkout`
2. `restore_cache` mit Schlüsselliste `v1-npm-{{ checksum "apps/website/package-lock.json" }}`, dann Fallback `v1-npm-`
3. `npm ci`
4. `save_cache` (nach dem Install, Schlüssel wie oben, Pfad `~/.npm`)
5. `npm run check`, `npm run test:run`, `npm run build` als getrennte `run`-Schritte mit eigenem `name`

Workflow `website` führt den Job bei jedem Push aus. Keine Branch-Filter (`branches` ist laut Referenz veraltet).

Gründe aus der CircleCI-Doku (Caching dependencies, Configuration reference): `restore_cache` vor, `save_cache` nach dem Install; der Schlüssel wird aus der Lockfile-Prüfsumme gebildet; ein Cache-Treffer ist nur eine Optimierung, kein Muss. Alternative wäre das Orb `circleci/node` mit eingebautem Caching; dessen aktuelle Version ist hier nicht geprüft, daher bleiben wir bei expliziten Schritten.

- [ ] **Step 3: Konfiguration validieren**

Die CircleCI-CLI ist auf diesem Rechner nicht installiert (Installation nur mit Freigabe). Run: `circleci config validate .circleci/config.yml`.
Expected: „Config file at .circleci/config.yml is valid.“ Ersatzweise nur Syntaxprüfung: `python -c "import yaml;yaml.safe_load(open('.circleci/config.yml'))"`; das ersetzt die Schema-Prüfung nicht.

- [ ] **Step 4: Lokal gegenprüfen, dass die Schritte grün sind**

Run: `cd apps/website && npm ci && npm run check && npm run test:run && npm run build`
Expected: alle vier Befehle enden mit Exit 0.

- [ ] **Step 5: Commit**

```bash
git add .circleci/config.yml
git commit -m "chore(ci): CircleCI-Konfiguration für die Website"
```

### Task 2: Pull Request und Verifikation

**Files:**
- Keine Dateiänderung.

**Interfaces:**
- Consumes: Branch `chore/circleci-config` aus Task 1.
- Produces: Offener PR gegen `main` mit grünem Check „CircleCI Pipeline“.

- [ ] **Step 1: `python apps/website/scripts/verify_ssot.py` ausführen** (mit `PYTHONIOENCODING=utf-8` unter Windows). Expected: Exit 0.
- [ ] **Step 2: Nach Freigabe pushen und PR öffnen**: `git push -u origin chore/circleci-config`, dann `gh pr create --base main`.
- [ ] **Step 3: Check prüfen**: `gh pr checks <PR-Nummer>`. Expected: „CircleCI Pipeline“ = pass.
- [ ] **Step 4: Alten Branch aufräumen** (nur mit Freigabe): `origin/circleci-project-setup` enthält nur den Platzhalter und kann gelöscht werden.

### Task 3 (Alternative, falls CircleCI nicht gebraucht wird): Projekt trennen

**Files:**
- Keine Repo-Änderung; Einstellung im CircleCI-Dashboard.

- [ ] **Step 1: Entscheidung**: GitHub Actions deckt Build, Typprüfung und Tests bereits ab (`ci.yml`, `quality.yml`). Ein zweites System dupliziert das.
- [ ] **Step 2: Im CircleCI-Dashboard** das Projekt `HSBHexagon/hsb-boden` über „Project Settings“ stoppen bzw. trennen (Dashboard-Aktion durch den Konto-Inhaber).
- [ ] **Step 3: Prüfen**: Auf einem neuen PR erscheint kein „CircleCI Pipeline“-Check mehr.

Task 1 und 2 oder Task 3, nicht beides.
