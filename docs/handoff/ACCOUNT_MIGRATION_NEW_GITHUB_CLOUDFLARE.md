# ACCOUNT_MIGRATION_NEW_GITHUB_CLOUDFLARE — HSB-Boden

Stand: 2026-06-29
Status: `migration-prepared-waiting-for-new-accounts`

Diese Datei ist die kanonische Operator-Anleitung fuer den geplanten Umzug auf
einen neuen GitHub-Account und einen neuen Cloudflare-Account.

Sie ersetzt keinen Trigger-Day-Runbook fuer den Live-Cutover. Sie bereitet den
Account-Wechsel so vor, dass danach keine Informationen mehr aus verteilten
Dateien zusammengesucht werden muessen.

## 1. Zielbild

- GitHub-Repository `hsb-boden` wird vom aktuellen Owner auf einen neuen
  GitHub-Account uebertragen.
- Cloudflare-Setup fuer `hsb-boden.de` wird in einem neuen Cloudflare-Account
  neu aufgebaut.
- Die Domain selbst bleibt extern beim Registrar gesteuert.
- Der Live-Cutover bleibt weiterhin getrennt freigabepflichtig.

## 2. Wichtiger Realitaetscheck

### 2.1 GitHub-Stand

- Repo-Pfad lokal:
  `/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden`
- Aktueller Branch: `main`
- Aktueller verifizierter HEAD am 2026-06-29: `85b977c`
- Remote:
  `https://github.com/cherinojoel-lang/hsb-boden.git`
- Aktueller GitHub-Owner:
  `cherinojoel-lang/hsb-boden`

### 2.2 Cloudflare-Altstand

- Aktueller Cloudflare-Account:
  `cherinojoel@gmail.com`
- Aktuelle Cloudflare Account ID:
  `043ec899a435f150995d89f402ed7b12`
- Zone:
  `hsb-boden.de`
- Aktuelle Zone ID:
  `2aefa04f69a2339b2f9f3f2876d7e35c`
- Aktueller Zonenstatus laut Repo-Doku:
  `pending`
- Preview Worker:
  `hsb-boden-preview`
- Production Worker:
  `hsb-boden`
- Production-KV:
  `hsb-boden-session`
- Kritisches Worker-Secret:
  `LEAD_WEBHOOK_URL`

### 2.3 Neuer Cloudflare-Account — live verifiziert am 2026-06-29

- Neuer Cloudflare-Account:
  `Info@hsb-boden.de's Account`
- Neue Cloudflare Account ID:
  `01dc37803d1c687b4f9d6249ec89f700`
- Neue Zone:
  `hsb-boden.de`
- Neue Zone ID:
  `a81248882b0a80ecb77c68af9f343206`
- Setup-Typ:
  `Full`
- Aktueller Zonenstatus:
  `pending` / wartet auf Nameserver-Umstellung beim Registrar
- Neue Cloudflare-Nameserver:
  `bart.ns.cloudflare.com`
  `melody.ns.cloudflare.com`
- Bisherige beim Registrar zu ersetzende Nameserver:
  `ns5.kasserver.com`
  `ns6.kasserver.com`
- Live verifizierter DNS-Bestand im neuen Account:
  - `*` A -> `85.13.130.17` (`proxied`)
  - `@` A -> `85.13.130.17` (`proxied`)
  - `www` A -> `85.13.130.17` (`proxied`)
  - `autodiscover` CNAME -> `autodiscover.outlook.com` (`proxied`)
  - `@` MX -> `hsbboden-de0i.mail.protection.outlook.com` Prio `10` (`DNS-only`)
  - `_dmarc` TXT -> `v=DMARC1; p=none;` (`DNS-only`)
  - `@` TXT -> `v=spf1 include:spf.protection.outlook.com -all` (`DNS-only`)
  - `@` TXT -> `MS=ms97748082` (`DNS-only`)
- Live verifizierter Worker-Routes-Stand im neuen Account:
  keine Routes vorhanden
- Noch nicht live verifiziert im neuen Account:
  - ob `hsb-boden-preview` bereits existiert
  - ob `hsb-boden` bereits existiert
  - ob `LEAD_WEBHOOK_URL` bereits gesetzt ist
  - ob DKIM `selector1` / `selector2` bereits eingetragen sind

### 2.4 Externe, nicht in GitHub/Cloudflare enthaltene Betriebsabhaengigkeiten

- Microsoft 365 / Exchange Online fuer `hsb-boden.de`
- Allgemeine Mailbox:
  `info@hsb-boden.de`
- Outreach-Mailbox:
  `j-cherino@hsb-boden.de`
- Google Apps Script Web App fuer Lead Intake
- Google Sheet:
  `HSB CRM Light`
- Domain-Registrar / Nameserver-Steuerung ausserhalb des Repos

## 3. Harte Constraints fuer den Umzug

### 3.1 GitHub

- Ein E-Mail-Adresse kann auf GitHub nur einem Account gleichzeitig zugeordnet
  sein.
- Repository-Transfer ist deshalb nur sinnvoll, wenn der neue GitHub-Account
  bereits sauber existiert und die Ziel-E-Mail-/Login-Strategie geklaert ist.
- Der Repo-Transfer erhaelt laut GitHub-Doku Issues, Pull Requests, Wiki,
  Stars, Watcher, Webhooks, Services, Secrets und Deploy Keys.

### 3.2 Cloudflare

- Der Cloudflare-Teil ist praktisch kein "Transfer" wie bei GitHub, sondern ein
  kontrollierter Neuaufbau im neuen Account.
- Zone, Worker, Secrets, KV-Bindings und DNS muessen im neuen Account bewusst
  neu verifiziert werden.
- Nameserver-Aktivierung bleibt der Punkt, an dem die Zone im neuen Account
  erst wirklich `active` wird.

### 3.3 Projektintern

- `wrangler deploy --env production` bleibt fuer dieses Projekt unzulaessig.
- Fuer Production ist weiterhin der dokumentierte Workaround Pflicht:
  `wrangler deploy --name hsb-boden --var ENVIRONMENT:production`
- Kein Push, kein Production-Deploy, kein Route-Setzen ohne explizite
  Freigabe.

## 4. Was automatisch mitgeht und was nicht

### 4.1 GitHub-Transfer: mit hoher Sicherheit mitgehend

- Repository-Inhalt und Git-Historie
- Issues
- Pull Requests
- Wiki
- Webhooks
- Deploy Keys
- Repository Secrets

### 4.2 GitHub-Transfer: separat pruefen

- Branch Protection / Rulesets
- Environment-Konfigurationen
- GitHub-App-Installationen
- Deploy-/Preview-Integrationen von Drittanbietern
- Repository-Collaborators und Rollenmodell

### 4.3 Cloudflare-Neuaufbau: neu anlegen oder neu bestaetigen

- Zone im neuen Account anlegen
- DNS-Records importieren oder manuell anlegen
- Neue Cloudflare-Nameserver erhalten
- Worker `hsb-boden-preview` deployen
- Worker `hsb-boden` deployen
- Secret `LEAD_WEBHOOK_URL` in den neuen Worker setzen
- KV-/Session-Binding verifizieren
- Route-/Domain-Zuordnung spaeter getrennt aktivieren
- Optional spaeter:
  Turnstile / WAF / Analytics / weitere Account-Features

## 5. Werte, die in den neuen Cloudflare-Account uebernommen werden muessen

### 5.1 Worker-Namen

- Preview: `hsb-boden-preview`
- Production: `hsb-boden`

### 5.2 DNS-/Mail-Werte

- MX:
  `hsbboden-de0i.mail.protection.outlook.com.` mit Prioritaet `10`
- SPF TXT:
  `v=spf1 include:spf.protection.outlook.com -all`
- Microsoft Verification TXT:
  `MS=ms97748082`
- DMARC TXT:
  `v=DMARC1; p=none;`
- Autodiscover CNAME:
  `autodiscover.outlook.com.`
- DKIM selector1:
  aus M365 Admin Center beziehen
- DKIM selector2:
  aus M365 Admin Center beziehen

### 5.3 Geplante Route-Patterns fuer spaeteren Cutover

- `hsb-boden.de/*` -> `hsb-boden`
- `www.hsb-boden.de/*` -> `hsb-boden`

### 5.4 Worker-Secret

- `LEAD_WEBHOOK_URL`
- Ziel ist die bestehende Google Apps Script Web App

## 6. Vorbereitung vor dem eigentlichen Transfer

### 6.1 Unmittelbar vor GitHub-Transfer

1. Im aktuellen Repo lokal pruefen:
   `git status --short --branch`
2. Sicherstellen, dass der Ziel-Account auf GitHub bereits existiert.
3. Sicherstellen, dass im Ziel-Account kein Repo `hsb-boden` existiert.
4. Entscheiden, ob der neue Owner ein Personal Account oder eine Organization
   wird.
5. Nach Transfer sofort den lokalen Remote auf den neuen Owner umstellen.

### 6.2 Unmittelbar vor Cloudflare-Neuaufbau

1. Alten DNS-Bestand exportieren oder vollstaendig abschreiben.
2. DKIM-Werte aus M365 Admin Center holen.
3. Alle Mail-Records als `DNS-only` vorbereiten.
4. Entscheiden, ob die neue Zone sofort oder erst spaeter per NS-Switch aktiv
   werden soll.
5. Sicherstellen, dass der neue Cloudflare-Account Zugriff auf Workers hat.
6. Den bereits angelegten neuen DNS-Bestand gegenpruefen:
   - `autodiscover` wahrscheinlich auf `DNS-only` umstellen
   - DKIM-Records ergaenzen
   - keine ueberfluessigen Legacy-Records anlegen

## 7. Exakte Reihenfolge nach Erstellung der neuen Accounts

### Phase A — GitHub zuerst

1. Neuen GitHub-Account fertig einrichten.
2. E-Mail-Verifikation abschliessen.
3. Repository `cherinojoel-lang/hsb-boden` an den neuen Account transferieren.
4. Im neuen Account pruefen:
   - Repo sichtbar
   - `main` vorhanden
   - Issues / PRs / Wiki sichtbar
   - Actions-Tab sichtbar
5. Lokalen Remote aktualisieren:
   - neue `origin`-URL setzen
6. Repository Settings pruefen:
   - Branch Protection / Rulesets
   - Secrets / Variables
   - Environments
   - Webhooks / Apps

#### Phase A — vorbereitete Terminal-Befehle

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden
git status --short --branch
git remote -v
git remote set-url origin https://github.com/<NEUER_GITHUB_OWNER>/hsb-boden.git
git remote -v
git fetch origin --prune
git branch -vv
```

Optional mit GitHub CLI, falls lokal bereits authentifiziert:

```bash
gh repo view <NEUER_GITHUB_OWNER>/hsb-boden
gh auth status
```

### Phase B — Cloudflare neu aufbauen

1. Im neuen Cloudflare-Account `hsb-boden.de` als Zone anlegen.
2. DNS-Records importieren oder manuell anlegen.
3. Mail-Records streng auf `DNS-only` setzen.
4. Aktuelle Cloudflare-Nameserver des neuen Accounts notieren.
5. Vor dem NS-Switch Workers im neuen Account bereitstellen.
6. Bestehenden verifizierten Ist-Stand nutzen statt neu zu beginnen:
   - Zone existiert bereits
   - 8 DNS-Records sind bereits vorhanden
   - Nameserver sind bereits bekannt
   - Routes fehlen noch komplett

### Phase C — Worker-Neuaufbau im neuen Cloudflare-Account

1. Neue `CLOUDFLARE_ACCOUNT_ID` fuer den neuen Account beschaffen.
2. Neues API-Token mit Workers-/DNS-Rechten anlegen.
3. Im GitHub-Repo die Actions-Secrets fuer den neuen Cloudflare-Account
   aktualisieren:
   - `CLOUDFLARE_API_TOKEN`
   - `CLOUDFLARE_ACCOUNT_ID`
4. Preview deployen:
   - Standardpfad aus `wrangler.toml` / Preview-Workflow
5. Production route-los deployen:
   - `wrangler deploy --name hsb-boden --var ENVIRONMENT:production`
6. Secret neu setzen:
   - `wrangler secret put LEAD_WEBHOOK_URL --name hsb-boden`
7. Workers.dev-URLs pruefen:
   - Preview erreichbar
   - Production erreichbar
8. Session-KV/Binding pruefen.

#### Phase C — vorbereitete Terminal-Befehle

```bash
cd /Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden
export CLOUDFLARE_API_TOKEN='<NEUES_CLOUDFLARE_API_TOKEN>'
export CLOUDFLARE_ACCOUNT_ID='01dc37803d1c687b4f9d6249ec89f700'
npm run test:run
npm run check
npm run build
npm run deploy:dry-run
wrangler whoami
wrangler deploy --name hsb-boden-preview
wrangler deploy --name hsb-boden --var ENVIRONMENT:production
wrangler secret put LEAD_WEBHOOK_URL --name hsb-boden
```

Danach manuell verifizieren:

```bash
curl -I https://hsb-boden-preview.<SUBDOMAIN>.workers.dev/
curl -I https://hsb-boden.<SUBDOMAIN>.workers.dev/
```

### Phase D — Registrar / DNS / Aktivierung

1. Erst wenn der neue Cloudflare-Aufbau vollstaendig ist:
   Nameserver beim Registrar auf die neuen Cloudflare-Nameserver umstellen.
2. Warten, bis die neue Zone `active` wird.
3. Danach DNS-Records im neuen Cloudflare-Account nochmals pruefen.
4. Erst bei expliziter Freigabe:
   Route `hsb-boden.de/*` und `www.hsb-boden.de/*` auf `hsb-boden` setzen.

## 8. GitHub-spezifische Nachkontrolle

- Remote lokal zeigt auf den neuen Owner.
- Push nach `main` funktioniert nicht ungeprueft, sondern gemaess Repo-Regeln.
- `quality.yml`, `ci.yml`, `deploy-preview.yml`, `deploy-production.yml`
  laufen im neuen Repo.
- Falls Actions wegen fehlender Secrets stoppen:
  zuerst Secrets reparieren, dann erneut laufen lassen.

## 9. Cloudflare-spezifische Nachkontrolle

- Neue Zone hat alle benoetigten DNS-Records.
- Mail-Records sind `DNS-only`.
- DKIM-Selectoren sind gesetzt oder explizit noch offen dokumentiert.
- `autodiscover` ist nicht versehentlich `proxied`, falls M365 dies stoert.
- `hsb-boden-preview` laeuft im neuen Account.
- `hsb-boden` laeuft route-los im neuen Account.
- `LEAD_WEBHOOK_URL` ist gesetzt.
- Vor echtem Domain-Cutover:
  Build, Check und Tests erneut laufen lassen.

## 10. Bekannte Stolperstellen

- Alte Repo-Dokumente nennen aeltere Commits (`bf0f998`, `d4ea032`); der reale
  verifizierte Stand fuer diese Migration ist `85b977c`.
- Cloudflare-Account-ID und Zone-ID aus der alten Umgebung duerfen nicht blind
  in die neue Umgebung uebernommen werden.
- Im neuen Cloudflare-Account ist `autodiscover` aktuell live als `proxied`
  sichtbar; fuer Mail-/Autodiscover-Records ist `DNS-only` der sichere
  Zielzustand.
- Im neuen Cloudflare-Account sind die Kern-Mail-Records bereits angelegt, aber
  DKIM `selector1` / `selector2` sind noch nicht als verifiziert dokumentiert.
- Die Mail- und Lead-Infrastruktur lebt nicht nur in GitHub/Cloudflare.
  M365, Apps Script und Google Sheets bleiben separat kritisch.
- `info@hsb-boden.de` ist im Projekt die allgemeine/legal Mailbox, nicht der
  kanonische Outreach-Sender.

## 11. Sofort nach Account-Erstellung vom Operator liefern

Sobald die neuen Accounts existieren, werden fuer die eigentliche Uebernahme nur
noch diese Angaben benoetigt:

- Neuer GitHub-Owner-Name
- Bestaetigung, ob DKIM-Werte aus M365 bereits vorliegen
- Bestaetigung, ob im neuen Cloudflare-Account Workers verfuegbar sind
- Bestaetigung, welcher GitHub-Account das Ziel fuer den Repo-Transfer wird

Dann kann die eigentliche Transfer-/Neuaufbau-Sequenz Schritt fuer Schritt
abgearbeitet werden.

## 12. Ausfuehrungsstand 2026-07-02 (Claude Code)

### GitHub
- Neues Repo `HSBHexagon/hsb-boden` angelegt, vollstaendiger Mirror-Push
  (alle 30 Branches/Tags), `main`-HEAD identisch zu Alt-Repo verifiziert
  (`85b977c...`).
- Labels aus Alt-Repo uebernommen.
- `HSBHexagon` zusaetzlich als Admin-Collaborator ins Alt-Repo
  (`cherinojoel-lang/hsb-boden`) eingeladen und die Einladung per API
  angenommen — voller Zugriff auf beide Repos, unabhaengig vom
  Ownership-Transfer.
- Nativer Ownership-Transfer `cherinojoel-lang` -> `HSBHexagon` wurde
  angestossen, haengt aber an einer E-Mail-Bestaetigung an
  `info@hsb-boden.de` (kein Postfach) und ist weiterhin **pending**. Nicht
  mehr blockierend, da Collaborator-Zugriff den praktischen Bedarf deckt.
- `info@hsb-boden.de` (HSBHexagon) hat jetzt eine zweite verifizierte
  E-Mail: `j-cherino@hsb-boden.de` (Outlook/M365, erreichbar).
- Lokales `git clone --mirror`-Backup unter
  `~/KI-System/04_SYSTEM/backups/hsb-boden-mirror-20260702-172259.git`.
- Lokaler Arbeits-Remote in `~/KI-System/02_Projects/active/hsb-boden`
  umgestellt: `origin` = `HSBHexagon/hsb-boden`,
  `origin-old-cherinojoel-lang` = Alt-Repo (Backup-Remote).
- `CLOUDFLARE_ACCOUNT_ID` / `CLOUDFLARE_API_TOKEN` als GitHub-Actions-Secrets
  im neuen Repo neu gesetzt (nicht kopiert).
- Externe Verbindungen geprueft (beide Accounts): keine installierten
  GitHub Apps, keine autorisierten OAuth Apps, keine Repo-Webhooks — sauber,
  nichts zu migrieren.

### Cloudflare
- Account `Info@hsb-boden.de's Account` (ID `01dc37803d1c687b4f9d6249ec89f700`),
  einziges Mitglied `info@hsb-boden.de` als Super Administrator.
- Zone `hsb-boden.de` war bereits vor dieser Session als Zone im neuen
  Account angelegt (Status `pending`, NS beim Registrar noch nicht
  umgestellt: `ns5/ns6.kasserver.com`, Ziel-NS `bart`/`melody.ns.cloudflare.com`).
  DNS-Records darin bereits vorbereitet (Kopie des Live-Zustands):
  A `hsb-boden.de`/`www`/`*` -> `85.13.130.17` (proxied), MX/SPF/DMARC ->
  Microsoft 365, `autodiscover` CNAME -> `autodiscover.outlook.com`
  (aktuell **proxied**, siehe bekannte Stolperstelle oben — sollte vor
  Cutover auf DNS-only geprueft werden). DKIM-Selektoren noch nicht sichtbar
  gesetzt.
- Cloudflare Email Routing: `enabled: false` (erwartet, da Mail ueber M365
  laeuft, nicht ueber Cloudflare).
- Access/Zero Trust: nicht aktiviert.
- `workers.dev`-Subdomain `hsb-boden` frisch registriert (existierte vorher
  nicht).
- Beide Worker deployed und live verifiziert (HTTP 200):
  `hsb-boden-preview.hsb-boden.workers.dev`,
  `hsb-boden.hsb-boden.workers.dev` (Name-Workaround statt `--env production`,
  wie in `CICD_REMEDIATION_REPORT.md` dokumentiert).
- KV-Namespaces `hsb-boden-preview-session` / `hsb-boden-session` frisch im
  neuen Account provisioniert (waren im Alt-Account zwar vorhanden, aber in
  `wrangler.toml` nicht gebunden — kein Datenverlust, da ungenutzt).
- `LEAD_WEBHOOK_URL` gesetzt: bestehende, unveraenderte Apps-Script-Web-App-URL
  wiederverwendet (`AKfycbygp7VIA3...270O-Cu4ugm/exec`, Projekt „HSBBODEN",
  Sheet „HSB CRM Light", beide unter `cherinodiaz@outlook.com`-Google-Konto).
  Kein neues Deployment noetig.
- End-to-End-Lead-Test gruen: Testlead `WEB-20260702-180225` korrekt im Sheet
  angekommen, danach wieder entfernt.

### Verbindungen zwischen den Accounts (2026-07-02, zweite Runde)
- Klargestellt: Die einzige Verbindung GitHub<->Cloudflare lief schon immer
  ueber GitHub-Actions-Secrets (`CLOUDFLARE_API_TOKEN`/`CLOUDFLARE_ACCOUNT_ID`),
  keine native App-Kopplung noetig fuer den CI/CD-Pfad.
- **Cloudflare "Workers Builds" Git-Integration**: existierte im Alt-Setup
  tatsaechlich (Check `Workers Builds: hsb-boden-preview` lief auf PRs im
  Alt-Repo). Der User hat die Verbindung `HSBHexagon/hsb-boden` <-> neuer
  Cloudflare-Account manuell im Dashboard hergestellt (Git-Repository
  verbunden, Build-Befehl `npm run build`, Deploy-Befehl `npx wrangler
  deploy`, eigener API-Token "Workers Builds" automatisch erzeugt) -- das
  entspricht dem Alt-Zustand und bleibt bestehen.
- **Render / Vercel**: sind keine Hosting-Verbindungen des Projekts, sondern
  Jules-interne Hilfsintegrationen (Jules nutzt sie, um eigene
  PR-Preview-Fehler selbst zu reparieren). Sie sind an den persoenlichen
  Jules-/Google-Account gebunden (jules.google.com/settings/integrations),
  nicht repo- oder Cloudflare-Account-spezifisch -- nichts zu migrieren,
  laeuft bereits fuer beide Repos.
- **Jules (Google Labs) GitHub App**: war im Alt-Setup auf
  `cherinojoel-lang` installiert (Codebase `cherinojoel-lang/hsb-boden`
  aktiv in Jules). Ueber Jules' "Configure repo access" wurde die App jetzt
  auch auf `HSBHexagon` installiert, mit Zugriff auf "All repositories"
  (Read/Write auf actions, code, issues, pull requests, workflows) --
  deckt `HSBHexagon/hsb-boden` automatisch ab. Jules' Codebase-Liste zeigte
  das neue Repo im UI noch nicht sofort (Sync-Verzoegerung auf Google-Seite,
  kein Blocker) -- ggf. spaeter in jules.google.com pruefen, ob
  `HSBHexagon/hsb-boden` als Codebase waehlbar ist, sonst manuell dort
  hinzufuegen.
- GitHub Apps aktuell an `HSBHexagon` installiert: `Cloudflare Workers and
  Pages`, `Google Labs Jules`.

### Offen / bewusst nicht angefasst
- DNS-Cutover (NS-Umstellung beim Registrar) — wartet auf explizite Freigabe.
- `PUBLIC_LEAD_FORM_ENABLED` — erst nach Freigabe fuers echte Live-Formular.
- Der bei der Cloudflare-Token-Erstellung im Chat sichtbar gewordene
  API-Token (`cfat_...`) sollte nach Abschluss rotiert werden.
- GitHub-Ownership-Transfer bleibt pending bis das Postfach
  `info@hsb-boden.de` erreichbar ist (optional, da Collaborator-Zugriff
  bereits genuegt).
- DKIM-Selektor-Verifikation im neuen Cloudflare-DNS.
- `autodiscover`-Record von proxied auf DNS-only pruefen/umstellen.
