# Release Checklist

- [ ] All Vitest tests pass (`npm run test:run`).
- [ ] TypeScript compiler passes (`npm run check`).
- [ ] Astro build is successful (`npm run build`).
- [ ] Dry-run deployment is clean (`npm run deploy:dry-run`).
- [ ] Manual visual verification of critical paths (e.g., Lead Form submission).
- [ ] Webhook URL (`PUBLIC_LEAD_ENDPOINT`) is correctly configured for production.
- [ ] Legal texts (Impressum, Datenschutz) are confirmed up-to-date.
