/// <reference path="../.astro/types.d.ts" />
/// <reference types="astro/client" />

declare module "cloudflare:workers" {
  interface Env {
    LEAD_WEBHOOK_URL?: string;
    LEAD_WEBHOOK_CONFIG?: string;
  }
}
