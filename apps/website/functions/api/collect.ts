interface Env {
  GA4_MEASUREMENT_ID?: string;
  GA4_API_SECRET?: string;
}

interface TelemetryPayload {
  event_name: string;
  params?: Record<string, unknown>;
  client_id?: string;
}

const ALLOWED_ORIGINS = new Set([
  "https://hsb-boden.de",
  "https://www.hsb-boden.de",
]);

const MAX_PAYLOAD_BYTES = 16 * 1024;
const EVENT_NAME_PATTERN = /^[a-z0-9_]{1,64}$/;
const CLIENT_ID_PATTERN = /^[a-zA-Z0-9._-]{1,128}$/;
const PARAM_KEY_PATTERN = /^[a-z0-9_]{1,40}$/i;
const MAX_PARAMS = 25;
const MAX_PARAM_VALUE_LENGTH = 500;

function isAllowedOrigin(origin: string | null): boolean {
  if (!origin) return false;
  if (ALLOWED_ORIGINS.has(origin)) return true;

  try {
    const url = new URL(origin);
    if (url.origin !== origin) return false;

    // Lokale Entwicklung zulassen (http://localhost:<port> oder http://127.0.0.1:<port>)
    if (
      url.protocol === "http:" &&
      (url.hostname === "localhost" || url.hostname === "127.0.0.1")
    ) {
      return true;
    }

    // Cloudflare Pages Previews zulassen (https://<preview>.hsb-boden.pages.dev)
    if (
      url.protocol === "https:" &&
      /^[a-z0-9-]+\.hsb-boden\.pages\.dev$/.test(url.hostname)
    ) {
      return true;
    }
  } catch {
    return false;
  }

  return false;
}

function sanitizeParams(rawParams: unknown): Record<string, string | number | boolean> {
  if (!rawParams || typeof rawParams !== "object" || Array.isArray(rawParams)) {
    return Object.create(null);
  }

  const sanitized: Record<string, string | number | boolean> = Object.create(null);
  let count = 0;

  for (const [key, value] of Object.entries(rawParams)) {
    if (count >= MAX_PARAMS) break;
    if (typeof key !== "string" || !PARAM_KEY_PATTERN.test(key)) {
      continue;
    }

    if (typeof value === "string") {
      if (value.length <= MAX_PARAM_VALUE_LENGTH) {
        sanitized[key] = value;
        count++;
      }
    } else if (typeof value === "number") {
      if (Number.isFinite(value)) {
        sanitized[key] = value;
        count++;
      }
    } else if (typeof value === "boolean") {
      sanitized[key] = value;
      count++;
    }
  }

  return sanitized;
}

export async function onRequestPost(context: {
  request: Request;
  env: Env;
  waitUntil: (promise: Promise<unknown>) => void;
}): Promise<Response> {
  const { request, env, waitUntil } = context;
  const origin = request.headers.get("Origin");

  if (!isAllowedOrigin(origin)) {
    return new Response(JSON.stringify({ error: "forbidden_origin" }), {
      status: 403,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  }

  const contentLength = Number(request.headers.get("content-length") || "0");
  if (contentLength > MAX_PAYLOAD_BYTES) {
    return new Response(JSON.stringify({ error: "payload_too_large" }), {
      status: 413,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  }

  let payload: TelemetryPayload;
  try {
    payload = await request.json();
  } catch {
    return new Response(JSON.stringify({ error: "invalid_json" }), {
      status: 400,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  }

  if (!payload.event_name || !EVENT_NAME_PATTERN.test(payload.event_name)) {
    return new Response(JSON.stringify({ error: "invalid_or_missing_event_name" }), {
      status: 422,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  }

  const clientId =
    typeof payload.client_id === "string" && CLIENT_ID_PATTERN.test(payload.client_id)
      ? payload.client_id
      : "anonymous-edge-user";

  const sanitizedParams = sanitizeParams(payload.params);

  const measurementId = env.GA4_MEASUREMENT_ID || "G-VC4BJBEFTV";
  const apiSecret = env.GA4_API_SECRET;

  if (apiSecret) {
    const gaEndpoint = `https://www.google-analytics.com/mp/collect?measurement_id=${measurementId}&api_secret=${apiSecret}`;
    const forwardPromise = fetch(gaEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        client_id: clientId,
        events: [
          {
            name: payload.event_name,
            params: {
              ...sanitizedParams,
              engagement_time_msec: "100",
            },
          },
        ],
      }),
    }).catch((err) => console.error("GA4 edge proxy forward failed:", err));

    waitUntil(forwardPromise);
  }

  return new Response(null, {
    status: 204,
    headers: {
      "Cache-Control": "no-store",
      "Access-Control-Allow-Origin": origin || "https://www.hsb-boden.de",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
}

export async function onRequestOptions(context: { request: Request }): Promise<Response> {
  const origin = context.request.headers.get("Origin");
  if (!isAllowedOrigin(origin)) {
    return new Response(null, { status: 403 });
  }
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": origin || "https://www.hsb-boden.de",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Access-Control-Max-Age": "86400",
    },
  });
}
