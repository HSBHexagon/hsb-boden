// Foto-Upload für die Reparatur-Ersteinschätzung.
// Die Bilder werden nicht gespeichert: Sie gehen direkt als Anhang per SMTP (.com-Postfach, All-Inkl)
// an das HSB-Postfach. So entsteht keine zweite Datenablage mit Personen- oder Betriebsfotos.

import { headerSafe, sendMail, type MailAttachment, type SocketFactory } from "./smtp";

export interface RepairPhotoEnv {
  RATE_LIMIT_KV?: KVNamespace;
  SMTP_HOST?: string;
  SMTP_PORT?: string;
  SMTP_USER?: string;
  SMTP_PASS?: string;
  SMTP_FROM?: string;
  REPAIR_PHOTO_TO?: string;
  /** "off" schaltet die Eingangsbestätigung an den Absender ab. */
  REPAIR_CONFIRMATION?: string;
}

/** Drei Wege zur Ersteinschätzung: Foto, Rückruf (kein Foto zur Hand) oder Termin vor Ort. */
export type RepairIntent = "photo" | "callback" | "visit";
const INTENTS: readonly RepairIntent[] = ["photo", "callback", "visit"];
const CALLBACK_WINDOWS: Record<string, string> = {
  vormittags: "vormittags (8–12 Uhr)",
  nachmittags: "nachmittags (12–16 Uhr)",
  egal: "jederzeit",
};
const PHONE_PATTERN = /^[+()0-9\s/-]{6,40}$/;

export const MAX_PHOTOS = 3;
export const MAX_PHOTO_BYTES = 4 * 1024 * 1024;
export const MAX_BODY_BYTES = MAX_PHOTOS * MAX_PHOTO_BYTES + 64 * 1024;
const IP_LIMIT = { max: 5, windowMs: 10 * 60 * 1000 };
const DEFAULT_TO = "info@hsb-boden.de";
const ALLOWED_ORIGINS = new Set(["https://hsb-boden.de", "https://www.hsb-boden.de"]);
const EMAIL_PATTERN = /^[^\s@<>()"',;:]+@[^\s@<>()"',;:]+\.[a-z]{2,}$/i;

type ImageKind = { contentType: string; extension: string };

/** Erkennt das Bildformat an den ersten Bytes, nicht am Dateinamen oder am vom Browser gemeldeten Typ. */
export function sniffImage(bytes: Uint8Array): ImageKind | null {
  if (bytes.length >= 3 && bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff) {
    return { contentType: "image/jpeg", extension: "jpg" };
  }
  if (bytes.length >= 8 && [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a].every((b, i) => bytes[i] === b)) {
    return { contentType: "image/png", extension: "png" };
  }
  const ascii = (from: number, to: number) => String.fromCharCode(...bytes.subarray(from, to));
  if (bytes.length >= 12 && ascii(0, 4) === "RIFF" && ascii(8, 12) === "WEBP") {
    return { contentType: "image/webp", extension: "webp" };
  }
  return null;
}

export function isAllowedOrigin(origin: string | null): boolean {
  if (!origin) return false;
  if (ALLOWED_ORIGINS.has(origin)) return true;
  try {
    const url = new URL(origin);
    return url.origin === origin && url.protocol === "https:" && /^[a-z0-9-]+\.hsb-boden\.pages\.dev$/.test(url.hostname);
  } catch {
    return false;
  }
}

function json(status: number, body: Record<string, unknown>, origin: string | null): Response {
  const headers = new Headers({
    "Content-Type": "application/json",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
  });
  if (origin && isAllowedOrigin(origin)) headers.set("Access-Control-Allow-Origin", origin);
  return new Response(JSON.stringify(body), { status, headers });
}

function text(form: FormData, name: string, max: number): string {
  const value = form.get(name);
  return typeof value === "string" ? value.trim().slice(0, max) : "";
}

async function isRateLimited(kv: KVNamespace, key: string, now: number): Promise<boolean> {
  const raw = await kv.get(key, "json");
  const hits = ((raw as number[] | null) ?? []).filter((t) => now - t < IP_LIMIT.windowMs);
  hits.push(now);
  await kv.put(key, JSON.stringify(hits), { expirationTtl: Math.ceil(IP_LIMIT.windowMs / 1000) });
  return hits.length > IP_LIMIT.max;
}

export interface RepairPhotoInquiry {
  intent: RepairIntent;
  company: string;
  name: string;
  email: string;
  phone: string;
  callbackWindow: string;
  location: string;
  blackout: string;
  message: string;
  page: string;
}

const INTENT_TITLES: Record<RepairIntent, { headline: string; subject: string; promise: string }> = {
  photo: {
    headline: "Neue Anfrage zur Ersteinschätzung einer Schadstelle per Foto (hsb-boden.de).",
    subject: "Foto Schadstelle",
    promise: "Zugesagt: kostenfreie Ersteinschätzung innerhalb eines Arbeitstags.",
  },
  callback: {
    headline: "RÜCKRUF erbeten: Schadstelle am Industrieboden, Kunde hat gerade kein Foto (hsb-boden.de).",
    subject: "Rückruf Schadstelle",
    promise: "Zugesagt: Rückruf innerhalb eines Arbeitstags im gewünschten Zeitfenster.",
  },
  visit: {
    headline: "TERMIN VOR ORT angefragt: Schadstelle am Industrieboden (hsb-boden.de).",
    subject: "Vor-Ort-Termin Schadstelle",
    promise: "Zugesagt: Rückmeldung mit Terminvorschlag innerhalb eines Arbeitstags.",
  },
};

export function buildMailText(inquiry: RepairPhotoInquiry, photoCount: number, receivedAt: Date): string {
  const title = INTENT_TITLES[inquiry.intent];
  return [
    title.headline,
    "",
    `Firma:        ${inquiry.company}`,
    `Ansprechpartner: ${inquiry.name}`,
    `E-Mail:       ${inquiry.email}`,
    `Telefon:      ${inquiry.phone || "nicht angegeben"}`,
    ...(inquiry.intent === "callback" ? [`Rückruf:      ${CALLBACK_WINDOWS[inquiry.callbackWindow] ?? "jederzeit"}`] : []),
    ...(inquiry.intent === "visit"
      ? [`Standort:     ${inquiry.location}`, `Sperrfenster: ${inquiry.blackout || "nicht angegeben"}`]
      : []),
    `Fotos:        ${photoCount ? `${photoCount} (im Anhang)` : "keine"}`,
    `Seite:        ${inquiry.page || "nicht übermittelt"}`,
    `Eingang:      ${receivedAt.toISOString()}`,
    "",
    "Beschreibung:",
    inquiry.message || "keine Beschreibung",
    "",
    title.promise,
    "Der Absender hat eine automatische Eingangsbestätigung erhalten.",
    "Antworten Sie direkt auf diese Mail, um den Absender zu erreichen.",
  ].join("\n");
}

/**
 * Eingangsbestätigung an den Absender. Bewusst ohne jede Nutzereingabe (auch nicht Name oder Firma),
 * damit das Formular nicht missbraucht werden kann, um fremden Text an beliebige Adressen zu schicken.
 */
export function buildConfirmationText(intent: RepairIntent): string {
  const next: Record<RepairIntent, string[]> = {
    photo: [
      "1. Wir sehen uns Ihr Foto und Ihre Angaben an.",
      "2. Innerhalb eines Arbeitstags erhalten Sie eine erste, kostenfreie Einschätzung per E-Mail oder Telefon.",
      "3. Falls nötig, schlagen wir einen Termin vor Ort vor.",
    ],
    callback: [
      "1. Wir rufen Sie innerhalb eines Arbeitstags im gewünschten Zeitfenster an.",
      "2. Im Gespräch klären wir Schadensbild, betroffene Fläche und mögliche Sperrzeiten.",
      "3. Fotos können Sie jederzeit nachreichen: einfach auf diese E-Mail antworten und das Bild anhängen.",
    ],
    visit: [
      "1. Wir melden uns innerhalb eines Arbeitstags mit einem Terminvorschlag.",
      "2. Vor Ort prüfen wir die Schadstelle und den Untergrund.",
      "3. Danach erhalten Sie unsere Empfehlung: gezielte Reparatur oder größere Instandsetzung.",
      "Fotos vorab helfen bei der Vorbereitung: einfach auf diese E-Mail antworten und das Bild anhängen.",
    ],
  };
  return [
    "Guten Tag,",
    "",
    "vielen Dank für Ihre Anfrage zur Schadstelle an Ihrem Industrieboden. Sie ist bei uns angekommen.",
    "",
    "So geht es weiter:",
    ...next[intent],
    "",
    "Haben Sie Rückfragen? Antworten Sie einfach auf diese E-Mail.",
    "",
    "Freundliche Grüße",
    "HSB Hexagon Säurebau GmbH",
    "https://www.hsb-boden.de",
    "",
    "Diese Nachricht wurde automatisch versendet, weil über hsb-boden.de eine Anfrage mit dieser",
    "E-Mail-Adresse gestellt wurde. Falls Sie das nicht waren, können Sie sie ignorieren.",
  ].join("\n");
}

export async function handleRepairPhoto(
  request: Request,
  env: RepairPhotoEnv,
  connect: SocketFactory,
  now = new Date(),
  waitUntil?: (promise: Promise<unknown>) => void,
): Promise<Response> {
  const origin = request.headers.get("Origin");
  if (!isAllowedOrigin(origin)) return json(403, { ok: false, error: "origin" }, origin);

  if (!env.SMTP_HOST || !env.SMTP_USER || !env.SMTP_PASS || !env.RATE_LIMIT_KV) {
    console.error("repair-photo: SMTP_* oder RATE_LIMIT_KV fehlt");
    return json(503, { ok: false, error: "not_configured" }, origin);
  }

  // Browser senden FormData immer mit Content-Length. Ohne diese Angabe (z. B. chunked) ließe sich
  // die Größenprüfung umgehen, bevor request.formData() den ganzen Körper einliest.
  const lengthHeader = request.headers.get("Content-Length");
  const declared = lengthHeader === null ? Number.NaN : Number(lengthHeader);
  if (!Number.isInteger(declared) || declared < 0) return json(411, { ok: false, error: "length_required" }, origin);
  if (declared > MAX_BODY_BYTES) return json(413, { ok: false, error: "too_large" }, origin);
  if (!(request.headers.get("Content-Type") ?? "").toLowerCase().startsWith("multipart/form-data")) {
    return json(415, { ok: false, error: "content_type" }, origin);
  }

  // Rate-Limit vor dem Einlesen des Körpers, damit Missbrauch keine Parse-Arbeit erzeugt.
  const ip = request.headers.get("CF-Connecting-IP") ?? "unknown";
  if (await isRateLimited(env.RATE_LIMIT_KV, `repair-photo:ip:${ip}`, now.getTime())) {
    return json(429, { ok: false, error: "rate_limited" }, origin);
  }

  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return json(400, { ok: false, error: "form" }, origin);
  }

  // Honeypot: echte Besucher sehen das Feld nicht. Bots bekommen eine neutrale Erfolgsmeldung.
  if (text(form, "website", 200)) return json(200, { ok: true }, origin);

  const rawIntent = text(form, "intent", 20);
  const inquiry: RepairPhotoInquiry = {
    intent: (INTENTS as readonly string[]).includes(rawIntent) ? (rawIntent as RepairIntent) : "photo",
    callbackWindow: Object.hasOwn(CALLBACK_WINDOWS, text(form, "callbackWindow", 20)) ? text(form, "callbackWindow", 20) : "egal",
    location: headerSafe(text(form, "location", 120)),
    blackout: headerSafe(text(form, "blackout", 120)),
    company: headerSafe(text(form, "company", 120)),
    name: headerSafe(text(form, "name", 80)),
    email: headerSafe(text(form, "email", 160)),
    phone: headerSafe(text(form, "phone", 40)),
    message: text(form, "message", 2000),
    page: headerSafe(text(form, "page", 200)),
  };

  const errors: string[] = [];
  if (inquiry.company.length < 2) errors.push("company");
  if (inquiry.name.length < 2) errors.push("name");
  if (!EMAIL_PATTERN.test(inquiry.email)) errors.push("email");
  if (form.get("privacyConsent") !== "on") errors.push("privacyConsent");
  if (inquiry.intent === "callback" && !PHONE_PATTERN.test(inquiry.phone)) errors.push("phone");
  if (inquiry.intent === "visit" && inquiry.location.length < 2) errors.push("location");

  const files = form.getAll("photos").filter((entry): entry is File => typeof entry !== "string" && entry.size > 0);
  // Nur der Foto-Weg verlangt ein Bild; Rückruf und Termin dürfen Fotos optional mitschicken.
  if (inquiry.intent === "photo" && files.length === 0) errors.push("photos");
  if (files.length > MAX_PHOTOS) errors.push("photos_count");
  if (errors.length) return json(422, { ok: false, error: "validation", fields: errors }, origin);

  const attachments: MailAttachment[] = [];
  for (const [index, file] of files.entries()) {
    if (file.size > MAX_PHOTO_BYTES) return json(413, { ok: false, error: "photo_too_large" }, origin);
    const data = new Uint8Array(await file.arrayBuffer());
    const kind = sniffImage(data);
    if (!kind) return json(422, { ok: false, error: "validation", fields: ["photos_type"] }, origin);
    attachments.push({ filename: `schadstelle-${index + 1}.${kind.extension}`, contentType: kind.contentType, data });
  }

  const from = env.SMTP_FROM || env.SMTP_USER;
  const to = env.REPAIR_PHOTO_TO || DEFAULT_TO;
  const smtp = {
    host: env.SMTP_HOST,
    port: Number(env.SMTP_PORT || "465"),
    user: env.SMTP_USER,
    pass: env.SMTP_PASS,
    heloName: from.split("@")[1] ?? "hsb-boden.com",
  };
  try {
    await sendMail(connect, smtp, {
      from: { email: from, name: "HSB Website" },
      to,
      replyTo: inquiry.email,
      subject: `${INTENT_TITLES[inquiry.intent].subject}: ${inquiry.company}`,
      text: buildMailText(inquiry, attachments.length, now),
      attachments,
    });
  } catch (err) {
    console.error("repair-photo: Versand fehlgeschlagen:", err instanceof Error ? err.message : err);
    return json(502, { ok: false, error: "delivery" }, origin);
  }

  // Die Anfrage ist zugestellt; die Bestätigung an den Absender ist Zusatz und darf den Erfolg nicht kippen.
  const confirmation = env.REPAIR_CONFIRMATION === "off"
    ? false
    : sendMail(connect, smtp, {
        from: { email: from, name: "HSB Hexagon Säurebau" },
        to: inquiry.email,
        replyTo: to,
        subject: "Ihre Anfrage zur Schadstelle ist bei HSB angekommen",
        text: buildConfirmationText(inquiry.intent),
      }).then(
        () => true,
        (err) => {
          console.error("repair-photo: Bestätigung fehlgeschlagen:", err instanceof Error ? err.message : err);
          return false;
        },
      );
  // confirmation=true heißt: eine Bestätigung ist unterwegs (im Hintergrund) bzw. wurde angenommen.
  let confirmationSent = false;
  if (confirmation && waitUntil) {
    waitUntil(confirmation);
    confirmationSent = true;
  } else if (confirmation) {
    confirmationSent = await confirmation;
  }

  return json(200, { ok: true, confirmation: confirmationSent }, origin);
}
