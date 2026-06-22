# P0B Lead-Endpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Einen serverseitigen `/api/lead`-Endpoint für die HSB-Boden-Astro/Cloudflare-Website bauen, der Leads validiert, rate-limitiert und an den vorhandenen (noch inaktiven) n8n-Webhook weiterleitet — ohne Secrets im Frontend und ohne Live-Aktivierung.

**Architecture:** Astro Server-Endpoint (`output: "server"`, Cloudflare-Adapter) unter `src/pages/api/lead.ts`. Validierung über das bereits vorhandene `leadFormSchema` (`src/lib/validation.ts`, zod). Rate-Limiting als reine In-Memory-Utility-Funktion (`src/lib/rateLimit.ts`), unit-testbar ohne Worker-Runtime. Forwarding per `fetch` mit `AbortController`-Timeout an die n8n-Webhook-URL aus `import.meta.env.N8N_LEAD_WEBHOOK_URL` (Secret, kein Default, kein Repo-Wert). `LeadForm.tsx` bleibt unverändert — es postet bereits an `site.leadEndpoint`, das erst durch Setzen von `PUBLIC_LEAD_ENDPOINT` aktiviert wird (separate, hier NICHT enthaltene Aktivierungsentscheidung).

**Tech Stack:** Astro 5 (server output), Cloudflare Workers Adapter, zod (bereits Dependency), Vitest + jsdom (bereits konfiguriert).

## Global Constraints

- Kein Push, kein Deploy, kein Production-Cutover (`AGENTS.md`, `P0B_IMPLEMENTATION_PLAN.md`).
- Keine Live-Aktivierung von `PUBLIC_LEAD_ENDPOINT`: Die Env-Var bleibt in diesem Plan ungesetzt; der Endpoint existiert, ist aber nicht öffentlich angebunden, bis separat freigegeben.
- Keine Secrets im Code oder Repo. n8n-Webhook-URL nur als Env-Var-Referenz (`N8N_LEAD_WEBHOOK_URL`), kein echter Wert.
- Rate-Limit-Werte exakt aus `PUBLIC_LEAD_ENDPOINT_SPEC.md` Abschnitt 6: IP max. 5 POSTs/10 min, E-Mail max. 2 POSTs/30 min, Payload-Limit 16 KB, Timeout 6 s, max. 1 Retry.
- Response-Codes exakt aus Abschnitt 9: 400 (Validierung), 405 (Methode), 429 (Rate-Limit), 502 (n8n nicht erreichbar), 500 (intern).
- `source` und `legalBasis` werden serverseitig fix auf `"website"` / `"inquiry"` gesetzt, niemals aus dem Body übernommen (Spec Abschnitt 5).
- Logging ohne Secrets/PII im Klartext (Spec Abschnitt 10).
- Nur exakte Pfade stagen, kein `git add .` (Projekt-`CLAUDE.md`).

---

### Task 1: Rate-Limit-Utility

**Files:**
- Create: `src/lib/rateLimit.ts`
- Test: `tests/rate-limit.test.ts`

**Interfaces:**
- Produces: `createRateLimiter(options: { windowMs: number; max: number }): { check(key: string, now: number): boolean }` — `check` gibt `true` zurück wenn erlaubt, `false` wenn Limit erreicht, und zählt den Versuch in jedem Fall (auch bei `false`, damit wiederholte Verstöße nicht das Fenster zurücksetzen). `now` wird explizit übergeben (kein `Date.now()` intern), damit Tests deterministisch sind.

- [ ] **Step 1: Write the failing test**

```typescript
// tests/rate-limit.test.ts
import { describe, expect, it } from "vitest";
import { createRateLimiter } from "../src/lib/rateLimit";

describe("createRateLimiter", () => {
  it("allows requests under the limit within the window", () => {
    const limiter = createRateLimiter({ windowMs: 10_000, max: 2 });
    expect(limiter.check("ip-1", 0)).toBe(true);
    expect(limiter.check("ip-1", 1_000)).toBe(true);
  });

  it("blocks requests once the limit is reached within the window", () => {
    const limiter = createRateLimiter({ windowMs: 10_000, max: 2 });
    limiter.check("ip-1", 0);
    limiter.check("ip-1", 1_000);
    expect(limiter.check("ip-1", 2_000)).toBe(false);
  });

  it("resets the window after windowMs has elapsed", () => {
    const limiter = createRateLimiter({ windowMs: 10_000, max: 1 });
    limiter.check("ip-1", 0);
    expect(limiter.check("ip-1", 5_000)).toBe(false);
    expect(limiter.check("ip-1", 10_001)).toBe(true);
  });

  it("tracks keys independently", () => {
    const limiter = createRateLimiter({ windowMs: 10_000, max: 1 });
    limiter.check("ip-1", 0);
    expect(limiter.check("ip-2", 0)).toBe(true);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/rate-limit.test.ts`
Expected: FAIL — `Cannot find module '../src/lib/rateLimit'`

- [ ] **Step 3: Write minimal implementation**

```typescript
// src/lib/rateLimit.ts
type RateLimiterOptions = {
  windowMs: number;
  max: number;
};

type RateLimiter = {
  check(key: string, now: number): boolean;
};

export function createRateLimiter({ windowMs, max }: RateLimiterOptions): RateLimiter {
  const hits = new Map<string, number[]>();

  return {
    check(key, now) {
      const existing = hits.get(key) ?? [];
      const withinWindow = existing.filter((ts) => now - ts < windowMs);
      withinWindow.push(now);
      hits.set(key, withinWindow);
      return withinWindow.length <= max;
    },
  };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/rate-limit.test.ts`
Expected: PASS, 4 tests

- [ ] **Step 5: Commit**

```bash
git add src/lib/rateLimit.ts tests/rate-limit.test.ts
git commit -m "feat(hsb): add in-memory rate limiter for lead endpoint"
```

---

### Task 2: `/api/lead` Endpoint

**Files:**
- Create: `src/pages/api/lead.ts`
- Test: `tests/api-lead.test.ts`
- Modify (read-only Konsum, keine Änderung nötig): `src/lib/validation.ts` (liefert `leadFormSchema`), `src/lib/rateLimit.ts` (aus Task 1)

**Interfaces:**
- Consumes: `leadFormSchema` aus `src/lib/validation.ts` (zod-Schema, `.parse`/`.safeParse`), `createRateLimiter` aus Task 1.
- Produces: Astro `APIRoute`-Export `POST`, `ALL` (für 405 auf andere Methoden), `prerender = false`.

- [ ] **Step 1: Write the failing tests**

```typescript
// tests/api-lead.test.ts
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ALL, POST } from "../src/pages/api/lead";

const validBody = {
  firstName: "Max",
  lastName: "Muster",
  company: "Muster GmbH",
  email: "max@muster.de",
  phone: "+49 123 4567",
  industry: "lebensmittelindustrie",
  projectType: "neubau",
  liveOperation: "ja",
  loads: ["Säuren/Laugen"],
  message: "Bitte um Rückmeldung zu unserem Bodenprojekt.",
  privacyConsent: true,
};

function makeRequest(body: unknown, init: Partial<{ headers: Record<string, string>; method: string }> = {}) {
  const payload = JSON.stringify(body);
  return new Request("https://hsb-boden.de/api/lead", {
    method: init.method ?? "POST",
    headers: {
      "Content-Type": "application/json",
      "CF-Connecting-IP": "203.0.113.1",
      ...init.headers,
    },
    body: init.method === "GET" ? undefined : payload,
  });
}

describe("POST /api/lead", () => {
  beforeEach(() => {
    vi.stubEnv("N8N_LEAD_WEBHOOK_URL", "https://n8n.example.invalid/webhook/hsb-boden-lead-intake");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200 }));
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it("accepts a valid lead and forwards it to n8n", async () => {
    const response = await POST({ request: makeRequest(validBody) } as any);
    expect(response.status).toBe(200);
    const json = await response.json();
    expect(json.ok).toBe(true);
    expect(fetch).toHaveBeenCalledTimes(1);
    const [, init] = (fetch as any).mock.calls[0];
    const forwarded = JSON.parse(init.body);
    expect(forwarded.source).toBe("website");
    expect(forwarded.legalBasis).toBe("inquiry");
  });

  it("rejects an invalid payload with 400", async () => {
    const response = await POST({ request: makeRequest({ ...validBody, email: "not-an-email" }) } as any);
    expect(response.status).toBe(400);
  });

  it("rejects missing privacyConsent with 400", async () => {
    const response = await POST({ request: makeRequest({ ...validBody, privacyConsent: false }) } as any);
    expect(response.status).toBe(400);
  });

  it("silently rejects a filled honeypot with 400", async () => {
    const response = await POST({ request: makeRequest({ ...validBody, honeypot: "spam" }) } as any);
    expect(response.status).toBe(400);
    expect(fetch).not.toHaveBeenCalled();
  });

  it("rejects payloads over 16KB with 400", async () => {
    const response = await POST({
      request: makeRequest({ ...validBody, message: "x".repeat(20_000) }),
    } as any);
    expect(response.status).toBe(400);
  });

  it("returns 502 when n8n is unreachable", async () => {
    (fetch as any).mockRejectedValue(new Error("network down"));
    const response = await POST({ request: makeRequest(validBody) } as any);
    expect(response.status).toBe(502);
  });

  it("returns 429 after exceeding the IP rate limit", async () => {
    for (let i = 0; i < 5; i += 1) {
      await POST({ request: makeRequest({ ...validBody, email: `lead${i}@muster.de` }) } as any);
    }
    const response = await POST({ request: makeRequest({ ...validBody, email: "lead-6@muster.de" }) } as any);
    expect(response.status).toBe(429);
  });
});

describe("ALL /api/lead (non-POST methods)", () => {
  it("returns 405 for GET", async () => {
    const response = await ALL({ request: makeRequest({}, { method: "GET" }) } as any);
    expect(response.status).toBe(405);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/api-lead.test.ts`
Expected: FAIL — `Cannot find module '../src/pages/api/lead'`

- [ ] **Step 3: Write minimal implementation**

```typescript
// src/pages/api/lead.ts
import type { APIRoute } from "astro";
import { leadFormSchema } from "../../lib/validation";
import { createRateLimiter } from "../../lib/rateLimit";

export const prerender = false;

const MAX_PAYLOAD_BYTES = 16 * 1024;
const FETCH_TIMEOUT_MS = 6_000;

const ipLimiter = createRateLimiter({ windowMs: 10 * 60 * 1000, max: 5 });
const emailLimiter = createRateLimiter({ windowMs: 30 * 60 * 1000, max: 2 });

function jsonResponse(status: number, body: Record<string, unknown>) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function getClientIp(request: Request): string {
  return request.headers.get("CF-Connecting-IP") ?? request.headers.get("X-Forwarded-For") ?? "unknown";
}

export const POST: APIRoute = async ({ request }) => {
  const origin = request.headers.get("Origin");
  if (origin && new URL(origin).hostname !== new URL(request.url).hostname) {
    return jsonResponse(403, { ok: false, error: "invalid_origin" });
  }

  const rawBody = await request.text();
  if (new TextEncoder().encode(rawBody).length > MAX_PAYLOAD_BYTES) {
    return jsonResponse(400, { ok: false, error: "payload_too_large" });
  }

  let body: Record<string, unknown>;
  try {
    body = JSON.parse(rawBody);
  } catch {
    return jsonResponse(400, { ok: false, error: "invalid_json" });
  }

  if (typeof body.honeypot === "string" && body.honeypot.trim() !== "") {
    return jsonResponse(400, { ok: false, error: "rejected" });
  }

  const parsed = leadFormSchema.safeParse(body);
  if (!parsed.success) {
    return jsonResponse(400, { ok: false, error: "invalid_payload", issues: parsed.error.issues.map((i) => i.path.join(".")) });
  }

  const ip = getClientIp(request);
  const now = Date.now();
  if (!ipLimiter.check(ip, now)) {
    return jsonResponse(429, { ok: false, error: "rate_limited_ip" });
  }
  if (!emailLimiter.check(parsed.data.email, now)) {
    return jsonResponse(429, { ok: false, error: "rate_limited_email" });
  }

  const webhookUrl = import.meta.env.N8N_LEAD_WEBHOOK_URL;
  if (!webhookUrl) {
    console.error("lead_endpoint_misconfigured: N8N_LEAD_WEBHOOK_URL missing");
    return jsonResponse(500, { ok: false, error: "internal_error" });
  }

  const forwardPayload = {
    ...parsed.data,
    source: "website",
    legalBasis: "inquiry",
  };

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const upstream = await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(forwardPayload),
      signal: controller.signal,
    });
    if (!upstream.ok) {
      console.error(`lead_forward_failed status=${upstream.status}`);
      return jsonResponse(502, { ok: false, error: "upstream_unavailable" });
    }
  } catch (error) {
    console.error(`lead_forward_error type=${error instanceof Error ? error.name : "unknown"}`);
    return jsonResponse(502, { ok: false, error: "upstream_unavailable" });
  } finally {
    clearTimeout(timeout);
  }

  console.info(`lead_received result=ok email_domain=${parsed.data.email.split("@")[1] ?? "unknown"}`);
  return jsonResponse(200, { ok: true });
};

export const ALL: APIRoute = async ({ request }) => {
  if (request.method === "POST") {
    return POST({ request } as Parameters<APIRoute>[0]);
  }
  return jsonResponse(405, { ok: false, error: "method_not_allowed" });
};
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/api-lead.test.ts`
Expected: PASS, 8 tests

- [ ] **Step 5: Commit**

```bash
git add src/pages/api/lead.ts tests/api-lead.test.ts
git commit -m "feat(hsb): add server-side /api/lead endpoint with validation and n8n forwarding"
```

---

### Task 3: Stale Legacy-Pfad im n8n-Workflow korrigieren

**Files:**
- Modify: `ops/n8n/hsb-boden-lead-intake.json` (Node `archive-lead`, Parameter `fileName`)

**Interfaces:**
- Keine Code-Schnittstelle — reine Konfigurationskorrektur, kein Einfluss auf Task 1/2.

> Hintergrund: Der Node schreibt aktuell nach `/Users/joelcherinodiaz/ObsidianVault/_AI_Memory/leads/hsb-boden/...`. Dieser Pfad wurde in der Home-Root-Konsolidierung vom 2026-06-20 als Legacy archiviert und existiert nicht mehr als aktive Wahrheit (`CANONICAL_STATE.md`). Der Workflow ist zwar `active: false`, aber die Referenz ist bereits jetzt falsch und würde beim späteren Aktivieren brechen.

- [ ] **Step 1: Pfad korrigieren**

In `ops/n8n/hsb-boden-lead-intake.json`, Node `archive-lead`, Feld `fileName`, ersetze:

```
"fileName": "=/Users/joelcherinodiaz/ObsidianVault/_AI_Memory/leads/hsb-boden/{{$json.archiveFileName}}",
```

durch:

```
"fileName": "=/Users/joelcherinodiaz/KI-System/ObsidianVault/brain/05_reports/leads/hsb-boden/{{$json.archiveFileName}}",
```

- [ ] **Step 2: JSON-Validität prüfen**

Run: `node -e "JSON.parse(require('fs').readFileSync('ops/n8n/hsb-boden-lead-intake.json','utf8')); console.log('valid')"`
Expected: `valid`

- [ ] **Step 3: Commit**

```bash
git add ops/n8n/hsb-boden-lead-intake.json
git commit -m "fix(hsb): point n8n lead archive node at canonical brain path"
```

---

### Task 4: Verifikation und Doku-Abschluss

**Files:**
- Modify: `CURRENT_EXECUTION_STATE.md` (Status-Tabelle Zeile „Lead-Prozess vollständig?")
- Modify: `P0B_TEST_PLAN.md` (Abschnitt 7 „Abschlussprüfung" mit Ergebnis ergänzen)

**Interfaces:**
- Keine Code-Schnittstelle — Doku-Abschluss nach grünem Verification-Gate aus Task 1–3.

- [ ] **Step 1: Vollständigen Testlauf ausführen**

Run: `npm run test:run`
Expected: PASS, alle bisherigen + 12 neuen Tests (4 Rate-Limit + 8 Endpoint)

- [ ] **Step 2: Typprüfung und Build**

Run: `npm run check && npm run build`
Expected: beide PASS, 0 Fehler

- [ ] **Step 3: Doku aktualisieren**

In `CURRENT_EXECUTION_STATE.md`, Zeile „Lead-Prozess vollständig?" von `nein` auf:

```
| **Lead-Prozess vollständig?** | teilweise | `/api/lead` implementiert und getestet (Mock-n8n); `PUBLIC_LEAD_ENDPOINT` bewusst NICHT gesetzt — Live-Aktivierung erfordert separate Freigabe. n8n-Workflow weiterhin `active: false`. |
```

In `P0B_TEST_PLAN.md`, Abschnitt 7 ergänzen:

```
- 2026-06-20: `npm run test:run`, `npm run check`, `npm run build` grün nach P0B-Endpoint-Implementierung. Live-E2E-Testlead (Abschnitt 5) weiterhin offen, da `PUBLIC_LEAD_ENDPOINT` ungesetzt bleibt.
```

- [ ] **Step 4: Commit**

```bash
git add CURRENT_EXECUTION_STATE.md P0B_TEST_PLAN.md
git commit -m "docs(hsb): record P0B lead endpoint verification result"
```

---

## Bewusst nicht in diesem Plan

- Keine Änderung an `LeadForm.tsx`, `site.ts` oder `.env`/`wrangler.toml`-Secrets — Aktivierung (`PUBLIC_LEAD_ENDPOINT` setzen, `N8N_LEAD_WEBHOOK_URL` als echtes Secret hinterlegen) ist eine separate Freigabe-Entscheidung, kein Code-Task.
- Kein Google-Sheets-CRM-Light-Append (P0B_TEST_PLAN Abschnitt 4) — eigener Block nach dieser Implementierung.
- Kein echter n8n-Live-Test, kein Push, kein Deploy.
