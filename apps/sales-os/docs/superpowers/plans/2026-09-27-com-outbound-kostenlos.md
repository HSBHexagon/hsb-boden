# .com-Outbound kostenlos: Entwürfe, Senden per Knopf, Rückläufer – Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Joel und Jordie erzeugen in der Sidebar des HSB Sales OS beliebig viele Entwürfe (z. B. 500) im eigenen `.com`-Postfach, sehen und prüfen sie, klicken „Markierte senden“, und das System verschickt sie gedrosselt über All-Inkl. Antworten landen per Reply-To in `.de`; Bounces und Abwesenheitsnotizen werden automatisch erkannt und ins CRM geschrieben. Ohne laufende Kosten.

**Architecture:** Erweiterung des Basisplans `2026-09-27-com-entwuerfe-per-knopf.md`. Die COM-Bridge (Cloudflare Worker, Gratis-Tarif) bekommt zwei weitere Routen: `/send` (verschickt **genau einen bereits vorhandenen Entwurf** per All-Inkl-SMTP, legt ihn in „Gesendet“ ab, löscht ihn aus „Entwürfe“) und `/inbox` (liest den `.com`-Posteingang mit Kennzeichen für Bounce und Autoreply). Alle Entscheidungen (Warteschlange, Versandfenster, Tageslimit mit Warm-up, Notbremse, Firmen-Stopp) trifft Apps Script, und zwar in einer reinen, testbaren Funktion. Ein 10-Minuten-Trigger sendet höchstens eine Mail je Postfach und Takt. Die Sidebar bekommt einen Bereich „Versand über .com“.

**Tech Stack:** Google Apps Script (V8, clasp), Cloudflare Workers Free (TypeScript, `cloudflare:sockets`), vitest, Node-`vm`-Harness.

**Spec:** Kein separates Spec-Dokument. Entscheidungen und Belege stehen unten unter „Entscheidung“. Der Basisplan gilt für alles, was hier nicht geändert wird.

---

## Entscheidung (belegt am 2026-09-27)

| Option | Ergebnis | Beleg |
|---|---|---|
| Cloudflare Email Service | verworfen | Terms: nur „Transactional Emails … in response to a specific customer interaction“; verlangt Cloudflare-DNS (`hsb-boden.com` liegt bei `ns5/ns6.kasserver.com`); Beta, nur Workers Paid |
| Gmail „Senden als“ + Apps Script `GmailApp` | verworfen | Google: „Starting January 2027, Gmail will no longer support the ‚Send as‘ feature for third-party email addresses“; POP-Abruf für neue Nutzer seit Q1 2026 abgeschaltet; Apps-Script-Consumer-Quote 100 Empfänger pro Tag |
| Eigener M365-Tenant / Google Workspace / MX-Umzug | verworfen | kostenpflichtig (Nutzervorgabe: keine Kosten) |
| GitHub Actions + Python-Engine | verworfen | `HSBHexagon/hsb-boden` ist **öffentlich**, also wären Workflow-Logs mit Empfängerdaten öffentlich; in einem privaten Repo gäbe es 2 000 Minuten pro Monat bei laufender CI |
| Nur Mac (launchd) | verworfen | Versand hinge davon ab, dass Joels Mac läuft |
| **All-Inkl (vorhanden) + Worker Free + Apps Script** | **gewählt** | keine Zusatzkosten; Ports 465/993 erlaubt (nur 25 gesperrt); Entscheidungslogik bleibt im System of Record |

Risiko Gratis-Tarif: 10 ms CPU je Anfrage. Die Bridge reicht nur Bytes durch. Ob TLS dabei in das CPU-Budget fällt, ist nicht belegt; Task 9 Step 4 misst das. Liegt ein Lauf darüber: STOPP und Nutzer entscheidet (Workers Paid oder Mac-Betrieb). Nicht still weiterbauen.

## Global Constraints

- Die 200 bestehenden `.com`-Entwürfe vom 26.09. (Message-ID `<1790…@hsb-boden.com>` steht in `Draft_ID`, im Postfach geprüft 100/100 je Owner) werden **weiterverwendet**, nicht neu erzeugt.
- Freigabe = Häkchen in der Sidebar. `Versandfreigabe` sperrt die Entwurfserstellung nicht mehr (Inhaber-Entscheidung 2026-09-27; heute hätten nur 76 Leads `yes`). Beim Einreihen wird `Versandfreigabe=yes` und `Approved_At` als Nachweis geschrieben.
- Alle Constraints des Basisplans gelten, **außer**: Die Bridge darf senden, aber **nur** einen Entwurf, der schon in „Entwürfe“ des eigenen Postfachs liegt, **nur** an dessen einen `To`-Empfänger, **nur** wenn `From` zum Postfach passt, und **nie** mit Cc/Bcc.
- Senden wird nie automatisch wiederholt, wenn der Ausgang unklar ist (`send_unklar`). Doppelversand ist schlimmer als ein ausgelassener Lead.
- Versandfenster Mo–Fr 08:00–16:59 Europe/Berlin. Tageslimit je Postfach: Woche 1 → 10, 2 → 20, 3 → 30, 4 → 40, ab 5 → 50 (Woche zählt ab erstem echten Versand). Mindestabstand: 1 Mail je Postfach und 10-Minuten-Takt, 30 % der Takte werden zufällig ausgelassen.
- Notbremse: ab 20 Sendungen in 7 Tagen und Hard-Bounce-Quote > 2 % → Versand für beide Postfächer pausiert, bis ein Mensch „Fortsetzen“ klickt.
- Firmen-Stopp: Hat irgendein Lead derselben E-Mail-Domain einen Eintrag in `Reply_Status`, geht an diese Domain nichts mehr raus.
- Flyer-PDF ist in jedem Entwurf Pflicht (Basisplan, Anhangprüfung).
- Rechtsgrundlage: Inhaber-Entscheidung vom 2026-09-27, alle Leads im Sales OS dürfen kontaktiert werden. Nur `Legal_Basis=BLOCKED` sperrt.
- Keine personenbezogenen Daten in Logs der Bridge (`console.log` nur mit Zählern, nie mit Adressen).

## Review Focus

1. **Zweiter Klick / Takt-Überschneidung:** Zwei Takte dürfen denselben Lead nicht zweimal senden. Abgedeckt durch `LockService`, durch `Send_Status=sending` vor dem Aufruf und durch die „schon in Gesendet?“-Prüfung in `/send` (Task 2, Test `schon gesendet → kein SMTP`).
2. **Verbindung reißt nach dem Punkt am Ende der DATA-Phase:** Der Ausgang ist unklar, also keine Wiederholung. Abgedeckt: Task 1 Test `Abbruch nach DATA ist unklar`, Task 5 Test `unklar wird nicht erneut gesendet`.
3. **Abmeldung trifft ein, während der Lead in der Warteschlange steht:** Der Lead darf nicht mehr raus. Abgedeckt: Task 5 Test `gesperrter Lead wird übersprungen und markiert`.
4. **Bounce-Mail enthält die eigene `.com`-Adresse:** Sie darf nicht als „fehlgeschlagener Empfänger“ gelten. Abgedeckt: Task 6 Test `DSN mit .com-Absender erkennt den echten Empfänger`.
5. **Zeitzone/Wochenende:** Sonntag 10 Uhr und Montag 07:59 senden nichts, Montag 08:00 sendet. Abgedeckt: Task 5 Tests zum Fenster.

## Dateistruktur (zusätzlich zum Basisplan)

| Datei | Aktion | Verantwortung |
|---|---|---|
| `com_bridge/src/smtp.ts` | neu | Minimaler SMTP-Client (AUTH PLAIN, implizites TLS), Dot-Stuffing |
| `com_bridge/src/send.ts` | neu | `sendDraft`: Entwurf holen → prüfen → SMTP → „Gesendet“ → Entwurf löschen |
| `com_bridge/src/mailbox.ts` | ändern | `withSession`/`searchNumbers` exportieren, `listInbox`, RFC-2047-Decoder |
| `com_bridge/src/handler.ts` | ersetzen | Routen `/draft`, `/sent`, `/send`, `/inbox` |
| `com_bridge/src/socket.ts` | ändern | Port als Parameter |
| `com_bridge/test/fake_server.ts` | ändern | `BODY.PEEK[]`, `BODY.PEEK[TEXT]`, `STORE`, `EXPUNGE` |
| `com_bridge/test/fake_smtp.ts` | neu | Nachgebauter SMTP-Server |
| `com_bridge/test/smtp.test.ts`, `send.test.ts`, `inbox.test.ts` | neu | Tests |
| `apps_script/HSB_ComVersand.gs` | neu | Warteschlange, Entscheidung, Takt, Sidebar-Serverfunktionen |
| `apps_script/HSB_ComBridge.gs` | ändern | `comReconcileInbox_` |
| `apps_script/HSB_GraphAdapter.gs` | ändern | Klassifizierer nutzt `dsn`/`autoReply`; `.com`-Posteingang im 15-Minuten-Abgleich |
| `apps_script/Engine.gs` | ändern | Legal-Gate: nur `BLOCKED` sperrt |
| `apps_script/Sidebar.html` | ändern | Bereich „Versand über .com“ |
| `apps_script/Code.gs` | ändern | Menüeinträge |
| `deploy.sh`, `deploy/.claspignore` | ändern | `HSB_ComVersand.gs` ausliefern |
| `tests/test_com_versand.js` | neu | Apps-Script-Tests |

Die „Offline-Suite“ aus dem Basisplan bekommt eine weitere Zeile. Ab Task 5 gilt:

```bash
test -f apps_script/HSB_ComVersand.gs && cp apps_script/HSB_ComVersand.gs deploy/HSB_ComVersand.js
test -f tests/test_com_versand.js && node tests/test_com_versand.js
```

---

### Task 0: Basisplan Tasks 1–5 ausführen

**Files:** siehe `docs/superpowers/plans/2026-09-27-com-entwuerfe-per-knopf.md`.

- [ ] **Step 1:** Tasks 1 bis 5 des Basisplans vollständig ausführen, inklusive aller Commits. Tasks 6 und 7 dort **nicht**, sie werden durch Task 9 und Task 10 hier ersetzt.
- [ ] **Step 2:** `cd apps/sales-os/com_bridge && npx vitest run` → alle Tests PASS; Offline-Suite ohne `ROT:`.

---

### Task 1: SMTP-Client

**Files:**
- Create: `apps/sales-os/com_bridge/src/smtp.ts`
- Create: `apps/sales-os/com_bridge/test/fake_smtp.ts`
- Test: `apps/sales-os/com_bridge/test/smtp.test.ts`

**Interfaces:**
- Consumes: `Wire` aus `src/imap.ts`.
- Produces: `class SmtpError extends Error { beforeData: boolean }`, `dotStuff(raw: Uint8Array): Uint8Array`, `smtpSend(wire: Wire, creds: { user: string; pass: string }, from: string, to: string, raw: Uint8Array): Promise<void>`.

- [ ] **Step 1: Fake-SMTP-Server schreiben**

`apps/sales-os/com_bridge/test/fake_smtp.ts`:

```ts
import type { Wire } from '../src/imap';

const enc = new TextEncoder();
const dec = new TextDecoder();

/** Nachgebauter SMTP-Server (nur die Befehle, die smtpSend benutzt). */
export class FakeSmtp {
  log: string[] = [];
  data = '';
  rejectRcpt = false;
  authFails = false;
  /** Server schluckt die Nachricht und antwortet nie (Verbindungsabbruch nach dem Punkt). */
  dropAfterData = false;
  connects = 0;
  private inbox: Uint8Array[] = [];
  private pending = '';
  private inData = false;

  wire(): Wire {
    this.connects++;
    this.inbox.push(enc.encode('220 fake ESMTP\r\n'));
    return {
      write: async (d) => { this.pending += dec.decode(d); this.process(); },
      read: async () => (this.inbox.length ? this.inbox.shift()! : null),
      close: async () => undefined,
    };
  }

  private send(s: string) { this.inbox.push(enc.encode(s)); }

  private process() {
    for (;;) {
      if (this.inData) {
        const end = this.pending.indexOf('\r\n.\r\n');
        if (end < 0) return;
        this.data = this.pending.slice(0, end + 2);
        this.pending = this.pending.slice(end + 5);
        this.inData = false;
        this.log.push('DATA-ENDE');
        if (!this.dropAfterData) this.send('250 2.0.0 queued\r\n');
        continue;
      }
      const i = this.pending.indexOf('\r\n');
      if (i < 0) return;
      const line = this.pending.slice(0, i);
      this.pending = this.pending.slice(i + 2);
      const verb = line.split(' ')[0].toUpperCase();
      this.log.push(verb === 'AUTH' ? 'AUTH ***' : line);
      if (verb === 'EHLO') this.send('250-fake\r\n250 AUTH PLAIN LOGIN\r\n');
      else if (verb === 'AUTH') this.send(this.authFails ? '535 5.7.8 auth failed\r\n' : '235 2.7.0 ok\r\n');
      else if (verb === 'MAIL') this.send('250 ok\r\n');
      else if (verb === 'RCPT') this.send(this.rejectRcpt ? '550 5.1.1 no such user\r\n' : '250 ok\r\n');
      else if (verb === 'DATA') { this.inData = true; this.send('354 go ahead\r\n'); }
      else if (verb === 'QUIT') this.send('221 bye\r\n');
      else this.send('500 unknown\r\n');
    }
  }
}
```

- [ ] **Step 2: Failing Tests schreiben**

`apps/sales-os/com_bridge/test/smtp.test.ts`:

```ts
import { describe, expect, it } from 'vitest';
import { SmtpError, dotStuff, smtpSend } from '../src/smtp';
import { FakeSmtp } from './fake_smtp';

const creds = { user: 'm0821e5d', pass: 'pässwort' };
const bytes = (s: string) => new TextEncoder().encode(s);
const txt = (b: Uint8Array) => new TextDecoder().decode(b);
const MAIL = 'From: A <j-cherino@hsb-boden.com>\r\nTo: kunde@firma.de\r\nSubject: x\r\n\r\nHallo\r\n.Punktzeile\r\n';

describe('dotStuff', () => {
  it('verdoppelt Punkte am Zeilenanfang', () => {
    expect(txt(dotStuff(bytes('a\r\n.b\r\n')))).toBe('a\r\n..b\r\n');
  });
  it('ergänzt fehlendes CRLF am Ende', () => {
    expect(txt(dotStuff(bytes('a')))).toBe('a\r\n');
  });
  it('gibt unveränderte Nachricht ohne Punkte identisch zurück', () => {
    const b = bytes('a\r\nb\r\n');
    expect(dotStuff(b)).toBe(b);
  });
});

describe('smtpSend', () => {
  it('sendet mit AUTH PLAIN, MAIL FROM, RCPT TO und dot-gestufter Nachricht', async () => {
    const srv = new FakeSmtp();
    await smtpSend(srv.wire(), creds, 'j-cherino@hsb-boden.com', 'kunde@firma.de', bytes(MAIL));
    expect(srv.log).toContain('MAIL FROM:<j-cherino@hsb-boden.com>');
    expect(srv.log).toContain('RCPT TO:<kunde@firma.de>');
    expect(srv.log).toContain('AUTH ***');
    expect(srv.data).toContain('\r\n..Punktzeile\r\n');
  });

  it('abgelehnter Empfänger: SmtpError mit beforeData=true (sicher nicht gesendet)', async () => {
    const srv = new FakeSmtp();
    srv.rejectRcpt = true;
    const e = await smtpSend(srv.wire(), creds, 'j-cherino@hsb-boden.com', 'x@y.de', bytes(MAIL)).catch((x) => x);
    expect(e).toBeInstanceOf(SmtpError);
    expect(e.beforeData).toBe(true);
    expect(srv.log).not.toContain('DATA-ENDE');
  });

  it('Anmeldefehler nennt kein Passwort', async () => {
    const srv = new FakeSmtp();
    srv.authFails = true;
    const e = await smtpSend(srv.wire(), creds, 'j-cherino@hsb-boden.com', 'x@y.de', bytes(MAIL)).catch((x) => x);
    expect(e.beforeData).toBe(true);
    expect(String(e.message)).not.toContain('pässwort');
  });

  it('Abbruch nach DATA ist unklar (beforeData=false)', async () => {
    const srv = new FakeSmtp();
    srv.dropAfterData = true;
    const e = await smtpSend(srv.wire(), creds, 'j-cherino@hsb-boden.com', 'x@y.de', bytes(MAIL)).catch((x) => x);
    expect(e).toBeInstanceOf(SmtpError);
    expect(e.beforeData).toBe(false);
  });
});
```

- [ ] **Step 3: Test laufen lassen, er muss scheitern**

Run: `cd apps/sales-os/com_bridge && npx vitest run test/smtp.test.ts`
Expected: FAIL, `Failed to resolve import "../src/smtp"`.

- [ ] **Step 4: SMTP-Client implementieren**

`apps/sales-os/com_bridge/src/smtp.ts`:

```ts
import type { Wire } from './imap';

const enc = new TextEncoder();
const dec = new TextDecoder();

/**
 * beforeData=true: der Server hat die Nachricht sicher NICHT angenommen
 * (Fehler vor dem abschliessenden Punkt). beforeData=false: Ausgang unklar.
 */
export class SmtpError extends Error {
  constructor(message: string, public beforeData: boolean) {
    super(message);
  }
}

class Lines {
  private buf = new Uint8Array(0);
  constructor(private wire: Wire) {}

  async line(): Promise<string> {
    for (;;) {
      const i = this.buf.indexOf(10);
      if (i >= 0) {
        const l = dec.decode(this.buf.subarray(0, i)).replace(/\r$/, '');
        this.buf = this.buf.subarray(i + 1);
        return l;
      }
      const chunk = await this.wire.read();
      if (chunk === null) throw new Error('Verbindung geschlossen');
      const next = new Uint8Array(this.buf.length + chunk.length);
      next.set(this.buf);
      next.set(chunk, this.buf.length);
      this.buf = next;
    }
  }
}

function base64Utf8(s: string): string {
  let bin = '';
  for (const b of enc.encode(s)) bin += String.fromCharCode(b);
  return btoa(bin);
}

/** Punkte am Zeilenanfang verdoppeln (RFC 5321 4.5.2), CRLF am Ende sicherstellen. */
export function dotStuff(raw: Uint8Array): Uint8Array {
  let extra = 0;
  let lineStart = true;
  for (let i = 0; i < raw.length; i++) {
    if (lineStart && raw[i] === 0x2e) extra++;
    lineStart = raw[i] === 0x0a;
  }
  const endsCrlf = raw.length >= 2 && raw[raw.length - 2] === 0x0d && raw[raw.length - 1] === 0x0a;
  if (extra === 0 && endsCrlf) return raw;
  const out = new Uint8Array(raw.length + extra + (endsCrlf ? 0 : 2));
  let o = 0;
  lineStart = true;
  for (let i = 0; i < raw.length; i++) {
    if (lineStart && raw[i] === 0x2e) out[o++] = 0x2e;
    out[o++] = raw[i];
    lineStart = raw[i] === 0x0a;
  }
  if (!endsCrlf) { out[o++] = 0x0d; out[o++] = 0x0a; }
  return out;
}

export async function smtpSend(wire: Wire, creds: { user: string; pass: string }, from: string, to: string, raw: Uint8Array): Promise<void> {
  const lines = new Lines(wire);
  const step = async (cmd: string | null, ok: number[], name: string, beforeData = true): Promise<void> => {
    try {
      if (cmd !== null) await wire.write(enc.encode(cmd + '\r\n'));
      let code = 0;
      let text = '';
      for (;;) {
        const l = await lines.line();
        code = Number(l.slice(0, 3));
        text += l.slice(4) + ' ';
        if (l.charAt(3) !== '-') break;
      }
      if (!ok.includes(code)) throw new SmtpError(`${name}: ${code} ${text.trim().slice(0, 120)}`, beforeData);
    } catch (e) {
      if (e instanceof SmtpError) throw e;
      throw new SmtpError(`${name}: ${(e as Error).message}`, beforeData);
    }
  };
  try {
    await step(null, [220], 'Begruessung');
    await step('EHLO hsb-com-bridge', [250], 'EHLO');
    await step('AUTH PLAIN ' + base64Utf8('\0' + creds.user + '\0' + creds.pass), [235], 'Anmeldung');
    await step(`MAIL FROM:<${from}>`, [250], 'MAIL FROM');
    await step(`RCPT TO:<${to}>`, [250, 251], 'RCPT TO');
    await step('DATA', [354], 'DATA');
    try {
      await wire.write(dotStuff(raw));
    } catch (e) {
      // Ohne abschliessenden Punkt nimmt der Server nichts an.
      throw new SmtpError('Nachricht: ' + (e as Error).message, true);
    }
    await step('.', [250], 'Nachricht', false);
    await wire.write(enc.encode('QUIT\r\n')).catch(() => undefined);
  } finally {
    await wire.close();
  }
}
```

- [ ] **Step 5: Tests laufen lassen**

Run: `npx vitest run test/smtp.test.ts && npx tsc --noEmit`
Expected: 7 Tests PASS, `tsc` ohne Ausgabe.

- [ ] **Step 6: Commit**

```bash
cd ~/KI-System/02_Projects/active/hsb-boden
python3 scripts/verify_ssot.py
git add apps/sales-os/com_bridge/src/smtp.ts apps/sales-os/com_bridge/test/fake_smtp.ts apps/sales-os/com_bridge/test/smtp.test.ts
git commit -m "feat(sales-os): COM-Bridge SMTP-Client mit sicherer Unterscheidung gesendet/unklar"
```

---

### Task 2: `sendDraft` – vorhandenen Entwurf senden

**Files:**
- Modify: `apps/sales-os/com_bridge/src/mailbox.ts` (Export von `withSession`, `searchNumbers`)
- Modify: `apps/sales-os/com_bridge/test/fake_server.ts` (FETCH-Varianten, STORE, EXPUNGE)
- Create: `apps/sales-os/com_bridge/src/send.ts`
- Test: `apps/sales-os/com_bridge/test/send.test.ts`

**Interfaces:**
- Consumes: `ImapSession`, `ImapError`, `Wire`; `DRAFTS`, `SENT`, `quote`, `parseHeaders`, `firstAddress`, `Creds`; `smtpSend`, `SmtpError`.
- Produces:
  - `export const SMTP_PORT = 465`
  - `export class NotSentError extends Error`
  - `export interface SendDeps { openImap(): Promise<Wire>; openSmtp(): Promise<Wire> }`
  - `export type SendResult = { status: 'sent' | 'already_sent' | 'sent_unfiled'; to: string; warning?: string }`
  - `sendDraft(deps: SendDeps, creds: Creds, fromAddr: string, messageId: string): Promise<SendResult>`

- [ ] **Step 1: Hilfsfunktionen in `mailbox.ts` exportieren**

In `apps/sales-os/com_bridge/src/mailbox.ts`:
- `async function withSession<T>(` → `export async function withSession<T>(`
- `function searchNumbers(` → `export function searchNumbers(`

- [ ] **Step 2: Fake-IMAP-Server erweitern**

In `apps/sales-os/com_bridge/test/fake_server.ts` den kompletten Block `case 'FETCH': { … }` ersetzen durch:

```ts
      case 'FETCH': {
        const [set, ...itemParts] = arg.split(' ');
        const items = itemParts.join(' ');
        const nums = set.split(',').map(Number);
        for (const n of nums) {
          const m = box[n - 1];
          if (!m) continue;
          if (items.includes('RFC822.SIZE')) {
            this.send(`* ${n} FETCH (RFC822.SIZE ${enc.encode(m.raw).length})\r\n`);
            continue;
          }
          let part: string;
          let label: string;
          if (items.includes('BODY.PEEK[]')) {
            part = m.raw;
            label = 'BODY[]';
          } else if (items.includes('BODY.PEEK[TEXT]')) {
            const cut = m.raw.indexOf('\r\n\r\n');
            part = (cut >= 0 ? m.raw.slice(cut + 4) : '').slice(0, 2000);
            label = 'BODY[TEXT]<0>';
          } else {
            part = m.raw.split('\r\n\r\n')[0] + '\r\n\r\n';
            label = 'BODY[HEADER.FIELDS (X)]';
          }
          this.send(`* ${n} FETCH (${label} {${enc.encode(part).length}}\r\n${part})\r\n`);
        }
        this.send(`${tag} OK FETCH done\r\n`);
        return;
      }
      case 'STORE': {
        const [n] = arg.split(' ');
        const m = box[Number(n) - 1];
        if (m && !m.flags.includes('\\Deleted')) m.flags.push('\\Deleted');
        this.send(`${tag} OK STORE done\r\n`);
        return;
      }
      case 'EXPUNGE': {
        this.folders[this.selected] = box.filter((m) => !m.flags.includes('\\Deleted'));
        this.send(`${tag} OK EXPUNGE done\r\n`);
        return;
      }
```

Außerdem in derselben Datei die Ordnerliste um den Posteingang ergänzen:

```ts
  folders: Record<string, FakeMessage[]> = { '"Entw&APw-rfe"': [], '"Gesendet"': [], '"INBOX"': [] };
```

- [ ] **Step 3: Failing Tests schreiben**

`apps/sales-os/com_bridge/test/send.test.ts`:

```ts
import { describe, expect, it } from 'vitest';
import { NotSentError, sendDraft } from '../src/send';
import { SmtpError } from '../src/smtp';
import { FakeImap, eml } from './fake_server';
import { FakeSmtp } from './fake_smtp';

const creds = { user: 'm0821e5d', pass: 'p' };
const FROM = 'j-cherino@hsb-boden.com';
const MID = '<hsb.L1.B1@hsb-boden.com>';

function setup(raw = eml(MID)) {
  const imap = new FakeImap();
  const smtp = new FakeSmtp();
  imap.folders['"Entw&APw-rfe"'].push({ raw, flags: ['\\Draft'] });
  const deps = { openImap: async () => imap.wire(), openSmtp: async () => smtp.wire() };
  return { imap, smtp, deps };
}

describe('sendDraft', () => {
  it('sendet den Entwurf an seinen Empfänger, legt ihn in Gesendet ab und entfernt ihn aus Entwürfe', async () => {
    const { imap, smtp, deps } = setup();
    const r = await sendDraft(deps, creds, FROM, MID);
    expect(r).toEqual({ status: 'sent', to: 'kunde@firma.de' });
    expect(smtp.log).toContain('RCPT TO:<kunde@firma.de>');
    expect(smtp.data).toContain(`Message-ID: ${MID}`);
    expect(imap.folders['"Gesendet"']).toHaveLength(1);
    expect(imap.folders['"Entw&APw-rfe"']).toHaveLength(0);
  });

  it('schon gesendet → kein SMTP', async () => {
    const { imap, smtp, deps } = setup();
    imap.folders['"Gesendet"'].push({ raw: eml(MID), flags: [] });
    const r = await sendDraft(deps, creds, FROM, MID);
    expect(r.status).toBe('already_sent');
    expect(smtp.connects).toBe(0);
  });

  it('fehlender Entwurf → NotSentError, kein SMTP', async () => {
    const { deps, smtp } = setup();
    await expect(sendDraft(deps, creds, FROM, '<hsb.X.B1@hsb-boden.com>')).rejects.toBeInstanceOf(NotSentError);
    expect(smtp.connects).toBe(0);
  });

  it('fremder Absender im Entwurf → NotSentError, kein SMTP', async () => {
    const { deps, smtp } = setup(eml(MID, 'kunde@firma.de', 'Jordie <j-post@hsb-boden.com>'));
    await expect(sendDraft(deps, creds, FROM, MID)).rejects.toBeInstanceOf(NotSentError);
    expect(smtp.connects).toBe(0);
  });

  it('mehrere Empfänger → NotSentError', async () => {
    const { deps } = setup(eml(MID, 'a@firma.de, b@firma.de'));
    await expect(sendDraft(deps, creds, FROM, MID)).rejects.toBeInstanceOf(NotSentError);
  });

  it('Bcc im Entwurf → NotSentError', async () => {
    const raw = eml(MID).replace('To: kunde@firma.de', 'To: kunde@firma.de\r\nBcc: x@y.de');
    const { deps } = setup(raw);
    await expect(sendDraft(deps, creds, FROM, MID)).rejects.toBeInstanceOf(NotSentError);
  });

  it('Empfänger abgelehnt → NotSentError, Entwurf bleibt liegen', async () => {
    const { deps, smtp, imap } = setup();
    smtp.rejectRcpt = true;
    await expect(sendDraft(deps, creds, FROM, MID)).rejects.toBeInstanceOf(NotSentError);
    expect(imap.folders['"Entw&APw-rfe"']).toHaveLength(1);
  });

  it('entfernt X-Unsent, setzt Date neu und legt die gesendete Fassung ab', async () => {
    const alt = eml(MID).replace('Date: Sun, 27 Sep 2026 10:00:00 +0200', 'Date: Sat, 26 Sep 2026 10:00:00 +0200\r\nX-Unsent: 1');
    const { deps, smtp, imap } = setup(alt);
    await sendDraft(deps, creds, FROM, MID);
    expect(smtp.data).not.toContain('X-Unsent');
    expect(smtp.data).not.toContain('26 Sep 2026');
    expect(smtp.data).toMatch(/\r\nDate: .+ \+0000\r\n/);
    expect(imap.folders['"Gesendet"'][0].raw).not.toContain('X-Unsent');
  });

  it('Abbruch nach DATA → SmtpError (unklar), kein NotSentError', async () => {
    const { deps, smtp } = setup();
    smtp.dropAfterData = true;
    const e = await sendDraft(deps, creds, FROM, MID).catch((x) => x);
    expect(e).toBeInstanceOf(SmtpError);
    expect(e).not.toBeInstanceOf(NotSentError);
  });
});
```

- [ ] **Step 4: Test laufen lassen, er muss scheitern**

Run: `npx vitest run test/send.test.ts`
Expected: FAIL, `Failed to resolve import "../src/send"`.

- [ ] **Step 5: `send.ts` implementieren**

`apps/sales-os/com_bridge/src/send.ts`:

```ts
import type { Wire } from './imap';
import { DRAFTS, SENT, firstAddress, parseHeaders, quote, searchNumbers, withSession, type Creds } from './mailbox';
import { SmtpError, smtpSend } from './smtp';

export const SMTP_PORT = 465;

/** Sicher NICHT versendet - Apps Script darf den Lead als send_failed markieren. */
export class NotSentError extends Error {}

export interface SendDeps {
  openImap(): Promise<Wire>;
  openSmtp(): Promise<Wire>;
}

export type SendResult = { status: 'sent' | 'already_sent' | 'sent_unfiled'; to: string; warning?: string };

/**
 * Entwurfs-Kopf fuer den Versand bereinigen: X-Unsent (Outlook-Entwurfsmarke)
 * entfernen, Date auf den Sendezeitpunkt setzen. Ein Entwurf kann Tage in der
 * Warteschlange liegen; ein altes Datum sortiert die Mail beim Empfaenger nach
 * unten und ist ein Spam-Signal. Der Rumpf bleibt byte-identisch.
 */
export function prepareOutgoing(raw: Uint8Array, now: Date): Uint8Array {
  let cut = -1;
  for (let i = 0; i + 3 < raw.length; i++) {
    if (raw[i] === 13 && raw[i + 1] === 10 && raw[i + 2] === 13 && raw[i + 3] === 10) { cut = i; break; }
  }
  if (cut < 0) return raw;
  const kopf = new TextDecoder().decode(raw.subarray(0, cut));
  const zeilen: string[] = [];
  let skip = false;
  for (const z of kopf.split('\r\n')) {
    if (/^[ \t]/.test(z)) { if (!skip) zeilen.push(z); continue; }
    skip = /^(x-unsent|date):/i.test(z);
    if (!skip) zeilen.push(z);
  }
  zeilen.push('Date: ' + now.toUTCString().replace('GMT', '+0000'));
  const neu = new TextEncoder().encode(zeilen.join('\r\n'));
  const out = new Uint8Array(neu.length + (raw.length - cut));
  out.set(neu);
  out.set(raw.subarray(cut), neu.length);
  return out;
}

/**
 * Sendet genau einen Entwurf, der bereits im eigenen Postfach liegt.
 * Die Bridge kann keine frei formulierten Mails senden - nur das, was
 * Apps Script vorher als gepruefter Entwurf abgelegt hat.
 */
export async function sendDraft(deps: SendDeps, creds: Creds, fromAddr: string, messageId: string): Promise<SendResult> {
  const pre = await withSession(await deps.openImap(), creds, async (s) => {
    await s.command(`EXAMINE ${SENT}`);
    if (searchNumbers(await s.command(`SEARCH HEADER Message-ID ${quote(messageId)}`)).length) {
      return { already: true, raw: null as Uint8Array | null };
    }
    await s.command(`EXAMINE ${DRAFTS}`);
    const nums = searchNumbers(await s.command(`SEARCH HEADER Message-ID ${quote(messageId)}`));
    if (!nums.length) return { already: false, raw: null };
    const fetched = await s.command(`FETCH ${nums[nums.length - 1]} (BODY.PEEK[])`);
    return { already: false, raw: fetched.find((u) => u.literal)?.literal ?? null };
  });
  if (pre.already) return { status: 'already_sent', to: '' };
  if (!pre.raw) throw new NotSentError('Entwurf nicht gefunden');
  const raw = pre.raw;

  const kopf = new TextDecoder().decode(raw.subarray(0, 16384)).split('\r\n\r\n')[0] + '\r\n';
  const h = parseHeaders(kopf);
  if (!(h['from'] || '').toLowerCase().includes('<' + fromAddr.toLowerCase() + '>')) throw new NotSentError('Absender passt nicht zum Postfach');
  if (h['message-id'] !== messageId) throw new NotSentError('Message-ID passt nicht');
  if (h['cc'] || h['bcc']) throw new NotSentError('Cc/Bcc im Entwurf nicht erlaubt');
  const toHeader = h['to'] || '';
  const to = firstAddress(toHeader);
  if (!to || /[,;]/.test(toHeader)) throw new NotSentError('Genau ein Empfaenger erforderlich');

  const out = prepareOutgoing(raw, new Date());
  try {
    await smtpSend(await deps.openSmtp(), creds, fromAddr, to, out);
  } catch (e) {
    if (e instanceof SmtpError && e.beforeData) throw new NotSentError(e.message);
    throw e;
  }

  try {
    await withSession(await deps.openImap(), creds, async (s) => {
      await s.command(`APPEND ${SENT} (\\Seen)`, out);
      await s.command(`SELECT ${DRAFTS}`);
      const nums = searchNumbers(await s.command(`SEARCH HEADER Message-ID ${quote(messageId)}`));
      for (const n of nums) await s.command(`STORE ${n} +FLAGS (\\Deleted)`);
      if (nums.length) await s.command('EXPUNGE');
    });
    return { status: 'sent', to };
  } catch (e) {
    return { status: 'sent_unfiled', to, warning: 'Gesendet, Ablage fehlgeschlagen: ' + String((e as Error).message).slice(0, 120) };
  }
}
```

- [ ] **Step 6: Tests laufen lassen**

Run: `npx vitest run && npx tsc --noEmit`
Expected: alle Tests PASS (Basisplan + Task 1 + 9 neue).

- [ ] **Step 7: Commit**

```bash
cd ~/KI-System/02_Projects/active/hsb-boden
python3 scripts/verify_ssot.py
git add apps/sales-os/com_bridge/src/mailbox.ts apps/sales-os/com_bridge/src/send.ts apps/sales-os/com_bridge/test/fake_server.ts apps/sales-os/com_bridge/test/send.test.ts
git commit -m "feat(sales-os): COM-Bridge sendet nur vorhandene Entwuerfe, idempotent ueber Gesendet"
```

---

### Task 3: `listInbox` und Routen `/send`, `/inbox`

**Files:**
- Modify: `apps/sales-os/com_bridge/src/mailbox.ts` (anhängen)
- Replace: `apps/sales-os/com_bridge/src/handler.ts`
- Modify: `apps/sales-os/com_bridge/src/socket.ts`, `src/index.ts`
- Test: `apps/sales-os/com_bridge/test/inbox.test.ts`

**Interfaces:**
- Produces:
  - `interface InboxMessage { id: string; subject: string; from: { emailAddress: { address: string } }; receivedDateTime: string; internetMessageId: string; bodyPreview: string; dsn: boolean; autoReply: boolean }`
  - `listInbox(wire, creds, days, now): Promise<InboxMessage[]>`
  - `decodeWords(s: string): string`
  - HTTP: `POST /send?owner&messageId` → 200 `{ok:true,status,to,warning?}` | 409 `{ok:false,sent:false,error}` | 502 `{ok:false,sent:false|'unklar',error}`; `GET /inbox?owner&days` → 200 `{ok:true,messages:InboxMessage[]}`
  - `createHandler(openWire: (host: string, port: number) => Promise<Wire>, now?)`

- [ ] **Step 1: Failing Tests schreiben**

`apps/sales-os/com_bridge/test/inbox.test.ts`:

```ts
import { describe, expect, it } from 'vitest';
import { createHandler, type Env } from '../src/handler';
import { decodeWords, listInbox } from '../src/mailbox';
import { FakeImap, eml } from './fake_server';
import { FakeSmtp } from './fake_smtp';

const creds = { user: 'u', pass: 'p' };
const NOW = new Date('2026-09-28T10:00:00Z');
const env: Env = {
  IMAP_HOST: 'imap.test', JOEL_EMAIL: 'j-cherino@hsb-boden.com', JORDI_EMAIL: 'j-post@hsb-boden.com',
  BRIDGE_TOKEN: 'tok', JOEL_USER: 'u1', JOEL_PASS: 'p1', JORDI_USER: 'u2', JORDI_PASS: 'p2',
};

const DSN = [
  'From: Mail Delivery System <MAILER-DAEMON@w0221a9f.kasserver.com>',
  'To: j-cherino@hsb-boden.com',
  'Subject: Undelivered Mail Returned to Sender',
  'Message-ID: <dsn1@kas>',
  'Date: Mon, 28 Sep 2026 09:00:00 +0200',
  'Auto-Submitted: auto-replied',
  'Content-Type: multipart/report; report-type=delivery-status; boundary="b"',
  '',
  '--b',
  'Final-Recipient: rfc822; weg@firma.de',
  'Status: 5.1.1',
  '',
].join('\r\n');

const OOO = [
  'From: Max <max@firma.de>',
  'To: j-cherino@hsb-boden.com',
  'Subject: =?UTF-8?Q?Automatische_Antwort:_Industrieb=C3=B6den?=',
  'Message-ID: <ooo1@firma>',
  'Date: Mon, 28 Sep 2026 09:05:00 +0200',
  'Auto-Submitted: auto-replied',
  '',
  'Ich bin bis 05.10.2026 im Urlaub.',
  '',
].join('\r\n');

describe('listInbox', () => {
  it('kennzeichnet Bounce (dsn) und Abwesenheit (autoReply) und dekodiert den Betreff', async () => {
    const srv = new FakeImap();
    srv.folders['"INBOX"'].push({ raw: DSN, flags: [] }, { raw: OOO, flags: [] }, { raw: eml('<r1@firma>', 'j-cherino@hsb-boden.com', 'Kunde <k@firma.de>'), flags: [] });
    const r = await listInbox(srv.wire(), creds, 14, NOW);
    expect(r).toHaveLength(3);
    expect(r[0]).toMatchObject({ dsn: true, internetMessageId: '<dsn1@kas>' });
    expect(r[0].bodyPreview).toContain('Final-Recipient: rfc822; weg@firma.de');
    expect(r[1]).toMatchObject({ dsn: false, autoReply: true, subject: 'Automatische Antwort: Industrieböden' });
    expect(r[1].from.emailAddress.address).toBe('max@firma.de');
    expect(r[2]).toMatchObject({ dsn: false, autoReply: false });
  });

  it('decodeWords dekodiert B- und Q-Kodierung und lässt Klartext unverändert', () => {
    expect(decodeWords('=?UTF-8?B?R3LDvMOfZQ==?=')).toBe('Grüße');
    expect(decodeWords('=?iso-8859-1?Q?Gr=FC=DFe?= aus NRW')).toBe('Grüße aus NRW');
    expect(decodeWords('Hallo')).toBe('Hallo');
  });
});

describe('Handler /send und /inbox', () => {
  function setup() {
    const imap = new FakeImap();
    const smtp = new FakeSmtp();
    const ports: number[] = [];
    const handle = createHandler(async (_h, port) => { ports.push(port); return port === 465 ? smtp.wire() : imap.wire(); }, () => NOW);
    return { imap, smtp, ports, handle };
  }
  const req = (path: string, method = 'POST') => new Request('https://bridge.test' + path, { method, headers: { Authorization: 'Bearer tok' } });
  const MID = '<hsb.L1.B1@hsb-boden.com>';

  it('/send sendet über Port 465 und meldet status sent', async () => {
    const { imap, handle, ports } = setup();
    imap.folders['"Entw&APw-rfe"'].push({ raw: eml(MID), flags: ['\\Draft'] });
    const res = await handle(req(`/send?owner=JOEL&messageId=${encodeURIComponent(MID)}`), env);
    expect(res.status).toBe(200);
    expect(await res.json()).toMatchObject({ ok: true, status: 'sent', to: 'kunde@firma.de' });
    expect(ports).toContain(465);
  });

  it('/send ohne Entwurf → 409 sent:false', async () => {
    const { handle } = setup();
    const res = await handle(req(`/send?owner=JOEL&messageId=${encodeURIComponent(MID)}`), env);
    expect(res.status).toBe(409);
    expect(await res.json()).toMatchObject({ ok: false, sent: false });
  });

  it('/send Abbruch nach DATA → 502 sent:unklar', async () => {
    const { imap, smtp, handle } = setup();
    imap.folders['"Entw&APw-rfe"'].push({ raw: eml(MID), flags: ['\\Draft'] });
    smtp.dropAfterData = true;
    const res = await handle(req(`/send?owner=JOEL&messageId=${encodeURIComponent(MID)}`), env);
    expect(res.status).toBe(502);
    expect(await res.json()).toMatchObject({ ok: false, sent: 'unklar' });
  });

  it('/send per GET → 405', async () => {
    const { handle } = setup();
    expect((await handle(req(`/send?owner=JOEL&messageId=${encodeURIComponent(MID)}`, 'GET'), env)).status).toBe(405);
  });

  it('/inbox liefert Nachrichten', async () => {
    const { imap, handle } = setup();
    imap.folders['"INBOX"'].push({ raw: DSN, flags: [] });
    const res = await handle(req('/inbox?owner=JOEL&days=14', 'GET'), env);
    expect(res.status).toBe(200);
    const b = await res.json() as { messages: { dsn: boolean }[] };
    expect(b.messages[0].dsn).toBe(true);
  });
});
```

- [ ] **Step 2: Test laufen lassen, er muss scheitern**

Run: `npx vitest run test/inbox.test.ts`
Expected: FAIL, `listInbox`/`decodeWords` nicht exportiert.

- [ ] **Step 3: `listInbox` und `decodeWords` an `mailbox.ts` anhängen**

Am Ende von `apps/sales-os/com_bridge/src/mailbox.ts`:

```ts
export const INBOX = '"INBOX"';

export interface InboxMessage {
  id: string;
  subject: string;
  from: { emailAddress: { address: string } };
  receivedDateTime: string;
  internetMessageId: string;
  bodyPreview: string;
  dsn: boolean;
  autoReply: boolean;
}

function bytesFromBase64(s: string): Uint8Array {
  const bin = atob(s);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

/** RFC 2047 encoded-words (B und Q) in Klartext. Unbekannte Zeichensaetze bleiben roh. */
export function decodeWords(s: string): string {
  return s.replace(/=\?([^?]+)\?([BbQq])\?([^?]*)\?=\s*(?==\?)/g, '=?$1?$2?$3?=').replace(/=\?([^?]+)\?([BbQq])\?([^?]*)\?=/g, (all, cs: string, mode: string, data: string) => {
    try {
      let b: Uint8Array;
      if (mode.toUpperCase() === 'B') {
        b = bytesFromBase64(data);
      } else {
        const t = data.replace(/_/g, ' ');
        const arr: number[] = [];
        for (let i = 0; i < t.length; i++) {
          if (t[i] === '=' && /^[0-9A-Fa-f]{2}$/.test(t.slice(i + 1, i + 3))) { arr.push(parseInt(t.slice(i + 1, i + 3), 16)); i += 2; }
          else arr.push(t.charCodeAt(i));
        }
        b = Uint8Array.from(arr);
      }
      return new TextDecoder(cs.toLowerCase()).decode(b);
    } catch {
      return all;
    }
  });
}

function seqOf(line: string): string {
  return (line.match(/^\* (\d+) FETCH/) || [])[1] || '';
}

/** Posteingang der letzten `days` Tage (nur lesend) im Graph-Format plus Bounce-/Autoreply-Kennzeichen. */
export async function listInbox(wire: Wire, creds: Creds, days: number, now: Date): Promise<InboxMessage[]> {
  return withSession(wire, creds, async (s) => {
    await s.command(`EXAMINE ${INBOX}`);
    const since = new Date(now.getTime() - days * 86400000);
    const nums = searchNumbers(await s.command(`SEARCH SINCE ${imapDate(since)}`)).slice(-MAX_SENT);
    if (!nums.length) return [];
    const set = nums.join(',');
    const heads = await s.command(`FETCH ${set} (BODY.PEEK[HEADER.FIELDS (FROM SUBJECT MESSAGE-ID DATE AUTO-SUBMITTED X-AUTOREPLY X-AUTORESPOND PRECEDENCE CONTENT-TYPE)])`);
    const texts = await s.command(`FETCH ${set} (BODY.PEEK[TEXT]<0.2000>)`);
    const dec = new TextDecoder();
    const textBySeq = new Map<string, string>();
    for (const u of texts) if (u.literal) textBySeq.set(seqOf(u.line), dec.decode(u.literal));
    return heads.filter((u) => u.literal).map((u) => {
      const h = parseHeaders(dec.decode(u.literal));
      const seq = seqOf(u.line);
      const ct = (h['content-type'] || '').toLowerCase();
      const auto = (h['auto-submitted'] || '').toLowerCase();
      const prec = (h['precedence'] || '').toLowerCase();
      const date = new Date(h['date'] || '');
      return {
        id: h['message-id'] || `COM-IN-${seq}`,
        subject: decodeWords(h['subject'] || ''),
        from: { emailAddress: { address: firstAddress(h['from'] || '') } },
        receivedDateTime: isNaN(date.getTime()) ? '' : date.toISOString(),
        internetMessageId: h['message-id'] || '',
        bodyPreview: (textBySeq.get(seq) || '').slice(0, 2000),
        dsn: ct.includes('multipart/report') && ct.includes('delivery-status'),
        autoReply: (auto !== '' && auto !== 'no') || 'x-autoreply' in h || 'x-autorespond' in h || prec === 'auto_reply',
      };
    });
  });
}
```

Zusätzlich in `listSent` derselben Datei `subject: h['subject'] || '',` ersetzen durch `subject: decodeWords(h['subject'] || ''),`.

- [ ] **Step 4: Socket mit Port-Parameter**

`apps/sales-os/com_bridge/src/socket.ts`: Signatur und `connect`-Aufruf ändern zu

```ts
export async function openSocketWire(host: string, port: number): Promise<Wire> {
  const socket = connect({ hostname: host, port }, { secureTransport: 'on', allowHalfOpen: false });
```

(Rest der Datei unverändert.)

- [ ] **Step 5: `handler.ts` vollständig ersetzen**

`apps/sales-os/com_bridge/src/handler.ts`:

```ts
import { ImapError, type Wire } from './imap';
import { appendDraft, listInbox, listSent, type Creds } from './mailbox';
import { NotSentError, SMTP_PORT, sendDraft } from './send';
import { SmtpError } from './smtp';

export interface Env {
  IMAP_HOST: string;
  JOEL_EMAIL: string;
  JORDI_EMAIL: string;
  BRIDGE_TOKEN: string;
  JOEL_USER: string;
  JOEL_PASS: string;
  JORDI_USER: string;
  JORDI_PASS: string;
}

type Owner = 'JOEL' | 'JORDI';
const IMAP_PORT = 993;
const MESSAGE_ID = /^<[A-Za-z0-9._-]+@hsb-boden\.com>$/;
const MAX_EML_BYTES = 10 * 1024 * 1024;
const ROUTES = ['/draft', '/sent', '/send', '/inbox'];

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

function sameToken(a: string, b: string): boolean {
  if (!a || !b || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function ownerOf(v: string | null): Owner | null {
  return v === 'JOEL' || v === 'JORDI' ? v : null;
}

function credsFor(env: Env, owner: Owner): Creds {
  return owner === 'JOEL' ? { user: env.JOEL_USER, pass: env.JOEL_PASS } : { user: env.JORDI_USER, pass: env.JORDI_PASS };
}

function mailboxFor(env: Env, owner: Owner): string {
  return (owner === 'JOEL' ? env.JOEL_EMAIL : env.JORDI_EMAIL).toLowerCase();
}

function emlHeaders(eml: Uint8Array): Record<string, string> {
  const text = new TextDecoder().decode(eml.subarray(0, 16384));
  const head = text.split('\r\n\r\n')[0].replace(/\r\n[ \t]+/g, ' ');
  const out: Record<string, string> = {};
  for (const line of head.split('\r\n')) {
    const i = line.indexOf(':');
    if (i > 0) out[line.slice(0, i).trim().toLowerCase()] = line.slice(i + 1).trim();
  }
  return out;
}

function days(url: URL): number | null {
  const d = Number(url.searchParams.get('days') || '14');
  return Number.isInteger(d) && d >= 1 && d <= 60 ? d : null;
}

export function createHandler(openWire: (host: string, port: number) => Promise<Wire>, now: () => Date = () => new Date()) {
  return async function handle(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    const auth = req.headers.get('Authorization') || '';
    if (!sameToken(auth.replace(/^Bearer /, ''), env.BRIDGE_TOKEN)) return json(401, { ok: false, error: 'unauthorized' });

    const route = url.pathname;
    if (!ROUTES.includes(route)) return json(404, { ok: false, error: 'not_found' });
    const wantMethod = route === '/draft' || route === '/send' ? 'POST' : 'GET';
    if (req.method !== wantMethod) return json(405, { ok: false, error: 'method_not_allowed' });
    const owner = ownerOf(url.searchParams.get('owner'));
    if (!owner) return json(400, { ok: false, error: 'owner' });
    const imap = () => openWire(env.IMAP_HOST, IMAP_PORT);

    if (route === '/send') {
      const messageId = url.searchParams.get('messageId') || '';
      if (!MESSAGE_ID.test(messageId)) return json(400, { ok: false, sent: false, error: 'messageId' });
      try {
        const r = await sendDraft({ openImap: imap, openSmtp: () => openWire(env.IMAP_HOST, SMTP_PORT) }, credsFor(env, owner), mailboxFor(env, owner), messageId);
        return json(200, { ok: true, ...r });
      } catch (e) {
        if (e instanceof NotSentError) return json(409, { ok: false, sent: false, error: e.message });
        if (e instanceof ImapError) return json(502, { ok: false, sent: false, error: 'imap: ' + e.message });
        if (e instanceof SmtpError) return json(502, { ok: false, sent: 'unklar', error: 'smtp: ' + e.message });
        return json(502, { ok: false, sent: 'unklar', error: 'bridge: ' + String((e as Error).message || e).slice(0, 120) });
      }
    }

    try {
      if (route === '/draft') {
        const messageId = url.searchParams.get('messageId') || '';
        if (!MESSAGE_ID.test(messageId)) return json(400, { ok: false, error: 'messageId' });
        const eml = new Uint8Array(await req.arrayBuffer());
        if (!eml.length || eml.length > MAX_EML_BYTES) return json(400, { ok: false, error: 'eml_size' });
        const h = emlHeaders(eml);
        if (!(h['from'] || '').toLowerCase().includes('<' + mailboxFor(env, owner) + '>')) {
          return json(400, { ok: false, error: 'from_passt_nicht_zum_postfach' });
        }
        if (h['message-id'] !== messageId) return json(400, { ok: false, error: 'messageId_nicht_in_eml' });
        const r = await appendDraft(await imap(), credsFor(env, owner), messageId, eml);
        return json(200, { ok: true, draftId: messageId, internetMessageId: messageId, storedSize: r.storedSize, duplicate: r.duplicate });
      }
      const d = days(url);
      if (d === null) return json(400, { ok: false, error: 'days' });
      if (route === '/sent') return json(200, { ok: true, messages: await listSent(await imap(), credsFor(env, owner), d, now()) });
      return json(200, { ok: true, messages: await listInbox(await imap(), credsFor(env, owner), d, now()) });
    } catch (e) {
      if (e instanceof ImapError) return json(502, { ok: false, error: 'imap: ' + e.message });
      return json(502, { ok: false, error: 'bridge: ' + String((e as Error).message || e).slice(0, 120) });
    }
  };
}
```

`apps/sales-os/com_bridge/src/index.ts` bleibt unverändert (`createHandler(openSocketWire)` passt, weil `openSocketWire(host, port)` jetzt beide Parameter nimmt).

- [ ] **Step 6: Tests laufen lassen**

Run: `npx vitest run && npx tsc --noEmit && npx wrangler deploy --dry-run --outdir /tmp/hsb-com-bridge-dry`
Expected: alle Tests PASS (inklusive Basisplan-`handler.test.ts`: Die Route `/unbekannt` liefert weiter 404), `tsc` still, Dry-Run ohne Fehler.

- [ ] **Step 7: Commit**

```bash
cd ~/KI-System/02_Projects/active/hsb-boden
python3 scripts/verify_ssot.py
git add apps/sales-os/com_bridge/src/mailbox.ts apps/sales-os/com_bridge/src/handler.ts apps/sales-os/com_bridge/src/socket.ts apps/sales-os/com_bridge/test/inbox.test.ts
git commit -m "feat(sales-os): COM-Bridge Routen /send und /inbox mit Bounce-/Autoreply-Kennzeichen"
```

---

### Task 4: Gates auf Inhaber-Entscheidung umstellen (Legal_Basis, Versandfreigabe)

**Files:**
- Modify: `apps/sales-os/apps_script/Engine.gs` (`checkEligibility_`)
- Test: `apps/sales-os/tests/test_apps_script.js` (`testEligibility`)

**Interfaces:** `checkEligibility_(lead)` unverändert in Signatur und Rückgabe.

- [ ] **Step 1: Tests an die neue Regel anpassen (sie müssen dann scheitern)**

In `apps/sales-os/tests/test_apps_script.js`, Funktion `testEligibility`:
- Zeile `['Legal_Basis=UNKNOWN blockiert', { Legal_Basis: 'UNKNOWN' }],` **löschen**.
- Den Block

```js
  check('leeres Legal_Basis faellt auf UNKNOWN zurueck',
        !ctx.checkEligibility_(Object.assign({}, base,
          { Legal_Basis: '', Opt_In: 'unknown' })).eligible);
```

ersetzen durch

```js
  // Inhaber-Entscheidung 2026-09-27: alle Leads anwaltlich geprueft, nur BLOCKED sperrt.
  check('Legal_Basis UNKNOWN ist sendefaehig',
        ctx.checkEligibility_(Object.assign({}, base, { Legal_Basis: 'UNKNOWN' })).eligible);
  check('leeres Legal_Basis ist sendefaehig',
        ctx.checkEligibility_(Object.assign({}, base, { Legal_Basis: '', Opt_In: 'unknown' })).eligible);
  check('Legal_Basis no ist sendefaehig',
        ctx.checkEligibility_(Object.assign({}, base, { Legal_Basis: 'no' })).eligible);
```

(`['Legal_Basis=BLOCKED blockiert', { Legal_Basis: 'BLOCKED' }],` bleibt.)
- Zeile `['Versandfreigabe=no blockiert', { Versandfreigabe: 'no' }],` **löschen** und nach dem `cases.forEach(…)`-Block einfügen:

```js
  // Inhaber-Entscheidung 2026-09-27: Freigabe erfolgt per Haekchen in der Sidebar.
  check('Versandfreigabe no sperrt Entwuerfe nicht mehr',
        ctx.checkEligibility_(Object.assign({}, base, { Versandfreigabe: 'no' })).eligible);
```

Run: Offline-Suite. Expected: `ROT: test_apps_script` mit `FAIL … Legal_Basis UNKNOWN ist sendefaehig`.

- [ ] **Step 2: Regel ändern**

In `apps/sales-os/apps_script/Engine.gs`, `checkEligibility_`, den Block

```js
  if (LEGAL_BASIS_SENDABLE.indexOf(legal) === -1) {
    reasons.push('Legal_Basis=' + legal);
  }
```

ersetzen durch

```js
  // Inhaber-Entscheidung 2026-09-27: Alle Leads im Sales OS sind anwaltlich
  // geprueft und duerfen kontaktiert werden. Nur ein ausdruecklich gesetztes
  // BLOCKED sperrt weiterhin.
  if (legal === 'BLOCKED') {
    reasons.push('Legal_Basis=BLOCKED');
  }
```

In derselben Funktion den Block

```js
  if (!isTrue_(lead.Versandfreigabe)) {
    reasons.push('Versandfreigabe=' + (lead.Versandfreigabe || 'leer'));
  }
```

ersatzlos entfernen und an seiner Stelle einfügen:

```js
  // Inhaber-Entscheidung 2026-09-27: Die Freigabe ist das Haekchen in der
  // Sidebar (uiComEinreihen schreibt Versandfreigabe=yes und Approved_At).
```

- [ ] **Step 3: Offline-Suite**

Expected: keine Zeile `ROT:`. Wird ein anderer Test rot, weil er `UNKNOWN` oder `Versandfreigabe=no` als gesperrt erwartet (z. B. Zähler `no_release_count` in `prepareBatch`-Tests): genau diese Erwartung auf die Inhaber-Entscheidung umstellen und im Commit nennen. Sonst nichts ändern.

- [ ] **Step 4: Commit**

```bash
cd ~/KI-System/02_Projects/active/hsb-boden
python3 scripts/verify_ssot.py
python3 apps/sales-os/engine/build_single.py
cp apps/sales-os/apps_script/HSB_SALES_OS.gs apps/sales-os/deploy/HSB_SALES_OS.js
git add apps/sales-os/apps_script/Engine.gs apps/sales-os/apps_script/HSB_SALES_OS.gs apps/sales-os/deploy/HSB_SALES_OS.js apps/sales-os/tests/test_apps_script.js
git commit -m "feat(sales-os): Legal-Gate nach Inhaber-Entscheidung 2026-09-27 (nur BLOCKED sperrt)"
```

---

### Task 5: Versandsteuerung in Apps Script (`HSB_ComVersand.gs`)

**Files:**
- Create: `apps/sales-os/apps_script/HSB_ComVersand.gs`
- Modify: `apps/sales-os/deploy.sh`, `apps/sales-os/deploy/.claspignore`
- Test: `apps/sales-os/tests/test_com_versand.js`

**Interfaces:**
- Consumes: `comBridgeKonfig_`, `comBridgeAktiv_` (Basisplan Task 4); bestehend `readLeads_`, `normalizeOwner_`, `checkEligibility_`, `logActivity_`, `invalidateLeadsCache_`, `renderEmail_`, `bodyHtmlMitSignatur_`, `FLYERS`.
- Produces:
  - `COM_VERSAND` (Konstanten)
  - `comTagKey_(d: Date): string`, `comImFenster_(d: Date): boolean`, `comTageslimit_(startIso: string, jetzt: Date): number`, `comDatumKey_(v): string`
  - `comEntscheide_(leads, ownerKey, jetzt, zustand{startIso,pause,zufall}) → { aktion: 'senden'|'warten'|'pausieren', lead?, grund?, gesperrt: [{lead, grund}] }`
  - `comVersandTakt()`, `comEinenSenden_(lead, owner, props)`, `comFelderSetzen_(row, set)`
  - Sidebar: `uiComUebersicht(owner)`, `uiComEinreihen(owner, leadIds)`, `uiComVorschauOeffnen(leadId)`, `uiComPauseAufheben()`, `uiComVersandEinrichten()`

- [ ] **Step 1: Failing Test schreiben**

`apps/sales-os/tests/test_com_versand.js`:

```js
/**
 * Testet die Versandsteuerung: Fenster, Tageslimit mit Warm-up, Notbremse,
 * Firmen-Stopp, Neupruefung vor dem Senden und die sichere Behandlung
 * unklarer Ergebnisse. Geprueft wird die ausgelieferte Datei (deploy/).
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const DEPLOY = path.join(path.resolve(__dirname, '..'), 'deploy');
let bestanden = 0;
let fehlgeschlagen = 0;
function pruefe(name, ok, detail) {
  if (ok) { bestanden++; console.log('PASS  ' + name); }
  else { fehlgeschlagen++; console.log('FAIL  ' + name + (detail ? '  (' + detail + ')' : '')); }
}

function formatDate(d, tz, fmt) {
  const p = {};
  new Intl.DateTimeFormat('en-GB', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false, weekday: 'short' })
    .formatToParts(d).forEach(function (x) { p[x.type] = x.value; });
  const h = String(Number(p.hour) % 24).padStart(2, '0');
  if (fmt === 'yyyy-MM-dd') return p.year + '-' + p.month + '-' + p.day;
  if (fmt === 'u') return String(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].indexOf(p.weekday) + 1);
  if (fmt === 'H') return String(Number(h));
  if (fmt === 'yyyy-MM-dd HH:mm:ss') return p.year + '-' + p.month + '-' + p.day + ' ' + h + ':' + p.minute + ':' + p.second;
  throw new Error('Format im Test nicht nachgebaut: ' + fmt);
}

function kontext(opt) {
  opt = opt || {};
  const geschrieben = [];
  const props = Object.assign({}, opt.props || {});
  const k = {
    console: console,
    Utilities: { formatDate: formatDate },
    normalizeOwner_: function (o) { const s = String(o || '').toUpperCase(); return s.indexOf('JOEL') >= 0 ? 'JOEL' : (s.indexOf('JORD') >= 0 ? 'JORDI' : ''); },
    checkEligibility_: function (l) { return { eligible: String(l.Opt_Out || '') !== 'yes', reasons: String(l.Opt_Out || '') === 'yes' ? ['Opt_Out=YES'] : [] }; },
    comBridgeKonfig_: function () { return { url: 'https://bridge.test', token: 'tok' }; },
    comBridgeAktiv_: function () { return true; },
    logActivity_: function () {},
    invalidateLeadsCache_: function () {},
    PropertiesService: { getScriptProperties: function () { return {
      getProperty: function (n) { return props[n] || null; },
      setProperty: function (n, v) { props[n] = v; },
      deleteProperty: function (n) { delete props[n]; } }; } },
    LockService: { getScriptLock: function () { return { tryLock: function () { return true; }, releaseLock: function () {} }; } },
    UrlFetchApp: { fetch: function (url, o) { return opt.antwort(url, o); } },
    readLeads_: function () { return { leads: opt.leads || [] }; },
    Math: Object.create(Math)
  };
  k.Math.random = function () { return opt.zufall === undefined ? 0.9 : opt.zufall; };
  vm.createContext(k);
  vm.runInContext(fs.readFileSync(path.join(DEPLOY, 'HSB_ComVersand.js'), 'utf8'), k);
  // Schreibzugriffe abfangen, statt ein Sheet nachzubauen.
  k.comFelderSetzen_ = function (row, set) { geschrieben.push({ row: row, set: set }); };
  k._geschrieben = geschrieben;
  k._props = props;
  return k;
}

function lead(id, extra) {
  return Object.assign({ _row: id, Lead_ID: 'L' + id, Owner: 'Joel Cherino', Email: 'a' + id + '@firma' + id + '.de',
    Send_Status: 'queued', Draft_ID: '<hsb.L' + id + '.B@hsb-boden.com>', Reply_Status: '', Bounce_Status: '', Sent_At: '', Opt_Out: 'no' }, extra || {});
}

// Mo 28.09.2026 10:00 Berlin = 08:00 UTC
const MO_10 = new Date('2026-09-28T08:00:00Z');
const ZUSTAND = { startIso: '', pause: '', zufall: 0.9 };

(function fenster() {
  const k = kontext();
  pruefe('Sonntag 10 Uhr ausserhalb Fenster', !k.comImFenster_(new Date('2026-09-27T08:00:00Z')));
  pruefe('Montag 07:59 ausserhalb Fenster', !k.comImFenster_(new Date('2026-09-28T05:59:00Z')));
  pruefe('Montag 08:00 im Fenster', k.comImFenster_(new Date('2026-09-28T06:00:00Z')));
  pruefe('Freitag 16:59 im Fenster', k.comImFenster_(new Date('2026-10-02T14:59:00Z')));
  pruefe('Freitag 17:00 ausserhalb Fenster', !k.comImFenster_(new Date('2026-10-02T15:00:00Z')));
})();

(function staffel() {
  const k = kontext();
  pruefe('ohne Start Woche 1 = 10', k.comTageslimit_('', MO_10) === 10);
  pruefe('Tag 15 = Woche 3 = 30', k.comTageslimit_('2026-09-13', MO_10) === 30);
  pruefe('nach 2 Monaten = 50', k.comTageslimit_('2026-07-01', MO_10) === 50);
  pruefe('Datum aus Sheet (Date, ISO, deutsch)',
    k.comDatumKey_(new Date('2026-09-28T08:00:00Z')) === '2026-09-28' &&
    k.comDatumKey_('2026-09-28T07:49:41+00:00') === '2026-09-28' &&
    k.comDatumKey_('28.9.2026') === '2026-09-28');
})();

(function entscheidung() {
  const k = kontext();
  let e = k.comEntscheide_([lead(1)], 'JOEL', MO_10, ZUSTAND);
  pruefe('sendet den ersten eingereihten .com-Entwurf', e.aktion === 'senden' && e.lead.Lead_ID === 'L1', JSON.stringify(e));

  e = k.comEntscheide_([lead(1)], 'JOEL', new Date('2026-09-27T08:00:00Z'), ZUSTAND);
  pruefe('am Sonntag wird gewartet', e.aktion === 'warten');

  e = k.comEntscheide_([lead(1, { Owner: 'Jordie Post' })], 'JOEL', MO_10, ZUSTAND);
  pruefe('fremde Leads werden ignoriert', e.aktion === 'warten');

  e = k.comEntscheide_([lead(1, { Draft_ID: 'AAMkA-outlook' })], 'JOEL', MO_10, ZUSTAND);
  pruefe('.de-Entwurf wird nie ueber .com gesendet', e.aktion === 'warten');

  const zehn = [];
  for (let i = 10; i < 20; i++) zehn.push(lead(i, { Send_Status: 'sent', Sent_At: '2026-09-28 09:00:00' }));
  e = k.comEntscheide_(zehn.concat([lead(1)]), 'JOEL', MO_10, ZUSTAND);
  pruefe('Tageslimit Woche 1 (10) stoppt', e.aktion === 'warten' && /Tageslimit/.test(e.grund), e.grund);

  e = k.comEntscheide_([lead(1)], 'JOEL', MO_10, { startIso: '', pause: 'Bounce-Quote 4 %', zufall: 0.9 });
  pruefe('aktive Pause stoppt', e.aktion === 'warten' && /Notbremse/.test(e.grund));

  e = k.comEntscheide_([lead(1)], 'JOEL', MO_10, { startIso: '', pause: '', zufall: 0.1 });
  pruefe('zufaellig ausgelassener Takt', e.aktion === 'warten');

  const woche = [];
  for (let i = 30; i < 55; i++) woche.push(lead(i, { Send_Status: 'sent', Sent_At: '2026-09-24' }));
  woche[0].Bounce_Status = 'hard_bounce';
  e = k.comEntscheide_(woche.concat([lead(1)]), 'JOEL', MO_10, { startIso: '2026-09-01', pause: '', zufall: 0.9 });
  pruefe('Notbremse bei 1/25 = 4 % Hard Bounces', e.aktion === 'pausieren', JSON.stringify(e));
  woche[0].Bounce_Status = '';
  e = k.comEntscheide_(woche.concat([lead(1)]), 'JOEL', MO_10, { startIso: '2026-09-01', pause: '', zufall: 0.9 });
  pruefe('ohne Bounces keine Notbremse', e.aktion === 'senden');

  e = k.comEntscheide_([lead(1, { Email: 'x@firmaA.de' }), lead(2, { Email: 'y@firmaA.de', Send_Status: 'sent', Reply_Status: 'reply', Sent_At: '2026-09-20' }), lead(3)], 'JOEL', MO_10, ZUSTAND);
  pruefe('Firmen-Stopp: Domain mit Antwort wird uebersprungen', e.aktion === 'senden' && e.lead.Lead_ID === 'L3', JSON.stringify(e.lead && e.lead.Lead_ID));

  e = k.comEntscheide_([lead(1, { Opt_Out: 'yes' }), lead(2)], 'JOEL', MO_10, ZUSTAND);
  pruefe('gesperrter Lead wird uebersprungen und markiert', e.aktion === 'senden' && e.lead.Lead_ID === 'L2' && e.gesperrt.length === 1 && e.gesperrt[0].lead.Lead_ID === 'L1');
})();

function antwort(code, body) {
  return { getResponseCode: function () { return code; }, getContentText: function () { return JSON.stringify(body); } };
}

(function einSenden() {
  const k = kontext({ antwort: function () { return antwort(200, { ok: true, status: 'sent', to: 'a1@firma1.de' }); } });
  const r = k.comEinenSenden_(lead(1), 'JOEL', k.PropertiesService.getScriptProperties());
  const letzte = k._geschrieben[k._geschrieben.length - 1].set;
  pruefe('Erfolg setzt sent, Datum und SENT', r.aktion === 'gesendet' && letzte.Send_Status === 'sent' && letzte.Batch_Status === 'SENT' && /^\d{4}-\d{2}-\d{2} /.test(letzte.Send_Datum));
  pruefe('erster Versand startet das Warm-up', /^\d{4}-\d{2}-\d{2}$/.test(k._props.HSB_COM_WARMUP_START || ''));
  pruefe('vor dem Aufruf wird sending gesetzt', k._geschrieben[0].set.Send_Status === 'sending');

  const k2 = kontext({ antwort: function () { return antwort(409, { ok: false, sent: false, error: 'Entwurf nicht gefunden' }); } });
  k2.comEinenSenden_(lead(1), 'JOEL', k2.PropertiesService.getScriptProperties());
  pruefe('sicher nicht gesendet → send_failed', k2._geschrieben[1].set.Send_Status === 'send_failed');

  const k3 = kontext({ antwort: function () { return antwort(502, { ok: false, sent: 'unklar', error: 'smtp: Nachricht: Verbindung geschlossen' }); } });
  k3.comEinenSenden_(lead(1), 'JOEL', k3.PropertiesService.getScriptProperties());
  pruefe('unklar wird nicht erneut gesendet (send_unklar)', k3._geschrieben[1].set.Send_Status === 'send_unklar' && /NICHT automatisch/.test(k3._geschrieben[1].set.Last_Error));

  const k4 = kontext({ antwort: function () { throw new Error('Timeout'); } });
  k4.comEinenSenden_(lead(1), 'JOEL', k4.PropertiesService.getScriptProperties());
  pruefe('Transportfehler ist unklar', k4._geschrieben[1].set.Send_Status === 'send_unklar');
})();

(function takt() {
  let aufrufe = 0;
  const k = kontext({ leads: [lead(1), lead(2, { Owner: 'Jordie Post' })], antwort: function () { aufrufe++; return antwort(200, { ok: true, status: 'sent' }); } });
  const r = k.comVersandTaktZu_(MO_10);
  pruefe('ein Takt sendet hoechstens eine Mail je Postfach', aufrufe === 2 && r.ergebnis.length === 2, JSON.stringify(r));

  let gelesen = 0;
  const k2 = kontext({ leads: [lead(1)], antwort: function () { return antwort(200, { ok: true }); } });
  k2.readLeads_ = function () { gelesen++; return { leads: [lead(1)] }; };
  k2.comVersandTaktZu_(new Date('2026-09-27T08:00:00Z'));
  pruefe('ausserhalb des Fensters kein Sheet-Lesezugriff', gelesen === 0);
})();

console.log('\n' + bestanden + ' bestanden, ' + fehlgeschlagen + ' fehlgeschlagen');
process.exit(fehlgeschlagen ? 1 : 0);
```

- [ ] **Step 2: Test laufen lassen, er muss scheitern**

Run (aus `apps/sales-os`): `node tests/test_com_versand.js`
Expected: FAIL, `ENOENT … deploy/HSB_ComVersand.js`.

- [ ] **Step 3: `HSB_ComVersand.gs` schreiben**

`apps/sales-os/apps_script/HSB_ComVersand.gs`:

```js
/**
 * HSB Sales OS - Versand ueber .com (Warteschlange, Tageslimit, Notbremse).
 *
 * Ablauf: Sidebar "Markierte senden" setzt Send_Status=queued. Ein
 * 10-Minuten-Trigger (comVersandTakt) entscheidet je Postfach, ob jetzt
 * genau eine Mail rausgeht, und laesst sie von der COM-Bridge senden.
 * Die Bridge sendet nur Entwuerfe, die bereits im .com-Postfach liegen.
 *
 * Alle Regeln stehen in comEntscheide_ - einer reinen Funktion ohne
 * Sheet-Zugriff, damit sie vollstaendig testbar ist.
 */

var COM_VERSAND = {
  TAGE: [1, 2, 3, 4, 5],
  VON_STUNDE: 8,
  BIS_STUNDE: 17,
  STAFFEL: [10, 20, 30, 40, 50],
  NOTBREMSE_QUOTE: 0.02,
  NOTBREMSE_MIN: 20,
  AUSLASSEN: 0.3,
  TAKT_MINUTEN: 10,
  PROP_START: 'HSB_COM_WARMUP_START',
  PROP_PAUSE: 'HSB_COM_VERSAND_PAUSE',
  HANDLER: 'comVersandTakt',
  ZEITZONE: 'Europe/Berlin'
};

function comTagKey_(d) {
  return Utilities.formatDate(d, COM_VERSAND.ZEITZONE, 'yyyy-MM-dd');
}

function comImFenster_(jetzt) {
  var tag = Number(Utilities.formatDate(jetzt, COM_VERSAND.ZEITZONE, 'u'));
  var std = Number(Utilities.formatDate(jetzt, COM_VERSAND.ZEITZONE, 'H'));
  return COM_VERSAND.TAGE.indexOf(tag) >= 0 && std >= COM_VERSAND.VON_STUNDE && std < COM_VERSAND.BIS_STUNDE;
}

/** Warm-up: Woche 1 -> 10, 2 -> 20, ... ab Woche 5 -> 50. Start = erster echter Versand. */
function comTageslimit_(startIso, jetzt) {
  var s = COM_VERSAND.STAFFEL;
  if (!startIso) return s[0];
  var tage = Math.floor((jetzt.getTime() - new Date(startIso + 'T00:00:00Z').getTime()) / 86400000);
  var woche = Math.max(0, Math.floor(tage / 7));
  return s[Math.min(woche, s.length - 1)];
}

/** Datumsschluessel aus Date, ISO-Text oder deutschem Datum; leer wenn unlesbar. */
function comDatumKey_(v) {
  if (!v) return '';
  if (Object.prototype.toString.call(v) === '[object Date]') return comTagKey_(v);
  var s = String(v);
  var iso = s.match(/^(\d{4}-\d{2}-\d{2})/);
  if (iso) return iso[1];
  var de = s.match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})/);
  if (de) return de[3] + '-' + ('0' + de[2]).slice(-2) + '-' + ('0' + de[1]).slice(-2);
  return '';
}

/** .com-Entwurf = Message-ID auf hsb-boden.com (neu per Bridge: <hsb.…>, Bestand vom 26.09.: <1790…>). */
function comIstComEntwurf_(lead) {
  return /^<[A-Za-z0-9._-]+@hsb-boden\.com>$/.test(String(lead.Draft_ID || '').trim());
}

function comDomain_(email) {
  var e = String(email || '').toLowerCase();
  return e.indexOf('@') >= 0 ? e.split('@')[1] : '';
}

function comStatus_(lead) {
  return String(lead.Send_Status || '').toLowerCase();
}

function comEntscheide_(leads, ownerKey, jetzt, zustand) {
  var gesperrt = [];
  var warten = function (grund) { return { aktion: 'warten', grund: grund, gesperrt: gesperrt }; };
  if (zustand.pause) return warten('Notbremse aktiv: ' + zustand.pause);
  if (!comImFenster_(jetzt)) return warten('ausserhalb Versandfenster');

  var eigene = leads.filter(function (l) { return normalizeOwner_(l.Owner) === ownerKey; });
  var heute = comTagKey_(jetzt);
  var gesendetHeute = eigene.filter(function (l) {
    return comStatus_(l) === 'sent' && comDatumKey_(l.Sent_At) === heute;
  }).length;
  var limit = comTageslimit_(zustand.startIso, jetzt);
  if (gesendetHeute >= limit) return warten('Tageslimit ' + limit + ' erreicht');

  var grenze = comTagKey_(new Date(jetzt.getTime() - 7 * 86400000));
  var gesendet7 = 0;
  var bounces7 = 0;
  eigene.forEach(function (l) {
    var k = comDatumKey_(l.Sent_At);
    if (!k || k < grenze) return;
    gesendet7++;
    if (String(l.Bounce_Status || '').toLowerCase().indexOf('hard') >= 0) bounces7++;
  });
  if (gesendet7 >= COM_VERSAND.NOTBREMSE_MIN && bounces7 / gesendet7 > COM_VERSAND.NOTBREMSE_QUOTE) {
    return { aktion: 'pausieren', grund: ownerKey + ': Hard-Bounce-Quote ' + Math.round(bounces7 / gesendet7 * 1000) / 10 + ' % (' + bounces7 + '/' + gesendet7 + ' in 7 Tagen)', gesperrt: gesperrt };
  }
  if (zustand.zufall < COM_VERSAND.AUSLASSEN) return warten('zufaellig ausgelassener Takt');

  var antwortDomains = {};
  leads.forEach(function (l) {
    if (String(l.Reply_Status || '').trim()) antwortDomains[comDomain_(l.Email)] = true;
  });

  for (var i = 0; i < eigene.length; i++) {
    var l = eigene[i];
    if (comStatus_(l) !== 'queued' || !comIstComEntwurf_(l)) continue;
    if (antwortDomains[comDomain_(l.Email)]) {
      gesperrt.push({ lead: l, grund: 'Firma hat bereits geantwortet' });
      continue;
    }
    // Seit dem Einreihen kann eine Abmeldung oder ein Bounce eingegangen sein.
    // Send_Status wird fuer die Pruefung neutralisiert, weil 'queued' sonst selbst sperrt.
    var pruef = checkEligibility_(Object.assign({}, l, { Send_Status: 'not_sent' }));
    if (!pruef.eligible) {
      gesperrt.push({ lead: l, grund: (pruef.reasons || []).join(', ') });
      continue;
    }
    return { aktion: 'senden', lead: l, gesperrt: gesperrt };
  }
  return warten('Warteschlange leer');
}

function comFelderSetzen_(row, set) {
  var sheet = SpreadsheetApp.getActive().getSheetByName('ALL_LEADS');
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  Object.keys(set).forEach(function (col) {
    var idx = headers.indexOf(col);
    if (idx < 0) throw new Error('Spalte fehlt im Sheet: ' + col);
    sheet.getRange(row, idx + 1).setValue(set[col]);
  });
  if (typeof invalidateLeadsCache_ === 'function') invalidateLeadsCache_();
}

function comEinenSenden_(lead, owner, props) {
  var k = comBridgeKonfig_();
  comFelderSetzen_(lead._row, { Send_Status: 'sending' });
  var res;
  try {
    res = UrlFetchApp.fetch(k.url + '/send?owner=' + owner + '&messageId=' + encodeURIComponent(lead.Draft_ID), {
      method: 'post',
      headers: { Authorization: 'Bearer ' + k.token },
      muteHttpExceptions: true
    });
  } catch (e) {
    comFelderSetzen_(lead._row, { Send_Status: 'send_unklar',
      Last_Error: 'Transport unklar, NICHT automatisch wiederholt: ' + String(e).slice(0, 200) });
    return { owner: owner, aktion: 'unklar', lead: lead.Lead_ID };
  }
  var code = res.getResponseCode();
  var body = {};
  try { body = JSON.parse(res.getContentText()) || {}; } catch (x) { body = {}; }

  if (code === 200 && body.ok) {
    if (!props.getProperty(COM_VERSAND.PROP_START)) props.setProperty(COM_VERSAND.PROP_START, comTagKey_(new Date()));
    comFelderSetzen_(lead._row, {
      Send_Status: 'sent',
      Send_Datum: Utilities.formatDate(new Date(), COM_VERSAND.ZEITZONE, 'yyyy-MM-dd HH:mm:ss'),
      Batch_Status: 'SENT',
      Last_Error: body.warning || ''
    });
    logActivity_(lead.Lead_ID, 'SENT_COM', String(body.status || 'sent'));
    return { owner: owner, aktion: 'gesendet', lead: lead.Lead_ID, status: body.status };
  }
  if (body.sent === false) {
    comFelderSetzen_(lead._row, { Send_Status: 'send_failed', Last_Error: 'Nicht gesendet: ' + String(body.error || code).slice(0, 300) });
    logActivity_(lead.Lead_ID, 'SEND_FAILED', String(body.error || code));
    return { owner: owner, aktion: 'fehlgeschlagen', lead: lead.Lead_ID };
  }
  comFelderSetzen_(lead._row, { Send_Status: 'send_unklar',
    Last_Error: 'Ergebnis unklar (HTTP ' + code + '), NICHT automatisch wiederholt: ' + String(body.error || '').slice(0, 200) });
  logActivity_(lead.Lead_ID, 'SEND_UNKLAR', 'HTTP ' + code);
  return { owner: owner, aktion: 'unklar', lead: lead.Lead_ID };
}

/** Trigger-Einstieg. */
function comVersandTakt() {
  return comVersandTaktZu_(new Date());
}

function comVersandTaktZu_(jetzt) {
  if (!comBridgeAktiv_()) return { ok: false, skipped: 'bridge_inaktiv' };
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(30000)) return { ok: false, skipped: 'gesperrt' };
  try {
    var props = PropertiesService.getScriptProperties();
    // Vor dem Sheet-Lesen: 144 Takte am Tag, die meisten ausserhalb des Fensters.
    if (props.getProperty(COM_VERSAND.PROP_PAUSE)) return { ok: true, ergebnis: [], grund: 'pausiert' };
    if (!comImFenster_(jetzt)) return { ok: true, ergebnis: [], grund: 'ausserhalb Versandfenster' };
    var leads = readLeads_().leads;
    var ergebnis = [];
    ['JOEL', 'JORDI'].forEach(function (owner) {
      var e = comEntscheide_(leads, owner, jetzt, {
        startIso: props.getProperty(COM_VERSAND.PROP_START) || '',
        pause: props.getProperty(COM_VERSAND.PROP_PAUSE) || '',
        zufall: Math.random()
      });
      (e.gesperrt || []).forEach(function (g) {
        comFelderSetzen_(g.lead._row, { Send_Status: 'send_blocked', Last_Error: 'Vor Versand gesperrt: ' + g.grund });
      });
      if (e.aktion === 'pausieren') {
        props.setProperty(COM_VERSAND.PROP_PAUSE, e.grund);
        logActivity_('COM-VERSAND', 'VERSAND_PAUSE', e.grund);
        ergebnis.push({ owner: owner, aktion: 'pausiert', grund: e.grund });
        return;
      }
      if (e.aktion !== 'senden') {
        ergebnis.push({ owner: owner, aktion: e.aktion, grund: e.grund });
        return;
      }
      ergebnis.push(comEinenSenden_(e.lead, owner, props));
    });
    return { ok: true, ergebnis: ergebnis };
  } finally {
    lock.releaseLock();
  }
}

// ---------------------------------------------------------------- Sidebar

function uiComUebersicht(owner) {
  try {
    var ownerKey = normalizeOwner_(owner);
    var props = PropertiesService.getScriptProperties();
    var jetzt = new Date();
    var heute = comTagKey_(jetzt);
    var leads = readLeads_().leads.filter(function (l) { return normalizeOwner_(l.Owner) === ownerKey; });
    var zaehle = function (st) { return leads.filter(function (l) { return comStatus_(l) === st; }).length; };
    var offen = leads.filter(function (l) { return comStatus_(l) === 'drafted' && comIstComEntwurf_(l); });
    var limit = comTageslimit_(props.getProperty(COM_VERSAND.PROP_START) || '', jetzt);
    var warteschlange = zaehle('queued');
    return { ok: true, data: {
      owner: ownerKey,
      bridge: comBridgeAktiv_(),
      entwuerfeGesamt: offen.length,
      entwuerfe: offen.slice(0, 500).map(function (l) {
        return { leadId: String(l.Lead_ID), firma: String(l.Company || ''), email: String(l.Email || '') };
      }),
      warteschlange: warteschlange,
      heuteGesendet: leads.filter(function (l) { return comStatus_(l) === 'sent' && comDatumKey_(l.Sent_At) === heute; }).length,
      limit: limit,
      werktageRest: Math.ceil(warteschlange / Math.max(1, limit)),
      imFenster: comImFenster_(jetzt),
      pause: props.getProperty(COM_VERSAND.PROP_PAUSE) || '',
      unklar: zaehle('send_unklar') + zaehle('sending'),
      fehlgeschlagen: zaehle('send_failed'),
      gesperrt: zaehle('send_blocked')
    } };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

function uiComEinreihen(owner, leadIds) {
  // Gleicher Lock wie der Takt: writeColumnBulk_ schreibt ganze Spannen zurueck
  // und wuerde sonst parallel gesetzte Status (z. B. send_unklar) ueberschreiben.
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(30000)) return { ok: false, error: 'Versand laeuft gerade - bitte in einer Minute erneut.' };
  try {
    var ownerKey = normalizeOwner_(owner);
    var gewuenscht = {};
    (leadIds || []).forEach(function (id) { gewuenscht[String(id)] = true; });
    var sheet = SpreadsheetApp.getActive().getSheetByName('ALL_LEADS');
    var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    var spalte = headers.indexOf('Send_Status') + 1;
    var spalteFrei = headers.indexOf('Versandfreigabe') + 1;
    var spalteAm = headers.indexOf('Approved_At') + 1;
    if (!spalte || !spalteFrei || !spalteAm) throw new Error('Spalte fehlt im Sheet: Send_Status/Versandfreigabe/Approved_At');
    var stempel = Utilities.formatDate(new Date(), COM_VERSAND.ZEITZONE, 'yyyy-MM-dd HH:mm:ss');
    var updates = {};
    var frei = {};
    var am = {};
    var n = 0;
    var abgelehnt = 0;
    readLeads_().leads.forEach(function (l) {
      if (!gewuenscht[String(l.Lead_ID)]) return;
      if (normalizeOwner_(l.Owner) !== ownerKey || comStatus_(l) !== 'drafted' || !comIstComEntwurf_(l)) { abgelehnt++; return; }
      updates[l._row] = 'queued';
      frei[l._row] = 'yes';
      am[l._row] = stempel;
      n++;
    });
    // Ein Schreibvorgang je Spalte statt 500 Einzelzellen.
    writeColumnBulk_(sheet, spalte, updates);
    writeColumnBulk_(sheet, spalteFrei, frei);
    writeColumnBulk_(sheet, spalteAm, am);
    if (typeof invalidateLeadsCache_ === 'function') invalidateLeadsCache_();
    logActivity_('COM-VERSAND', 'QUEUED', ownerKey + ': ' + n + ' eingereiht, ' + abgelehnt + ' abgelehnt');
    return { ok: true, data: { eingereiht: n, abgelehnt: abgelehnt } };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  } finally {
    lock.releaseLock();
  }
}

function uiComVorschauOeffnen(leadId) {
  var l = readLeads_().leads.filter(function (x) { return String(x.Lead_ID) === String(leadId); })[0];
  if (!l) throw new Error('Lead nicht gefunden: ' + leadId);
  var flyer = FLYERS[normalizeOwner_(l.Owner)];
  var mail = renderEmail_(l, flyer);
  var html = '<div style="font:13px Arial;margin-bottom:10px;color:#444">'
    + '<b>Von:</b> ' + htmlEscape_(flyer.displayName + ' <' + flyer.mailbox + '>') + '<br>'
    + '<b>Antwort an:</b> ' + htmlEscape_(flyer.replyTo || flyer.mailbox) + '<br>'
    + '<b>An:</b> ' + htmlEscape_(String(l.Email)) + '<br>'
    + '<b>Betreff:</b> ' + htmlEscape_(mail.subject) + '<br>'
    + '<b>Anhang:</b> ' + htmlEscape_(flyer.attachmentName) + '<br>'
    + '<i>Vorschau aus der Vorlage neu gerendert.</i></div><hr>'
    + bodyHtmlMitSignatur_(mail, flyer);
  SpreadsheetApp.getUi().showModalDialog(HtmlService.createHtmlOutput(html).setWidth(720).setHeight(640), 'Vorschau ' + leadId);
}

function uiComPauseAufheben() {
  PropertiesService.getScriptProperties().deleteProperty(COM_VERSAND.PROP_PAUSE);
  logActivity_('COM-VERSAND', 'VERSAND_FORTGESETZT', 'manuell');
  return { ok: true };
}

function uiComVersandEinrichten() {
  // Nur EIN Nutzer darf den Takt besitzen - zwei Trigger halbierten den Mindestabstand.
  var props = PropertiesService.getScriptProperties();
  var ich = String(Session.getEffectiveUser().getEmail() || '');
  var besitzer = props.getProperty('HSB_COM_TAKT_NUTZER') || '';
  if (besitzer && besitzer !== ich) {
    SpreadsheetApp.getUi().alert('Versand läuft bereits', 'Der Versandtakt ist schon bei ' + besitzer + ' eingerichtet. Hier nichts zu tun.', SpreadsheetApp.getUi().ButtonSet.OK);
    return { ok: false, error: 'takt_bei_' + besitzer };
  }
  props.setProperty('HSB_COM_TAKT_NUTZER', ich);
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === COM_VERSAND.HANDLER) ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger(COM_VERSAND.HANDLER).timeBased().everyMinutes(COM_VERSAND.TAKT_MINUTEN).create();
  SpreadsheetApp.getUi().alert('Versand über .com aktiv',
    'Alle ' + COM_VERSAND.TAKT_MINUTEN + ' Minuten geht höchstens eine Mail je Postfach raus, Mo–Fr 8–17 Uhr, mit Tageslimit und Notbremse.',
    SpreadsheetApp.getUi().ButtonSet.OK);
  return { ok: true };
}
```

- [ ] **Step 4: Ausliefern und Tests laufen lassen**

In `apps/sales-os/deploy.sh` nach der Zeile `cp "$SRC/HSB_ComBridge.gs"   "$DEPLOY/HSB_ComBridge.js"` einfügen:

```bash
cp "$SRC/HSB_ComVersand.gs"  "$DEPLOY/HSB_ComVersand.js"
```

In `apps/sales-os/deploy/.claspignore` nach `!HSB_ComBridge.js` einfügen:

```
!HSB_ComVersand.js
```

Run: `cp apps_script/HSB_ComVersand.gs deploy/HSB_ComVersand.js && node tests/test_com_versand.js`, danach die Offline-Suite.
Expected: `… bestanden, 0 fehlgeschlagen`, keine Zeile `ROT:`.

- [ ] **Step 5: Commit**

```bash
cd ~/KI-System/02_Projects/active/hsb-boden
python3 scripts/verify_ssot.py
git add apps/sales-os/apps_script/HSB_ComVersand.gs apps/sales-os/deploy/HSB_ComVersand.js apps/sales-os/deploy.sh apps/sales-os/deploy/.claspignore apps/sales-os/tests/test_com_versand.js
git commit -m "feat(sales-os): gedrosselte .com-Versandsteuerung mit Warm-up, Notbremse und Firmen-Stopp"
```

---

### Task 6: `.com`-Posteingang automatisch auswerten

**Files:**
- Modify: `apps/sales-os/apps_script/HSB_ComBridge.gs` (anhängen)
- Modify: `apps/sales-os/apps_script/HSB_GraphAdapter.gs` (Klassifizierer, `hsbAutoReconcile`)
- Test: `apps/sales-os/tests/test_com_bridge.js` (ergänzen)

**Interfaces:**
- Produces: `comReconcileInbox_(): { ok, matched, checked, submitted, skipped, foreign }`; `hsbAutoReconcile()` liefert zusätzlich `comInbox`.
- Consumes: `reconcileInboxMessages_(messages, quelle)`, `classifyInboundMessage_(m)` (liest jetzt `m.dsn`, `m.autoReply`).

- [ ] **Step 1: Failing Tests ergänzen**

In `apps/sales-os/tests/test_com_bridge.js` **vor** `console.log('\n' + bestanden …` einfügen:

```js
// 10. .com-Posteingang wird an den bestehenden Posteingangs-Abgleich uebergeben
(function () {
  const dsn = { id: '<d1>', subject: 'Undelivered Mail Returned to Sender', from: { emailAddress: { address: 'mailer-daemon@w0221a9f.kasserver.com' } },
    internetMessageId: '<d1>', bodyPreview: 'Final-Recipient: rfc822; weg@firma.de', dsn: true, autoReply: true };
  const k = kontext({ antwort: function (url) { return antwortJson(200, { ok: true, messages: url.indexOf('owner=JOEL') >= 0 ? [dsn] : [] }); } });
  const erhalten = [];
  k.reconcileInboxMessages_ = function (msgs, quelle) { erhalten.push({ msgs: msgs, quelle: quelle }); return { ok: true, matched: msgs.length, checked: msgs.length, submitted: 0, skipped: 0, foreign: 0 }; };
  const r = k.comReconcileInbox_();
  pruefe('.com-Posteingang fragt /inbox beider Postfaecher', k._aufrufe.length === 2 && /\/inbox\?owner=JOEL&days=14$/.test(k._aufrufe[0].url));
  pruefe('.com-Posteingang geht mit Quelle COM an den Abgleich', erhalten[0].quelle === 'COM' && erhalten[0].msgs[0].dsn === true && r.checked === 1);
})();

// 11. Klassifizierer: Kennzeichen der Bridge und eigene .com-Adresse
(function () {
  const k = { console: console, PropertiesService: { getScriptProperties: function () { return { getProperty: function () { return null; } }; }, getUserProperties: function () { return { getProperty: function () { return null; } }; } } };
  vm.createContext(k);
  vm.runInContext(fs.readFileSync(path.join(DEPLOY, 'HSB_GraphAdapter.js'), 'utf8'), k);
  const bounce = k.classifyInboundMessage_({ subject: 'Rueckmeldung', from: { emailAddress: { address: 'postfach@irgendwo.de' } }, dsn: true,
    bodyPreview: 'Original-Sender: j-cherino@hsb-boden.com\nFinal-Recipient: rfc822; weg@firma.de\nStatus: 5.1.1 user unknown' });
  pruefe('DSN mit .com-Absender erkennt den echten Empfaenger', /BOUNCE/.test(bounce.event_type) && bounce.failed_recipient === 'weg@firma.de', JSON.stringify(bounce));
  const ooo = k.classifyInboundMessage_({ subject: 'Ihre Nachricht', from: { emailAddress: { address: 'max@firma.de' } }, autoReply: true, bodyPreview: 'Danke fuer Ihre Nachricht.' });
  pruefe('autoReply-Kennzeichen ergibt Abwesenheit', ooo.event_type === 'AUTO_REPLY_OOO', JSON.stringify(ooo));
  const echt = k.classifyInboundMessage_({ subject: 'Re: Industrieboeden', from: { emailAddress: { address: 'max@firma.de' } }, bodyPreview: 'Bitte rufen Sie mich an.' });
  pruefe('echte Antwort bleibt keine Abwesenheit', echt.event_type !== 'AUTO_REPLY_OOO' && !/BOUNCE/.test(echt.event_type));
})();
```

Außerdem im bestehenden Block `// 9. 15-Minuten-Abgleich …` direkt nach der Zeile `k.comReconcileSentItems_ = function () { return { ok: true, checked: 3, matched: 1 }; };` einfügen (sonst wird Test 9 durch Step 4 rot):

```js
  k.comReconcileInbox_ = function () { return { ok: true, checked: 0, matched: 0 }; };
```

Run: Offline-Suite. Expected: `test_com_bridge.js` mit FAIL bei 10 und 11 (Funktion fehlt bzw. Klassifizierer ignoriert die Kennzeichen).

- [ ] **Step 2: `comReconcileInbox_` an `HSB_ComBridge.gs` anhängen**

```js
/** Liest den .com-Posteingang beider Postfaecher (Bounces, Abwesenheiten, fehlgeleitete Antworten). */
function comReconcileInbox_() {
  var k = comBridgeKonfig_();
  var gesamt = { ok: true, matched: 0, checked: 0, submitted: 0, skipped: 0, foreign: 0 };
  ['JOEL', 'JORDI'].forEach(function (owner) {
    var res = UrlFetchApp.fetch(k.url + '/inbox?owner=' + owner + '&days=' + COM_SENT_TAGE, {
      headers: { Authorization: 'Bearer ' + k.token },
      muteHttpExceptions: true
    });
    var code = res.getResponseCode();
    if (code !== 200) throw new Error('COM_INBOX ' + owner + ' HTTP ' + code + ' ' + res.getContentText().slice(0, 200));
    var msgs = (JSON.parse(res.getContentText()) || {}).messages || [];
    var r = reconcileInboxMessages_(msgs, 'COM');
    ['matched', 'checked', 'submitted', 'skipped', 'foreign'].forEach(function (f) { gesamt[f] += r[f] || 0; });
  });
  return gesamt;
}
```

- [ ] **Step 3: Klassifizierer nutzt die Kennzeichen**

In `apps/sales-os/apps_script/HSB_GraphAdapter.gs`, `classifyInboundMessage_`:
- `if (isMailerDaemon || isUndeliverableSubj) {` → `if (m.dsn || isMailerDaemon || isUndeliverableSubj) {`
- `if (cand.indexOf('hsb-boden.de') === -1 &&` → `if (cand.indexOf('hsb-boden.') === -1 &&`
- `var isOoo = subjLower.indexOf('automatische antwort') >= 0 ||` → `var isOoo = m.autoReply === true || subjLower.indexOf('automatische antwort') >= 0 ||`

- [ ] **Step 4: 15-Minuten-Abgleich liest auch den `.com`-Posteingang**

In `hsbAutoReconcile` (Stand nach Basisplan Task 5) direkt nach dem Block

```js
    if (com) {
      try { out.comSent = comReconcileSentItems_(); }
      catch (e4) { comFehler.push('com-sent: ' + String(e4.message || e4)); out.errors.push(comFehler[0]); }
    }
```

einfügen:

```js
    if (com) {
      try { out.comInbox = comReconcileInbox_(); }
      catch (e6) { var f6 = 'com-inbox: ' + String(e6.message || e6); comFehler.push(f6); out.errors.push(f6); }
    }
```

und in derselben Funktion `syncStatusSchreiben_('hsb-boden.com', { weg: 'COM', sent: out.comSent, inbox: null, errors: comFehler });` ersetzen durch `syncStatusSchreiben_('hsb-boden.com', { weg: 'COM', sent: out.comSent, inbox: out.comInbox, errors: comFehler });`.

- [ ] **Step 5: Offline-Suite**

Expected: alle PASS, keine Zeile `ROT:`.

- [ ] **Step 6: Commit**

```bash
cd ~/KI-System/02_Projects/active/hsb-boden
python3 scripts/verify_ssot.py
git add apps/sales-os/apps_script/HSB_ComBridge.gs apps/sales-os/apps_script/HSB_GraphAdapter.gs apps/sales-os/deploy/HSB_ComBridge.js apps/sales-os/deploy/HSB_GraphAdapter.js apps/sales-os/tests/test_com_bridge.js
git commit -m "feat(sales-os): .com-Posteingang (Bounce, Abwesenheit) automatisch ins CRM"
```

---

### Task 7: Sidebar „Versand über .com“ und Menü

**Files:**
- Modify: `apps/sales-os/apps_script/Sidebar.html`
- Modify: `apps/sales-os/apps_script/Code.gs` (`onOpen`)

**Interfaces:** nutzt `uiComUebersicht`, `uiComEinreihen`, `uiComVorschauOeffnen`, `uiComPauseAufheben`, `uiComVersandEinrichten` aus Task 5 und die globale Sidebar-Variable `OWNER`.

- [ ] **Step 1: Bereich einfügen**

In `apps/sales-os/apps_script/Sidebar.html` direkt **vor** der Zeile `<details class="schritt" id="s1" style="display:none">` einfügen:

```html
<section class="schnellstart" id="comVersandBox" style="border:1px solid #dadce0;border-radius:6px;padding:12px;margin:12px 0;">
  <div class="titel">Versand über .com</div>
  <div id="comStatus" class="leer-hinweis">Wird geladen…</div>
  <div style="margin:8px 0;display:flex;gap:6px;flex-wrap:wrap;">
    <button class="tat" onclick="comAlleMarkieren(true)">Alle markieren</button>
    <button class="tat" onclick="comAlleMarkieren(false)">Keine</button>
    <button class="tat primaer" onclick="comSenden()">Markierte senden</button>
    <button class="tat" onclick="comLaden()">Aktualisieren</button>
  </div>
  <div id="comListe" style="max-height:320px;overflow:auto;"></div>
</section>
```

- [ ] **Step 2: Skript ergänzen**

Direkt **vor** der (einzigen) Zeile `</script>` einfügen:

```js
/* --- Versand ueber .com --------------------------------------------- */
function comLaden() {
  laden('comStatus', 'Lade Versandstatus…');
  google.script.run.withSuccessHandler(function (r) {
    if (!r || !r.ok) { fehler('comStatus', r && r.error); return; }
    var d = r.data;
    var s = '<div><b>' + (d.owner === 'JOEL' ? 'Joel' : 'Jordie') + '</b> · heute gesendet <span class="zahl">'
      + nz(d.heuteGesendet) + '</span> von ' + nz(d.limit) + ' · Warteschlange <span class="zahl">'
      + nz(d.warteschlange) + '</span> (≈ ' + nz(d.werktageRest) + ' Werktage) · offene Entwürfe <span class="zahl">'
      + nz(d.entwuerfeGesamt) + '</span></div>';
    if (!d.bridge) s += '<div class="meldung m-warn">COM-Bridge ist nicht eingerichtet.</div>';
    if (d.pause) s += '<div class="meldung m-fehler"><b>Versand pausiert</b>' + esc(d.pause)
      + ' <button class="tat" onclick="comPauseAufheben()">Fortsetzen</button></div>';
    if (!d.imFenster) s += '<div class="leer-hinweis">Außerhalb Mo–Fr 8–17 Uhr – Versand ruht.</div>';
    if (d.unklar || d.fehlgeschlagen || d.gesperrt) s += '<div class="meldung m-warn">Bitte prüfen (Spalte Last_Error): '
      + nz(d.unklar) + ' unklar, ' + nz(d.fehlgeschlagen) + ' fehlgeschlagen, ' + nz(d.gesperrt) + ' vor Versand gesperrt.</div>';
    zeig('comStatus', s);
    var h = d.entwuerfe.length ? '' : '<div class="leer-hinweis">Keine offenen .com-Entwürfe.</div>';
    d.entwuerfe.forEach(function (e) {
      h += '<label style="display:flex;gap:6px;align-items:flex-start;padding:4px 0;border-bottom:1px solid #eee;">'
        + '<input type="checkbox" class="comWahl" value="' + esc(e.leadId) + '">'
        + '<span style="flex:1"><b>' + esc(e.firma || '–') + '</b><br><small>' + esc(e.email) + '</small></span>'
        + '<a href="#" data-lead="' + esc(e.leadId) + '" onclick="comVorschau(this.getAttribute(\'data-lead\'));return false;">Vorschau</a></label>';
    });
    if (d.entwuerfeGesamt > d.entwuerfe.length) h += '<div class="leer-hinweis">Angezeigt: erste ' + nz(d.entwuerfe.length) + ' von ' + nz(d.entwuerfeGesamt) + '.</div>';
    zeig('comListe', h);
  }).withFailureHandler(function (e) { fehler('comStatus', e.message); }).uiComUebersicht(OWNER);
}
function comAlleMarkieren(an) {
  Array.prototype.forEach.call(document.querySelectorAll('.comWahl'), function (c) { c.checked = an; });
}
function comSenden() {
  var ids = Array.prototype.filter.call(document.querySelectorAll('.comWahl'), function (c) { return c.checked; })
    .map(function (c) { return c.value; });
  if (!ids.length) { fehler('comStatus', 'Nichts markiert.'); return; }
  laden('comStatus', nz(ids.length) + ' Entwürfe werden in die Warteschlange gelegt…');
  google.script.run.withSuccessHandler(function (r) {
    if (!r || !r.ok) { fehler('comStatus', r && r.error); return; }
    comLaden();
  }).withFailureHandler(function (e) { fehler('comStatus', e.message); }).uiComEinreihen(OWNER, ids);
}
function comVorschau(id) {
  google.script.run.withFailureHandler(function (e) { fehler('comStatus', e.message); }).uiComVorschauOeffnen(id);
}
function comPauseAufheben() {
  google.script.run.withSuccessHandler(comLaden).withFailureHandler(function (e) { fehler('comStatus', e.message); }).uiComPauseAufheben();
}
comLaden();
```

- [ ] **Step 3: Beim Wechsel Joel/Jordie neu laden**

In `setOwner` nach der Zeile `el('wJoel').setAttribute('aria-pressed', String(o === 'JOEL'));` einfügen:

```js
  if (typeof comLaden === 'function') comLaden();
```

- [ ] **Step 4: Menüeinträge**

In `apps/sales-os/apps_script/Code.gs`, Funktion `onOpen`: Den Menü-Builder finden (`SpreadsheetApp.getUi().createMenu(`) und vor dem abschließenden `.addToUi()` einfügen:

```js
    .addSeparator()
    .addItem('📤 Versand über .com einrichten (Takt 10 min)', 'uiComVersandEinrichten')
    .addItem('▶️ Versand-Pause aufheben', 'uiComPauseAufheben')
```

- [ ] **Step 5: Offline-Suite**

Run: Offline-Suite (sie baut `HSB_SALES_OS.gs` neu und kopiert `Sidebar.html`).
Expected: keine Zeile `ROT:`. Die Sidebar-Tests in `test_apps_script.js` lesen `Sidebar.html`. Wird dort ein Muster verboten, das der neue Block benutzt (z. B. Inline-`onclick`), wird der Block auf das in der Sidebar übliche Muster umgestellt, nicht der Test.

- [ ] **Step 6: Commit**

```bash
cd ~/KI-System/02_Projects/active/hsb-boden
python3 scripts/verify_ssot.py
git add apps/sales-os/apps_script/Sidebar.html apps/sales-os/apps_script/Code.gs apps/sales-os/apps_script/HSB_SALES_OS.gs apps/sales-os/deploy/Sidebar.html apps/sales-os/deploy/HSB_SALES_OS.js
git commit -m "feat(sales-os): Sidebar Versand ueber .com mit Auswahl, Vorschau und Status"
```

---

### Task 8: Öffentliches Repo – fremde Adressen entfernen

**Files:**
- Modify: `apps/sales-os/docs/handoff/HSB_Sales_OS_Outbound_Hardening_Gesamtes_Gespraech_2026-09-19.md`
- Modify: `apps/sales-os/docs/superpowers/plans/2026-08-28-hsb-sales-os-mobile-appsheet.md`
- Modify: `apps/sales-os/docs/appsheet/operator_identities_matrix.json`

- [ ] **Step 1:** Fremde Adressen finden (nur zählen, nicht ausgeben):

```bash
cd ~/KI-System/02_Projects/active/hsb-boden/apps/sales-os
for f in docs/handoff/HSB_Sales_OS_Outbound_Hardening_Gesamtes_Gespraech_2026-09-19.md docs/superpowers/plans/2026-08-28-hsb-sales-os-mobile-appsheet.md docs/appsheet/operator_identities_matrix.json; do
  grep -noE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}' "$f" | grep -viE 'hsb-boden|example|test|noreply' | cut -d: -f1-2
done
```

- [ ] **Step 2:** Jede gefundene **fremde** Adresse durch `lead@beispiel.invalid` ersetzen. Adressen des Inhabers selbst (`cherinodiaz@outlook.com`, `cherinojoel@gmail.com`) nur ersetzen, wenn der Nutzer das beim Review bestätigt; sonst stehen lassen und im Handoff nennen.
- [ ] **Step 3:** Commit mit Hinweis: Die Git-Historie enthält die Adressen weiterhin. Ein History-Rewrite eines öffentlichen Repos ist eine eigene Entscheidung des Nutzers.

```bash
cd ~/KI-System/02_Projects/active/hsb-boden
python3 scripts/verify_ssot.py
git add apps/sales-os/docs/handoff/HSB_Sales_OS_Outbound_Hardening_Gesamtes_Gespraech_2026-09-19.md apps/sales-os/docs/superpowers/plans/2026-08-28-hsb-sales-os-mobile-appsheet.md apps/sales-os/docs/appsheet/operator_identities_matrix.json
git commit -m "docs(sales-os): fremde E-Mail-Adressen aus oeffentlichen Doku-Dateien entfernt"
```

---

### Task 9: Inbetriebnahme (jeder Außenschritt mit Freigabe)

**Files:** keine Codeänderung; Ergebnisse in `apps/sales-os/VERIFICATION_REPORT.md`.

- [ ] **Step 1: All-Inkl KAS (Nutzer meldet sich selbst an, Agent klickt danach)**
  - Domain `hsb-boden.com` → Bearbeiten → „DKIM Signierung“ einschalten.
  - Postfach `j-cherino@hsb-boden.com` → „Kopie-Empfänger“ `j-cherino@hsb-boden.de`; Postfach `j-post@hsb-boden.com` → `j-post@hsb-boden.de`. Die Postfächer behalten ihre Mails (nötig für `/inbox`).
  - DNS-Record `_dmarc.hsb-boden.com` TXT: `v=DMARC1; p=none; rua=mailto:j-cherino@hsb-boden.de`.
  - Beleg: `dig +short TXT _dmarc.hsb-boden.com` zeigt `rua`. Den DKIM-Selector aus dem KAS ablesen und mit `dig +short TXT <selector>._domainkey.hsb-boden.com` prüfen: Es muss ein `v=DKIM1`-Schlüssel erscheinen.

- [ ] **Step 2: Worker-Secrets und Deploy** (Basisplan Task 6 Step 1–2 wörtlich: `wrangler whoami`, Nutzer tippt die 5 Secrets selbst, `npx wrangler deploy`).

- [ ] **Step 3: Rauchtest nur lesend**

```bash
read -s T
curl -s -H "Authorization: Bearer $T" "https://hsb-com-bridge.<konto>.workers.dev/inbox?owner=JOEL&days=14" | head -c 300; echo
curl -s -H "Authorization: Bearer $T" "https://hsb-com-bridge.<konto>.workers.dev/sent?owner=JOEL&days=14" | head -c 300; echo
```

Expected: je `{"ok":true,"messages":[…]}`; unter `/sent` stehen die zwei Test-Mails vom 26.09.

- [ ] **Step 4: CPU-Messung im Gratis-Tarif**

In einem zweiten Terminal `npx wrangler tail --format json | grep -o '"cpuTime":[0-9]*'` offen lassen, dann Step 3 wiederholen. Expected: jeder Wert < 10. Die teuren Routen `/draft` (≈ 340 KB) und `/send` (3 TLS-Sitzungen, Dot-Stuffing) werden in Step 6 Punkt 2 und 4 mit laufendem `tail` gemessen; dort gilt dieselbe Grenze. **Liegt ein Wert ≥ 10: STOPP**, Befund dem Nutzer melden (Workers Paid oder Mac-Betrieb). Nicht weiter in Betrieb nehmen.

- [ ] **Step 5: Apps Script ausliefern und einrichten**
  - `./deploy.sh`, danach `clasp pull` in ein Scratch-Verzeichnis und mit `deploy/` vergleichen (identisch inklusive `HSB_ComBridge.js`, `HSB_ComVersand.js`).
  - Skripteigenschaften `HSB_COM_BRIDGE_URL`, `HSB_COM_BRIDGE_TOKEN` setzen (Nutzer).
  - Menü: automatischen Abgleich einrichten (bei beiden Nutzern), dann „📤 Versand über .com einrichten“ (einmal, Joel).

- [ ] **Step 6: Abnahme mit einem Test-Lead an eine eigene Adresse**
  1. Test-Lead anlegen (eigene Privatadresse, Owner Joel, Versandfreigabe yes).
  2. Batch N=1, „Outlook-Entwürfe direkt anlegen“ → Sidebar „Versand über .com“ zeigt ihn unter offene Entwürfe; „Vorschau“ öffnet die Mail mit Von `.com`, Antwort an `.de`, Anhang.
  3. Markieren → „Markierte senden“ → Warteschlange 1.
  4. Nächster Takt im Fenster (≤ 10 min, bei zufälligem Auslassen ≤ 20 min): `Send_Status=sent`, Entwurf aus „Entwürfe“ verschwunden, in „Gesendet“ vorhanden.
  5. Empfangene Mail, Quelltext: `From … hsb-boden.com`, `Reply-To … hsb-boden.de`, `DKIM-Signature … d=hsb-boden.com`, `Authentication-Results … dkim=pass spf=pass`.
  6. Antworten → Antwort liegt in `.de`; nach ≤ 15 min steht beim Test-Lead `Reply_Status`.
  7. An eine nicht existierende Adresse eines zweiten Test-Leads senden (z. B. `gibtsnicht-<datum>@<eigene-domain>`) → Bounce landet in `.com`, Kopie in `.de`, nach ≤ 15 min `Bounce_Status=hard_bounce`.
  8. Zweiten Test-Lead erneut einreihen → wird vor dem Versand gesperrt (`send_blocked`).

  9. Die `cpuTime`-Werte aus `wrangler tail` für den `/draft`-Aufruf (Punkt 2) und den `/send`-Aufruf (Punkt 4) liegen unter 10. Sonst STOPP (siehe Step 4).

  Erst wenn alle neun Punkte belegt sind, ist der Umbau abgenommen. Belege in `VERIFICATION_REPORT.md`.

- [ ] **Step 7: Die 200 vorhandenen `.com`-Entwürfe**
  Sie erscheinen ohne weiteres Zutun in der Sidebar, weil `Draft_ID` ihre Message-ID trägt. 103 Joel-Einträge im Sheet haben keinen Entwurf im Postfach; eingereiht landen sie über `/send` → 409 sicher als `send_failed` („Entwurf nicht gefunden“) und können danach per Knopf neu erzeugt werden (vorher `Send_Status` auf `not_sent`, `Draft_ID` leeren).

---

### Task 10: Doku und Übergabe

**Files:**
- Modify: `apps/sales-os/docs/MIGRATION_COM_DOMAIN.md` (liegt nur im archivierten Einzel-Repo; im Monorepo **neu anlegen** unter `apps/sales-os/docs/COM_OUTBOUND_BETRIEB.md`)
- Modify: `apps/sales-os/CURRENT_HANDOFF.md`

- [ ] **Step 1:** `apps/sales-os/docs/COM_OUTBOUND_BETRIEB.md` anlegen:

```markdown
# .com-Outbound – Betrieb (Stand <Datum der Abnahme>)

## Ablauf
1. Sidebar → Batch vorbereiten → „Outlook-Entwürfe direkt anlegen“: Entwürfe entstehen im .com-Postfach (All-Inkl) über die COM-Bridge.
2. Sidebar → „Versand über .com“: Entwürfe ansehen (Vorschau), markieren, „Markierte senden“.
3. Alle 10 Minuten geht höchstens eine Mail je Postfach raus: Mo–Fr 8–17 Uhr, Tageslimit 10/20/30/40/50 ab erstem Versand, Notbremse bei > 2 % Hard Bounces.
4. Antworten kommen per Reply-To in Outlook (.de). Bounces und Abwesenheiten im .com-Postfach werden automatisch ausgewertet und zusätzlich nach .de kopiert.

## Status im Sheet (Spalte Send_Status)
drafted → queued → sending → sent | send_failed (sicher nicht gesendet) | send_unklar (von Hand prüfen, wird nie automatisch wiederholt) | send_blocked (Abmeldung/Bounce/Firmen-Stopp vor Versand)

## Nicht verwenden
`engine/hsb_cli.py send-batch` und `purge-de --apply`.

## Notfall
Versand sofort stoppen: Skripteigenschaft `HSB_COM_BRIDGE_URL` löschen. Pause aufheben: Menü „Versand-Pause aufheben“.
```

- [ ] **Step 2:** Offene Entscheidungen in `CURRENT_HANDOFF.md` eintragen (Punkte 1, 3, 4 aus Basisplan Task 7 Step 2 wörtlich, ohne Punkt 2 zur Versandfreigabe).
- [ ] **Step 3:** Commit, `ai-state event --tool claude-code --type milestone --msg "hsb-sales-os: .com-Outbound per Sidebar live und abgenommen"`, `~/KI-System/tools/handoff.sh write "Claude Code" "<getan>" "<nächster Schritt>"`. Push/PR nur nach Freigabe.

---

## Bewusst nicht Teil dieses Plans

- Folgemails (Sequenzen), A/B-Betreffzeilen, Öffnungs-Tracking (schadet der Zustellung).
- History-Rewrite des öffentlichen Repos.
- Umzug der Domain oder der Postfächer.
