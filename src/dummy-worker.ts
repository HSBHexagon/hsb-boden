/**
 * DUMMY WORKER
 *
 * This project has been migrated to Cloudflare Pages.
 * The legacy Cloudflare Workers native GitHub integration ("Workers Builds")
 * still triggers on pushes. Since `astro.config.mjs` is now `output: "static"`,
 * the old `@astrojs/cloudflare/entrypoints/server` is no longer generated,
 * causing the native Workers Build to fail.
 *
 * This dummy file provides a valid `main` entrypoint for `wrangler.toml`
 * so the legacy check run succeeds. The actual deployment is managed by Pages.
 */
export default {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  async fetch(_request: Request, _env: any, _ctx: any) {
    return new Response("Project migrated to Cloudflare Pages. This is a stub worker.", { status: 410 });
  }
};
