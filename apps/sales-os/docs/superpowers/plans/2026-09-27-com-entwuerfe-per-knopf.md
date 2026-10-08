# .com-Entwürfe per Knopf – Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Der bestehende Knopf „Entwürfe erzeugen“ im HSB Sales OS legt die Entwürfe künftig im `.com`-Postfach (All-Inkl) statt per Power Automate im `.de`-Postfach an; Mensch prüft und sendet von Hand; der vorhandene 15-Minuten-Abgleich setzt danach den Status `sent` im Sheet.

**Architecture:** Apps Script kann kein IMAP. Deshalb kommt ein kleiner Cloudflare Worker („COM-Bridge“) dazwischen, der genau zwei Dinge kann: einen fertigen Entwurf per IMAP-APPEND in „Entwürfe“ legen und den Ordner „Gesendet“ lesen. Apps Script baut die komplette E-Mail (HTML-Text, Signatur, geprüfter Flyer) selbst, schickt sie als fertige EML an die Bridge und bekommt dasselbe Antwortformat zurück wie heute vom Power-Automate-Flow. Dadurch bleiben Batch-Auswahl, Asset-Gate, Anhangprüfung und Rückschreiben ins Sheet unverändert. Die Bridge kann strukturell **nicht senden** (kein SMTP-Code).

**Tech Stack:** Google Apps Script (clasp, `deploy.sh`), Cloudflare Workers (TypeScript, `cloudflare:sockets`, wrangler 4), vitest, Node-`vm`-Testharness für Apps Script.

**Spec:** Kein separates Spec-Dokument. Die Anforderungen stammen aus der Session vom 2026-09-27 (Audit + Nutzerziel) und stehen vollständig unten unter „Ausgangslage“ und „Global Constraints“.

---

## Ausgangslage (belegt am 2026-09-27, read-only geprüft)

- **Kanonischer Code:** `~/KI-System/02_Projects/active/hsb-boden/apps/sales-os`. `clasp pull` des Live-Skripts (`1Xl6xkMT…`) ist identisch mit `apps/sales-os/deploy/`. Das Einzel-Repo `hsb-sales-os` ist laut `PROJECT_TRUTH.md` archiviert und veraltet (seine Apps-Script-Tests sind rot, die des Monorepos grün). **Nichts im Einzel-Repo ändern.**
- **Heutiger Ablauf:** Sidebar → `uiCreateDraftsChunk`/`uiCreateDraftsForBatch` → `createDraftsForBatch` (`apps_script/HSB_DraftAdapter.gs`) → `entwurfAnlegen_` wählt FlowConnect (Jordie), Graph oder Power-Automate-URL (Joel) → Entwurf in M365 `.de` → Rückschreiben `Draft_ID`, `Internet_Message_ID`, `Drafted_At`, `Batch_Status=DRAFTED`, `Send_Status=drafted`.
- **Status nach dem Senden:** `hsbAutoReconcile` (`HSB_GraphAdapter.gs`, alle 15 min) liest „Gesendete Elemente“ von `.de` und übergibt Nachrichten im Graph-Format an `reconcileSentMessages_(messages, quelle)`, das über `processInboundEvent` `Send_Status=sent` setzt.
- **Flyer:** Live-Drive-Dateien `1UMX…` (246 960 B) und `16Kt…` (247 437 B) passen zu den Prüfsummen `a11876…`/`6ac5ed…` in `Config.gs`.
- **All-Inkl IMAP** `w0221a9f.kasserver.com:993`: Fähigkeiten `IMAP4REV1 LITERAL+ AUTH=PLAIN …`, **kein UIDPLUS**. Ordner: Entwürfe `"Entw&APw-rfe"`, Gesendet `"Gesendet"`.
- **Antworten an `.de`:** Reply-To-Header zeigt auf `.de`; den Posteingang von `.de` liest der vorhandene Abgleich weiter (lesend, das ist erlaubt).
- **Datenlage:** Im Sheet stehen 203 Joel-Leads als `.com`-Entwurf (`COM-JOEL-20260926` + `OVERHAUL-JOEL-COM-…`), im Postfach liegen nur 100. 62 davon ohne Versandfreigabe. Klärung in Task 7 (Nutzerentscheidung, kein Code).

## Global Constraints

- Die IMAP-Module der Bridge (`imap.ts`, `mailbox.ts`) enthalten keinen SMTP-Code; ein Test prüft das. Versand kommt erst mit dem Erweiterungsplan `2026-09-27-com-outbound-kostenlos.md` und nur für bereits vorhandene Entwürfe.
- `.de` wird nie als Absender benutzt. Lesen von `.de` (Abgleich Posteingang) bleibt erlaubt.
- Absender `From`: `j-cherino@hsb-boden.com` bzw. `j-post@hsb-boden.com`. `Reply-To`: `j-cherino@hsb-boden.de` bzw. `j-post@hsb-boden.de`.
- Name immer „Jordie Post“ (mit -ie).
- Zugangsdaten nur als Worker-Secrets (`wrangler secret put`) bzw. Apps-Script-Skripteigenschaften. Nie in Code, Git, Logs oder Antworttexten. `.env` nie lesen.
- Rückfallebene: Skripteigenschaft `HSB_COM_BRIDGE_URL` löschen → Knopf nutzt wieder den heutigen Power-Automate-Weg, ohne Redeploy.
- Nur exakte Pfade stagen, kein `git add .`. Vor jedem Commit aus dem Repo-Root: `python3 scripts/verify_ssot.py` (Exit 0).
- Kein Push, kein `deploy.sh`, kein `wrangler deploy` ohne ausdrückliche Freigabe des Nutzers (Task 6).
- Arbeit auf Branch `feat/sales-os-com-bridge` (Jules-Auto-Merge merged freigegebene PRs selbstständig, deshalb PR erst nach Abnahme).

## Review Focus

1. **Zeitüberschreitung nach erfolgreichem APPEND** (UrlFetch bricht ab, Entwurf liegt aber schon im Postfach): Ein zweiter Klick darf keinen zweiten Entwurf erzeugen. Abgedeckt durch die deterministische Message-ID + Suche vor dem APPEND (Task 2, Test `appendDraft ist idempotent`).
2. **Falsches Postfach:** Eine EML mit Joels Absender darf nie in Jordies Postfach landen. Abgedeckt durch die `From`-Prüfung im Handler (Task 3, Test `lehnt fremden Absender ab`).
3. **Leads mit vorhandenem Entwurf** (ca. 1 800 alte `.de`-Entwürfe, `Send_Status=drafted`) dürfen nicht erneut in einen Batch rutschen. Abgedeckt in Task 5 (Eligibility-Test `vorhandener Entwurf blockiert`).
4. **Mailprogramm ändert beim Senden die Message-ID:** Der Abgleich muss trotzdem über die Empfängeradresse treffen. Abgedeckt, weil `reconcileSentMessages_` primär über `toRecipients` matcht (Task 4, Test `Sent-Abgleich reicht Empfänger im Graph-Format weiter`).
5. **Gespeicherte Größe ≠ gesendete Größe** (Server verändert die Nachricht): Dann darf der Entwurf nicht als geprüft gelten. Abgedeckt, `attachmentSize` wird `null` → `ANHANG_UNGEPRUEFT` (Task 4, Test `Größenabweichung ergibt ungeprüft`).

## Dateistruktur

| Datei | Aktion | Verantwortung |
|---|---|---|
| `apps/sales-os/com_bridge/package.json` | neu | Worker-Paket, Skripte `test`, `deploy` |
| `apps/sales-os/com_bridge/tsconfig.json` | neu | TS-Konfiguration |
| `apps/sales-os/com_bridge/wrangler.jsonc` | neu | Worker-Konfiguration, Vars, deklarierte Secrets |
| `apps/sales-os/com_bridge/vitest.config.ts` | neu | Tests laufen in Node, ohne Workers-Runtime |
| `apps/sales-os/com_bridge/src/imap.ts` | neu | Minimaler IMAP-Client über abstraktes `Wire` |
| `apps/sales-os/com_bridge/src/mailbox.ts` | neu | `appendDraft`, `listSent`, Header-Parser |
| `apps/sales-os/com_bridge/src/handler.ts` | neu | HTTP-Routen, Auth, Validierung (ohne Socket-Import, testbar) |
| `apps/sales-os/com_bridge/src/socket.ts` | neu | TLS-Socket → `Wire` (einzige Datei mit `cloudflare:sockets`) |
| `apps/sales-os/com_bridge/src/index.ts` | neu | Worker-Einstieg, verbindet Handler mit Socket |
| `apps/sales-os/com_bridge/test/*.test.ts` | neu | vitest-Tests mit Fake-Server |
| `apps/sales-os/apps_script/HSB_ComBridge.gs` | neu | EML bauen, Entwurf über Bridge, Sent-Abgleich über Bridge |
| `apps/sales-os/apps_script/Config.gs` | ändern | `replyTo` je Flyer |
| `apps/sales-os/apps_script/Engine.gs` | ändern | Eligibility: vorhandener Entwurf blockiert |
| `apps/sales-os/apps_script/HSB_DraftAdapter.gs` | ändern | `.com`-Zweig in `entwurfAnlegen_`, Signatur mit `replyTo` |
| `apps/sales-os/apps_script/HSB_GraphAdapter.gs` | ändern | `hsbAutoReconcile` + Menü-Einrichtung + Knopf „Gesendete abgleichen“ kennen `.com` |
| `apps/sales-os/deploy.sh` | ändern | `HSB_ComBridge.gs` mit ausliefern |
| `apps/sales-os/tests/test_com_bridge.js` | neu | Apps-Script-Tests für `HSB_ComBridge.gs` und die Verdrahtung |
| `apps/sales-os/tests/test_apps_script.js` | ändern | Eligibility-Fall ergänzen |
| `apps/sales-os/docs/MIGRATION_COM_DOMAIN.md` | ändern | Korrekter Ist-Stand, Warnung zu `send-batch` |

Befehle für die komplette Offline-Testsuite (werden in mehreren Tasks gebraucht), aus `apps/sales-os`:

```bash
python3 engine/build_single.py
cp apps_script/HSB_SALES_OS.gs deploy/HSB_SALES_OS.js
cp apps_script/HSB_DraftAdapter.gs deploy/HSB_DraftAdapter.gs.js
cp apps_script/HSB_GraphAdapter.gs deploy/HSB_GraphAdapter.js
cp apps_script/HSB_FlowConnect.gs deploy/HSB_FlowConnect.js
cp apps_script/Sidebar.html deploy/Sidebar.html
test -f apps_script/HSB_ComBridge.gs && cp apps_script/HSB_ComBridge.gs deploy/HSB_ComBridge.js
for f in test_apps_script test_draft_chunking test_flowconnect test_graph_adapter; do node tests/$f.js > /tmp/hsb_$f.log 2>&1 || echo "ROT: $f"; done
test -f tests/test_com_bridge.js && node tests/test_com_bridge.js
```

Im Folgenden heißt das **„Offline-Suite“**. Erwartet: keine Zeile `ROT:` und Exit 0 von `test_com_bridge.js`.

---

### Task 1: Branch und Baseline

**Files:** keine Änderungen.

**Interfaces:** – 

- [ ] **Step 1: Branch anlegen**

```bash
cd ~/KI-System/02_Projects/active/hsb-boden
git status --short apps/sales-os   # Erwartet: nur ?? apps/sales-os/docs/superpowers/plans/2026-09-27-com-entwuerfe-per-knopf.md
git switch -c feat/sales-os-com-bridge
python3 scripts/verify_ssot.py
git add apps/sales-os/docs/superpowers/plans/2026-09-27-com-entwuerfe-per-knopf.md
git commit -m "docs(sales-os): Plan .com-Entwuerfe per Knopf"
```

- [ ] **Step 2: Baseline messen**

```bash
cd apps/sales-os
python3 -m pytest tests/ -q 2>&1 | tail -2
for f in test_apps_script test_draft_chunking test_flowconnect test_graph_adapter; do node tests/$f.js > /tmp/hsb_$f.log 2>&1; echo "$f exit $?"; done
```

Erwartet: pytest `passed`, alle vier Node-Suiten `exit 0`. Wenn nicht: STOPP, Befund dem Nutzer melden, nicht weiterbauen.

- [ ] **Step 3: Sicherstellen, dass `deploy/` dem Quellstand entspricht**

```bash
python3 engine/build_single.py
diff -q apps_script/HSB_SALES_OS.gs deploy/HSB_SALES_OS.js && diff -q apps_script/HSB_DraftAdapter.gs deploy/HSB_DraftAdapter.gs.js && diff -q apps_script/HSB_GraphAdapter.gs deploy/HSB_GraphAdapter.js && echo DEPLOY_SYNCHRON
git status --short   # Erwartet: leer (build_single erzeugt nichts Neues)
```

Erwartet: `DEPLOY_SYNCHRON`. Bei Abweichung: STOPP und dem Nutzer melden, denn dann ist unklar, was live läuft.

---

### Task 2: Bridge – IMAP-Session und Postfach-Operationen

**Files:**
- Create: `apps/sales-os/com_bridge/package.json`, `tsconfig.json`, `vitest.config.ts`
- Create: `apps/sales-os/com_bridge/src/imap.ts`, `src/mailbox.ts`
- Test: `apps/sales-os/com_bridge/test/fake_server.ts`, `test/mailbox.test.ts`

**Interfaces:**
- Produces:
  - `interface Wire { write(d: Uint8Array): Promise<void>; read(): Promise<Uint8Array | null>; close(): Promise<void> }`
  - `class ImapSession { constructor(wire: Wire); greeting(): Promise<void>; command(cmd: string, literal?: Uint8Array): Promise<Untagged[]> }`
  - `class ImapError extends Error`
  - `interface Creds { user: string; pass: string }`
  - `appendDraft(wire: Wire, creds: Creds, messageId: string, eml: Uint8Array): Promise<{ storedSize: number; duplicate: boolean }>`
  - `listSent(wire: Wire, creds: Creds, days: number, now: Date): Promise<SentMessage[]>`
  - `interface SentMessage { id: string; subject: string; toRecipients: { emailAddress: { address: string } }[]; internetMessageId: string; sentDateTime: string }`

- [ ] **Step 1: Paketgerüst anlegen**

`apps/sales-os/com_bridge/package.json`:

```json
{
  "name": "hsb-com-bridge",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "vitest run",
    "deploy": "wrangler deploy",
    "typecheck": "tsc --noEmit"
  },
  "devDependencies": {
    "@cloudflare/workers-types": "^4",
    "typescript": "^5.5.2",
    "vitest": "~4.1.0",
    "wrangler": "^4"
  }
}
```

`apps/sales-os/com_bridge/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "Bundler",
    "strict": true,
    "lib": ["ES2022"],
    "types": ["@cloudflare/workers-types"],
    "noEmit": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

`apps/sales-os/com_bridge/vitest.config.ts`:

```ts
import { defineConfig } from 'vitest/config';

// Tests laufen bewusst in Node: der einzige Workers-spezifische Teil
// (cloudflare:sockets) steckt in src/socket.ts und wird nie importiert.
export default defineConfig({ test: { environment: 'node', include: ['test/**/*.test.ts'] } });
```

```bash
cd ~/KI-System/02_Projects/active/hsb-boden/apps/sales-os/com_bridge
npm install
printf 'node_modules/\n.wrangler/\n.dev.vars\n' > .gitignore
```

- [ ] **Step 2: Fake-IMAP-Server für Tests schreiben**

`apps/sales-os/com_bridge/test/fake_server.ts`:

```ts
import type { Wire } from '../src/imap';

const enc = new TextEncoder();
const dec = new TextDecoder();

export interface FakeMessage { raw: string; flags: string[] }

/**
 * Nachgebauter IMAP-Server mit genau den Befehlen, die die Bridge nutzt.
 * Speichert Nachrichten je Ordner und protokolliert jeden Befehl, damit
 * Tests pruefen koennen, was wirklich gesendet wurde.
 */
export class FakeImap {
  folders: Record<string, FakeMessage[]> = { '"Entw&APw-rfe"': [], '"Gesendet"': [] };
  log: string[] = [];
  loginOk = true;
  /** Wenn gesetzt, wird beim APPEND dieser Inhalt statt des gesendeten gespeichert. */
  mutateAppend: ((raw: string) => string) | null = null;

  private inbox: Uint8Array[] = [];
  private pending = '';
  private selected = '';
  private closed = false;

  wire(): Wire {
    this.inbox.push(enc.encode('* OK [CAPABILITY IMAP4rev1 LITERAL+] ready\r\n'));
    return {
      write: async (d) => { this.pending += dec.decode(d); this.process(); },
      // Der Fake antwortet synchron auf write. Ist nichts mehr da, waere jedes
      // weitere Warten ein Endlos-Spin - deshalb null (= Verbindung zu), dann
      // scheitert der Test sofort mit klarer Meldung statt zu haengen.
      read: async () => (this.inbox.length ? this.inbox.shift()! : null),
      close: async () => { this.closed = true; },
    };
  }

  private send(s: string) { this.inbox.push(enc.encode(s)); }

  private process() {
    for (;;) {
      const lit = this.pending.match(/^(\S+) APPEND (\S+) \(([^)]*)\) \{(\d+)\+\}\r\n/);
      if (lit) {
        const n = Number(lit[4]);
        const start = lit[0].length;
        if (this.pending.length < start + n + 2) return;
        let raw = this.pending.slice(start, start + n);
        this.pending = this.pending.slice(start + n + 2);
        this.log.push(`APPEND ${lit[2]}`);
        if (this.mutateAppend) raw = this.mutateAppend(raw);
        (this.folders[lit[2]] ||= []).push({ raw, flags: lit[3].split(' ') });
        this.send(`${lit[1]} OK APPEND completed\r\n`);
        continue;
      }
      const i = this.pending.indexOf('\r\n');
      if (i < 0) return;
      const line = this.pending.slice(0, i);
      this.pending = this.pending.slice(i + 2);
      this.handle(line);
    }
  }

  private handle(line: string) {
    const [tag, verb, ...rest] = line.split(' ');
    const arg = rest.join(' ');
    this.log.push(verb === 'LOGIN' ? 'LOGIN ***' : `${verb} ${arg}`.trim());
    const box = this.folders[this.selected] || [];
    switch (verb) {
      case 'LOGIN':
        this.send(this.loginOk ? `${tag} OK LOGIN done\r\n` : `${tag} NO [AUTHENTICATIONFAILED] failed\r\n`);
        return;
      case 'EXAMINE':
      case 'SELECT':
        this.selected = arg;
        this.send(`* ${(this.folders[arg] || []).length} EXISTS\r\n${tag} OK [READ-ONLY] done\r\n`);
        return;
      case 'SEARCH': {
        const hdr = arg.match(/^HEADER Message-ID "(.*)"$/);
        const since = arg.match(/^SINCE (\S+)$/);
        const hits: number[] = [];
        box.forEach((m, idx) => {
          if (hdr && m.raw.includes(`Message-ID: ${hdr[1]}`)) hits.push(idx + 1);
          if (since) hits.push(idx + 1);
        });
        this.send(`* SEARCH${hits.length ? ' ' + hits.join(' ') : ''}\r\n${tag} OK done\r\n`);
        return;
      }
      case 'FETCH': {
        const [set, ...itemParts] = arg.split(' ');
        const items = itemParts.join(' ');
        const nums = set.includes(',') ? set.split(',').map(Number) : [Number(set)];
        for (const n of nums) {
          const m = box[n - 1];
          if (!m) continue;
          if (items.includes('RFC822.SIZE')) {
            this.send(`* ${n} FETCH (RFC822.SIZE ${enc.encode(m.raw).length})\r\n`);
          } else {
            const head = m.raw.split('\r\n\r\n')[0] + '\r\n\r\n';
            const len = enc.encode(head).length;
            this.send(`* ${n} FETCH (BODY[HEADER.FIELDS (TO SUBJECT MESSAGE-ID DATE)] {${len}}\r\n${head})\r\n`);
          }
        }
        this.send(`${tag} OK FETCH done\r\n`);
        return;
      }
      case 'LOGOUT':
        this.send(`* BYE bye\r\n${tag} OK LOGOUT done\r\n`);
        return;
      default:
        this.send(`${tag} BAD unknown\r\n`);
    }
  }
}

export function eml(messageId: string, to = 'kunde@firma.de', from = 'Joel <j-cherino@hsb-boden.com>'): string {
  return [
    `From: ${from}`,
    `To: ${to}`,
    'Subject: =?UTF-8?B?VGVzdA==?=',
    'Date: Sun, 27 Sep 2026 10:00:00 +0200',
    `Message-ID: ${messageId}`,
    '',
    'Hallo',
    '',
  ].join('\r\n');
}
```

- [ ] **Step 3: Failing Tests schreiben**

`apps/sales-os/com_bridge/test/mailbox.test.ts`:

```ts
import { describe, expect, it } from 'vitest';
import { appendDraft, listSent } from '../src/mailbox';
import { ImapError } from '../src/imap';
import { FakeImap, eml } from './fake_server';

const creds = { user: 'm0821e5d', pass: 'geheim"mit\\zeichen' };
const bytes = (s: string) => new TextEncoder().encode(s);

describe('appendDraft', () => {
  it('legt den Entwurf mit \\Draft-Flag in Entwürfe ab und meldet die gespeicherte Größe', async () => {
    const srv = new FakeImap();
    const raw = eml('<hsb.L1.B1@hsb-boden.com>');
    const r = await appendDraft(srv.wire(), creds, '<hsb.L1.B1@hsb-boden.com>', bytes(raw));
    expect(r).toEqual({ storedSize: bytes(raw).length, duplicate: false });
    expect(srv.folders['"Entw&APw-rfe"']).toHaveLength(1);
    expect(srv.folders['"Entw&APw-rfe"'][0].flags).toEqual(['\\Draft']);
  });

  it('appendDraft ist idempotent: gleiche Message-ID erzeugt keinen zweiten Entwurf', async () => {
    const srv = new FakeImap();
    const raw = bytes(eml('<hsb.L1.B1@hsb-boden.com>'));
    await appendDraft(srv.wire(), creds, '<hsb.L1.B1@hsb-boden.com>', raw);
    const r2 = await appendDraft(srv.wire(), creds, '<hsb.L1.B1@hsb-boden.com>', raw);
    expect(r2.duplicate).toBe(true);
    expect(srv.folders['"Entw&APw-rfe"']).toHaveLength(1);
  });

  it('meldet die tatsächlich gespeicherte Größe, auch wenn der Server verändert', async () => {
    const srv = new FakeImap();
    srv.mutateAppend = (raw) => raw + 'X';
    const raw = bytes(eml('<hsb.L2.B1@hsb-boden.com>'));
    const r = await appendDraft(srv.wire(), creds, '<hsb.L2.B1@hsb-boden.com>', raw);
    expect(r.storedSize).toBe(raw.length + 1);
  });

  it('wirft ImapError bei falschem Login, ohne das Passwort zu nennen', async () => {
    const srv = new FakeImap();
    srv.loginOk = false;
    const p = appendDraft(srv.wire(), creds, '<hsb.L3.B1@hsb-boden.com>', bytes(eml('<hsb.L3.B1@hsb-boden.com>')));
    await expect(p).rejects.toBeInstanceOf(ImapError);
    await expect(p).rejects.not.toThrow(/geheim/);
  });

  it('quotet Passwörter mit Anführungszeichen und Backslash korrekt', async () => {
    const srv = new FakeImap();
    const writes: string[] = [];
    const w = srv.wire();
    const spy = { ...w, write: async (d: Uint8Array) => { writes.push(new TextDecoder().decode(d)); return w.write(d); } };
    await appendDraft(spy, creds, '<hsb.L4.B1@hsb-boden.com>', bytes(eml('<hsb.L4.B1@hsb-boden.com>')));
    expect(writes.some((s) => s.includes('LOGIN "m0821e5d" "geheim\\"mit\\\\zeichen"'))).toBe(true);
  });
});

describe('listSent', () => {
  it('liefert gesendete Mails im Graph-Format mit reiner Empfängeradresse', async () => {
    const srv = new FakeImap();
    srv.folders['"Gesendet"'].push({ raw: eml('<a@x>', 'Firma GmbH <Info@Firma.de>'), flags: [] });
    srv.folders['"Gesendet"'].push({ raw: eml('<b@x>', 'zwei@firma.de'), flags: [] });
    const r = await listSent(srv.wire(), creds, 14, new Date('2026-09-27T12:00:00Z'));
    expect(r).toHaveLength(2);
    expect(r[0].toRecipients[0].emailAddress.address).toBe('info@firma.de');
    expect(r[0].internetMessageId).toBe('<a@x>');
    expect(r[1].toRecipients[0].emailAddress.address).toBe('zwei@firma.de');
    expect(srv.log).toContain('SEARCH SINCE 13-Sep-2026');
    expect(srv.log.some((l) => l.startsWith('EXAMINE "Gesendet"'))).toBe(true);
  });

  it('leerer Ordner ergibt leere Liste ohne FETCH', async () => {
    const srv = new FakeImap();
    const r = await listSent(srv.wire(), creds, 14, new Date('2026-09-27T12:00:00Z'));
    expect(r).toEqual([]);
    expect(srv.log.some((l) => l.startsWith('FETCH'))).toBe(false);
  });
});
```

- [ ] **Step 4: Test laufen lassen, er muss scheitern**

Run: `npx vitest run test/mailbox.test.ts`
Expected: FAIL, `Failed to resolve import "../src/mailbox"`.

- [ ] **Step 5: IMAP-Session implementieren**

`apps/sales-os/com_bridge/src/imap.ts`:

```ts
const enc = new TextEncoder();
const dec = new TextDecoder();

/** Byte-Leitung zum Server. In Produktion ein TLS-Socket, in Tests ein Fake. */
export interface Wire {
  write(data: Uint8Array): Promise<void>;
  read(): Promise<Uint8Array | null>;
  close(): Promise<void>;
}

export class ImapError extends Error {}

export interface Untagged { line: string; literal?: Uint8Array }

/**
 * Minimaler IMAP4rev1-Client: genau die Befehle, die die Bridge braucht.
 * Literale werden mit LITERAL+ gesendet (vom Server angeboten), dadurch
 * entfaellt das Warten auf die "+"-Fortsetzung.
 */
export class ImapSession {
  private buf = new Uint8Array(0);
  private seq = 0;

  constructor(private wire: Wire) {}

  private async fill(): Promise<void> {
    const chunk = await this.wire.read();
    if (chunk === null) throw new ImapError('Verbindung vom Server geschlossen');
    const next = new Uint8Array(this.buf.length + chunk.length);
    next.set(this.buf);
    next.set(chunk, this.buf.length);
    this.buf = next;
  }

  private async readLine(): Promise<string> {
    for (;;) {
      const i = this.buf.indexOf(10);
      if (i >= 0) {
        const line = dec.decode(this.buf.subarray(0, i)).replace(/\r$/, '');
        this.buf = this.buf.subarray(i + 1);
        return line;
      }
      await this.fill();
    }
  }

  private async readBytes(n: number): Promise<Uint8Array> {
    while (this.buf.length < n) await this.fill();
    const out = this.buf.slice(0, n);
    this.buf = this.buf.subarray(n);
    return out;
  }

  async greeting(): Promise<void> {
    const line = await this.readLine();
    if (!line.startsWith('* OK')) throw new ImapError('Unerwartete Begruessung: ' + line.slice(0, 80));
  }

  /**
   * Sendet einen Befehl und sammelt die ungetaggten Antworten.
   * Fehlermeldungen nennen nur das Befehlswort, nie Argumente - sonst
   * stuende bei LOGIN das Passwort in der Meldung.
   */
  async command(cmd: string, literal?: Uint8Array): Promise<Untagged[]> {
    const tag = 'A' + ++this.seq;
    if (literal) {
      await this.wire.write(enc.encode(`${tag} ${cmd} {${literal.length}+}\r\n`));
      await this.wire.write(literal);
      await this.wire.write(enc.encode('\r\n'));
    } else {
      await this.wire.write(enc.encode(`${tag} ${cmd}\r\n`));
    }
    const out: Untagged[] = [];
    for (;;) {
      const line = await this.readLine();
      if (line.startsWith(tag + ' ')) {
        const rest = line.slice(tag.length + 1);
        if (!rest.startsWith('OK')) {
          throw new ImapError(`${cmd.split(' ')[0]} fehlgeschlagen: ${rest.slice(0, 120)}`);
        }
        return out;
      }
      const m = line.match(/\{(\d+)\}$/);
      if (m) {
        const literalBytes = await this.readBytes(Number(m[1]));
        const tail = await this.readLine();
        out.push({ line: line + tail, literal: literalBytes });
      } else {
        out.push({ line });
      }
    }
  }
}
```

- [ ] **Step 6: Postfach-Operationen implementieren**

`apps/sales-os/com_bridge/src/mailbox.ts`:

```ts
import { ImapError, ImapSession, type Wire } from './imap';

export interface Creds { user: string; pass: string }

export interface SentMessage {
  id: string;
  subject: string;
  toRecipients: { emailAddress: { address: string } }[];
  internetMessageId: string;
  sentDateTime: string;
}

// Ordnernamen bei All-Inkl (modified UTF-7), gemessen am 2026-09-26.
export const DRAFTS = '"Entw&APw-rfe"';
export const SENT = '"Gesendet"';
const MAX_SENT = 200;
const MONATE = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export function quote(s: string): string {
  return '"' + s.replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"';
}

async function withSession<T>(wire: Wire, creds: Creds, fn: (s: ImapSession) => Promise<T>): Promise<T> {
  const s = new ImapSession(wire);
  try {
    await s.greeting();
    await s.command(`LOGIN ${quote(creds.user)} ${quote(creds.pass)}`);
    const result = await fn(s);
    await s.command('LOGOUT').catch(() => undefined);
    return result;
  } finally {
    await wire.close();
  }
}

function searchNumbers(untagged: { line: string }[]): number[] {
  const hit = untagged.find((u) => u.line.startsWith('* SEARCH'));
  if (!hit) return [];
  return hit.line.slice('* SEARCH'.length).trim().split(/\s+/).filter(Boolean).map(Number);
}

async function findDraftSize(s: ImapSession, messageId: string): Promise<number | null> {
  await s.command(`EXAMINE ${DRAFTS}`);
  const nums = searchNumbers(await s.command(`SEARCH HEADER Message-ID ${quote(messageId)}`));
  if (!nums.length) return null;
  const fetched = await s.command(`FETCH ${nums[nums.length - 1]} (RFC822.SIZE)`);
  const m = fetched.map((u) => u.line.match(/RFC822\.SIZE (\d+)/)).find(Boolean);
  if (!m) throw new ImapError('RFC822.SIZE fehlt in der Antwort');
  return Number(m[1]);
}

/**
 * Legt einen Entwurf an - genau einmal je Message-ID.
 *
 * Der Server kann kein UIDPLUS, deshalb wird der Entwurf ueber seine
 * Message-ID wiedergefunden. Dieselbe Suche vor dem APPEND verhindert ein
 * Duplikat, wenn Apps Script nach einem erfolgreichen APPEND in einen
 * Timeout gelaufen ist und den Lead erneut schickt.
 */
export async function appendDraft(wire: Wire, creds: Creds, messageId: string, eml: Uint8Array): Promise<{ storedSize: number; duplicate: boolean }> {
  return withSession(wire, creds, async (s) => {
    const existing = await findDraftSize(s, messageId);
    if (existing !== null) return { storedSize: existing, duplicate: true };
    await s.command(`APPEND ${DRAFTS} (\\Draft)`, eml);
    const stored = await findDraftSize(s, messageId);
    if (stored === null) throw new ImapError('Entwurf nach APPEND nicht auffindbar');
    return { storedSize: stored, duplicate: false };
  });
}

function imapDate(d: Date): string {
  return `${String(d.getUTCDate()).padStart(2, '0')}-${MONATE[d.getUTCMonth()]}-${d.getUTCFullYear()}`;
}

export function parseHeaders(text: string): Record<string, string> {
  const out: Record<string, string> = {};
  const unfolded = text.replace(/\r\n[ \t]+/g, ' ');
  for (const line of unfolded.split('\r\n')) {
    const i = line.indexOf(':');
    if (i > 0) out[line.slice(0, i).trim().toLowerCase()] = line.slice(i + 1).trim();
  }
  return out;
}

export function firstAddress(to: string): string {
  const angle = to.match(/<([^>]+)>/);
  if (angle) return angle[1].trim().toLowerCase();
  const bare = to.match(/[^\s,;<>"]+@[^\s,;<>"]+/);
  return bare ? bare[0].toLowerCase() : '';
}

/** Gesendete Nachrichten der letzten `days` Tage im Graph-Format (nur lesend). */
export async function listSent(wire: Wire, creds: Creds, days: number, now: Date): Promise<SentMessage[]> {
  return withSession(wire, creds, async (s) => {
    await s.command(`EXAMINE ${SENT}`);
    const since = new Date(now.getTime() - days * 86400000);
    const nums = searchNumbers(await s.command(`SEARCH SINCE ${imapDate(since)}`)).slice(-MAX_SENT);
    if (!nums.length) return [];
    const fetched = await s.command(`FETCH ${nums.join(',')} (BODY.PEEK[HEADER.FIELDS (TO SUBJECT MESSAGE-ID DATE)])`);
    return fetched
      .filter((u) => u.literal)
      .map((u) => {
        const h = parseHeaders(new TextDecoder().decode(u.literal));
        const seq = (u.line.match(/^\* (\d+) FETCH/) || [])[1] || '';
        const date = new Date(h['date'] || '');
        return {
          id: h['message-id'] || `COM-${seq}`,
          subject: h['subject'] || '',
          toRecipients: [{ emailAddress: { address: firstAddress(h['to'] || '') } }],
          internetMessageId: h['message-id'] || '',
          sentDateTime: isNaN(date.getTime()) ? '' : date.toISOString(),
        };
      });
  });
}
```

- [ ] **Step 7: Tests laufen lassen**

Run: `npx vitest run test/mailbox.test.ts && npx tsc --noEmit`
Expected: 7 Tests PASS, `tsc` ohne Ausgabe.

- [ ] **Step 8: Commit**

```bash
cd ~/KI-System/02_Projects/active/hsb-boden
python3 scripts/verify_ssot.py
git add apps/sales-os/com_bridge/package.json apps/sales-os/com_bridge/package-lock.json apps/sales-os/com_bridge/tsconfig.json apps/sales-os/com_bridge/vitest.config.ts apps/sales-os/com_bridge/.gitignore apps/sales-os/com_bridge/src/imap.ts apps/sales-os/com_bridge/src/mailbox.ts apps/sales-os/com_bridge/test/fake_server.ts apps/sales-os/com_bridge/test/mailbox.test.ts
git commit -m "feat(sales-os): COM-Bridge IMAP-Kern fuer Entwuerfe und Gesendet (ohne Versand)"
```

---

### Task 3: Bridge – HTTP-Handler, Socket, Worker-Konfiguration

**Files:**
- Create: `apps/sales-os/com_bridge/src/handler.ts`, `src/socket.ts`, `src/index.ts`, `wrangler.jsonc`
- Test: `apps/sales-os/com_bridge/test/handler.test.ts`

**Interfaces:**
- Consumes: `appendDraft`, `listSent`, `Wire`, `ImapError` aus Task 2.
- Produces (HTTP-Vertrag, von Task 4 benutzt):
  - `POST /draft?owner=JOEL|JORDI&messageId=<hsb.…@hsb-boden.com>`, Header `Authorization: Bearer <token>`, Body = EML (ASCII), Antwort 200 `{"ok":true,"draftId":"<…>","internetMessageId":"<…>","storedSize":123,"duplicate":false}`
  - `GET /sent?owner=JOEL|JORDI&days=1..60`, Antwort 200 `{"ok":true,"messages":[SentMessage…]}`
  - Fehler: 401 `{"ok":false,"error":"unauthorized"}`, 400 `{"ok":false,"error":"…"}`, 502 `{"ok":false,"error":"imap: …"}`, 404, 405.
  - `interface Env { IMAP_HOST: string; JOEL_EMAIL: string; JORDI_EMAIL: string; BRIDGE_TOKEN: string; JOEL_USER: string; JOEL_PASS: string; JORDI_USER: string; JORDI_PASS: string }`
  - `createHandler(openWire: (host: string) => Promise<Wire>, now?: () => Date): (req: Request, env: Env) => Promise<Response>`

- [ ] **Step 1: Failing Tests schreiben**

`apps/sales-os/com_bridge/test/handler.test.ts`:

```ts
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { createHandler, type Env } from '../src/handler';
import { FakeImap, eml } from './fake_server';

const env: Env = {
  IMAP_HOST: 'imap.test', JOEL_EMAIL: 'j-cherino@hsb-boden.com', JORDI_EMAIL: 'j-post@hsb-boden.com',
  BRIDGE_TOKEN: 'tok-123', JOEL_USER: 'm0821e5d', JOEL_PASS: 'p1', JORDI_USER: 'm0821e5b', JORDI_PASS: 'p2',
};
const MID = '<hsb.L1.B1@hsb-boden.com>';

function setup() {
  const srv = new FakeImap();
  const hosts: string[] = [];
  const handle = createHandler(async (host) => { hosts.push(host); return srv.wire(); }, () => new Date('2026-09-27T12:00:00Z'));
  return { srv, hosts, handle };
}

function draftReq(body: string, q = `owner=JOEL&messageId=${encodeURIComponent(MID)}`, token = 'tok-123') {
  return new Request(`https://bridge.test/draft?${q}`, {
    method: 'POST', body, headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'message/rfc822' },
  });
}

describe('Handler', () => {
  it('lehnt fehlendes oder falsches Token mit 401 ab', async () => {
    const { handle, hosts } = setup();
    expect((await handle(draftReq(eml(MID), undefined, 'falsch'), env)).status).toBe(401);
    expect(hosts).toHaveLength(0);
  });

  it('legt einen Entwurf an und meldet Größe und Message-ID', async () => {
    const { handle, srv, hosts } = setup();
    const res = await handle(draftReq(eml(MID)), env);
    expect(res.status).toBe(200);
    const body = await res.json() as Record<string, unknown>;
    expect(body).toMatchObject({ ok: true, draftId: MID, internetMessageId: MID, duplicate: false });
    expect(body.storedSize).toBe(new TextEncoder().encode(eml(MID)).length);
    expect(hosts).toEqual(['imap.test']);
    expect(srv.folders['"Entw&APw-rfe"']).toHaveLength(1);
  });

  it('lehnt fremden Absender ab (Joel-EML in Jordies Postfach)', async () => {
    const { handle, srv } = setup();
    const res = await handle(draftReq(eml(MID), `owner=JORDI&messageId=${encodeURIComponent(MID)}`), env);
    expect(res.status).toBe(400);
    expect(srv.folders['"Entw&APw-rfe"']).toHaveLength(0);
  });

  it('lehnt Message-ID ab, die nicht in der EML steht oder nicht zur Domain passt', async () => {
    const { handle } = setup();
    expect((await handle(draftReq(eml('<andere@hsb-boden.com>')), env)).status).toBe(400);
    expect((await handle(draftReq(eml('<x@evil.com>'), 'owner=JOEL&messageId=' + encodeURIComponent('<x@evil.com>')), env)).status).toBe(400);
  });

  it('lehnt unbekannten Owner ab', async () => {
    const { handle } = setup();
    expect((await handle(draftReq(eml(MID), `owner=MAX&messageId=${encodeURIComponent(MID)}`), env)).status).toBe(400);
  });

  it('liefert Gesendet im Graph-Format', async () => {
    const { handle, srv } = setup();
    srv.folders['"Gesendet"'].push({ raw: eml('<s1@x>', 'kunde@firma.de'), flags: [] });
    const res = await handle(new Request('https://bridge.test/sent?owner=JOEL&days=14', { headers: { Authorization: 'Bearer tok-123' } }), env);
    expect(res.status).toBe(200);
    const body = await res.json() as { messages: { toRecipients: { emailAddress: { address: string } }[] }[] };
    expect(body.messages[0].toRecipients[0].emailAddress.address).toBe('kunde@firma.de');
  });

  it('begrenzt days auf 1..60', async () => {
    const { handle } = setup();
    const r = await handle(new Request('https://bridge.test/sent?owner=JOEL&days=365', { headers: { Authorization: 'Bearer tok-123' } }), env);
    expect(r.status).toBe(400);
  });

  it('meldet IMAP-Fehler als 502 ohne Passwort', async () => {
    const { handle, srv } = setup();
    srv.loginOk = false;
    const res = await handle(draftReq(eml(MID)), env);
    expect(res.status).toBe(502);
    expect(await res.text()).not.toContain('p1');
  });

  it('unbekannte Route 404, falsche Methode 405', async () => {
    const { handle } = setup();
    expect((await handle(new Request('https://bridge.test/unbekannt', { method: 'POST', headers: { Authorization: 'Bearer tok-123' } }), env)).status).toBe(404);
    expect((await handle(new Request('https://bridge.test/draft', { method: 'GET', headers: { Authorization: 'Bearer tok-123' } }), env)).status).toBe(405);
  });

  it('die IMAP-Module enthalten keinen Versandweg (kein SMTP, keine Sendeports)', () => {
    const dir = fileURLToPath(new URL('../src', import.meta.url));
    for (const f of readdirSync(dir).filter((n) => n === 'imap.ts' || n === 'mailbox.ts')) {
      const src = readFileSync(join(dir, f), 'utf8');
      expect(src, f).not.toMatch(/smtp|\b465\b|\b587\b/i);
    }
  });
});
```

- [ ] **Step 2: Test laufen lassen, er muss scheitern**

Run: `npx vitest run test/handler.test.ts`
Expected: FAIL, `Failed to resolve import "../src/handler"`.

- [ ] **Step 3: Handler implementieren**

`apps/sales-os/com_bridge/src/handler.ts`:

```ts
import { ImapError, type Wire } from './imap';
import { appendDraft, listSent, type Creds } from './mailbox';

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
const MESSAGE_ID = /^<[A-Za-z0-9._-]+@hsb-boden\.com>$/;
const MAX_EML_BYTES = 10 * 1024 * 1024;

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

/** Kopfzeilen der EML (bis zur ersten Leerzeile), Folgezeilen entfaltet. */
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

export function createHandler(openWire: (host: string) => Promise<Wire>, now: () => Date = () => new Date()) {
  return async function handle(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    const auth = req.headers.get('Authorization') || '';
    if (!sameToken(auth.replace(/^Bearer /, ''), env.BRIDGE_TOKEN)) return json(401, { ok: false, error: 'unauthorized' });

    const route = url.pathname;
    if (route !== '/draft' && route !== '/sent') return json(404, { ok: false, error: 'not_found' });
    const owner = ownerOf(url.searchParams.get('owner'));

    try {
      if (route === '/draft') {
        if (req.method !== 'POST') return json(405, { ok: false, error: 'method_not_allowed' });
        if (!owner) return json(400, { ok: false, error: 'owner' });
        const messageId = url.searchParams.get('messageId') || '';
        if (!MESSAGE_ID.test(messageId)) return json(400, { ok: false, error: 'messageId' });
        const eml = new Uint8Array(await req.arrayBuffer());
        if (!eml.length || eml.length > MAX_EML_BYTES) return json(400, { ok: false, error: 'eml_size' });
        const h = emlHeaders(eml);
        // Fail-closed: ein Entwurf darf nur im Postfach seines Absenders landen.
        if (!(h['from'] || '').toLowerCase().includes('<' + mailboxFor(env, owner) + '>')) {
          return json(400, { ok: false, error: 'from_passt_nicht_zum_postfach' });
        }
        if (h['message-id'] !== messageId) return json(400, { ok: false, error: 'messageId_nicht_in_eml' });
        const r = await appendDraft(await openWire(env.IMAP_HOST), credsFor(env, owner), messageId, eml);
        return json(200, { ok: true, draftId: messageId, internetMessageId: messageId, storedSize: r.storedSize, duplicate: r.duplicate });
      }

      if (req.method !== 'GET') return json(405, { ok: false, error: 'method_not_allowed' });
      if (!owner) return json(400, { ok: false, error: 'owner' });
      const days = Number(url.searchParams.get('days') || '14');
      if (!Number.isInteger(days) || days < 1 || days > 60) return json(400, { ok: false, error: 'days' });
      const messages = await listSent(await openWire(env.IMAP_HOST), credsFor(env, owner), days, now());
      return json(200, { ok: true, messages });
    } catch (e) {
      if (e instanceof ImapError) return json(502, { ok: false, error: 'imap: ' + e.message });
      return json(502, { ok: false, error: 'bridge: ' + String((e as Error).message || e).slice(0, 120) });
    }
  };
}
```

- [ ] **Step 4: Tests laufen lassen**

Run: `npx vitest run`
Expected: alle Tests aus Task 2 und Task 3 PASS (17).

- [ ] **Step 5: Socket, Einstieg und Worker-Konfiguration anlegen**

`apps/sales-os/com_bridge/src/socket.ts`:

```ts
import { connect } from 'cloudflare:sockets';
import type { Wire } from './imap';

/** TLS-Verbindung zum IMAP-Server (Port 993, implizites TLS). */
export async function openSocketWire(host: string): Promise<Wire> {
  const socket = connect({ hostname: host, port: 993 }, { secureTransport: 'on', allowHalfOpen: false });
  const writer = socket.writable.getWriter();
  const reader = socket.readable.getReader();
  return {
    write: (data) => writer.write(data),
    read: async () => {
      const r = await reader.read();
      return r.done ? null : r.value;
    },
    close: async () => {
      try { await socket.close(); } catch { /* bereits geschlossen */ }
    },
  };
}
```

`apps/sales-os/com_bridge/src/index.ts`:

```ts
import { createHandler, type Env } from './handler';
import { openSocketWire } from './socket';

const handle = createHandler(openSocketWire);

export default {
  fetch(req: Request, env: Env): Promise<Response> {
    return handle(req, env);
  },
} satisfies ExportedHandler<Env>;
```

`apps/sales-os/com_bridge/wrangler.jsonc`:

```jsonc
{
  "$schema": "node_modules/wrangler/config-schema.json",
  "name": "hsb-com-bridge",
  "main": "src/index.ts",
  "compatibility_date": "2026-09-27",
  "observability": { "enabled": true },
  "vars": {
    "IMAP_HOST": "w0221a9f.kasserver.com",
    "JOEL_EMAIL": "j-cherino@hsb-boden.com",
    "JORDI_EMAIL": "j-post@hsb-boden.com"
  },
  // Werte nie hier, sondern per `wrangler secret put <NAME>` (Task 6).
  "secrets": {
    "required": ["BRIDGE_TOKEN", "JOEL_USER", "JOEL_PASS", "JORDI_USER", "JORDI_PASS"]
  }
}
```

- [ ] **Step 6: Typprüfung und Trockenlauf-Bundle**

Run: `npx tsc --noEmit && npx wrangler deploy --dry-run --outdir /tmp/hsb-com-bridge-dry`
Expected: `tsc` ohne Ausgabe. Wrangler meldet `--dry-run: exiting now.` ohne Fehler. (Kein Login nötig, es wird nichts hochgeladen.)

- [ ] **Step 7: Commit**

```bash
cd ~/KI-System/02_Projects/active/hsb-boden
python3 scripts/verify_ssot.py
git add apps/sales-os/com_bridge/src/handler.ts apps/sales-os/com_bridge/src/socket.ts apps/sales-os/com_bridge/src/index.ts apps/sales-os/com_bridge/wrangler.jsonc apps/sales-os/com_bridge/test/handler.test.ts
git commit -m "feat(sales-os): COM-Bridge HTTP-Vertrag /draft und /sent mit Postfach-Pruefung"
```

---

### Task 4: Apps Script – `HSB_ComBridge.gs` und Reply-To

**Files:**
- Create: `apps/sales-os/apps_script/HSB_ComBridge.gs`
- Modify: `apps/sales-os/apps_script/Config.gs` (FLYERS: Feld `replyTo`)
- Modify: `apps/sales-os/apps_script/HSB_DraftAdapter.gs` (`bodyHtmlMitSignatur_`: Signatur mit `replyTo`)
- Modify: `apps/sales-os/deploy.sh` (Kopierzeile)
- Test: `apps/sales-os/tests/test_com_bridge.js`

**Interfaces:**
- Consumes: HTTP-Vertrag aus Task 3. Aus dem Bestand: `FLYERS` (Config.gs), `reconcileSentMessages_(messages, quelle)` (HSB_GraphAdapter.gs), Payload aus `createDraftsForBatch` mit `leadId`, `batchId`, `owner`, `to`, `subject`, `bodyHtml`, `attachmentName`, `attachmentContentBytes` (Base64).
- Produces:
  - `comBridgeAktiv_(): boolean`
  - `comMessageId_(leadId, batchId): string`
  - `comEmlBauen_(payload, flyer, messageId): string`
  - `comEntwurfErzeugen_(payload, ownerKey): { draftId, internetMessageId, conversationId, attachmentSize, verifyError }`
  - `comReconcileSentItems_(): { ok, matched, checked, submitted, skipped, foreign }`

- [ ] **Step 1: Failing Test schreiben**

`apps/sales-os/tests/test_com_bridge.js`:

```js
/**
 * Testet den .com-Weg: Apps Script -> COM-Bridge -> All-Inkl-Entwurf.
 *
 * Geprueft wird die AUSGELIEFERTE Datei (deploy/), wie bei test_graph_adapter.js.
 *   1. Absender .com, Antwortadresse .de, Name "Jordie Post".
 *   2. Die Anhangpruefung gilt nur, wenn der Server exakt die gesendete
 *      Nachricht gespeichert hat.
 *   3. Gleicher Lead + Batch ergibt dieselbe Message-ID (Duplikatschutz).
 *   4. Der Sent-Abgleich reicht Nachrichten unveraendert an
 *      reconcileSentMessages_ weiter.
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');
const DEPLOY = path.join(ROOT, 'deploy');

let bestanden = 0;
let fehlgeschlagen = 0;
function pruefe(name, bedingung, detail) {
  if (bedingung) { bestanden++; console.log('PASS  ' + name); }
  else { fehlgeschlagen++; console.log('FAIL  ' + name + (detail ? '  (' + detail + ')' : '')); }
}

const FLYERS = {
  JORDI: { key: 'JORDI', displayName: 'Jordie Post', mailbox: 'j-post@hsb-boden.com', replyTo: 'j-post@hsb-boden.de' },
  JOEL: { key: 'JOEL', displayName: 'Joel Cherino Diaz', mailbox: 'j-cherino@hsb-boden.com', replyTo: 'j-cherino@hsb-boden.de' }
};

function kontext(opt) {
  opt = opt || {};
  const aufrufe = [];
  const reconciled = [];
  const props = Object.assign({ HSB_COM_BRIDGE_URL: 'https://bridge.test/', HSB_COM_BRIDGE_TOKEN: 'tok' }, opt.props || {});
  const k = {
    FLYERS: FLYERS,
    console: console,
    encodeURIComponent: encodeURIComponent,
    Utilities: {
      base64Encode: function (s) { return Buffer.from(String(s), 'utf8').toString('base64'); },
      Charset: { UTF_8: 'UTF-8' },
      getUuid: function () { return '00000000-0000-0000-0000-000000000000'; },
      formatDate: function () { return 'Sun, 27 Sep 2026 10:00:00 +0200'; }
    },
    PropertiesService: { getScriptProperties: function () { return { getProperty: function (n) { return props[n] || null; } }; } },
    UrlFetchApp: {
      fetch: function (url, o) {
        aufrufe.push({ url: url, o: o || {} });
        return opt.antwort(url, o || {});
      }
    },
    reconcileSentMessages_: function (msgs, quelle) { reconciled.push({ msgs: msgs, quelle: quelle }); return { ok: true, matched: msgs.length, checked: msgs.length, submitted: msgs.length, skipped: 0, foreign: 0 }; }
  };
  vm.createContext(k);
  vm.runInContext(fs.readFileSync(path.join(DEPLOY, 'HSB_ComBridge.js'), 'utf8'), k);
  k._aufrufe = aufrufe;
  k._reconciled = reconciled;
  return k;
}

function antwortJson(code, obj) {
  return { getResponseCode: function () { return code; }, getContentText: function () { return JSON.stringify(obj); } };
}

const FLYER_B64 = Buffer.from('PDF-INHALT-0123456789').toString('base64');
const PAYLOAD = {
  leadId: 'L-1', batchId: 'HSB-20260927-JORDI-0001', owner: 'JORDI', to: 'kunde@firma.de',
  subject: 'Industrieböden für Firma – Beratung von Jordie Post', bodyHtml: '<p>Grüße</p>',
  attachmentName: 'HSB-HEXAGON-Industrieboeden-Flyer.pdf', attachmentContentBytes: FLYER_B64
};

// 1. Aktivierung
pruefe('Bridge aktiv mit URL und Token', kontext({ antwort: function () {} }).comBridgeAktiv_() === true);
pruefe('Bridge inaktiv ohne URL', kontext({ props: { HSB_COM_BRIDGE_URL: '' }, antwort: function () {} }).comBridgeAktiv_() === false);
pruefe('Bridge inaktiv mit http statt https', kontext({ props: { HSB_COM_BRIDGE_URL: 'http://x' }, antwort: function () {} }).comBridgeAktiv_() === false);

// 2. Message-ID deterministisch
(function () {
  const k = kontext({ antwort: function () {} });
  const a = k.comMessageId_('L-1', 'HSB-20260927-JORDI-0001');
  pruefe('Message-ID deterministisch', a === k.comMessageId_('L-1', 'HSB-20260927-JORDI-0001'), a);
  pruefe('Message-ID Format passt zur Bridge', /^<[A-Za-z0-9._-]+@hsb-boden\.com>$/.test(a), a);
  pruefe('Message-ID entschaerft Sonderzeichen', /^<[A-Za-z0-9._-]+@hsb-boden\.com>$/.test(k.comMessageId_('L 1/ä', 'B<1>')));
})();

// 3. EML-Aufbau
(function () {
  const k = kontext({ antwort: function () {} });
  const eml = k.comEmlBauen_(PAYLOAD, FLYERS.JORDI, '<hsb.L-1.B@hsb-boden.com>');
  const kopf = eml.split('\r\n\r\n')[0];
  pruefe('From ist .com', /^From: .*<j-post@hsb-boden\.com>$/m.test(kopf));
  pruefe('Reply-To ist .de', /^Reply-To: .*<j-post@hsb-boden\.de>$/m.test(kopf));
  pruefe('Anzeigename kodiert "Jordie Post"', kopf.indexOf(Buffer.from('Jordie Post').toString('base64')) >= 0);
  pruefe('Message-ID gesetzt', /^Message-ID: <hsb\.L-1\.B@hsb-boden\.com>$/m.test(kopf));
  pruefe('EML ist reines ASCII', /^[\x00-\x7F]*$/.test(eml));
  pruefe('Zeilenenden sind CRLF', eml.indexOf('\n') === eml.indexOf('\r\n') + 1 && !/[^\r]\n/.test(eml));
  pruefe('genau ein PDF-Anhang', (eml.match(/Content-Type: application\/pdf/g) || []).length === 1);
  pruefe('Flyer-Bytes unveraendert enthalten', eml.replace(/\r\n/g, '').indexOf(FLYER_B64) >= 0);
})();

// 4. Entwurf: Erfolg
(function () {
  let gesendet = '';
  const k = kontext({ antwort: function (url, o) {
    gesendet = o.payload;
    return antwortJson(200, { ok: true, draftId: '<m>', internetMessageId: '<m>', storedSize: o.payload.length, duplicate: false });
  } });
  const r = k.comEntwurfErzeugen_(PAYLOAD, 'JORDI');
  const a = k._aufrufe[0];
  pruefe('ruft /draft der Bridge (ohne doppelten Slash)', a.url.indexOf('https://bridge.test/draft?owner=JORDI&messageId=') === 0, a.url);
  pruefe('sendet Bearer-Token', a.o.headers && a.o.headers.Authorization === 'Bearer tok');
  pruefe('sendet POST mit message/rfc822', a.o.method === 'post' && a.o.contentType === 'message/rfc822');
  pruefe('attachmentSize = Flyer-Bytes bei gleicher Groesse', r.attachmentSize === Buffer.from(FLYER_B64, 'base64').length, String(r.attachmentSize));
  pruefe('draftId und internetMessageId durchgereicht', r.draftId === '<m>' && r.internetMessageId === '<m>');
  pruefe('keine Sendefunktion aufgerufen', !/send|smtp/i.test(k._aufrufe.map(function (x) { return x.url; }).join(' ')));
  pruefe('Nutzlast ist die EML', /^From: /.test(gesendet));
})();

// 5. Groessenabweichung ergibt ungeprueft
(function () {
  const k = kontext({ antwort: function (url, o) {
    return antwortJson(200, { ok: true, draftId: '<m>', internetMessageId: '<m>', storedSize: o.payload.length + 7, duplicate: false });
  } });
  const r = k.comEntwurfErzeugen_(PAYLOAD, 'JORDI');
  pruefe('Groessenabweichung ergibt ungeprueft (attachmentSize null)', r.attachmentSize === null);
  pruefe('verifyError nennt beide Groessen', /Gespeichert \d+ .*gesendet \d+/.test(r.verifyError), r.verifyError);
})();

// 6. Fehlerfaelle
(function () {
  const k = kontext({ antwort: function () { return antwortJson(502, { ok: false, error: 'imap: LOGIN fehlgeschlagen' }); } });
  let fehler = '';
  try { k.comEntwurfErzeugen_(PAYLOAD, 'JORDI'); } catch (e) { fehler = String(e.message); }
  pruefe('HTTP-Fehler wird geworfen', /COM_BRIDGE HTTP 502/.test(fehler), fehler);

  const k2 = kontext({ antwort: function () { return antwortJson(200, {}); } });
  let f2 = '';
  try { k2.comEntwurfErzeugen_(Object.assign({}, PAYLOAD, { to: 'a@b.de\r\nBcc: x@y.de' }), 'JORDI'); } catch (e) { f2 = String(e.message); }
  pruefe('Header-Injection im Empfaenger wird abgelehnt', /COM_EMPFAENGER_UNGUELTIG/.test(f2) && k2._aufrufe.length === 0, f2);

  const k3 = kontext({ antwort: function () { return antwortJson(200, {}); } });
  let f3 = '';
  try { k3.comEntwurfErzeugen_(PAYLOAD, 'MAX'); } catch (e) { f3 = String(e.message); }
  pruefe('unbekannter Owner wird abgelehnt', /COM_OWNER_UNBEKANNT/.test(f3), f3);
})();

// 7. Sent-Abgleich
(function () {
  const msg = { id: '<s1>', subject: 'x', toRecipients: [{ emailAddress: { address: 'kunde@firma.de' } }], internetMessageId: '<s1>', sentDateTime: '' };
  const k = kontext({ antwort: function (url) { return antwortJson(200, { ok: true, messages: url.indexOf('owner=JOEL') >= 0 ? [msg] : [] }); } });
  const r = k.comReconcileSentItems_();
  pruefe('Sent-Abgleich fragt beide Postfaecher', k._aufrufe.length === 2 && /owner=JOEL/.test(k._aufrufe[0].url) && /owner=JORDI/.test(k._aufrufe[1].url));
  pruefe('Sent-Abgleich nutzt GET /sent mit days', /\/sent\?owner=JOEL&days=14$/.test(k._aufrufe[0].url), k._aufrufe[0].url);
  pruefe('Sent-Abgleich reicht Empfaenger im Graph-Format weiter', k._reconciled[0].msgs[0].toRecipients[0].emailAddress.address === 'kunde@firma.de' && k._reconciled[0].quelle === 'COM');
  pruefe('Sent-Abgleich summiert', r.checked === 1 && r.matched === 1);
})();

console.log('\n' + bestanden + ' bestanden, ' + fehlgeschlagen + ' fehlgeschlagen');
process.exit(fehlgeschlagen ? 1 : 0);
```

- [ ] **Step 2: Test laufen lassen, er muss scheitern**

Run (aus `apps/sales-os`): `node tests/test_com_bridge.js`
Expected: FAIL mit `ENOENT … deploy/HSB_ComBridge.js`.

- [ ] **Step 3: `HSB_ComBridge.gs` schreiben**

`apps/sales-os/apps_script/HSB_ComBridge.gs`:

```js
/**
 * HSB Sales OS - .com-Weg (Apps Script -> COM-Bridge -> All-Inkl-Entwurf).
 *
 * Vertrag:
 *   - Apps Script baut die komplette E-Mail selbst (Text, Signatur, geprüfter
 *     Flyer). Die Bridge legt sie nur als Entwurf ab und liest "Gesendet".
 *   - Die Bridge kann nicht senden. Versand macht ein Mensch im Mailprogramm.
 *   - Antwortformat wie beim Power-Automate-Flow, damit createDraftsForBatch
 *     (Anhangpruefung, Rueckschreiben) unveraendert bleibt.
 *   - Aktiv nur, wenn HSB_COM_BRIDGE_URL und HSB_COM_BRIDGE_TOKEN gesetzt
 *     sind. URL loeschen = zurueck auf Power Automate, ohne Redeploy.
 */

var COM_BRIDGE_PROPS = { url: 'HSB_COM_BRIDGE_URL', token: 'HSB_COM_BRIDGE_TOKEN' };
var COM_SENT_TAGE = 14;

function comBridgeKonfig_() {
  var p = PropertiesService.getScriptProperties();
  return {
    url: String(p.getProperty(COM_BRIDGE_PROPS.url) || '').trim().replace(/\/+$/, ''),
    token: String(p.getProperty(COM_BRIDGE_PROPS.token) || '').trim()
  };
}

function comBridgeAktiv_() {
  var k = comBridgeKonfig_();
  return k.url.indexOf('https://') === 0 && !!k.token;
}

/** Gleicher Lead im gleichen Batch = gleiche Message-ID. Darauf baut der Duplikatschutz der Bridge. */
function comMessageId_(leadId, batchId) {
  var sauber = function (v) { return String(v || '').replace(/[^A-Za-z0-9.-]/g, '-'); };
  return '<hsb.' + sauber(leadId) + '.' + sauber(batchId) + '@hsb-boden.com>';
}

function comHeaderWort_(text) {
  return '=?UTF-8?B?' + Utilities.base64Encode(String(text), Utilities.Charset.UTF_8) + '?=';
}

function comChunk76_(b64) {
  var s = String(b64 || '').replace(/[\r\n]/g, '');
  var out = [];
  for (var i = 0; i < s.length; i += 76) out.push(s.slice(i, i + 76));
  return out.join('\r\n');
}

/** Anzahl Bytes, die ein Base64-Text dekodiert ergibt. */
function comBase64Bytes_(b64) {
  var s = String(b64 || '').replace(/[\r\n]/g, '');
  var pad = s.slice(-2) === '==' ? 2 : (s.slice(-1) === '=' ? 1 : 0);
  return (s.length / 4) * 3 - pad;
}

/** Fertige RFC-822-Nachricht, reines ASCII, CRLF. */
function comEmlBauen_(payload, flyer, messageId) {
  var grenze = 'HSB-COM-' + Utilities.getUuid();
  var antwortAn = flyer.replyTo || flyer.mailbox;
  var z = [];
  z.push('From: ' + comHeaderWort_(flyer.displayName) + ' <' + flyer.mailbox + '>');
  z.push('Reply-To: ' + comHeaderWort_(flyer.displayName) + ' <' + antwortAn + '>');
  z.push('To: ' + String(payload.to).trim());
  z.push('Subject: ' + comHeaderWort_(payload.subject));
  z.push('Date: ' + Utilities.formatDate(new Date(), 'Europe/Berlin', 'EEE, dd MMM yyyy HH:mm:ss Z'));
  z.push('Message-ID: ' + messageId);
  z.push('MIME-Version: 1.0');
  z.push('Content-Type: multipart/mixed; boundary="' + grenze + '"');
  z.push('');
  z.push('--' + grenze);
  z.push('Content-Type: text/html; charset=UTF-8');
  z.push('Content-Transfer-Encoding: base64');
  z.push('');
  z.push(comChunk76_(Utilities.base64Encode(String(payload.bodyHtml), Utilities.Charset.UTF_8)));
  z.push('--' + grenze);
  z.push('Content-Type: application/pdf; name="' + payload.attachmentName + '"');
  z.push('Content-Transfer-Encoding: base64');
  z.push('Content-Disposition: attachment; filename="' + payload.attachmentName + '"');
  z.push('');
  z.push(comChunk76_(payload.attachmentContentBytes));
  z.push('--' + grenze + '--');
  z.push('');
  return z.join('\r\n');
}

/**
 * Legt den Entwurf im .com-Postfach an. Rueckgabe im Flow-Format.
 *
 * Anhangpruefung: Die Bridge meldet die Groesse, die der Server wirklich
 * gespeichert hat. Nur wenn sie exakt der gesendeten EML entspricht, ist
 * belegt, dass der gepruefte Flyer unveraendert im Entwurf liegt. Sonst
 * bleibt attachmentSize leer und createDraftsForBatch markiert den Entwurf
 * als ANHANG_UNGEPRUEFT.
 */
function comEntwurfErzeugen_(payload, ownerKey) {
  var flyer = FLYERS[ownerKey];
  if (!flyer) throw new Error('COM_OWNER_UNBEKANNT: ' + ownerKey);
  if (/[\r\n]/.test(String(payload.to || ''))) throw new Error('COM_EMPFAENGER_UNGUELTIG');

  var k = comBridgeKonfig_();
  var messageId = comMessageId_(payload.leadId, payload.batchId);
  var eml = comEmlBauen_(payload, flyer, messageId);

  var res;
  try {
    res = UrlFetchApp.fetch(k.url + '/draft?owner=' + encodeURIComponent(ownerKey) +
                            '&messageId=' + encodeURIComponent(messageId), {
      method: 'post',
      contentType: 'message/rfc822',
      payload: eml,
      headers: { Authorization: 'Bearer ' + k.token },
      muteHttpExceptions: true
    });
  } catch (transportError) {
    throw new Error('TRANSPORT_UNKLAR: ' + String(transportError));
  }

  var code = res.getResponseCode();
  if (code !== 200) throw new Error('COM_BRIDGE HTTP ' + code + ' ' + res.getContentText().slice(0, 200));
  var body;
  try { body = JSON.parse(res.getContentText()); } catch (parseError) { throw new Error('INVALID_RESPONSE_JSON'); }

  var gleich = body.storedSize === eml.length;
  return {
    draftId: body.draftId,
    internetMessageId: body.internetMessageId,
    conversationId: '',
    attachmentSize: gleich ? comBase64Bytes_(payload.attachmentContentBytes) : null,
    verifyError: gleich ? '' : ('Gespeichert ' + body.storedSize + ' Bytes, gesendet ' + eml.length)
  };
}

/** Liest "Gesendet" beider .com-Postfaecher und uebergibt an den bestehenden Abgleich. */
function comReconcileSentItems_() {
  var k = comBridgeKonfig_();
  var gesamt = { ok: true, matched: 0, checked: 0, submitted: 0, skipped: 0, foreign: 0 };
  ['JOEL', 'JORDI'].forEach(function (owner) {
    var res = UrlFetchApp.fetch(k.url + '/sent?owner=' + owner + '&days=' + COM_SENT_TAGE, {
      headers: { Authorization: 'Bearer ' + k.token },
      muteHttpExceptions: true
    });
    var code = res.getResponseCode();
    if (code !== 200) throw new Error('COM_SENT ' + owner + ' HTTP ' + code + ' ' + res.getContentText().slice(0, 200));
    var msgs = (JSON.parse(res.getContentText()) || {}).messages || [];
    var r = reconcileSentMessages_(msgs, 'COM');
    ['matched', 'checked', 'submitted', 'skipped', 'foreign'].forEach(function (f) { gesamt[f] += r[f] || 0; });
  });
  return gesamt;
}
```

- [ ] **Step 4: `replyTo` in `Config.gs` ergänzen**

In `apps/sales-os/apps_script/Config.gs` im Block `JORDI` direkt nach der Zeile `mailbox: 'j-post@hsb-boden.com',` einfügen:

```js
    // Antworten gehen an das Hauptpostfach. Die .com-Adresse sendet nur.
    replyTo: 'j-post@hsb-boden.de',
```

Im Block `JOEL` direkt nach `mailbox: 'j-cherino@hsb-boden.com',` einfügen:

```js
    replyTo: 'j-cherino@hsb-boden.de',
```

- [ ] **Step 5: Signatur zeigt die Antwortadresse**

In `apps/sales-os/apps_script/HSB_DraftAdapter.gs` in `bodyHtmlMitSignatur_` die Zeile

```js
    + signaturHtml_(flyer.displayName, flyer.mailbox, flyer.mobile)
```

ersetzen durch

```js
    + signaturHtml_(flyer.displayName, flyer.replyTo || flyer.mailbox, flyer.mobile)
```

- [ ] **Step 6: `deploy.sh` liefert die neue Datei aus**

In `apps/sales-os/deploy.sh` nach der Zeile `cp "$SRC/HSB_FlowConnect.gs" "$DEPLOY/HSB_FlowConnect.js"` einfügen:

```bash
cp "$SRC/HSB_ComBridge.gs"   "$DEPLOY/HSB_ComBridge.js"
```

Außerdem ist `apps/sales-os/deploy/.claspignore` eine Allowlist (`**/**` plus `!…`). Ohne Eintrag würde clasp die neue Datei stillschweigend **nicht** hochladen. Nach der Zeile `!HSB_FlowConnect.js` einfügen:

```
!HSB_ComBridge.js
```

Prüfen: `grep -c 'HSB_ComBridge.js' deploy/.claspignore` → `1`. (`deploy/appsscript.json` hat keine `urlFetchWhitelist` und den Scope `script.external_request`, dort ist nichts zu tun.)

- [ ] **Step 7: Offline-Suite laufen lassen**

Run: die Offline-Suite (siehe oben).
Expected: `test_com_bridge.js` meldet `… bestanden, 0 fehlgeschlagen`, keine Zeile `ROT:`. Falls `test_graph_adapter` oder `test_apps_script` wegen der Signatur rot wird: `grep -n "hsb-boden.com" /tmp/hsb_test_*.log` zeigt die Erwartung. Die Tests dort erwarten dann die `.com`-Adresse in der Signatur und werden auf `.de` angepasst (Signatur = Antwortadresse, siehe Global Constraints). Keine anderen Testanpassungen.

- [ ] **Step 8: Commit**

```bash
cd ~/KI-System/02_Projects/active/hsb-boden
python3 scripts/verify_ssot.py
git add apps/sales-os/apps_script/HSB_ComBridge.gs apps/sales-os/apps_script/Config.gs apps/sales-os/apps_script/HSB_DraftAdapter.gs apps/sales-os/apps_script/HSB_SALES_OS.gs apps/sales-os/deploy.sh apps/sales-os/deploy/.claspignore apps/sales-os/deploy/HSB_ComBridge.js apps/sales-os/deploy/HSB_SALES_OS.js apps/sales-os/deploy/HSB_DraftAdapter.gs.js apps/sales-os/tests/test_com_bridge.js
git status --short apps/sales-os   # nur angepasste Testdateien aus Step 7 duerfen noch offen sein; diese exakt nachstagen
git commit -m "feat(sales-os): .com-Entwurf ueber COM-Bridge, Reply-To und Signatur auf .de"
```

---

### Task 5: Verdrahtung – Knopf, 15-Minuten-Abgleich, Batch-Auswahl

**Files:**
- Modify: `apps/sales-os/apps_script/HSB_DraftAdapter.gs` (`entwurfAnlegen_`)
- Modify: `apps/sales-os/apps_script/HSB_GraphAdapter.gs` (`hsbAutoReconcile`, `uiAutoReconcileEinrichten`, `uiGraphReconcileSent`)
- Modify: `apps/sales-os/apps_script/Engine.gs` (`checkEligibility_`)
- Test: `apps/sales-os/tests/test_com_bridge.js` (ergänzen), `apps/sales-os/tests/test_apps_script.js` (ein Fall)

**Interfaces:**
- Consumes: `comBridgeAktiv_`, `comEntwurfErzeugen_`, `comReconcileSentItems_` aus Task 4; bestehend `mailboxLeseweg_`, `mailboxKonto_`, `fcReconcileSentItems_`, `graphReconcileSentItems_`, `fcReconcileInboxReplies_`, `graphReconcileInboxReplies_`, `syncStatusSchreiben_`.
- Produces: `hsbAutoReconcile()` Rückgabe zusätzlich `comSent`.

- [ ] **Step 1: Failing Tests ergänzen**

In `apps/sales-os/tests/test_com_bridge.js` **vor** der Zeile `console.log('\n' + bestanden …` einfügen:

```js
// 8. Verdrahtung im Draft-Adapter: .com hat Vorrang vor FlowConnect/Graph/Power Automate
(function () {
  const genutzt = [];
  const k = {
    console: console,
    PropertiesService: { getScriptProperties: function () { return { getProperty: function () { return null; } }; } },
    UrlFetchApp: { fetch: function () { genutzt.push('PA'); throw new Error('darf nicht aufgerufen werden'); } }
  };
  vm.createContext(k);
  vm.runInContext(fs.readFileSync(path.join(DEPLOY, 'HSB_DraftAdapter.gs.js'), 'utf8'), k);
  k.comBridgeAktiv_ = function () { return true; };
  k.comEntwurfErzeugen_ = function (p, o) { genutzt.push('COM:' + o); return { draftId: '<m>' }; };
  k.fcBrauchtConnector_ = function () { return true; };
  k.fcEntwurfErzeugen_ = function () { genutzt.push('FC'); return {}; };
  k.graphVerbunden_ = function () { return true; };
  k.graphEntwurfErzeugen_ = function () { genutzt.push('GRAPH'); return {}; };
  const r = k.entwurfAnlegen_('Jordie Post', 'JORDI', { leadId: 'L' });
  pruefe('.com-Zweig hat Vorrang', genutzt.join(',') === 'COM:JORDI' && r.draftId === '<m>', genutzt.join(','));

  genutzt.length = 0;
  k.comBridgeAktiv_ = function () { return false; };
  k.entwurfAnlegen_('Jordie Post', 'JORDI', { leadId: 'L' });
  pruefe('ohne Bridge bleibt der bisherige Weg (Rueckfallebene)', genutzt.join(',') === 'FC', genutzt.join(','));
})();

// 9. 15-Minuten-Abgleich laeuft fuer .com auch ohne .de-Verbindung
(function () {
  const status = [];
  const k = {
    console: { warn: function () {}, error: function () {}, log: function () {} },
    LockService: { getScriptLock: function () { return { tryLock: function () { return true; }, releaseLock: function () {} }; } },
    PropertiesService: { getScriptProperties: function () { return { getProperty: function () { return null; } }; }, getUserProperties: function () { return { getProperty: function () { return null; } }; } },
    SpreadsheetApp: {}, UrlFetchApp: {}, ScriptApp: {}
  };
  vm.createContext(k);
  vm.runInContext(fs.readFileSync(path.join(DEPLOY, 'HSB_GraphAdapter.js'), 'utf8'), k);
  k.mailboxLeseweg_ = function () { return ''; };
  k.comBridgeAktiv_ = function () { return true; };
  k.comReconcileSentItems_ = function () { return { ok: true, checked: 3, matched: 1 }; };
  k.syncStatusSchreiben_ = function (mb, r) { status.push({ mb: mb, r: r }); };
  const r = k.hsbAutoReconcile();
  pruefe('Abgleich laeuft mit .com ohne .de-Verbindung', r.ok === true && r.comSent && r.comSent.matched === 1, JSON.stringify(r));
  pruefe('SYNC_STATUS bekommt eine .com-Zeile', status.some(function (s) { return s.mb === 'hsb-boden.com' && s.r.weg === 'COM'; }));

  k.comBridgeAktiv_ = function () { return false; };
  const r2 = k.hsbAutoReconcile();
  pruefe('ohne .de und ohne .com wird uebersprungen', r2.ok === false && r2.skipped === 'nicht_verbunden');
})();
```

In `apps/sales-os/tests/test_apps_script.js` in `testEligibility` im Array `cases` nach der Zeile `['bereits gesendet blockiert', { Send_Status: 'sent' }],` einfügen:

```js
    ['vorhandener Entwurf blockiert', { Send_Status: 'drafted' }],
    ['ungepruefter Entwurf blockiert', { Send_Status: 'needs_check' }],
```

- [ ] **Step 2: Tests laufen lassen, sie müssen scheitern**

Run: Offline-Suite.
Expected: `FAIL  .com-Zweig hat Vorrang`, `FAIL  Abgleich laeuft mit .com ohne .de-Verbindung`, und `ROT: test_apps_script` mit `FAIL … vorhandener Entwurf blockiert`.

- [ ] **Step 3: `.com`-Zweig in `entwurfAnlegen_`**

In `apps/sales-os/apps_script/HSB_DraftAdapter.gs` direkt als erste Anweisung im Rumpf von `function entwurfAnlegen_(owner, ownerKey, payload) {` einfügen:

```js
  // .com-Postfach (All-Inkl) ueber die COM-Bridge. Hat Vorrang, damit kein
  // Entwurf mehr im .de-Postfach entsteht, sobald die Bridge eingerichtet
  // ist. Skripteigenschaft HSB_COM_BRIDGE_URL loeschen = alter Weg.
  if (typeof comBridgeAktiv_ === 'function' && comBridgeAktiv_()) {
    return comEntwurfErzeugen_(payload, ownerKey);
  }

```

- [ ] **Step 4: Eligibility – vorhandener Entwurf blockiert**

In `apps/sales-os/apps_script/Engine.gs` in `checkEligibility_` direkt nach dem Block

```js
  if (sendStatus === 'sent' || sendStatus === 'gesendet') {
    reasons.push('bereits gesendet');
  }
```

einfügen:

```js
  // Ein Lead mit liegendem Entwurf (egal ob .de oder .com) bekommt keinen
  // zweiten. Wer ihn neu entwerfen will, setzt Send_Status bewusst zurueck.
  if (sendStatus === 'drafted' || sendStatus === 'needs_check') {
    reasons.push('bereits Entwurf vorhanden');
  }
```

- [ ] **Step 5: `hsbAutoReconcile` kennt `.com`**

In `apps/sales-os/apps_script/HSB_GraphAdapter.gs` die komplette Funktion `hsbAutoReconcile` ersetzen durch:

```js
function hsbAutoReconcile() {
  var weg = mailboxLeseweg_();
  var com = (typeof comBridgeAktiv_ === 'function') && comBridgeAktiv_();
  if (!weg && !com) {
    console.warn('hsbAutoReconcile: kein Postfach-Lesezugang fuer diesen Nutzer - Abgleich uebersprungen.');
    return { ok: false, skipped: 'nicht_verbunden' };
  }
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(30000)) {
    console.warn('hsbAutoReconcile: Sperre belegt - anderer Abgleich laeuft.');
    return { ok: false, skipped: 'gesperrt' };
  }
  var out = { ok: true, weg: weg, mailbox: weg ? mailboxKonto_() : '', sent: null, comSent: null, inbox: null, errors: [] };
  try {
    if (weg) {
      try { out.sent = (weg === 'APIHUB') ? fcReconcileSentItems_() : graphReconcileSentItems_(); }
      catch (e1) { out.errors.push('sent: ' + String(e1.message || e1)); }
    }
    // Versand laeuft ueber .com. "Gesendet" dort ist die Quelle fuer SENT.
    var comFehler = [];
    if (com) {
      try { out.comSent = comReconcileSentItems_(); }
      catch (e4) { comFehler.push('com-sent: ' + String(e4.message || e4)); out.errors.push(comFehler[0]); }
    }
    // Antworten landen per Reply-To in .de - der Posteingang dort bleibt die Quelle.
    if (weg) {
      try { out.inbox = (weg === 'APIHUB') ? fcReconcileInboxReplies_() : graphReconcileInboxReplies_(); }
      catch (e2) { out.errors.push('inbox: ' + String(e2.message || e2)); }
    }
    out.ok = out.errors.length === 0;
    if (!out.ok) console.error('hsbAutoReconcile: ' + out.errors.join(' | '));
    if (weg) {
      try { syncStatusSchreiben_(out.mailbox, out); } catch (e3) { console.warn('SYNC_STATUS: ' + e3); }
    }
    if (com) {
      try { syncStatusSchreiben_('hsb-boden.com', { weg: 'COM', sent: out.comSent, inbox: null, errors: comFehler }); }
      catch (e5) { console.warn('SYNC_STATUS com: ' + e5); }
    }
    return out;
  } finally {
    lock.releaseLock();
  }
}
```

- [ ] **Step 6: Einrichtung und Knopf „Gesendete abgleichen“**

In `uiAutoReconcileEinrichten` die Bedingung

```js
  if (!mailboxLeseweg_()) {
```

ersetzen durch

```js
  if (!mailboxLeseweg_() && !(typeof comBridgeAktiv_ === 'function' && comBridgeAktiv_())) {
```

und in derselben Funktion die Zeile

```js
    'Postfach: ' + mailboxKonto_() + ' (Weg: ' + mailboxLeseweg_() + ')\n' +
```

ersetzen durch

```js
    'Postfach: ' + (mailboxLeseweg_() ? mailboxKonto_() + ' (Weg: ' + mailboxLeseweg_() + ')' : '-') +
    ((typeof comBridgeAktiv_ === 'function' && comBridgeAktiv_()) ? ' + .com Gesendet (COM-Bridge)' : '') + '\n' +
```

In `uiGraphReconcileSent` die Zeile

```js
    var res = (mailboxLeseweg_() === 'APIHUB') ? fcReconcileSentItems_() : graphReconcileSentItems_();
```

ersetzen durch

```js
    var res = (typeof comBridgeAktiv_ === 'function' && comBridgeAktiv_())
      ? comReconcileSentItems_()
      : ((mailboxLeseweg_() === 'APIHUB') ? fcReconcileSentItems_() : graphReconcileSentItems_());
```

- [ ] **Step 7: Offline-Suite laufen lassen**

Run: Offline-Suite.
Expected: alle PASS, keine Zeile `ROT:`. Wenn ein bestehender Test in `test_apps_script.js` rot wird, weil er einen Lead mit `Send_Status: 'drafted'` als batchfähig erwartet: STOPP und dem Nutzer melden (Verhaltensänderung, nicht still anpassen).

- [ ] **Step 8: Commit**

```bash
cd ~/KI-System/02_Projects/active/hsb-boden
python3 scripts/verify_ssot.py
git add apps/sales-os/apps_script/HSB_DraftAdapter.gs apps/sales-os/apps_script/HSB_GraphAdapter.gs apps/sales-os/apps_script/Engine.gs apps/sales-os/apps_script/HSB_SALES_OS.gs apps/sales-os/deploy/HSB_DraftAdapter.gs.js apps/sales-os/deploy/HSB_GraphAdapter.js apps/sales-os/deploy/HSB_SALES_OS.js apps/sales-os/tests/test_com_bridge.js apps/sales-os/tests/test_apps_script.js
git commit -m "feat(sales-os): Knopf und 15-Minuten-Abgleich nutzen .com, vorhandene Entwuerfe werden nicht erneut gebatcht"
```

---

### Task 6: Inbetriebnahme (jeder Schritt mit Nutzerfreigabe)

> **Ersetzt:** Diese Task und Task 7 werden NICHT ausgeführt. Inbetriebnahme, Doku und Übergabe stehen im Erweiterungsplan `2026-09-27-com-outbound-kostenlos.md` (Tasks 9–10). Dieser Text bleibt nur als Referenz.

**Files:** keine Codeänderung. Ergebnisse in `apps/sales-os/VERIFICATION_REPORT.md` und `RELEASE_MANIFEST.json` (Projektregel nach Deploy).

**Interfaces:** – 

Jeder Schritt ist ein Außenschritt. Vor jedem Schritt beim Nutzer nachfragen, dann ausführen und die Ausgabe zeigen.

- [ ] **Step 1: Cloudflare-Konto wählen und Secrets setzen (Nutzer tippt die Werte selbst)**

```bash
cd ~/KI-System/02_Projects/active/hsb-boden/apps/sales-os/com_bridge
npx wrangler whoami            # Konto und workers.dev-Subdomain vom Nutzer bestätigen lassen (HSB-Konto)
openssl rand -hex 32           # Wert für BRIDGE_TOKEN; Nutzer kopiert ihn selbst
npx wrangler secret put BRIDGE_TOKEN
npx wrangler secret put JOEL_USER    # m0821e5d
npx wrangler secret put JOEL_PASS
npx wrangler secret put JORDI_USER   # m0821e5b
npx wrangler secret put JORDI_PASS
```

Der Nutzer gibt die Passwörter selbst am Prompt ein (`! npx wrangler secret put JOEL_PASS`). Der Agent sieht sie nie.

- [ ] **Step 2: Worker deployen**

```bash
npx wrangler deploy
```

Expected: URL `https://hsb-com-bridge.<konto>.workers.dev`.

- [ ] **Step 3: Rauchtest nur lesend**

```bash
read -s T; curl -s -o /dev/null -w '%{http_code}\n' "https://hsb-com-bridge.<konto>.workers.dev/sent?owner=JOEL&days=14"; curl -s -H "Authorization: Bearer $T" "https://hsb-com-bridge.<konto>.workers.dev/sent?owner=JOEL&days=14" | head -c 400; echo
```

Expected: erste Zeile `401`. Danach `{"ok":true,"messages":[…]}` mit den zwei Test-Mails vom 26.09. an `j-cherino@hsb-boden.de`.

- [ ] **Step 4: Apps Script ausliefern**

```bash
cd ~/KI-System/02_Projects/active/hsb-boden/apps/sales-os
./deploy.sh
```

Expected: `clasp push` erfolgreich, angemeldet als `cherinodiaz@outlook.com`. Danach `clasp pull` in ein Scratch-Verzeichnis und mit `deploy/` vergleichen (wie in der Ausgangslage).

- [ ] **Step 5: Skripteigenschaften setzen (Nutzer im Apps-Script-Editor)**

Projekteinstellungen → Skripteigenschaften:
- `HSB_COM_BRIDGE_URL` = Worker-URL aus Step 2
- `HSB_COM_BRIDGE_TOKEN` = Wert aus Step 1

Danach im Sheet: Menü „HSB Sales OS“ → automatischen Abgleich einrichten (`uiAutoReconcileEinrichten`), bei **beiden** Nutzern.

- [ ] **Step 6: Mailprogramm einrichten (Nutzer, einmalig je Person)**

Outlook oder Apple Mail als IMAP-Konto für `j-cherino@hsb-boden.com` bzw. `j-post@hsb-boden.com`, Server `w0221a9f.kasserver.com`, IMAP 993/SSL, SMTP 465/SSL. Pflicht:
- „Entwürfe“ = Serverordner `Entwürfe`
- „Gesendet“ = Serverordner `Gesendet`, und **gesendete Mails auf dem Server speichern** (sonst sieht der Abgleich nichts)

Ohne Mailprogramm geht es auch über `https://webmail.all-inkl.com/`.

- [ ] **Step 7: Abnahme mit genau einem Lead an eine eigene Adresse**

1. Im Sheet einen Test-Lead anlegen (E-Mail = private Testadresse des Nutzers, Owner Joel, Versandfreigabe yes, Legal_Basis OPT_IN).
2. Batch mit N=1 vorbereiten, „Outlook-Entwürfe direkt anlegen“ klicken.
3. Prüfen: Entwurf liegt in `j-cherino@hsb-boden.com` → Entwürfe, Flyer hängt an, Sheet zeigt `Send_Status=drafted`, `Last_Error` leer.
4. Nochmals auf den Knopf klicken → kein zweiter Entwurf (Batch meldet „übersprungen“).
5. Nutzer sendet den Entwurf von Hand, und zwar mit dem Mailprogramm, das Joel und Jordie im Alltag benutzen werden (nicht nur Webmail). Manche Programme verwerfen beim Öffnen eines fremd angelegten Entwurfs Kopfzeilen oder legen „Gesendet“ lokal ab.
6. Innerhalb von 15 Minuten: `Send_Status=sent`, Zeile blau, `SYNC_STATUS` hat Zeile `hsb-boden.com`.
7. In der Testadresse die **empfangene** Mail öffnen, Quelltext anzeigen und belegen: `From: … <j-cherino@hsb-boden.com>`, `Reply-To: … <j-cherino@hsb-boden.de>`, `Authentication-Results … spf=pass` (DKIM notieren, wie es ist).
8. Auf diese Mail antworten → Antwort erscheint im `.de`-Postfach.
9. Getrennt davon die Weiterleitung belegen: von der Testadresse direkt an `j-cherino@hsb-boden.com` schreiben → Mail erscheint im `.de`-Postfach. (Ohne diesen Test verdeckt die Weiterleitung, ob Reply-To wirkt, und umgekehrt.)

Erst wenn alle neun Punkte belegt sind, gilt der Umbau als abgenommen. Ergebnis mit Belegen in `VERIFICATION_REPORT.md` eintragen.

- [ ] **Step 8: Rückfallebene einmal ausprobieren**

`HSB_COM_BRIDGE_URL` in den Skripteigenschaften löschen → Sidebar zeigt beim nächsten Entwurf wieder den bisherigen Weg. Danach Eigenschaft wieder setzen.

---

### Task 7: Doku, Datenlage, Übergabe

**Files:**
- Modify: `apps/sales-os/docs/MIGRATION_COM_DOMAIN.md`
- Modify: `apps/sales-os/CURRENT_HANDOFF.md`

**Interfaces:** – 

- [ ] **Step 1: `MIGRATION_COM_DOMAIN.md` korrigieren**

Folgenden Abschnitt am Anfang der Datei (nach dem Hinweisblock) einfügen:

```markdown
## Stand 2026-09-27 (ersetzt die Aussagen weiter unten, wo sie widersprechen)

- **Betriebsweg:** Knopf „Entwürfe erzeugen“ im Sheet → COM-Bridge (Cloudflare Worker `hsb-com-bridge`) → Entwurf im `.com`-Postfach → Mensch prüft und sendet → 15-Minuten-Abgleich setzt `sent`.
- **Die Bridge kann nicht senden.** Sie legt nur Entwürfe ab und liest „Gesendet“.
- **Nicht verwenden:** `engine/hsb_cli.py send-batch` (prüft keine Versandfreigabe, Tageslimit nicht dauerhaft, erzeugt neue Mails statt der Entwürfe → Doppelkontakt) und `purge-de --apply` (löscht ungefiltert).
- **Antworten:** per `Reply-To` an `.de`. Die Server-Weiterleitung `.com` → `.de` ist in Task 6 Step 7 zu belegen.
- **Zustellbarkeit:** `hsb-boden.com` registriert am 2026-09-21, DMARC `p=none`. In den ersten Wochen klein anfangen.
```

- [ ] **Step 2: Datenlage dem Nutzer zur Entscheidung vorlegen (kein Code, keine Löschung)**

In `CURRENT_HANDOFF.md` unter einer neuen Überschrift `## Offene Entscheidungen (.com, 2026-09-27)` eintragen:

```markdown
1. 203 Joel-Leads stehen im Sheet als `.com`-Entwurf (`COM-JOEL-20260926`, `OVERHAUL-JOEL-COM-…`), im Postfach liegen 100. Die übrigen bleiben durch `Send_Status=drafted` gesperrt, bis jemand sie bewusst zurücksetzt.
2. 62 der 100 Joel-Entwürfe in `.com` gehören zu Leads mit `Versandfreigabe=no`. Vor dem Senden aussortieren oder Freigabe nachholen.
3. Rund 1 800 alte `.de`-Entwürfe (`Send_Status=drafted`) sind durch die neue Eligibility-Regel gesperrt. Sollen sie als `.com`-Entwürfe neu erzeugt werden, muss ihr Status bewusst zurückgesetzt werden (eigener Auftrag).
4. Das Einzel-Repo `hsb-sales-os` ist veraltet. Archivieren oder löschen ist eine eigene Entscheidung.
```

- [ ] **Step 3: Commit, dann PR nur nach Freigabe**

```bash
cd ~/KI-System/02_Projects/active/hsb-boden
python3 scripts/verify_ssot.py
git add apps/sales-os/docs/MIGRATION_COM_DOMAIN.md apps/sales-os/CURRENT_HANDOFF.md apps/sales-os/VERIFICATION_REPORT.md apps/sales-os/RELEASE_MANIFEST.json
git commit -m "docs(sales-os): .com-Betriebsweg, Abnahme und offene Entscheidungen"
```

Push und PR erst nach ausdrücklicher Freigabe durch den Nutzer.

- [ ] **Step 4: Zustand festhalten**

```bash
ai-state event --tool claude-code --type milestone --msg "hsb-sales-os: .com-Entwürfe per Knopf über COM-Bridge live und abgenommen (Task 6 Step 7)"
```

---

## Bewusst nicht Teil dieses Plans

- Automatischer Versand (später, nach Warm-up und eigenem Plan).
- Umbau der Antwort-Erkennung (läuft weiter über den `.de`-Posteingang).
- Löschen oder Bereinigen der vorhandenen 200 `.com`-Entwürfe und der Sheet-Einträge (nur mit Einzelfreigabe).
- Änderungen am archivierten Einzel-Repo `hsb-sales-os`.
