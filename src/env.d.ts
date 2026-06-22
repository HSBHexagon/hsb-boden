/// <reference path="../.astro/types.d.ts" />
/// <reference types="astro/client" />

import type { Runtime } from "@astrojs/cloudflare";

type CloudflareEnv = {
  N8N_WEBHOOK_URL?: string;
};

declare global {
  namespace App {
    interface Locals extends Runtime<CloudflareEnv> {}
  }
}
