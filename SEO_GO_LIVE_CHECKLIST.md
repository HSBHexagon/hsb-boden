# SEO_GO_LIVE_CHECKLIST — HSB-Boden

> Stand: 2026-06-14. Status je Punkt: ✅ vorhanden / ⬜ offen / ❓ zu prüfen. Keine Vermutung als Wahrheit.

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
- [ ] Core Web Vitals — ✅ Lighthouse 100/100 Desktop (Stand 2026-06-11); ❓ Re-Audit nach 697cce6.
- [ ] Mobile — ✅ UX-Blocker behoben (iPhone SE 390px); re-verifizieren.

## Deploy / Environment
- [ ] Cloudflare Preview (`hsb-boden-preview`) — ✅ aktiv.
- [ ] Production (`hsb-boden`) — ⬜ blockiert bis Lead-Pipeline live + WordPress-Cutover.
- [ ] Custom Domain / Route (`hsb-boden.de`) — ❓ Stand offen.

## Go-Live-Freigabepunkte (Reihenfolge)
1. P0: Lead-Pipeline nur planen und Freigabe vorbereiten (`PUBLIC_LEAD_ENDPOINT`, n8n Webhook, Test-Lead erst nach ausdrücklicher Freigabe).
2. P1: Flyer/Mail-Konsistenz + Rechtstext-Abnahme.
3. P1: Re-Build + Re-Audit.
4. P2: Search Console vorbereiten, GA4/GTM vorbereiten, Cookie-/Consent prüfen, Sitemap/robots/canonical prüfen, Structured Data prüfen, Cloudflare Preview validieren, Core Web Vitals prüfen, Go-live-Checkliste vollständig machen.
5. P3: `hsb-boden.de` Cutover, Production Route / Custom Domain aktivieren, Cloudflare Production Deployment, Tracking produktiv aktivieren, Live-Formular aktivieren, n8n produktiv anbinden, Push/Deploy/Go-live nur mit ausdrücklicher Freigabe.

Dieser Schritt ist eine Planung. Keine Live-Aktivierung, kein Endpoint, kein Deploy, kein Push, kein Production-Cutover ohne ausdrückliche Freigabe.
