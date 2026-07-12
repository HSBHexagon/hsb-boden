import {
  handleGithubModelsPoc,
  type GithubModelsPocEnv,
} from "../../src/lib/githubModelsPoc";

interface Env extends GithubModelsPocEnv {}

function methodNotAllowed() {
  return new Response(
    JSON.stringify({ ok: false, error: "method_not_allowed" }),
    {
      status: 405,
      headers: {
        Allow: "POST",
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",
      },
    },
  );
}

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) =>
  handleGithubModelsPoc(request, env);

export const onRequestGet: PagesFunction<Env> = async () => methodNotAllowed();
export const onRequestPut = onRequestGet;
export const onRequestDelete = onRequestGet;
export const onRequestPatch = onRequestGet;
export const onRequestOptions = onRequestGet;
