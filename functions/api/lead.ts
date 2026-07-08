import { leadEndpointSchema } from "../../src/lib/leadSchema";

// Cloudflare Pages Function (nicht mehr Astro-API-Route) — Portierung von
// src/pages/api/lead.ts im Rahmen der Migration output:"server" -> output:"static",
// da Pages-Deploy (statt Workers) keine Astro-SSR-Routen mehr baut.

interface Env {
  LEAD_WEBHOOK_URL?: string;
}

const ALLOWED_ORIGINS = new Set(["https://hsb-boden.de", "https://www.hsb-boden.de"]);

const MAX_PAYLOAD_BYTES = 16 * 1024;
const IP_LIMIT = { max: 5, windowMs: 10 * 60 * 1000 };
const EMAIL_LIMIT = { max: 2, windowMs: 30 * 60 * 1000 };
const WEBHOOK_TIMEOUT_MS = 6000;

// In-memory pro Worker-Instanz, siehe P0B_SECRET_REQUIREMENTS.md.
let ipHits = new Map<string, number[]>();
let emailHits = new Map<string, number[]>();

export function resetLeadRateLimiter() {
  ipHits = new Map();
  emailHits = new Map();
}

function isRateLimited(key: string, store: Map<string, number[]>, limit: { max: number; windowMs: number }, now: number) {
  const hits = (store.get(key) ?? []).filter((t) => now - t < limit.windowMs);
  hits.push(now);
  store.set(key, hits);
  return hits.length > limit.max;
}

function corsHeaders(origin: string | null) {
  const headers = new Headers({ "Content-Type": "application/json" });
  if (origin && ALLOWED_ORIGINS.has(origin)) {
    headers.set("Access-Control-Allow-Origin", origin);
  }
  return headers;
}

function jsonResponse(status: number, body: unknown, origin: string | null) {
  return new Response(JSON.stringify(body), { status, headers: corsHeaders(origin) });
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

export const onRequestGet: PagesFunction<Env> = async ({ request }) =>
  jsonResponse(405, { ok: false, error: "method_not_allowed" }, request.headers.get("Origin"));
export const onRequestPut = onRequestGet;
export const onRequestDelete = onRequestGet;

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;
  const origin = request.headers.get("Origin");

  if (origin && !ALLOWED_ORIGINS.has(origin)) {
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
  if (isRateLimited(ip, ipHits, IP_LIMIT, now) || isRateLimited(lead.email, emailHits, EMAIL_LIMIT, now)) {
    return jsonResponse(429, { ok: false, error: "rate_limited" }, origin);
  }

  const webhookUrl = env.LEAD_WEBHOOK_URL;

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), WEBHOOK_TIMEOUT_MS);
    if (!webhookUrl) throw new Error("webhook_not_configured");
    await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(lead),
      signal: controller.signal,
    });
    clearTimeout(timeout);
  } catch {
    console.error(JSON.stringify({ ts: new Date(now).toISOString(), result: "error", code: "webhook_unreachable" }));
    return jsonResponse(502, { ok: false, error: "webhook_unreachable" }, origin);
  }

  console.log(JSON.stringify({ ts: new Date(now).toISOString(), result: "ok", emailDomain: lead.email.split("@")[1] }));
  return jsonResponse(200, { ok: true }, origin);
};
