# Deployment Runbook

1.  **Pre-flight Checks**:
    *   Ensure tests pass: `npm run test:run`
    *   Ensure type checks pass: `npm run check`
    *   Build project locally: `npm run build`
2.  **Staging/Preview Deployment**:
    *   Run `npm run deploy:dry-run` to preview changes.
    *   Deploy to preview environment: `npm run deploy`
3.  **Production Deployment**:
    *   Verify staging environment.
    *   Deploy to production: `npm run deploy:production`
