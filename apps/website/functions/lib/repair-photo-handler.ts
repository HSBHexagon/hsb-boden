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
}

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
  company: string;
  name: string;
  email: string;
  phone: string;
  message: string;
  page: string;
}

export function buildMailText(inquiry: RepairPhotoInquiry, photoCount: number, receivedAt: Date): string {
  return [
    "Neue Anfrage zur Ersteinschätzung einer Schadstelle (Foto-Upload auf hsb-boden.de).",
    "",
    `Firma:        ${inquiry.company}`,
    `Ansprechpartner: ${inquiry.name}`,
    `E-Mail:       ${inquiry.email}`,
    `Telefon:      ${inquiry.phone || "nicht angegeben"}`,
    `Fotos:        ${photoCount} (im Anhang)`,
    `Seite:        ${inquiry.page || "nicht übermittelt"}`,
    `Eingang:      ${receivedAt.toISOString()}`,
    "",
    "Beschreibung:",
    inquiry.message || "keine Beschreibung",
    "",
    "Zugesagt ist eine kostenfreie Ersteinschätzung innerhalb eines Arbeitstags.",
    "Antworten Sie direkt auf diese Mail, um den Absender zu erreichen.",
  ].join("\n");
}

export async function handleRepairPhoto(
  request: Request,
  env: RepairPhotoEnv,
  connect: SocketFactory,
  now = new Date(),
): Promise<Response> {
  const origin = request.headers.get("Origin");
  if (!isAllowedOrigin(origin)) return json(403, { ok: false, error: "origin" }, origin);

  if (!env.SMTP_HOST || !env.SMTP_USER || !env.SMTP_PASS || !env.RATE_LIMIT_KV) {
    console.error("repair-photo: SMTP_* oder RATE_LIMIT_KV fehlt");
    return json(503, { ok: false, error: "not_configured" }, origin);
  }

  const declared = Number(request.headers.get("Content-Length") ?? "0");
  if (declared > MAX_BODY_BYTES) return json(413, { ok: false, error: "too_large" }, origin);
  if (!(request.headers.get("Content-Type") ?? "").toLowerCase().startsWith("multipart/form-data")) {
    return json(415, { ok: false, error: "content_type" }, origin);
  }

  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return json(400, { ok: false, error: "form" }, origin);
  }

  // Honeypot: echte Besucher sehen das Feld nicht. Bots bekommen eine neutrale Erfolgsmeldung.
  if (text(form, "website", 200)) return json(200, { ok: true }, origin);

  const inquiry: RepairPhotoInquiry = {
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

  const files = form.getAll("photos").filter((entry): entry is File => typeof entry !== "string" && entry.size > 0);
  if (files.length === 0) errors.push("photos");
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

  const ip = request.headers.get("CF-Connecting-IP") ?? "unknown";
  if (await isRateLimited(env.RATE_LIMIT_KV, `repair-photo:ip:${ip}`, now.getTime())) {
    return json(429, { ok: false, error: "rate_limited" }, origin);
  }

  const from = env.SMTP_FROM || env.SMTP_USER;
  try {
    await sendMail(
      connect,
      {
        host: env.SMTP_HOST,
        port: Number(env.SMTP_PORT || "465"),
        user: env.SMTP_USER,
        pass: env.SMTP_PASS,
        heloName: from.split("@")[1] ?? "hsb-boden.com",
      },
      {
        from: { email: from, name: "HSB Website" },
        to: env.REPAIR_PHOTO_TO || DEFAULT_TO,
        replyTo: inquiry.email,
        subject: `Foto Schadstelle: ${inquiry.company}`,
        text: buildMailText(inquiry, attachments.length, now),
        attachments,
      },
    );
  } catch (err) {
    console.error("repair-photo: Versand fehlgeschlagen:", err instanceof Error ? err.message : err);
    return json(502, { ok: false, error: "delivery" }, origin);
  }

  return json(200, { ok: true }, origin);
}
