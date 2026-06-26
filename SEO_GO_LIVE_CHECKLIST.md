# SEO_GO_LIVE_CHECKLIST — HSB-Boden

> Stand: 2026-06-26. Status je Punkt: ✅ vorhanden / ⬜ offen / ❓ zu prüfen. Keine Vermutung als Wahrheit.

## Technisches SEO
- [ ] `robots.txt` — ❓ als dynamische Route `src/pages/robots.txt.ts` vorhanden; Inhalt/Allow-Disallow prüfen.
- [ ] `sitemap.xml` — ❓ dynamische Route `src/pages/sitemap.xml.ts` vorhanden; Vollständigkeit prüfen.
- [ ] Canonical URLs — ❓ pro Seite prüfen (inkl. mehrsprachig de/en/fr/nl/pl/tr + hreflang).
- [ ] Meta Titles — ❓ je Seite prüfen.
- [ ] Meta Descriptions — ❓ je Seite prüfen.
- [ ] Open Graph / Twitter Cards — ✅ laut Docs OG-Images implementiert; verifizieren.
- [ ] Structured Data (JSON-LD) — ✅ laut Docs vorhanden (LocalBusiness u. a.); gegen echte Firmendaten prüfen.

## Tracking & Consent
- [ ] Google Search Console — ⬜ Property + Verifizierung (Domain-Stand offen).
- [ ] GA4 / GTM — ❓ Einbindung vorbereiten; keine produktive Aktivierung ohne ausdrückliche Freigabe.
- [ ] Cookie-/Consent — ✅ CookieConsent + LocalStorage laut Docs; DSGVO-Konformität final prüfen.

## Performance
- [ ] Core Web Vitals — ✅ lokales Lighthouse-Re-Audit 2026-06-26: Performance 95, Accessibility 100, Best Practices 100, SEO 100.
- [ ] Mobile — ✅ UX-Blocker behoben (iPhone SE 390px); re-verifizieren.

## Deploy / Environment
- [ ] Cloudflare Preview (`hsb-boden-preview`) — ✅ aktiv.
- [ ] Production (`hsb-boden`) — ✅ route-los vorbereitet; Live-Cutover weiter blockiert bis DNS/NS-Switch + explizite Freigabe.
- [ ] Custom Domain / Route (`hsb-boden.de`) — ⬜ blockiert bis externem DNS/NS-Switch.

## Go-Live-Freigabepunkte (Reihenfolge)
1. P0: Lead-Intake ist technisch vorbereitet; keine Versand- oder Automationsfreigabe ableiten.
2. P1: Flyer/Mail-Konsistenz + Rechtstext-Abnahme abgeschlossen halten.
3. P1: Re-Build + Re-Audit als technische Referenz aktuell halten.
4. P2: Search Console vorbereiten, GA4/GTM vorbereiten, Cookie-/Consent prüfen, Sitemap/robots/canonical prüfen, Structured Data prüfen, Cloudflare Preview validieren, Go-live-Checkliste vollständig machen.
5. P3: `hsb-boden.de` Cutover nur nach DNS/NS-Switch und expliziter Freigabe; Routes setzen, Live-Formular verifizieren, Tracking produktiv aktivieren. Kein n8n-Livebetrieb.

Dieser Schritt ist eine Planung. Keine Live-Aktivierung, kein Endpoint, kein Deploy, kein Push, kein Production-Cutover ohne ausdrückliche Freigabe.
