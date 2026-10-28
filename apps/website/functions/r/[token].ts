interface KVLike {
  get(key: string): Promise<string | null>;
  put(key: string, value: string, options?: { expirationTtl?: number }): Promise<void>;
}

interface Env {
  EMAIL_CLICKS?: KVLike;
  CLICK_SECRET?: string;
}

const SEGMENTS: Record<string, string> = { a: "architekten", p: "produktion" };
const DEFAULT_SEGMENT = "produktion";

// Rechenzentren und Mail-Security-Scanner, die Links vorab abrufen.
const DATACENTER_ASNS = new Set([
  8075, 8068, 15169, 396982, 16509, 14618, 13335, 30238, 26211, 52129,
]);

const LEAD_PATTERN = /^[A-Za-z0-9_-]{1,64}$/;
const HMAC_PATTERN = /^[0-9a-f]{16}$/;
// Nur echte Klicks 180 Tage; Bot-/Invalid-Records kurz, damit Floods begrenzt bleiben.
const HUMAN_TTL_SECONDS = 180 * 24 * 3600;
const BOT_TTL_SECONDS = 7 * 24 * 3600;
const REPEAT_WINDOW_MS = 10_000;
const LAST_KEY_TTL_SECONDS = 60;

interface Context {
  request: Request;
  env: Env;
  waitUntil: (promise: Promise<unknown>) => void;
  params?: { token?: string | string[] };
}

async function hmac16(secret: string, leadId: string): Promise<string> {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = new Uint8Array(await crypto.subtle.sign("HMAC", key, enc.encode(leadId)));
  return Array.from(sig, (b) => b.toString(16).padStart(2, "0")).join("").slice(0, 16);
}

function constantTimeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function uaFamily(ua: string): string {
  const s = ua.toLowerCase();
  if (!s) return "none";
  if (/bot|crawler|spider|preview|scanner|python|curl|wget|go-http|java\//.test(s)) return "bot";
  if (s.includes("edg/")) return "edge";
  if (s.includes("firefox/")) return "firefox";
  if (s.includes("chrome/") || s.includes("crios/")) return "chrome";
  if (s.includes("safari/")) return "safari";
  if (s.includes("outlook")) return "outlook";
  return "other";
}

function redirect(segment: string): Response {
  const location =
    "/flyer/?utm_source=hsb_outreach&utm_medium=email" + `&utm_campaign=iboden_v2_${segment}`;
  return new Response(null, {
    status: 302,
    headers: {
      Location: location,
      "Cache-Control": "no-store",
      "X-Robots-Tag": "noindex",
    },
  });
}

function segmentOf(request: Request): string {
  const s = new URL(request.url).searchParams.get("s") ?? "";
  return SEGMENTS[s] ?? DEFAULT_SEGMENT;
}

async function record(context: Context, token: string): Promise<void> {
  const { request, env } = context;
  const kv = env.EMAIL_CLICKS;
  const secret = env.CLICK_SECRET;
  if (!kv || !secret) return;

  const now = Date.now();
  const reasons: string[] = [];

  const dot = token.lastIndexOf(".");
  const lead = dot > 0 ? token.slice(0, dot) : "";
  const mac = dot > 0 ? token.slice(dot + 1) : "";
  let valid = false;
  if (LEAD_PATTERN.test(lead) && HMAC_PATTERN.test(mac)) {
    valid = constantTimeEqual(await hmac16(secret, lead), mac);
  }
  if (!valid) reasons.push("invalid_hmac");

  const asn = Number((request as { cf?: { asn?: number } }).cf?.asn ?? 0) || null;
  if (asn !== null && DATACENTER_ASNS.has(asn)) reasons.push("datacenter_asn");
  if (!(request.headers.get("Accept-Language") || "").trim()) reasons.push("no_accept_language");
  const family = uaFamily(request.headers.get("User-Agent") || "");
  if (family === "bot" || family === "none") reasons.push("ua_bot");

  if (valid) {
    // Nicht atomar: KV hat kein compare-and-set, zwei gleichzeitige Erstklicks
    // koennen beide als "erster" durchgehen. Fuer die Bot-Heuristik akzeptiert.
    let repeat = false;
    const lastKey = `last:${lead}`;
    const last = Number(await kv.get(lastKey));
    if (Number.isFinite(last) && last > 0 && now - last < REPEAT_WINDOW_MS) {
      reasons.push("repeat_click_10s");
      repeat = true;
    }
    await kv.put(lastKey, String(now), { expirationTtl: LAST_KEY_TTL_SECONDS });
    // Wiederholungsklick: kein dauerhafter click:-Record, last: genuegt.
    if (repeat) return;
  }

  const value = JSON.stringify({
    class: reasons.length ? "bot" : "human",
    reasons,
    asn,
    ua_family: family,
    at: new Date(now).toISOString(),
  });
  // Ungueltige Token: grober Minuten-Key, ein Flood erzeugt max. einen Key je Minute.
  const key = valid ? `click:${lead}:${now}` : `click:invalid:${Math.floor(now / 60_000)}`;
  const ttl = reasons.length ? BOT_TTL_SECONDS : HUMAN_TTL_SECONDS;
  await kv.put(key, value, { expirationTtl: ttl });
}

function tokenParam(context: Context): string {
  const raw = context.params?.token;
  return (Array.isArray(raw) ? raw[0] : raw) ?? "";
}

export async function onRequestGet(context: Context): Promise<Response> {
  const token = tokenParam(context);
  context.waitUntil(
    record(context, token).catch((err) => console.error("click record failed:", err?.message ?? err)),
  );
  return redirect(segmentOf(context.request));
}

// Link-Scanner prüfen oft per HEAD: nur weiterleiten, nicht zählen.
export async function onRequestHead(context: Context): Promise<Response> {
  return redirect(segmentOf(context.request));
}
