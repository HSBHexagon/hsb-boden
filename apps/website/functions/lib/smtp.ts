// Minimaler SMTP-Client (implizites TLS, Port 465) für Pages Functions über cloudflare:sockets.
// Bewusst ohne Fremdpaket: nur EHLO, AUTH LOGIN, MAIL FROM, RCPT TO, DATA, QUIT.
// Die Socket-Fabrik wird injiziert, damit der Ablauf ohne Netz testbar bleibt.

export interface SmtpSocket {
  readable: ReadableStream<Uint8Array>;
  writable: WritableStream<Uint8Array>;
  close(): Promise<void> | void;
}

export type SocketFactory = (hostname: string, port: number) => SmtpSocket;

export interface SmtpConfig {
  host: string;
  port: number;
  user: string;
  pass: string;
  /** Name für EHLO, z. B. die Absenderdomain. */
  heloName: string;
}

export interface MailAttachment {
  filename: string;
  contentType: string;
  data: Uint8Array;
}

export interface MailMessage {
  from: { email: string; name?: string };
  to: string;
  replyTo?: string;
  subject: string;
  text: string;
  attachments?: MailAttachment[];
}

const TIMEOUT_MS = 15000;
const encoder = new TextEncoder();
const decoder = new TextDecoder();

export class SmtpError extends Error {
  constructor(message: string, readonly code?: number) {
    super(message);
    this.name = "SmtpError";
  }
}

export function toBase64(data: Uint8Array): string {
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < data.length; i += chunk) {
    binary += String.fromCharCode(...data.subarray(i, i + chunk));
  }
  return btoa(binary);
}

function utf8Base64(value: string): string {
  return toBase64(encoder.encode(value));
}

function wrap76(value: string): string {
  return value.replace(/.{1,76}/g, "$&\r\n").trimEnd();
}

/** Entfernt Zeilenumbrüche, damit Nutzereingaben keine Header einschleusen. */
export function headerSafe(value: string): string {
  return value.replace(/[\r\n]+/g, " ").trim();
}

function encodeWord(value: string): string {
  const safe = headerSafe(value);
  return /^[\x20-\x7e]*$/.test(safe) ? safe : `=?UTF-8?B?${utf8Base64(safe)}?=`;
}

function formatAddress(email: string, name?: string): string {
  const addr = headerSafe(email);
  return name ? `${encodeWord(name)} <${addr}>` : `<${addr}>`;
}

export function buildMime(message: MailMessage, now = new Date(), boundarySeed: string = crypto.randomUUID()): string {
  const boundary = `hsb-${boundarySeed}`;
  const domain = message.from.email.split("@")[1] ?? "localhost";
  const headers = [
    `From: ${formatAddress(message.from.email, message.from.name)}`,
    `To: ${formatAddress(message.to)}`,
    ...(message.replyTo ? [`Reply-To: ${formatAddress(message.replyTo)}`] : []),
    `Subject: ${encodeWord(message.subject)}`,
    `Date: ${now.toUTCString().replace("GMT", "+0000")}`,
    `Message-ID: <${boundarySeed}@${domain}>`,
    "MIME-Version: 1.0",
    `Content-Type: multipart/mixed; boundary="${boundary}"`,
  ];
  const parts = [
    [
      `--${boundary}`,
      "Content-Type: text/plain; charset=UTF-8",
      "Content-Transfer-Encoding: base64",
      "",
      wrap76(utf8Base64(message.text)),
    ].join("\r\n"),
    ...(message.attachments ?? []).map((file) =>
      [
        `--${boundary}`,
        `Content-Type: ${headerSafe(file.contentType)}; name="${headerSafe(file.filename)}"`,
        "Content-Transfer-Encoding: base64",
        `Content-Disposition: attachment; filename="${headerSafe(file.filename)}"`,
        "",
        wrap76(toBase64(file.data)),
      ].join("\r\n"),
    ),
  ];
  return `${headers.join("\r\n")}\r\n\r\n${parts.join("\r\n")}\r\n--${boundary}--\r\n`;
}

/** Punkt am Zeilenanfang verdoppeln (RFC 5321, 4.5.2). */
export function dotStuff(data: string): string {
  return data.replace(/(^|\r\n)\./g, "$1..");
}

class ReplyReader {
  private buffer = "";
  constructor(private readonly reader: ReadableStreamDefaultReader<Uint8Array>) {}

  async read(): Promise<{ code: number; text: string }> {
    const lines: string[] = [];
    for (;;) {
      const newline = this.buffer.indexOf("\r\n");
      if (newline >= 0) {
        const line = this.buffer.slice(0, newline);
        this.buffer = this.buffer.slice(newline + 2);
        lines.push(line);
        if (/^\d{3}(?: |$)/.test(line)) {
          return { code: Number(line.slice(0, 3)), text: lines.join("\n") };
        }
        continue;
      }
      const { value, done } = await this.reader.read();
      if (done) throw new SmtpError("SMTP-Verbindung vorzeitig geschlossen");
      this.buffer += decoder.decode(value, { stream: true });
    }
  }
}

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  let timer: ReturnType<typeof setTimeout>;
  return Promise.race([
    promise,
    new Promise<T>((_, reject) => {
      timer = setTimeout(() => reject(new SmtpError("SMTP-Zeitüberschreitung")), ms);
    }),
  ]).finally(() => clearTimeout(timer));
}

export async function sendMail(connect: SocketFactory, config: SmtpConfig, message: MailMessage): Promise<void> {
  const socket = connect(config.host, config.port);
  const writer = socket.writable.getWriter();
  const replies = new ReplyReader(socket.readable.getReader());

  const expect = async (allowed: number[]) => {
    const reply = await replies.read();
    if (!allowed.includes(reply.code)) {
      throw new SmtpError(`SMTP ${reply.code}: ${reply.text.slice(0, 200)}`, reply.code);
    }
  };
  const command = async (line: string, allowed: number[]) => {
    await writer.write(encoder.encode(`${line}\r\n`));
    await expect(allowed);
  };

  const run = async () => {
    await expect([220]);
    await command(`EHLO ${config.heloName}`, [250]);
    await command("AUTH LOGIN", [334]);
    await command(utf8Base64(config.user), [334]);
    await command(utf8Base64(config.pass), [235]);
    await command(`MAIL FROM:<${headerSafe(message.from.email)}>`, [250]);
    await command(`RCPT TO:<${headerSafe(message.to)}>`, [250, 251]);
    await command("DATA", [354]);
    await command(`${dotStuff(buildMime(message))}\r\n.`, [250]);
    try {
      await command("QUIT", [221]);
    } catch {
      // Die Mail ist nach 250 auf DATA angenommen; ein Fehler beim QUIT ändert daran nichts.
    }
  };

  try {
    await withTimeout(run(), TIMEOUT_MS);
  } finally {
    try {
      await socket.close();
    } catch {
      // Schließen ist best effort.
    }
  }
}
