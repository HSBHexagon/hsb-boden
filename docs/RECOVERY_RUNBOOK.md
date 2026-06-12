# Recovery Runbook

If the Cloudflare Worker deployment fails or causes a site outage:

1.  **Identify Failure**: Check Cloudflare dashboard logs for the worker.
2.  **Revert to Previous Deployment**: Use the Cloudflare dashboard to rollback to the last known working deployment.
3.  **Local Reproduction**:
    *   Checkout the problematic commit locally.
    *   Run `npm run build` and `npx wrangler dev` to reproduce the issue locally.
4.  **Fix and Deploy**: Once fixed locally, deploy a new patch following the standard deployment runbook.
