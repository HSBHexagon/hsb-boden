# HSB-Boden — Masterpiece SOTA 2026, Phase 1 + 2 (Umsetzungsbericht)

**Datum:** 2026-06-11
**Branch:** `claude/hsb-boden-architecture-o2479f` (PR #5, bleibt Draft)
**Basis:** `a591724` → Endstand `f300873` (7 Commits)
**Modell:** Claude Fable 5 (Lead-Engineer-Modus, executing-plans)

## Ziel
Die Seite von „sehr gut" auf „Weltklasse" heben durch (1) fachliches Content-Hardening und
(2) High-End-Motion-Polish (Emil-Kowalski-Stil), ohne Lighthouse-Regression, unter Anti-Slop-/KLINGER-Leitplanken.
Scope vom User: **Phase 1 + Phase 2** (Phase 3 „eigene SOTA-Ideen" bewusst abgewählt).

## Umgesetzt (7 Commits, je mit grünem Gate)

### Phase 1 — Content-Hardening (TDD)
| Commit | Inhalt |
|--------|--------|
| `f329a0d` | services.ts: Säureschutz → WHG-Konformität + Vinylester-Verfugung (pH 0–14); Keramik → Rüttelverlegetechnik DIN EN 14411 |
| `a171478` | industries.ts: Chemie → WHG § 62/63, ESD, Stoffbeständigkeit; Pharma → ISO 14644, GMP/FDA, porenfrei, CIP, Kreuzkontamination |
| `9660f2d` | articles.ts: Struktur `sections: string[]` → `{title, body?}` (rückwärtskompatibel, Schema in lib/content.ts mitmigriert) + freigegebene Fachprosa für Molkerei- und PU-Beton-Artikel; Template wissen/[slug].astro rendert `body` (ersetzt generischen Fülltext) |

Jede Anreicherung ist durch neue Assertions in `tests/content.test.ts` abgesichert (6 neue Tests, alle grün).

### Phase 2 — High-End-Motion (CSS-first, reduced-motion-safe)
| Commit | Inhalt |
|--------|--------|
| `46780fc` | Reveal-Fundament: `.reveal`-Utility (opacity+translateY, CLS-neutral) in global.css; EIN globaler IntersectionObserver in BaseLayout; `prefers-reduced-motion`-Block |
| `8e419d2` | Staggered Scroll-Reveal an Grids (ServiceGrid, IndustryGrid, Schmerzpunkte, ProofMedia) mit `--reveal-delay: i*60ms` |
| `b1192b6` | Taktiles `active:scale-[0.99]` auf klickbare Karten; Interaktion von der 560ms-Reveal-Transition entkoppelt (`:hover/:active` → 200ms) |
| `f300873` | Hero: Marken-Hexagon als dezente Eyebrow-Punktuation |

## Bewusste Abweichungen vom Plan (mit Begründung)
1. **Tailwind-Keyframes weggelassen** — `.reveal` nutzt `transition` (nicht `@keyframes`); CLS-sicherer, kein zusätzlicher Surface. YAGNI.
2. **Hero-Copy NICHT mit `.reveal` versehen** — der Hero-H1 ist das LCP-Element; `opacity:0` bis JS-Start würde LCP verzögern. Above-the-fold bleibt sofort sichtbar (Lighthouse-100-Schutz). Reveal nur below-the-fold.
3. **Hero-Inline-Icon → Eyebrow-Punktuation** — statt das Icon in die lange, 6-sprachige H1 zu zwängen (Umbruch-/Anti-Slop-Risiko), sitzt das Marken-Hexagon dezent vor dem Eyebrow. Markenkonsistent, risikofrei.
4. **„Argelith Hexalith®" nicht übernommen** — Marken-/Produktname aus dem Content-Dokument = Claim-Risiko; durch generisches „Feinsteinzeug-Platten" ersetzt. Argelith bleibt nur dort, wo es bereits als Herstellerinfo steht.
5. **Content-Strings auf reale Felder gemappt** — das Quelldokument nahm `technicalFocus`/`challenges` (industries) und Prosa-`sections` (articles) an, die real nicht existierten; gemappt auf `floorRequirements`/`typicalProblems` bzw. neue `{title, body}`-Struktur.
6. **ReferenceCard übersprungen** — nicht klickbar (`<article>` ohne Link), daher kein active/hover-Feedback sinnvoll.

## Verifikation (ADR-003)
- **Gate nach jedem Task:** `npm run check` 0 errors / 0 warnings / 1 hint (vorbestehend, ungenutzte `lang`-Prop) · `npm run test:run` 15/15 · `npm run build` ok.
- **Visuell (Prod-Build via wrangler dev :8788):** Playwright-Screenshots Desktop 1440 + Mobile 390 für `/` und Molkerei-Artikel → Layout intakt, Prosa sichtbar, Hexagon sichtbar. Artefakte in `docs/audit/screenshots/`.
- **Console:** 0 Errors gegen Prod-Build (Desktop + Mobile). (Die im Dev-Server gemeldeten React-`useState`-Errors sind ein Vite-/HMR-Artefakt aus `node_modules/.cache/.vite/deps`, in Produktion nicht vorhanden — gegen den Prod-Build verifiziert.)
- **CLS = 0** (PerformanceObserver, deterministisch, auch während Reveal-Trigger beim Scrollen).
- **Reveal-Mechanik:** 23 `.reveal`-Elemente, Observer triggert below-fold korrekt; CSS-Kaskade empirisch bestätigt (`.reveal` unlayered überstimmt Tailwind → `transition-duration` 0.56s im Ruhezustand, 0.2s bei `:hover/:active`).
- **reduced-motion:** CSS-Regel (`opacity/transform/transition` per `!important` neutralisiert) **und** JS-Observer-Branch per CSSOM gegen Prod-Build verifiziert.

## Offen / nicht in diesem Scope
- **Definitive Lighthouse-Score-Messung gegen die deployte Cloudflare-Preview** — lokal gegen `wrangler dev` nicht 1:1 mit der Audit-Baseline (100/99) vergleichbar; CLS=0 und das CSS-only-Design (GPU-composited opacity/transform, LCP-Hero geschützt) machen eine Perf-Regression praktisch aus. Echte Messung erfordert Deploy (out of scope).
- **chrome-devtools Lighthouse lokal blockiert** durch Chrome-Profil-Lock einer Parallelsession (`chrome-profile-stable`) — kein Defekt, Ressourcenkonflikt.
- Phase 3 (eigene SOTA-Ideen), Artikel-Volltext aller 5 Wissensartikel, Go-Live/DNS/SMTP/n8n/PR-Merge — bewusst außerhalb.
