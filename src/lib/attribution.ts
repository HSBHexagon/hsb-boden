// Session-bezogene Lead-Attribution: UTM-Parameter, externer Referrer und
// Landingpage werden beim Einstieg erfasst, in sessionStorage gehalten und
// beim Formular-Submit ins Lead-Payload übernommen. Alle Werte sind längen-
// und zeichenbegrenzt; Storage-Fehler dürfen den Versand nie verhindern.

export const ATTRIBUTION_STORAGE_KEY = "hsb-attribution-v1";

const UTM_MAX = 100;
const PATH_MAX = 200;
const UTM_KEYS = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"] as const;

export interface Attribution {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_term?: string;
  utm_content?: string;
  /** Nur externes Origin (Schema + Host), nie Pfad/Query — kein PII-Risiko. */
  referrer?: string;
  /** Pfad ohne Query/Hash der ersten Seite dieser Session. */
  landing_page?: string;
}

type ReadableStorage = Pick<Storage, "getItem">;
type WritableStorage = Pick<Storage, "getItem" | "setItem">;

/**
 * UTM-Werte strikt per Allowlist (Wortzeichen, Leerzeichen, `-_.~%+`); führende
 * `=+-@` werden entfernt (Spreadsheet-Formula-Injection). Läuft auch serverseitig
 * im Lead-Endpoint — die Vertrauensgrenze ist der Endpoint, nicht der Browser.
 */
export function sanitizeUtmValue(value: unknown): string | undefined {
  if (typeof value !== "string") return undefined;
  // Reihenfolge wichtig: erst trimmen, dann Formula-Präfixe strippen — sonst
  // schützt " +SUM(...)" das führende Plus hinter dem Leerzeichen.
  const cleaned = value
    .replace(/[^\w .~%+-]/g, "")
    .trim()
    .replace(/^[=+@-]+/, "")
    .trim()
    .slice(0, UTM_MAX);
  return cleaned.length > 0 ? cleaned : undefined;
}

/** Pfade/Origins: Steuerzeichen und HTML-relevante Zeichen entfernen, Länge kappen. */
function sanitizePathValue(value: unknown): string | undefined {
  if (typeof value !== "string") return undefined;
  // eslint-disable-next-line no-control-regex
  const cleaned = value.replace(/[\u0000-\u001F\u007F<>"'`\\]/g, "").trim().slice(0, PATH_MAX);
  return cleaned.length > 0 ? cleaned : undefined;
}

/** Seitenpfad ohne Query/Hash; alles, was nicht mit `/` beginnt, wird verworfen. */
export function sanitizePagePath(value: unknown): string | undefined {
  if (typeof value !== "string") return undefined;
  const withoutQuery = value.split(/[?#]/, 1)[0];
  const cleaned = sanitizePathValue(withoutQuery);
  if (!cleaned || !cleaned.startsWith("/")) return undefined;
  return cleaned;
}

/** Referrer auf ein externes http(s)-Origin reduzieren; sonst verwerfen. */
export function sanitizeReferrerOrigin(referrer: unknown, ownOrigin = ""): string | undefined {
  if (typeof referrer !== "string" || !referrer) return undefined;
  try {
    const url = new URL(referrer);
    if (ownOrigin && url.origin === ownOrigin) return undefined;
    if (url.protocol !== "https:" && url.protocol !== "http:") return undefined;
    return sanitizePathValue(url.origin);
  } catch {
    return undefined;
  }
}

export function captureAttribution(input: {
  search: string;
  referrer: string;
  pathname: string;
  origin: string;
}): Attribution {
  const params = new URLSearchParams(input.search);
  const attr: Attribution = {};
  for (const key of UTM_KEYS) {
    const value = sanitizeUtmValue(params.get(key));
    if (value) attr[key] = value;
  }
  const referrer = sanitizeReferrerOrigin(input.referrer, input.origin);
  if (referrer) attr.referrer = referrer;
  const landing = sanitizePagePath(input.pathname);
  if (landing) attr.landing_page = landing;
  return attr;
}

function hasCampaign(attr: Attribution): boolean {
  return Boolean(attr.utm_source || attr.utm_medium || attr.utm_campaign);
}

/** Re-sanitisiert gespeicherte Daten — Storage-Inhalt gilt als untrusted. */
function sanitizeStored(raw: unknown): Attribution | undefined {
  if (typeof raw !== "object" || raw === null) return undefined;
  const source = raw as Record<string, unknown>;
  const attr: Attribution = {};
  for (const key of UTM_KEYS) {
    const value = sanitizeUtmValue(source[key]);
    if (value) attr[key] = value;
  }
  const referrer = sanitizePathValue(source.referrer);
  if (referrer) attr.referrer = referrer;
  const landing = sanitizePagePath(source.landing_page);
  if (landing) attr.landing_page = landing;
  return attr;
}

export function loadAttribution(storage: ReadableStorage | null): Attribution | undefined {
  if (!storage) return undefined;
  try {
    const raw = storage.getItem(ATTRIBUTION_STORAGE_KEY);
    if (!raw) return undefined;
    return sanitizeStored(JSON.parse(raw));
  } catch {
    return undefined;
  }
}

/**
 * Erst-Attribution der Session speichern; eine neue gültige Kampagne
 * überschreibt die gespeicherte. Gibt die effektive Attribution zurück.
 */
export function updateSessionAttribution(
  storage: WritableStorage | null,
  current: Attribution,
): Attribution {
  const stored = loadAttribution(storage);
  const shouldStoreCurrent = hasCampaign(current) || !stored;
  const effective = shouldStoreCurrent ? current : stored;
  if (storage && shouldStoreCurrent) {
    try {
      storage.setItem(ATTRIBUTION_STORAGE_KEY, JSON.stringify(current));
    } catch {
      // sessionStorage blockiert (z. B. Privacy-Modus) — Attribution bleibt
      // für diese Seite nutzbar, geht nur beim Seitenwechsel verloren.
    }
  }
  return effective;
}

export function resolveChannel(attr: Attribution): "campaign" | "referral" | "direct" {
  if (hasCampaign(attr)) return "campaign";
  if (attr.referrer) return "referral";
  return "direct";
}

/** Attribution als flache, ausschließlich definierte String-Felder fürs Lead-Payload. */
export function buildLeadAttributionFields(
  attr: Attribution | undefined,
  formPath: string,
): Record<string, string> {
  const fields: Record<string, string> = {};
  const source = attr ?? {};
  for (const key of UTM_KEYS) {
    const value = source[key];
    if (value) fields[key] = value;
  }
  if (source.referrer) fields.referrer = source.referrer;
  if (source.landing_page) fields.landing_page = source.landing_page;
  const path = sanitizePagePath(formPath);
  if (path) fields.form_path = path;
  fields.attribution_channel = resolveChannel(source);
  return fields;
}
