// @vitest-environment node
import { describe, expect, it } from "vitest";
import { buildMime, dotStuff, headerSafe, sendMail, type SmtpSocket } from "../functions/lib/smtp";
import { handleRepairPhoto, MAX_PHOTOS, sniffImage, type RepairPhotoEnv } from "../functions/lib/repair-photo-handler";

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
}

function env(overrides: Partial<RepairPhotoEnv> = {}): RepairPhotoEnv {
  return {
    RATE_LIMIT_KV: new FakeKV() as unknown as KVNamespace,
    SMTP_HOST: "w0221a9f.kasserver.com",
    SMTP_USER: "j-post@hsb-boden.com",
    SMTP_PASS: "geheim",
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

function request(fd: FormData, origin = "https://www.hsb-boden.de") {
  return new Request("https://www.hsb-boden.de/api/repair-photo", { method: "POST", body: fd, headers: { Origin: origin, "CF-Connecting-IP": "203.0.113.7" } });
}

describe("POST /api/repair-photo", () => {
  it("schickt Angaben und Foto als Anhang an info@hsb-boden.de", async () => {
    const smtp = fakeSmtp();
    const res = await handleRepairPhoto(request(form()), env(), smtp.connect);
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ ok: true });
    expect(smtp.received).toContain("RCPT TO:<info@hsb-boden.de>");
    const body = smtp.received.find((l) => l.startsWith("DATA-BODY:"))!;
    expect(body).toContain("Content-Type: image/jpeg");
    expect(body).toContain("Reply-To: <erika@example.com>");
  });

  it("lehnt fremde Herkunft ab, ohne zu senden", async () => {
    const smtp = fakeSmtp();
    const res = await handleRepairPhoto(request(form(), "https://evil.example"), env(), smtp.connect);
    expect(res.status).toBe(403);
    expect(smtp.received).toHaveLength(0);
  });

  it("meldet 503, solange die SMTP-Zugangsdaten fehlen", async () => {
    const res = await handleRepairPhoto(request(form()), env({ SMTP_PASS: undefined }), fakeSmtp().connect);
    expect(res.status).toBe(503);
  });

  it("verlangt Einwilligung, gültige E-Mail und mindestens ein Foto", async () => {
    const res = await handleRepairPhoto(request(form({ privacyConsent: "", email: "kein-mail" }, [])), env(), fakeSmtp().connect);
    expect(res.status).toBe(422);
    const body = (await res.json()) as { fields: string[] };
    expect(body.fields).toEqual(expect.arrayContaining(["privacyConsent", "email", "photos"]));
  });

  it("lehnt Nicht-Bilder und mehr als drei Fotos ab", async () => {
    const svg = new TextEncoder().encode("<svg/>");
    expect((await handleRepairPhoto(request(form({}, [svg])), env(), fakeSmtp().connect)).status).toBe(422);
    const tooMany = Array.from({ length: MAX_PHOTOS + 1 }, () => JPEG);
    expect((await handleRepairPhoto(request(form({}, tooMany)), env(), fakeSmtp().connect)).status).toBe(422);
  });

  it("verwirft Bot-Einsendungen über das Honeypot-Feld still", async () => {
    const smtp = fakeSmtp();
    const res = await handleRepairPhoto(request(form({ website: "http://spam" })), env(), smtp.connect);
    expect(res.status).toBe(200);
    expect(smtp.received).toHaveLength(0);
  });

  it("begrenzt auf fünf Einsendungen je IP in zehn Minuten", async () => {
    const shared = env();
    for (let i = 0; i < 5; i++) {
      expect((await handleRepairPhoto(request(form()), shared, fakeSmtp().connect)).status).toBe(200);
    }
    expect((await handleRepairPhoto(request(form()), shared, fakeSmtp().connect)).status).toBe(429);
  });

  it("meldet 502, wenn der Mailserver ablehnt", async () => {
    const res = await handleRepairPhoto(request(form()), env(), fakeSmtp({ rcpt: "550 5.1.1 User unknown" }).connect);
    expect(res.status).toBe(502);
  });
});
