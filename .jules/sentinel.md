## 2026-07-04 - [Add Global Security Headers]
**Vulnerability:** Application lacked globally applied security headers like Strict-Transport-Security, X-Frame-Options, X-Content-Type-Options, etc.
**Learning:** In Astro, security headers can be added globally using `astro:middleware` instead of manually applying them per route or at the web server layer exclusively. This ensures they apply consistently, including on static files and dynamic endpoints.
**Prevention:** Setup standard `src/middleware.ts` for all Astro projects running on Cloudflare Workers/Pages from the beginning to bake-in defense-in-depth automatically.
