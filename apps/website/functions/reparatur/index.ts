// Mail-Link /reparatur/: anonyme Klickzählung je Tag, dann 302 auf die Reparatur-Seite mit Kampagnen-UTM.
// Gespeichert werden nur Tag und Klasse (human/bot) im Schlüssel – keine IP, kein Empfänger, kein Cookie.
// GA4 sieht nur Besucher mit Einwilligung; diese Zählung deckt alle Klicks ab.

interface KVLike {
  put(key: string, value: string, options?: { expirationTtl?: number }): Promise<void>;
}

interface Env {
  EMAIL_CLICKS?: KVLike;
}

interface Context {
  request: Request;
  env: Env;
  waitUntil: (promise: Promise<unknown>) => void;
}

export const REPAIR_TARGET =
  "/leistungen/boden-reparatur-instandsetzung/?utm_source=email&utm_medium=outreach&utm_campaign=reparatur-2026-11#reparaturanfrage";

// Rechenzentren und Mail-Security-Scanner, die Links vorab abrufen (wie /r/[token]).
const DATACENTER_ASNS = new Set([8075, 8068, 15169, 396982, 16509, 14618, 13335, 30238, 26211, 52129]);
const TTL_SECONDS = 180 * 24 * 3600;

export function classify(request: Request): "human" | "bot" {
  const asn = Number((request as { cf?: { asn?: number } }).cf?.asn ?? 0);
  const ua = (request.headers.get("User-Agent") || "").toLowerCase();
  if (asn && DATACENTER_ASNS.has(asn)) return "bot";
  if (!(request.headers.get("Accept-Language") || "").trim()) return "bot";
  if (!ua || /bot|crawler|spider|preview|scanner|python|curl|wget|go-http|java\//.test(ua)) return "bot";
  return "human";
}

function redirect(): Response {
  return new Response(null, {
    status: 302,
    headers: { Location: REPAIR_TARGET, "Cache-Control": "no-store", "X-Robots-Tag": "noindex" },
  });
}

export async function onRequestGet(context: Context): Promise<Response> {
  const kv = context.env.EMAIL_CLICKS;
  if (kv) {
    const now = Date.now();
    const day = new Date(now).toISOString().slice(0, 10);
    const key = `agg:reparatur:${day}:${classify(context.request)}:${now}-${Math.random().toString(36).slice(2, 8)}`;
    context.waitUntil(
      kv.put(key, "1", { expirationTtl: TTL_SECONDS }).catch((err) => console.error("repair click failed:", err?.message ?? err)),
    );
  }
  return redirect();
}

// Link-Scanner prüfen oft per HEAD: nur weiterleiten, nicht zählen.
export async function onRequestHead(): Promise<Response> {
  return redirect();
}
