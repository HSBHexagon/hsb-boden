# Performance Analysis: Eager Loading for LCP Images

The frontend pages for industries (`/branchen/[slug]`) and services (`/leistungen/[slug]`) display an image directly below the page hero component (the title block). Because this image appears at the top of the viewport when the page initially loads, it is highly likely to be the Largest Contentful Paint (LCP) element on those pages.

Currently, these images are rendered with `loading="lazy"`.

```html
<img src={industryImage.src} alt={industryImage.alt} class="max-h-[480px] w-full object-cover object-center" loading="lazy" width="1200" height="480" />
```

**Problem:** Lazy-loading images that are present in the initial viewport delays their loading because the browser waits until layout is complete and Intersection Observer or native lazy-loading heuristics kick in to start the image request. This negatively impacts the LCP (Largest Contentful Paint) core web vital metric.

**Solution:** Remove `loading="lazy"` and add `fetchpriority="high" loading="eager" decoding="async"` to these above-the-fold hero images.

The prompt instructions specifically mention:
> For critical above-the-fold images (LCP candidates), use `fetchpriority="high" loading="eager" decoding="async"` instead of `loading="lazy"` to prevent rendering delays.
> In this codebase's layout, images injected immediately below the textual `PageHero` components (e.g., on content routes like service and industry pages) are LCP candidates and must be configured with eager loading attributes (`fetchpriority="high" loading="eager" decoding="async"`) instead of lazy loading.

Let's execute this fix for the two identified files:
1. `src/pages/leistungen/[slug].astro`
2. `src/pages/branchen/[slug].astro`
