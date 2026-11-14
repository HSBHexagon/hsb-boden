// @vitest-environment node
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { buildMime, dotStuff, headerSafe, sendMail, type SmtpSocket } from "../functions/lib/smtp";
import { buildConfirmationText, handleRepairPhoto, MAX_PHOTOS, sniffImage, type RepairPhotoEnv } from "../functions/lib/repair-photo-handler";

it("gibt bei fehlerhafter Bilddekodierung niemals das metadatenhaltige Original weiter", () => {
  const source = readFileSync(new URL("../src/lib/repairPhotoImage.ts", import.meta.url), "utf8");
  expect(source).toContain('canvas.toBlob(resolve, "image/jpeg", 0.82)');
  expect(source).not.toMatch(/\breturn\s+file\s*;/);
});

const JPEG = new Uint8Array([0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10, 0x4a, 0x46, 0x49, 0x46, 0x00, 0x01]);
const PNG = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0, 0, 0, 0]);

/** Nachgebauter SMTP-Server: beantwortet jede Zeile nach Skript und protokolliert, was ankommt. */
function fakeSmtp(overrides: Record<string, string> = {}) {
  const received: string[] = [];
  let closed = false;
  let inData = false;
  let dataBuffer = "";
  let controller!: ReadableStreamDefaultController<Uint8Array>;
  const enc = new TextEncoder();
  const dec = new TextDecoder();
  const reply = (line: string) => controller.enqueue(enc.encode(`${line}\r\n`));
  const answer = (key: string, fallback: string) => reply(overrides[key] ?? fallback);

  const readable = new ReadableStream<Uint8Array>({
    start(c) {
      controller = c;
      answer("greeting", "220 w0221a9f.kasserver.com ESMTP");
    },
  });
  let pending = "";
  const writable = new WritableStream<Uint8Array>({
    write(chunk) {
      pending += dec.decode(chunk);
      if (inData) {
        dataBuffer += pending;
        pending = "";
        if (dataBuffer.endsWith("\r\n.\r\n")) {
          inData = false;
          received.push(`DATA-BODY:${dataBuffer}`);
          answer("dataEnd", "250 2.0.0 Ok: queued");
        }
        return;
      }
      let idx: number;
      while ((idx = pending.indexOf("\r\n")) >= 0) {
        const line = pending.slice(0, idx);
        pending = pending.slice(idx + 2);
        received.push(line);
        if (line.startsWith("EHLO")) {
          reply("250-w0221a9f.kasserver.com");
          answer("ehlo", "250 AUTH LOGIN PLAIN");
        } else if (line === "AUTH LOGIN") answer("auth", "334 VXNlcm5hbWU6");
        else if (received.filter((l) => !l.startsWith("DATA-BODY")).length === 3) answer("user", "334 UGFzc3dvcmQ6");
        else if (received.filter((l) => !l.startsWith("DATA-BODY")).length === 4) answer("pass", "235 2.7.0 Authentication successful");
        else if (line.startsWith("MAIL FROM")) answer("mail", "250 2.1.0 Ok");
        else if (line.startsWith("RCPT TO")) answer("rcpt", "250 2.1.5 Ok");
        else if (line === "DATA") {
          inData = true;
          answer("data", "354 End data with <CR><LF>.<CR><LF>");
          if (pending) {
            dataBuffer += pending;
            pending = "";
          }
        } else if (line === "QUIT") answer("quit", "221 2.0.0 Bye");
      }
    },
  });
  const socket: SmtpSocket = {
    readable,
    writable,
    close: () => {
      closed = true;
    },
  };
  return { socket, received, isClosed: () => closed, connect: () => socket };
}

const CONFIG = { host: "w0221a9f.kasserver.com", port: 465, user: "m0123", pass: "geheim", heloName: "hsb-boden.com" };

describe("SMTP-Client", () => {
  it("authentifiziert, liefert die Mail aus und schließt die Verbindung", async () => {
    const smtp = fakeSmtp();
    await sendMail(smtp.connect, CONFIG, {
      from: { email: "j-post@hsb-boden.com", name: "HSB Website" },
      to: "info@hsb-boden.de",
      replyTo: "kunde@example.com",
      subject: "Foto Schadstelle: Müller GmbH",
      text: "Hallo",
      attachments: [{ filename: "schadstelle-1.jpg", contentType: "image/jpeg", data: JPEG }],
    });
    expect(smtp.received.slice(0, 7)).toEqual([
      "EHLO hsb-boden.com",
      "AUTH LOGIN",
      btoa("m0123"),
      btoa("geheim"),
      "MAIL FROM:<j-post@hsb-boden.com>",
      "RCPT TO:<info@hsb-boden.de>",
      "DATA",
    ]);
    const body = smtp.received.find((l) => l.startsWith("DATA-BODY:"))!;
    expect(body).toContain("Reply-To: <kunde@example.com>");
    expect(body).toContain('filename="schadstelle-1.jpg"');
    expect(smtp.received.at(-1)).toBe("QUIT");
    expect(smtp.isClosed()).toBe(true);
  });

  it("bricht bei abgelehnter Anmeldung mit Fehler ab und schließt trotzdem", async () => {
    const smtp = fakeSmtp({ pass: "535 5.7.8 Authentication failed" });
    await expect(sendMail(smtp.connect, CONFIG, { from: { email: "a@hsb-boden.com" }, to: "info@hsb-boden.de", subject: "x", text: "y" })).rejects.toThrow(/535/);
    expect(smtp.received.some((l) => l.startsWith("MAIL FROM"))).toBe(false);
    expect(smtp.isClosed()).toBe(true);
  });

  it("verhindert Header-Injection und verdoppelt Punkte am Zeilenanfang", () => {
    expect(headerSafe("Firma\r\nBcc: opfer@example.com")).toBe("Firma Bcc: opfer@example.com");
    expect(dotStuff(".a\r\n.b\r\nc")).toBe("..a\r\n..b\r\nc");
    const mime = buildMime({ from: { email: "a@hsb-boden.com" }, to: "info@hsb-boden.de", subject: "Säure\r\nBcc: x@y.de", text: "t" }, new Date(0), "seed");
    expect(mime).not.toMatch(/\r\nBcc:/);
    expect(mime).toContain("Subject: =?UTF-8?B?");
  });
});

describe("sniffImage", () => {
  it("erkennt JPEG, PNG und WebP an den Bytes und lehnt anderes ab", () => {
    expect(sniffImage(JPEG)?.contentType).toBe("image/jpeg");
    expect(sniffImage(PNG)?.contentType).toBe("image/png");
    expect(sniffImage(new TextEncoder().encode("RIFF0000WEBPVP8 "))?.contentType).toBe("image/webp");
    expect(sniffImage(new TextEncoder().encode("<svg onload=alert(1)>"))).toBeNull();
  });
});

class FakeKV {
  store = new Map<string, string>();
  async get(key: string) {
    const v = this.store.get(key);
    return v ? JSON.parse(v) : null;
  }
  async put(key: string, value: string) {
    this.store.set(key, value);
  }
  async delete(key: string) {
    this.store.delete(key);
  }
}

function env(overrides: Partial<RepairPhotoEnv> = {}): RepairPhotoEnv {
  return {
    RATE_LIMIT_KV: new FakeKV() as unknown as KVNamespace,
    SMTP_HOST: "w0221a9f.kasserver.com",
    SMTP_USER: "j-post@hsb-boden.com",
    SMTP_PASS: "geheim",
    REPAIR_CONFIRMATION: "off",
    ...overrides,
  };
}

function form(fields: Record<string, string> = {}, photos: Uint8Array[] = [JPEG]) {
  const fd = new FormData();
  const base = { company: "Molkerei Beispiel GmbH", name: "Erika Muster", email: "erika@example.com", message: "Fuge an der Rinne ausgebrochen", privacyConsent: "on", ...fields };
  for (const [k, v] of Object.entries(base)) fd.set(k, v);
  photos.forEach((p, i) => fd.append("photos", new File([p as BlobPart], `foto-${i}.jpg`, { type: "image/jpeg" })));
  return fd;
}

/** Wie ein Browser: fertiger multipart-Körper mit Content-Length. */
async function request(fd: FormData, origin = "https://www.hsb-boden.de", withLength = true) {
  const encoded = new Response(fd);
  const body = new Uint8Array(await encoded.arrayBuffer());
  const headers: Record<string, string> = {
    Origin: origin,
    "CF-Connecting-IP": "203.0.113.7",
    "Content-Type": encoded.headers.get("Content-Type") ?? "",
  };
  if (withLength) headers["Content-Length"] = String(body.length);
  return new Request("https://www.hsb-boden.de/api/repair-photo", { method: "POST", body, headers });
}

describe("POST /api/repair-photo", () => {
  it("schickt Angaben und Foto als Anhang an info@hsb-boden.de", async () => {
    const smtp = fakeSmtp();
    const res = await handleRepairPhoto(await request(form()), env(), smtp.connect);
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ ok: true, confirmation: false });
    expect(smtp.received).toContain("RCPT TO:<info@hsb-boden.de>");
    const body = smtp.received.find((l) => l.startsWith("DATA-BODY:"))!;
    expect(body).toContain("Content-Type: image/jpeg");
    expect(body).toContain("Reply-To: <erika@example.com>");
  });

  it("lehnt fremde Herkunft ab, ohne zu senden", async () => {
    const smtp = fakeSmtp();
    const res = await handleRepairPhoto(await request(form(), "https://evil.example"), env(), smtp.connect);
    expect(res.status).toBe(403);
    expect(smtp.received).toHaveLength(0);
  });

  it("verlangt Content-Length, damit die Größengrenze nicht umgangen werden kann", async () => {
    const smtp = fakeSmtp();
    const res = await handleRepairPhoto(await request(form(), undefined, false), env(), smtp.connect);
    expect(res.status).toBe(411);
    expect(smtp.received).toHaveLength(0);
  });

  it("meldet 503, solange die SMTP-Zugangsdaten fehlen", async () => {
    const res = await handleRepairPhoto(await request(form()), env({ SMTP_PASS: undefined }), fakeSmtp().connect);
    expect(res.status).toBe(503);
  });

  it("verlangt Einwilligung, gültige E-Mail und mindestens ein Foto", async () => {
    const res = await handleRepairPhoto(await request(form({ privacyConsent: "", email: "kein-mail" }, [])), env(), fakeSmtp().connect);
    expect(res.status).toBe(422);
    const body = (await res.json()) as { fields: string[] };
    expect(body.fields).toEqual(expect.arrayContaining(["privacyConsent", "email", "photos"]));
  });

  it("lehnt Nicht-Bilder und mehr als drei Fotos ab", async () => {
    const svg = new TextEncoder().encode("<svg/>");
    expect((await handleRepairPhoto(await request(form({}, [svg])), env(), fakeSmtp().connect)).status).toBe(422);
    const tooMany = Array.from({ length: MAX_PHOTOS + 1 }, () => JPEG);
    expect((await handleRepairPhoto(await request(form({}, tooMany)), env(), fakeSmtp().connect)).status).toBe(422);
  });

  it("verwirft Bot-Einsendungen über das Honeypot-Feld still", async () => {
    const smtp = fakeSmtp();
    const res = await handleRepairPhoto(await request(form({ website: "http://spam" })), env(), smtp.connect);
    expect(res.status).toBe(200);
    expect(smtp.received).toHaveLength(0);
  });

  it("begrenzt auf fünf Einsendungen je IP in zehn Minuten", async () => {
    const shared = env();
    for (let i = 0; i < 5; i++) {
      expect((await handleRepairPhoto(await request(form()), shared, fakeSmtp().connect)).status).toBe(200);
    }
    expect((await handleRepairPhoto(await request(form()), shared, fakeSmtp().connect)).status).toBe(429);
  });

  it("Rückruf ohne Foto: verlangt Telefon, schickt Zeitfenster und kein Anhang", async () => {
    const missing = await handleRepairPhoto(await request(form({ intent: "callback" }, [])), env(), fakeSmtp().connect);
    expect(missing.status).toBe(422);
    expect(((await missing.json()) as { fields: string[] }).fields).toEqual(["phone"]);

    const smtp = fakeSmtp();
    const res = await handleRepairPhoto(
      await request(form({ intent: "callback", phone: "+49 231 123456", callbackWindow: "vormittags" }, [])),
      env(),
      smtp.connect,
    );
    expect(res.status).toBe(200);
    const body = smtp.received.find((l) => l.startsWith("DATA-BODY:"))!;
    const decoded = atob(body.split("base64\r\n\r\n")[1].split("\r\n--")[0].replace(/\r\n/g, ""));
    const text = new TextDecoder().decode(Uint8Array.from(decoded, (c) => c.charCodeAt(0)));
    expect(text).toContain("RÜCKRUF");
    expect(text).toContain("vormittags (8–12 Uhr)");
    expect(text).toContain("Fotos:        keine");
    expect(body).not.toContain("Content-Disposition: attachment");
  });

  it("Vor-Ort-Termin verlangt einen Standort, Fotos bleiben optional", async () => {
    const missing = await handleRepairPhoto(await request(form({ intent: "visit" }, [])), env(), fakeSmtp().connect);
    expect(((await missing.json()) as { fields: string[] }).fields).toEqual(["location"]);
    const ok = await handleRepairPhoto(await request(form({ intent: "visit", location: "44137 Dortmund" }, [JPEG])), env(), fakeSmtp().connect);
    expect(ok.status).toBe(200);
  });

  it("unbekannter Weg fällt auf Foto zurück und verlangt dann ein Bild", async () => {
    const res = await handleRepairPhoto(await request(form({ intent: "hack", callbackWindow: "toString" }, [])), env(), fakeSmtp().connect);
    expect(((await res.json()) as { fields: string[] }).fields).toEqual(["photos"]);
  });

  it("schickt dem Absender eine Bestätigung ohne seine Eingaben und wartet per waitUntil", async () => {
    const sessions: ReturnType<typeof fakeSmtp>[] = [];
    const connect = () => {
      const s = fakeSmtp();
      sessions.push(s);
      return s.socket;
    };
    const pending: Promise<unknown>[] = [];
    const res = await handleRepairPhoto(
      await request(form({ company: "Spam <a href=x>klick</a>" })),
      env({ REPAIR_CONFIRMATION: undefined }),
      connect,
      new Date(),
      (p) => pending.push(p),
    );
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ ok: true, confirmation: true });
    expect(pending).toHaveLength(1);
    await Promise.all(pending);
    expect(sessions).toHaveLength(2);
    expect(sessions[1].received).toContain("RCPT TO:<erika@example.com>");
    const confirmation = sessions[1].received.find((l) => l.startsWith("DATA-BODY:"))!;
    expect(confirmation).toContain("Reply-To: <info@hsb-boden.de>");
    expect(confirmation).not.toContain("Spam");
    expect(buildConfirmationText("callback")).toContain("nachreichen");
  });

  it("eine fehlgeschlagene Bestätigung kippt die zugestellte Anfrage nicht", async () => {
    let call = 0;
    const res = await handleRepairPhoto(await request(form()), env({ REPAIR_CONFIRMATION: undefined }), () =>
      (call++ === 0 ? fakeSmtp() : fakeSmtp({ rcpt: "550 5.1.1 User unknown" })).socket,
    );
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ ok: true, confirmation: false });
  });

  it("schickt höchstens eine Bestätigung pro Adresse und Tag und vermerkt das in der internen Mail", async () => {
    const shared = env({ REPAIR_CONFIRMATION: undefined });
    const internal: string[] = [];
    const recipients: string[] = [];
    const sessionsOf: ReturnType<typeof fakeSmtp>[] = [];
    const connect = () => {
      const s = fakeSmtp();
      sessionsOf.push(s);
      return s.socket;
    };
    const textOf = (body: string) => {
      const decoded = atob(body.split("base64\r\n\r\n")[1].split("\r\n--")[0].replace(/\r\n/g, ""));
      return new TextDecoder().decode(Uint8Array.from(decoded, (c) => c.charCodeAt(0)));
    };
    const first = await handleRepairPhoto(await request(form()), shared, connect);
    expect(await first.json()).toEqual({ ok: true, confirmation: true });
    const second = await handleRepairPhoto(await request(form({ email: "ERIKA@example.com" })), shared, connect);
    expect(await second.json()).toEqual({ ok: true, confirmation: false });
    for (const s of sessionsOf) {
      recipients.push(...s.received.filter((l) => l.startsWith("RCPT TO:")));
      internal.push(s.received.find((l) => l.startsWith("DATA-BODY:")) ?? "");
    }
    // Erste Anfrage: interne Mail + Bestätigung, zweite Anfrage: nur interne Mail.
    expect(recipients.filter((r) => r.toLowerCase() === "rcpt to:<erika@example.com>")).toHaveLength(1);
    expect(textOf(internal[0])).toContain("Eingangsbestätigung an den Absender wurde angestoßen");
    expect(textOf(internal[2])).toContain("in den letzten 24 Stunden bereits eine");
    const kv = (shared.RATE_LIMIT_KV as unknown as { store: Map<string, string> }).store;
    expect([...kv.keys()].some((k) => k.includes("erika"))).toBe(false);
  });

  it("stoppt Bestätigungen an der Tagesobergrenze", async () => {
    const shared = env({ REPAIR_CONFIRMATION: undefined });
    const kv = (shared.RATE_LIMIT_KV as unknown as { store: Map<string, string> }).store;
    const now = new Date("2026-11-10T10:00:00Z");
    kv.set("repair-photo:confirm:day:2026-11-10", "50");
    const res = await handleRepairPhoto(await request(form()), shared, fakeSmtp().connect, now);
    expect(await res.json()).toEqual({ ok: true, confirmation: false });
  });

  it("liefert die Anfrage auch dann, wenn der Bestätigungszähler ausfällt", async () => {
    const shared = env({ REPAIR_CONFIRMATION: undefined });
    const kv = shared.RATE_LIMIT_KV as unknown as { get: (k: string) => Promise<unknown> };
    const originalGet = kv.get.bind(kv);
    kv.get = async (k: string) => {
      if (k.startsWith("repair-photo:confirm:")) throw new Error("KV down");
      return originalGet(k);
    };
    const res = await handleRepairPhoto(await request(form()), shared, fakeSmtp().connect);
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ ok: true, confirmation: false });
  });

  it("gibt die Empfänger-Sperre frei, wenn die interne Zustellung scheitert", async () => {
    const shared = env({ REPAIR_CONFIRMATION: undefined });
    const store = (shared.RATE_LIMIT_KV as unknown as { store: Map<string, string> }).store;
    const failed = await handleRepairPhoto(await request(form()), shared, fakeSmtp({ rcpt: "451 4.3.0 try later" }).connect);
    expect(failed.status).toBe(502);
    expect([...store.keys()].some((k) => k.startsWith("repair-photo:confirm:to:"))).toBe(false);
    const retry = await handleRepairPhoto(await request(form()), shared, () => fakeSmtp().socket);
    expect(await retry.json()).toEqual({ ok: true, confirmation: true });
  });

  it("meldet 502, wenn der Mailserver ablehnt", async () => {
    const res = await handleRepairPhoto(await request(form()), env(), fakeSmtp({ rcpt: "550 5.1.1 User unknown" }).connect);
    expect(res.status).toBe(502);
  });
});
