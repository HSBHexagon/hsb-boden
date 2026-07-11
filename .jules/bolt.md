## 2024-07-11 - [Optimize getPublicReferences and content iteration]
**Learning:** Generating the `getPublicReferences` output requires multiple mapping and filtering iterations. Also, some data can be pre-computed at build time since Astro is rendering static files. Specifically: `getPublicReferences()` gets executed multiple times when rendering the `LogoCloud` and the `ReferenceMapPreview`. However, caching the filtered data is explicitly discouraged by my memory context. I should investigate the `LogoCloud` component instead.
## 2024-07-11 - [Re-evaluate content optimizations vs code optimizations]
**Learning:** The prompt states I must NOT pre-compute and cache small static content arrays at the module scope as it is considered premature micro-optimization. The actual instruction is: 'Avoid pre-computing and caching small static content arrays (like mapping .filter() and .map()) at the module scope (e.g., in src/lib/content.ts). This is considered a premature micro-optimization that yields no measurable performance impact and introduces shared state mutation risks.'

Let's look for something else.

## 2024-07-11 - [LCP Image Optimization]
**Learning:** For critical above-the-fold images (LCP candidates), the prompt memory tells me to use `fetchpriority="high" loading="eager" decoding="async"` instead of `loading="lazy"` to prevent rendering delays. I should check if the images in `src/pages/branchen/[slug].astro` and `src/pages/leistungen/[slug].astro` are above the fold.
## 2024-07-11 - [LCP Image Optimization verified]
**Learning:** The images in `src/pages/branchen/[slug].astro` and `src/pages/leistungen/[slug].astro` are indeed LCP candidates (they appear right below the `PageHero`). They currently use `loading="lazy"`, which delays their loading. I should change this to `fetchpriority="high" loading="eager" decoding="async"`. Let's create a PR for this.
## 2024-07-11 - [Workers CI Build Failure Fix]
**Learning:** The prompt states: 'The project is deployed via Cloudflare Pages (with `output: "static"` in `astro.config.mjs`) and uses Pages Functions (e.g., `functions/api/lead.ts`) for APIs. To prevent legacy Cloudflare Workers native CI builds from failing due to the missing server entrypoint, `wrangler.toml` points its `main` entrypoint to a dummy worker stub (`src/dummy-worker.ts`).' The current `wrangler.toml` points to `@astrojs/cloudflare/entrypoints/server`. The CI failed on 'Workers Builds'.
**Action:** Let's check `astro.config.mjs` to see if the project is indeed static and then adjust `wrangler.toml`.
