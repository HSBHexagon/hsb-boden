/// <reference path="../.astro/types.d.ts" />
/// <reference types="astro/client" />

declare module "cloudflare:workers" {
  interface Env {
    LEAD_WEBHOOK_URL?: string;
  }
}
