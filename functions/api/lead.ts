import { leadEndpointSchema } from "../../src/lib/leadSchema";

// Cloudflare Pages Function (nicht mehr Astro-API-Route) — Portierung von
// src/pages/api/lead.ts im Rahmen der Migration output:"server" -> output:"static",
// da Pages-Deploy (statt Workers) keine Astro-SSR-Routen mehr baut.

interface Env {
  LEAD_WEBHOOK_URL?: string;
  LEAD_WEBHOOK_CONFIG?: string;
  RATE_LIMIT_KV?: KVNamespace;
}

const ALLOWED_ORIGINS = new Set(["https://hsb-boden.de", "https://www.hsb-boden.de"]);

const MAX_PAYLOAD_BYTES = 16 * 1024;
const IP_LIMIT = { max: 5, windowMs: 10 * 60 * 1000 };
const EMAIL_LIMIT = { max: 2, windowMs: 30 * 60 * 1000 };
const WEBHOOK_TIMEOUT_MS = 6000;
const MIN_WEBHOOK_TOKEN_LENGTH = 32;
const MAX_WEBHOOK_TOKEN_LENGTH = 512;

interface WebhookTarget {
  url: string;
  body: unknown;
  requireAcknowledgement: boolean;
}

// Distributed across Worker/Pages Function instances via Cloudflare KV — an
// in-memory Map resets per instance/cold start and does not enforce a limit
// reliably across a serverless fleet (see PR #42 / rate-limit-bypass fix).
let memoryIpHits = new Map<string, number[]>();
let memoryEmailHits = new Map<string, number[]>();

export function resetLeadRateLimiter() {
  memoryIpHits = new Map();
  memoryEmailHits = new Map();
}

function isRateLimitedMemory(key: string, store: Map<string, number[]>, limit: { max: number; windowMs: number }, now: number) {
  const hits = (store.get(key) ?? []).filter((t) => now - t < limit.windowMs);
  hits.push(now);
  store.set(key, hits);
  return hits.length > limit.max;
}

async function isRateLimited(
  kv: KVNamespace | undefined,
  memoryStore: Map<string, number[]>,
  key: string,
  limit: { max: number; windowMs: number },
  now: number,
) {
  if (!kv) return isRateLimitedMemory(key, memoryStore, limit, now);
  const raw = await kv.get(key, "json");
  const hits = ((raw as number[] | null) ?? []).filter((t) => now - t < limit.windowMs);
  hits.push(now);
  await kv.put(key, JSON.stringify(hits), { expirationTtl: Math.max(60, Math.ceil(limit.windowMs / 1000)) });
  return hits.length > limit.max;
}

function corsHeaders(origin: string | null) {
  const headers = new Headers({
    "Content-Type": "application/json",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Vary": "Origin",
  });
  if (origin && isAllowedOrigin(origin)) {
    headers.set("Access-Control-Allow-Origin", origin);
  }
  return headers;
}

function isAllowedOrigin(origin: string): boolean {
  if (ALLOWED_ORIGINS.has(origin)) return true;

  try {
    const url = new URL(origin);
    return (
      url.origin === origin &&
      url.protocol === "https:" &&
      /^[a-z0-9-]+\.hsb-boden\.pages\.dev$/.test(url.hostname)
    );
  } catch {
    return false;
  }
}

function jsonResponse(status: number, body: unknown, origin: string | null) {
  return new Response(JSON.stringify(body), { status, headers: corsHeaders(origin) });
}

function isAllowedAppsScriptUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return (
      url.protocol === "https:" &&
      url.hostname === "script.google.com" &&
      url.port === "" &&
      url.username === "" &&
      url.password === "" &&
      url.search === "" &&
      url.hash === "" &&
      /^\/macros\/s\/[A-Za-z0-9_-]+\/exec$/.test(url.pathname)
    );
  } catch {
    return false;
  }
}

function isStrongWebhookToken(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length >= MIN_WEBHOOK_TOKEN_LENGTH &&
    value.length <= MAX_WEBHOOK_TOKEN_LENGTH &&
    value.trim() === value &&
    !/[\u0000-\u001f\u007f]/.test(value)
  );
}

function parseAuthenticatedWebhookConfig(rawConfig: string): { url: string; token: string } {
  const parsed = JSON.parse(rawConfig) as unknown;
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("invalid_webhook_config");
  }

  const config = parsed as Record<string, unknown>;
  const keys = Object.keys(config);
  if (
    keys.length !== 2 ||
    !keys.includes("url") ||
    !keys.includes("token") ||
    typeof config.url !== "string" ||
    !isAllowedAppsScriptUrl(config.url) ||
    !isStrongWebhookToken(config.token)
  ) {
    throw new Error("invalid_webhook_config");
  }

  return { url: config.url, token: config.token };
}

function resolveWebhookTarget(env: Env, lead: unknown): WebhookTarget {
  if (env.LEAD_WEBHOOK_CONFIG !== undefined) {
    const config = parseAuthenticatedWebhookConfig(env.LEAD_WEBHOOK_CONFIG);
    return {
      url: config.url,
      body: { version: 1, authToken: config.token, lead },
      requireAcknowledgement: true,
    };
  }

  if (!env.LEAD_WEBHOOK_URL || !isAllowedAppsScriptUrl(env.LEAD_WEBHOOK_URL)) {
    throw new Error("webhook_not_configured");
  }

  return { url: env.LEAD_WEBHOOK_URL, body: lead, requireAcknowledgement: false };
}

class PayloadTooLargeError extends Error {}

async function readBodyWithLimit(request: Request, limitBytes: number): Promise<string> {
  const reader = request.body?.getReader();
  if (!reader) return "";
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
  const total = chunks.reduce((sum, c) => sum + c.byteLength, 0);
  const out = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    out.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return new TextDecoder().decode(out);
}

export const onRequestOptions: PagesFunction<Env> = async ({ request }) => {
  const origin = request.headers.get("Origin");
  const headers = corsHeaders(origin);
  headers.set("Access-Control-Allow-Methods", "POST, OPTIONS");
  headers.set("Access-Control-Allow-Headers", "Content-Type");
  return new Response(null, { status: 204, headers });
};

export const onRequestGet: PagesFunction<Env> = async ({ request }) => {
  const response = jsonResponse(405, { ok: false, error: "method_not_allowed" }, request.headers.get("Origin"));
  response.headers.set("Allow", "POST, OPTIONS");
  return response;
};
export const onRequestPut = onRequestGet;
export const onRequestDelete = onRequestGet;

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;
  const origin = request.headers.get("Origin");

  if (origin && !isAllowedOrigin(origin)) {
    return jsonResponse(403, { ok: false, error: "forbidden_origin" }, origin);
  }

  const declaredLength = Number(request.headers.get("Content-Length") ?? "0");
  if (declaredLength > MAX_PAYLOAD_BYTES) {
    return jsonResponse(413, { ok: false, error: "payload_too_large" }, origin);
  }

  let rawBody: string;
  try {
    rawBody = await readBodyWithLimit(request, MAX_PAYLOAD_BYTES);
  } catch (err) {
    if (err instanceof PayloadTooLargeError) {
      return jsonResponse(413, { ok: false, error: "payload_too_large" }, origin);
    }
    return jsonResponse(400, { ok: false, error: "invalid_body" }, origin);
  }

  let parsedBody: unknown;
  try {
    parsedBody = JSON.parse(rawBody);
  } catch {
    return jsonResponse(400, { ok: false, error: "invalid_json" }, origin);
  }

  const result = leadEndpointSchema.safeParse(parsedBody);
  if (!result.success) {
    return jsonResponse(400, { ok: false, error: "validation_failed" }, origin);
  }
  const lead = result.data;

  const now = Date.now();
  const ip = request.headers.get("CF-Connecting-IP") ?? "unknown";
  const ipLimited = await isRateLimited(env.RATE_LIMIT_KV, memoryIpHits, `ip:${ip}`, IP_LIMIT, now);
  const emailLimited = await isRateLimited(env.RATE_LIMIT_KV, memoryEmailHits, `email:${lead.email}`, EMAIL_LIMIT, now);
  if (ipLimited || emailLimited) {
    return jsonResponse(429, { ok: false, error: "rate_limited" }, origin);
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), WEBHOOK_TIMEOUT_MS);

  try {
    const target = resolveWebhookTarget(env, lead);
    const webhookResponse = await fetch(target.url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(target.body),
      signal: controller.signal,
    });
    if (!webhookResponse.ok) throw new Error("webhook_rejected");
    if (target.requireAcknowledgement) {
      const acknowledgement = await webhookResponse.json() as unknown;
      if (
        !acknowledgement ||
        typeof acknowledgement !== "object" ||
        Array.isArray(acknowledgement) ||
        Object.keys(acknowledgement).length !== 1 ||
        (acknowledgement as Record<string, unknown>).ok !== true
      ) {
        throw new Error("webhook_not_acknowledged");
      }
    }
  } catch {
    console.error(JSON.stringify({ ts: new Date(now).toISOString(), result: "error", code: "webhook_unreachable" }));
    return jsonResponse(502, { ok: false, error: "webhook_unreachable" }, origin);
  } finally {
    clearTimeout(timeout);
  }

  console.log(JSON.stringify({ ts: new Date(now).toISOString(), result: "ok", emailDomain: lead.email.split("@")[1] }));
  return jsonResponse(200, { ok: true }, origin);
};
