# HSB Boden

Paralleler Astro/Cloudflare-Relaunch für `hsb-boden.de`.

## Ziel

Organische B2B-Leads für Industrieböden, Säureschutz, Keramik, PU-Beton, Entwässerung, Abdichtung, Sanierung und branchenspezifische Produktionsflächen.

Die bestehende WordPress-Seite bleibt bis zum finalen DNS-/Cloudflare-Switch live.

## Stack

- Astro
- React
- TypeScript
- Tailwind CSS
- Zod
- Vitest
- Cloudflare/Wrangler

## Befehle

```bash
npm run dev
npm run check
npm run test:run
npm run build
npm run deploy:dry-run
```

## Inhalt

Die Inhalte sind dateibasiert in `src/data` organisiert:

- `services.ts`
- `industries.ts`
- `references.ts`
- `articles.ts`
- `manufacturers.ts`

Referenzen haben Freigabelogik. Nicht freigegebene Referenzen werden anonymisiert und ohne Logo/exakte Adresse ausgegeben.

## Deployment

Preview-Ziel: Cloudflare-Pages-Preview des Projekts `hsb-boden` (Branch-URL je PR bzw. `preview`-Branch)

Live: `https://www.hsb-boden.de` (Cloudflare Pages, Production-Deploy nur via `deploy-production.yml`)

Vor Livegang:

1. WordPress-URLs prüfen.
2. Redirect-Plan finalisieren.
3. Google Search Console, GA4 und Google Unternehmensprofil verbinden.
4. Referenzfreigaben prüfen.
5. Build, Typecheck, Tests und Browser-Review ausführen.
