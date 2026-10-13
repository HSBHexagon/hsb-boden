interface Env {
  LEAD_WEBHOOK_URL?: string;
  LEAD_WEBHOOK_CONFIG?: string;
  RATE_LIMIT_KV?: KVNamespace;
}

interface OptOutPayload {
  email: string;
  lead_id?: string;
  token?: string;
  reason?: string;
}

const ALLOWED_ORIGINS = new Set(["https://hsb-boden.de", "https://www.hsb-boden.de"]);
const MAX_PAYLOAD_BYTES = 8 * 1024;
const EMAIL_RE = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;

function corsHeaders(origin: string | null): Headers {
  const headers = new Headers({
    "Content-Type": "application/json",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
  });
  if (origin && isAllowedOrigin(origin)) {
    headers.set("Access-Control-Allow-Origin", origin);
  } else {
    headers.set("Access-Control-Allow-Origin", "https://www.hsb-boden.de");
  }
  return headers;
}

function isAllowedOrigin(origin: string | null): boolean {
  if (!origin) return false;
  if (ALLOWED_ORIGINS.has(origin)) return true;
  try {
    const url = new URL(origin);
    if (url.protocol === "http:" && (url.hostname === "localhost" || url.hostname === "127.0.0.1")) {
      return true;
    }
    return (
      url.protocol === "https:" &&
      /^[a-z0-9-]+\.hsb-boden\.pages\.dev$/.test(url.hostname)
    );
  } catch {
    return false;
  }
}

function jsonResponse(status: number, body: unknown, origin: string | null): Response {
  return new Response(JSON.stringify(body), { status, headers: corsHeaders(origin) });
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

  let payload: OptOutPayload;
  try {
    payload = await request.json();
  } catch {
    return jsonResponse(400, { ok: false, error: "invalid_json" }, origin);
  }

  const email = String(payload.email || "").trim().toLowerCase();
  if (!email || !EMAIL_RE.test(email)) {
    return jsonResponse(422, { ok: false, error: "invalid_email" }, origin);
  }

  const leadId = payload.lead_id ? String(payload.lead_id).slice(0, 64) : undefined;
  const reason = payload.reason ? String(payload.reason).slice(0, 255) : undefined;
  const token = payload.token ? String(payload.token).slice(0, 64) : undefined;

  const timestamp = new Date().toISOString();
  const eventPayload = {
    action: "optout",
    email,
    lead_id: leadId,
    reason,
    token,
    timestamp,
  };

  // Webhook-Weiterleitung an Google Apps Script / CRM falls konfiguriert
  const webhookUrl = env.LEAD_WEBHOOK_URL;
  if (webhookUrl && typeof fetch === "function") {
    try {
      context.waitUntil(
        fetch(webhookUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(eventPayload),
        }).catch((err) => console.error("Opt-out webhook dispatch failed:", err))
      );
    } catch {
      // Non-blocking
    }
  }

  return jsonResponse(200, {
    ok: true,
    suppressed: true,
    lead_id: leadId,
    email,
    timestamp,
    message: "Lead erfolgreich im Sperr-System hinterlegt.",
  }, origin);
};
