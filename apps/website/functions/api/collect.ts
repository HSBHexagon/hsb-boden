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

function isAllowedOrigin(origin: string | null): boolean {
  if (!origin) return false;
  if (ALLOWED_ORIGINS.has(origin)) return true;
  // Lokale Entwicklung und Cloudflare Pages Previews zulassen
  if (origin.startsWith("http://localhost:") || origin.endsWith(".hsb-boden.pages.dev")) {
    return true;
  }
  return false;
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

  const measurementId = env.GA4_MEASUREMENT_ID || "G-VC4BJBEFTV";
  const apiSecret = env.GA4_API_SECRET;

  if (apiSecret) {
    const gaEndpoint = `https://www.google-analytics.com/mp/collect?measurement_id=${measurementId}&api_secret=${apiSecret}`;
    const forwardPromise = fetch(gaEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        client_id: payload.client_id || "anonymous-edge-user",
        events: [
          {
            name: payload.event_name,
            params: {
              ...payload.params,
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
