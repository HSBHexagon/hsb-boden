import {
  handleGithubModelsPoc,
  type GithubModelsPocEnv,
} from "../../src/lib/githubModelsPoc";

interface Env extends GithubModelsPocEnv {}

export const onRequest: PagesFunction<Env> = async ({ request, env }) =>
  handleGithubModelsPoc(request, env);

export const onRequestPost = onRequest;
export const onRequestGet = onRequest;
export const onRequestPut = onRequest;
export const onRequestDelete = onRequest;
export const onRequestPatch = onRequest;
export const onRequestOptions = onRequest;
export const onRequestHead = onRequest;
