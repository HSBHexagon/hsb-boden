import { z } from "zod";

export const GITHUB_MODELS_ALLOWLIST = [
  "openai/gpt-5",
  "deepseek/DeepSeek-V3-0324",
  "meta/Llama-4-Scout-17B-16E-Instruct",
] as const;

export interface GithubModelsPocEnv {
  AI_POC_ENABLED?: string;
  AI_POC_ACCESS_TOKEN?: string;
  CF_ACCOUNT_ID?: string;
  CF_AI_GATEWAY_ID?: string;
  CF_AIG_TOKEN?: string;
}

type FetchLike = (
  input: RequestInfo | URL,
  init?: RequestInit,
) => Promise<Response>;

const MAX_REQUEST_BYTES = 16 * 1024;
const MAX_RESPONSE_BYTES = 256 * 1024;
const UPSTREAM_TIMEOUT_MS = 15_000;
const PROVIDER_SLUG = "github-models";

const requestSchema = z
  .object({
    model: z.enum(GITHUB_MODELS_ALLOWLIST),
    messages: z
      .array(
        z
          .object({
            role: z.enum(["system", "user", "assistant"]),
            content: z.string().min(1).max(4_000),
          })
          .strict(),
      )
      .min(1)
      .max(12),
    max_tokens: z.number().int().min(1).max(2_000).optional(),
    temperature: z.number().min(0).max(2).optional(),
    top_p: z.number().min(0).max(1).optional(),
  })
  .strict();

class PayloadTooLargeError extends Error {}

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}

async function readStreamWithLimit(
  body: ReadableStream<Uint8Array> | null,
  limitBytes: number,
): Promise<string> {
  if (!body) return "";

  const reader = body.getReader();
  const chunks: Uint8Array[] = [];
  let received = 0;

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;

    received += value.byteLength;
    if (received > limitBytes) {
      await reader.cancel();
      throw new PayloadTooLargeError();
    }
    chunks.push(value);
  }

  const output = new Uint8Array(received);
  let offset = 0;
  for (const chunk of chunks) {
    output.set(chunk, offset);
    offset += chunk.byteLength;
  }

  return new TextDecoder().decode(output);
}

function constantWorkEqual(left: string, right: string) {
  const leftBytes = new TextEncoder().encode(left);
  const rightBytes = new TextEncoder().encode(right);
  const length = Math.max(leftBytes.length, rightBytes.length);
  let mismatch = leftBytes.length ^ rightBytes.length;

  for (let index = 0; index < length; index += 1) {
    mismatch |= (leftBytes[index] ?? 0) ^ (rightBytes[index] ?? 0);
  }

  return mismatch === 0;
}

function extractBearerToken(request: Request) {
  const authorization = request.headers.get("Authorization") ?? "";
  const match = /^Bearer\s+(.+)$/i.exec(authorization);
  return match?.[1] ?? "";
}

function isSafePathSegment(value: string | undefined): value is string {
  return Boolean(value && /^[A-Za-z0-9_-]+$/.test(value));
}

function logResult(fields: {
  result: "ok" | "error";
  model?: string;
  durationMs: number;
  upstreamStatus?: number;
  code?: string;
}) {
  const payload = JSON.stringify({
    ts: new Date().toISOString(),
    component: "github_models_poc",
    ...fields,
  });

  if (fields.result === "error") {
    console.error(payload);
  } else {
    console.log(payload);
  }
}

export async function handleGithubModelsPoc(
  request: Request,
  env: GithubModelsPocEnv,
  fetchImpl: FetchLike = fetch,
): Promise<Response> {
  if (env.AI_POC_ENABLED !== "true") {
    return jsonResponse(404, { ok: false, error: "not_found" });
  }

  if (request.method !== "POST") {
    return jsonResponse(405, { ok: false, error: "method_not_allowed" });
  }

  if (!env.AI_POC_ACCESS_TOKEN) {
    return jsonResponse(503, { ok: false, error: "not_configured" });
  }

  const callerToken = extractBearerToken(request);
  if (!constantWorkEqual(callerToken, env.AI_POC_ACCESS_TOKEN)) {
    return jsonResponse(401, { ok: false, error: "unauthorized" });
  }

  const declaredLength = Number(request.headers.get("Content-Length") ?? "0");
  if (declaredLength > MAX_REQUEST_BYTES) {
    return jsonResponse(413, { ok: false, error: "payload_too_large" });
  }

  let rawBody: string;
  try {
    rawBody = await readStreamWithLimit(request.body, MAX_REQUEST_BYTES);
  } catch (error) {
    if (error instanceof PayloadTooLargeError) {
      return jsonResponse(413, { ok: false, error: "payload_too_large" });
    }
    return jsonResponse(400, { ok: false, error: "invalid_body" });
  }

  let input: unknown;
  try {
    input = JSON.parse(rawBody);
  } catch {
    return jsonResponse(400, { ok: false, error: "invalid_json" });
  }

  const parsed = requestSchema.safeParse(input);
  if (!parsed.success) {
    return jsonResponse(400, { ok: false, error: "validation_failed" });
  }

  if (
    !isSafePathSegment(env.CF_ACCOUNT_ID) ||
    !isSafePathSegment(env.CF_AI_GATEWAY_ID) ||
    !env.CF_AIG_TOKEN
  ) {
    return jsonResponse(503, { ok: false, error: "not_configured" });
  }

  const upstreamUrl =
    `https://gateway.ai.cloudflare.com/v1/${env.CF_ACCOUNT_ID}/` +
    `${env.CF_AI_GATEWAY_ID}/custom-${PROVIDER_SLUG}/inference/chat/completions`;
  const startedAt = Date.now();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), UPSTREAM_TIMEOUT_MS);

  try {
    const upstream = await fetchImpl(upstreamUrl, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "cf-aig-authorization": `Bearer ${env.CF_AIG_TOKEN}`,
        "cf-aig-cache-ttl": "0",
      },
      body: JSON.stringify(parsed.data),
      signal: controller.signal,
    });

    if (!upstream.ok) {
      logResult({
        result: "error",
        model: parsed.data.model,
        durationMs: Date.now() - startedAt,
        upstreamStatus: upstream.status,
        code: "upstream_unavailable",
      });
      return jsonResponse(502, { ok: false, error: "upstream_unavailable" });
    }

    let upstreamBody: string;
    try {
      upstreamBody = await readStreamWithLimit(
        upstream.body,
        MAX_RESPONSE_BYTES,
      );
    } catch {
      logResult({
        result: "error",
        model: parsed.data.model,
        durationMs: Date.now() - startedAt,
        upstreamStatus: upstream.status,
        code: "invalid_upstream_response",
      });
      return jsonResponse(502, {
        ok: false,
        error: "invalid_upstream_response",
      });
    }

    let result: unknown;
    try {
      result = JSON.parse(upstreamBody);
    } catch {
      logResult({
        result: "error",
        model: parsed.data.model,
        durationMs: Date.now() - startedAt,
        upstreamStatus: upstream.status,
        code: "invalid_upstream_response",
      });
      return jsonResponse(502, {
        ok: false,
        error: "invalid_upstream_response",
      });
    }

    logResult({
      result: "ok",
      model: parsed.data.model,
      durationMs: Date.now() - startedAt,
      upstreamStatus: upstream.status,
    });
    return jsonResponse(200, { ok: true, result });
  } catch {
    logResult({
      result: "error",
      model: parsed.data.model,
      durationMs: Date.now() - startedAt,
      code: "upstream_unavailable",
    });
    return jsonResponse(502, { ok: false, error: "upstream_unavailable" });
  } finally {
    clearTimeout(timeout);
  }
}
