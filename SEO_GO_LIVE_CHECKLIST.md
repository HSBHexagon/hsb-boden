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
- [ ] GA4 / GTM — ❓ Einbindung prüfen.
- [ ] Cookie-/Consent — ✅ CookieConsent + LocalStorage laut Docs; DSGVO-Konformität final prüfen.

## Performance
- [ ] Core Web Vitals — ✅ Lighthouse 100/100 Desktop (Stand 2026-06-11); ❓ Re-Audit nach 697cce6.
- [ ] Mobile — ✅ UX-Blocker behoben (iPhone SE 390px); re-verifizieren.

## Deploy / Environment
- [ ] Cloudflare Preview (`hsb-boden-preview`) — ✅ aktiv.
- [ ] Production (`hsb-boden`) — ⬜ blockiert bis Lead-Pipeline live + WordPress-Cutover.
- [ ] Custom Domain / Route (`hsb-boden.de`) — ❓ Stand offen.

## Go-Live-Freigabepunkte (Reihenfolge)
1. P0: Lead-Pipeline aktiv (`PUBLIC_LEAD_ENDPOINT` + Test-Lead).
2. P1: Flyer/Mail-Konsistenz + Rechtstext-Abnahme.
3. P1: Re-Build + Re-Audit.
4. P2: GSC/GA4/Consent final.
5. P2/P3: WordPress-Cutover-Plan + Production-Deploy (nur mit Freigabe).
