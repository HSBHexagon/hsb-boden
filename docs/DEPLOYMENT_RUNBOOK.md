# Deployment Runbook

1.  **Pre-flight Checks**:
    *   Ensure tests pass: `npm run test:run`
    *   Ensure type checks pass: `npm run check`
    *   Build project locally: `npm run build`
2.  **Staging/Preview Deployment**:
    *   Run `npm run deploy:dry-run` to validate the static build, compile the
        Pages Functions bundle, and confirm Cloudflare auth/project access
        (no deployment happens; `wrangler pages deploy` has no dry-run mode).
    *   Deploy to the non-production `preview` branch: `npm run deploy:preview`
3.  **Production Deployment**:
    *   Verify staging environment.
    *   Deploy to production: `npm run deploy:production`
