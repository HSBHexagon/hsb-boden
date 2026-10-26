# Ökosystem-Optimierung: Index der vier Pläne

Stand 2026-10-26. Auftrag: GitHub, Cloudflare, Google und Design der Website besser nutzen (Optimierungen, Installationen, Erweiterungen), mit belegten Quellen. Die vier Bereiche sind unabhängig lieferbar, deshalb gibt es vier Pläne statt eines.

| Plan | Datei | Tasks | Berührt Website-Code? |
|---|---|---|---|
| GitHub | `2026-10-26-github-oekosystem.md` | 5 | nein (`.github/`, `scripts/`, `docs/`) |
| Cloudflare | `2026-10-26-cloudflare-edge.md` | 5 | ja (`functions/`, `_headers`, `astro.config.mjs`) |
| Google | `2026-10-26-google-messung-seo.md` | 5 | ja (`analytics.ts`, evtl. Layout/Consent) |
| Design | `2026-10-26-design-system.md` | 4 | ja (`tailwind.config.mjs`, `global.css`, Formulare) |

## Empfohlene Reihenfolge

1. **GitHub 1 bis 4**: ohne Website-Code, sofort wirksam (Dependabot sieht heute weder `apps/website` noch `apps/sales-os`).
2. **Cloudflare 1** (nur Doku) und **Design 1** (Feldkontrast): kleine, klar belegte Korrekturen.
3. **Google 1** (Consent-Default) und **Google 2** (Origins messen).
4. **Cloudflare 2** (Turnstile samt CSP-Einträgen), dann **Cloudflare 4** (CSP ohne `unsafe-inline`; braucht Google 2 und Cloudflare 2).
5. Rest nach Owner-Entscheidungen: GitHub 5, Cloudflare 3 und 5, Google 3 bis 5, Design 2 bis 4.

Abhängigkeiten: Cloudflare 4 liest das Ergebnis von Google 2; Design 2 baut auf dem Token aus Design 1 auf; Cloudflare 3 braucht eine aktive Zone (Cloudflare 1, Step 2).

## Owner-Aktionen (nicht aus dieser Session ausführbar)

- GitHub: Ruleset „Protect Main“, Code-Owner-Pflicht, Security-Settings, App-Inventur, CircleCI behalten oder trennen.
- Cloudflare: Turnstile-Widget, Secret `TURNSTILE_SECRET`, WAF-Regel, Zonenstatus und Nameserver-Antwort, Pages vs. Workers.
- Google: DebugView und Key Event, Search-Console-Property, Sitemap, GA4/GSC-Verknüpfung.
- Rechtlich zu klären (keine Rechtsberatung in diesen Plänen): Cloudflare-Beacon ohne Einwilligung, Datenschutzerklärung nennt „Real Cookie Banner“.
- Lokal beim Owner: `~/KI-System`-Handoff aus `CLAUDE.md` (im Cloud-Container nicht vorhanden).

## Datenquellen und Verfügbarkeit (geprüft am 2026-10-26)

| Quelle | Status |
|---|---|
| Cloudflare-Dokumentation (Doku-Suche) | verfügbar, für Cloudflare-Aussagen genutzt |
| Google Tag Platform Doku (`developers.google.com`) | verfügbar, für Consent-Aussagen genutzt |
| GitHub Docs (`docs.github.com`) | verfügbar; die Dependabot-Referenz wurde nur zu etwa 55 % gelesen |
| Context7 (Astro, Tailwind) | verfügbar |
| W3C WCAG 2.2 | verfügbar |
| Ahrefs | nicht nutzbar: „Insufficient plan“ |
| Semrush | nicht nutzbar: keine API-Einheiten (Hinweis auf https://www.semrush.com/mcp-access) |
| GA4-/Search-Console-Konnektoren | nicht geprüft, Zugriff auf die Konten liegt beim Owner |

Keyword-, Ranking- und Wettbewerbsanalysen sind deshalb **nicht** Teil der Pläne; sie brauchen einen Zugang, der funktioniert.

## Hinweis zum Branch

Diese Pläne liegen im Branch `chore/circleci-config-vkr6iu` und damit im Draft-PR #485 (CircleCI). Sie sind nur Dokumente unter `docs/superpowers/plans/`. Wenn der PR auf CircleCI beschränkt bleiben soll, können die fünf Dateien in einen eigenen PR verschoben werden.
