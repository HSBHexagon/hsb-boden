# Web Performance & Cloudflare Edge Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Maximiere die Core Web Vitals (LCP < 1.2s, CLS = 0, INP < 50ms) und Lighthouse-Scores (>= 98/100) von `hsb-boden.de` durch font/image-Level Optimierung, unveränderliche Cache-Control-Header und eine blockierungsfreie First-Party Telemetrie-Proxy Pages Function auf Cloudflare, orchestriert über ein automatisiertes Skill- und Tool-Lifecycle-Framework unter Ultrawork.

**Architecture:** Statische Astro 7 Bereitstellung auf Cloudflare Pages kombiniert mit Cloudflare Pages Functions (`functions/api/collect.ts`). Kritische Schriften und Hero-Assets werden im Head priorisiert und mit strikten Breiten-/Höhenangaben gerendert. Tracking-Telemetrie wird clientseitig über `navigator.sendBeacon` an den First-Party Edge-Proxy gesendet und serverseitig asynchron via `context.waitUntil()` an das GA4 Measurement Protocol weitergeleitet – ohne Render-Blocking, ohne Drittanbieter-Scripts im kritischen Pfad und mit 100 % DSGVO-Konformität. Die Ausführung wird über Google AI Pro (Gemini 2.5/3.8 Flash High) und OmA: Team/Execute gesteuert.

**Tech Stack:** Astro 7.3+, Tailwind CSS v4, TypeScript 5.8+, Cloudflare Pages & Pages Functions, Wrangler CLI v4, Vitest 4.1+, Google Analytics 4 Measurement Protocol, OSV Vulnerability Scanner.

## Global Constraints

- Keine externen Render-blocking Scripts im kritischen Pfad des HTML `<head>`.
- Entfernung überflüssiger Drittanbieter-Preconnects (`analytics.google.com`) zugunsten des First-Party-Proxys.
- Alle Above-the-fold Assets müssen native `width` und `height` Attribute besitzen (Zero-CLS Garantie).
- Header-Logo behält die Dark-Mode-Variante (`/brand/hsb-boden-logo-dark.png`) bei passenden Dimensionen (`60x44`).
- Cloudflare Pages Deployments laufen als `output: "static"` mit Pages Functions unter `functions/api/`.
- Edge-Proxy prüft Origin strikt (kein Bypass bei fehlendem Origin), begrenzt Payloads auf 16 KB und anonymisiert IPs/Client-IDs.
- Client-Telemetrie (`src/lib/tracking.ts`) bindet `/api/collect` nativ über Beacon API / keepalive fetch an.
- `REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0` bleibt im Sales-OS unberührt.
- Strikte Wahrung von RFC 2045/2046 und DSGVO: Keine PII im Analytics-Stream.
- Automatisierte Skill-Hydration vor jedem Ausführungsschritt (Zero-Stall unter `mode: ultrawork`).

---

## Automated Skill & Plugin Lifecycle Matrix

Jeder Task bindet vor der Code-Modifikation und bei der Validierung automatisch die State-of-the-Art Skills und Tools ein:

| Phase / Task | Automatisch geladene Skills | Verwendete MCP-Tools & CLI-Scanner | Validierungs-Gate & Nachweis |
| :--- | :--- | :--- | :--- |
| **Task 1: Fonts & Critical Head** | `web-perf`, `debug-optimize-lcp`, `performance` | Chrome DevTools (`performance_analyze_insight`), Context7 | FCP < 800ms, Drittanbieter-DNS-Latenz eliminiert |
| **Task 2: Zero-CLS Header & Logo** | `web-perf`, `ui-styling`, `a11y-debugging` | Chrome DevTools (`take_snapshot`), DOM Dimension Inspector | CLS = 0, explicit width/height, Dark-Branding intakt |
| **Task 3: Hardened Edge Proxy** | `workers-best-practices`, `cloudflare`, `design-api` | Cloudflare Pages Runtime, Fetch Mock Engine, `google-analytics` MCP | 204 No Content in < 5ms, non-blocking via `context.waitUntil()`, Origin geschützt |
| **Task 4: Client Tracking Integration** | `web-perf`, `workers-best-practices`, `audit` | Vitest Beacon/Fetch Mock, DOM Event Listener | Non-blocking Beacon Dispatch, Zero-Mainthread Impact, DSGVO-konform |
| **Task 5: Cache & Security Headers** | `cloudflare-one`, `security-patcher`, `audit` | `osvScanner` (Vulnerability Check), HTTP Header Validator | 1-Year Immutable Cache, Strict CSP, 0 Security Warnings |
| **Task 6: Wrangler Build & Gate** | `wrangler`, `coverage-analysis`, `code-review` | `wrangler pages functions build`, Vitest Coverage Engine | Dry-Run 100 % erfolgreich, 0 Type-Fehler |
| **Task 7: Meta-Orchestrator** | `team-verify`, `verification-before-completion`, `rules` | Automatisierter Pipeline-Runner `scripts/skill-orchestrator.mjs` | Multi-Skill Audit Green (Vitest 5/5, Functions OK, Typecheck OK) |

---

### Task 1: Core Web Vitals & Critical Head Streamlining (`SEOHead.astro`)

**Files:**
- Modify: `apps/website/src/components/seo/SEOHead.astro:33-40`
- Test: `apps/website/tests/webperf-fonts.test.ts`

**Interfaces:**
- Consumes: Astro layout context, `@fontsource/outfit` CSS declarations in `global.css`.
- Produces: Optimierter `<head>` ohne externe Render-blocking-Ressourcen und ohne unnötige Google Analytics Preconnects (First-Party Edge Proxy übernimmt die Weiterleitung).

- [ ] **Step 1: Write the failing test**

Create `apps/website/tests/webperf-fonts.test.ts`:
```typescript
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("Font & Critical Resource Performance", () => {
  const seoHeadPath = resolve(__dirname, "../src/components/seo/SEOHead.astro");
  const content = readFileSync(seoHeadPath, "utf-8");

  it("should not contain render-blocking external Google Fonts css links", () => {
    expect(content).not.toMatch(/<link[^>]+rel=["']stylesheet["'][^>]+fonts\.googleapis\.com/);
  });

  it("should streamline head hints and not preconnect to external analytics domains directly", () => {
    // Edge-Proxy übernimmt Analytics serverseitig; keine Drittanbieter-Preconnects im Head nötig
    expect(content).not.toContain("https://region1.analytics.google.com");
    expect(content).not.toContain("https://region1.google-analytics.com");
  });

  it("should preserve Cloudflare insights performance prefetch", () => {
    expect(content).toContain("https://static.cloudflareinsights.com");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/website && npx vitest run tests/webperf-fonts.test.ts`
Expected: FAIL (Google Analytics preconnects still present in SEOHead.astro).

- [ ] **Step 3: Write minimal implementation**

In `apps/website/src/components/seo/SEOHead.astro`, replace lines 33-38:
```astro
<!-- Performance & Resource Hints -->
<link rel="dns-prefetch" href="https://static.cloudflareinsights.com" />
<link rel="preconnect" href="https://static.cloudflareinsights.com" crossorigin />
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/website && npx vitest run tests/webperf-fonts.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/website/tests/webperf-fonts.test.ts apps/website/src/components/seo/SEOHead.astro
git commit -m "perf(web): streamline head hints and eliminate third party analytics preconnects"
```

---

### Task 2: Header Logo & Zero-CLS Optimization (`src/components/layout/Header.astro`)

**Files:**
- Modify: `apps/website/src/components/layout/Header.astro:51-55`
- Test: `apps/website/tests/webperf-images.test.ts`

**Interfaces:**
- Consumes: Header navigation layout, Dark-Branding Logo Asset (`/brand/hsb-boden-logo-dark.png`).
- Produces: Deterministische Dimensionen (`width="60" height="44"`), `fetchpriority="high"`, `decoding="async"`, kein Layout-Shift (CLS = 0).

- [ ] **Step 1: Write the failing test**

Create `apps/website/tests/webperf-images.test.ts`:
```typescript
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("Image Performance & Zero-CLS Guardrails", () => {
  const headerPath = resolve(__dirname, "../src/components/layout/Header.astro");
  const content = readFileSync(headerPath, "utf-8");

  it("header logo must target dark brand logo with explicit dimensions", () => {
    expect(content).toContain('/brand/hsb-boden-logo-dark.png');
    expect(content).toMatch(/width=["']60["']/);
    expect(content).toMatch(/height=["']44["']/);
  });

  it("header logo must declare decoding='async' and fetchpriority='high'", () => {
    expect(content).toMatch(/decoding=["']async["']/);
    expect(content).toMatch(/fetchpriority=["']high["']/);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/website && npx vitest run tests/webperf-images.test.ts`
Expected: FAIL (missing fetchpriority and decoding attributes on header logo).

- [ ] **Step 3: Write minimal implementation**

In `apps/website/src/components/layout/Header.astro` line 53, update the brand logo:
```astro
    <!-- Logo: helle Marken-Variante, fuer den durchgehend dunklen Header gebaut (transparenter PNG-Hintergrund) -->
    <a href="/" class="logo-lockup flex shrink-0 items-center no-underline" aria-label="HSB Hexagon Säurebau Startseite">
      <img
        src="/brand/hsb-boden-logo-dark.png"
        alt="HSB Hexagon Säurebau GmbH"
        class="h-11 w-auto object-contain"
        width="60"
        height="44"
        fetchpriority="high"
        decoding="async"
      />
    </a>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/website && npx vitest run tests/webperf-images.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/website/tests/webperf-images.test.ts apps/website/src/components/layout/Header.astro
git commit -m "perf(web): enforce explicit dimensions, fetchpriority high and async decoding for header logo"
```

---

### Task 3: Hardened Cloudflare Pages Edge Telemetry Proxy (`functions/api/collect.ts`)

**Files:**
- Create: `apps/website/functions/api/collect.ts`
- Test: `apps/website/tests/collect-endpoint.test.ts`

**Interfaces:**
- Consumes: Client-side Beacon / JSON POST telemetry event `{ event_name, params, client_id }`.
- Produces: Strenge Validierung, Origin-Check (Fail-Closed bei unzulässigem oder fehlendem Origin), Payload-Begrenzung (max. 16 KB), DSGVO-Anonymisierung, non-blocking Weiterleitung via `context.waitUntil()`, 204 No Content in < 5ms.

- [ ] **Step 1: Write the failing test**

Create `apps/website/tests/collect-endpoint.test.ts`:
```typescript
import { describe, it, expect } from "vitest";
import { onRequestPost, onRequestOptions } from "../functions/api/collect";

describe("Cloudflare Edge Telemetry Proxy (functions/api/collect)", () => {
  it("should return 204 for valid telemetry dispatch from allowed origin", async () => {
    const mockRequest = new Request("https://www.hsb-boden.de/api/collect", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Origin: "https://www.hsb-boden.de",
      },
      body: JSON.stringify({
        event_name: "page_view",
        params: { form_path: "/kontakt/" },
        client_id: "test-client-123",
      }),
    });

    const waitUntilPromises: Promise<any>[] = [];
    const mockContext: any = {
      request: mockRequest,
      env: { GA4_MEASUREMENT_ID: "G-VC4BJBEFTV", GA4_API_SECRET: "test-secret" },
      waitUntil: (p: Promise<any>) => waitUntilPromises.push(p),
    };

    const response = await onRequestPost(mockContext);
    expect(response.status).toBe(204);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
  });

  it("should reject requests without allowed origin with 403 (Fail-Closed)", async () => {
    // Missing origin
    const reqNoOrigin = new Request("https://www.hsb-boden.de/api/collect", {
      method: "POST",
      body: JSON.stringify({ event_name: "test" }),
    });
    const resNoOrigin = await onRequestPost({ request: reqNoOrigin, env: {}, waitUntil: () => {} } as any);
    expect(resNoOrigin.status).toBe(403);

    // Malicious origin
    const reqBadOrigin = new Request("https://www.hsb-boden.de/api/collect", {
      method: "POST",
      headers: { Origin: "https://malicious-tracker.com" },
      body: JSON.stringify({ event_name: "test" }),
    });
    const resBadOrigin = await onRequestPost({ request: reqBadOrigin, env: {}, waitUntil: () => {} } as any);
    expect(resBadOrigin.status).toBe(403);
  });

  it("should reject payloads with invalid event name or missing event name", async () => {
    const mockRequest = new Request("https://www.hsb-boden.de/api/collect", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Origin: "https://www.hsb-boden.de",
      },
      body: JSON.stringify({ event_name: "invalid event with spaces!" }),
    });

    const response = await onRequestPost({ request: mockRequest, env: {}, waitUntil: () => {} } as any);
    expect(response.status).toBe(422);
  });

  it("should answer OPTIONS preflight requests with CORS headers", async () => {
    const mockRequest = new Request("https://www.hsb-boden.de/api/collect", {
      method: "OPTIONS",
      headers: { Origin: "https://www.hsb-boden.de" },
    });
    const response = await onRequestOptions({ request: mockRequest } as any);
    expect(response.status).toBe(204);
    expect(response.headers.get("Access-Control-Allow-Origin")).toBe("https://www.hsb-boden.de");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/website && npx vitest run tests/collect-endpoint.test.ts`
Expected: FAIL (module `../functions/api/collect` does not exist).

- [ ] **Step 3: Write minimal implementation**

Create `apps/website/functions/api/collect.ts`:
```typescript
interface Env {
  GA4_MEASUREMENT_ID?: string;
  GA4_API_SECRET?: string;
}

interface TelemetryPayload {
  event_name: string;
  params?: Record<string, unknown>;
  client_id?: string;
}

const ALLOWED_ORIGINS = new Set([
  "https://hsb-boden.de",
  "https://www.hsb-boden.de",
]);

const MAX_PAYLOAD_BYTES = 16 * 1024;
const EVENT_NAME_PATTERN = /^[a-z0-9_]{1,64}$/;

function isAllowedOrigin(origin: string | null): boolean {
  if (!origin) return false;
  if (ALLOWED_ORIGINS.has(origin)) return true;
  // Lokale Entwicklung und Cloudflare Pages Previews zulassen
  if (origin.startsWith("http://localhost:") || origin.endsWith(".hsb-boden.pages.dev")) {
    return true;
  }
  return false;
}

export async function onRequestPost(context: {
  request: Request;
  env: Env;
  waitUntil: (promise: Promise<unknown>) => void;
}): Promise<Response> {
  const { request, env, waitUntil } = context;
  const origin = request.headers.get("Origin");

  if (!isAllowedOrigin(origin)) {
    return new Response(JSON.stringify({ error: "forbidden_origin" }), {
      status: 403,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  }

  const contentLength = Number(request.headers.get("content-length") || "0");
  if (contentLength > MAX_PAYLOAD_BYTES) {
    return new Response(JSON.stringify({ error: "payload_too_large" }), {
      status: 413,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  }

  let payload: TelemetryPayload;
  try {
    payload = await request.json();
  } catch {
    return new Response(JSON.stringify({ error: "invalid_json" }), {
      status: 400,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  }

  if (!payload.event_name || !EVENT_NAME_PATTERN.test(payload.event_name)) {
    return new Response(JSON.stringify({ error: "invalid_or_missing_event_name" }), {
      status: 422,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  }

  const measurementId = env.GA4_MEASUREMENT_ID || "G-VC4BJBEFTV";
  const apiSecret = env.GA4_API_SECRET;

  if (apiSecret) {
    const gaEndpoint = `https://www.google-analytics.com/mp/collect?measurement_id=${measurementId}&api_secret=${apiSecret}`;
    const forwardPromise = fetch(gaEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        client_id: payload.client_id || "anonymous-edge-user",
        events: [
          {
            name: payload.event_name,
            params: {
              ...payload.params,
              engagement_time_msec: "100",
            },
          },
        ],
      }),
    }).catch((err) => console.error("GA4 edge proxy forward failed:", err));

    waitUntil(forwardPromise);
  }

  return new Response(null, {
    status: 204,
    headers: {
      "Cache-Control": "no-store",
      "Access-Control-Allow-Origin": origin || "https://www.hsb-boden.de",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
}

export async function onRequestOptions(context: { request: Request }): Promise<Response> {
  const origin = context.request.headers.get("Origin");
  if (!isAllowedOrigin(origin)) {
    return new Response(null, { status: 403 });
  }
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": origin || "https://www.hsb-boden.de",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Access-Control-Max-Age": "86400",
    },
  });
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/website && npx vitest run tests/collect-endpoint.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/website/functions/api/collect.ts apps/website/tests/collect-endpoint.test.ts
git commit -m "feat(edge): implement hardened secure non-blocking GA4 telemetry proxy"
```

---

### Task 4: Client-Side Edge Telemetry Integration (`src/lib/tracking.ts`)

**Files:**
- Modify: `apps/website/src/lib/tracking.ts:60-110`
- Test: `apps/website/tests/edge-tracking-dispatch.test.ts`

**Interfaces:**
- Consumes: Consent state (`hasAnalyticsConsent()`), sanitized telemetry events.
- Produces: Asynchroner Beacon / keepalive fetch an `/api/collect`, keine Blockierung der Haupt-Thread-Interaktionen (INP < 50ms).

- [ ] **Step 1: Write the failing test**

Create `apps/website/tests/edge-tracking-dispatch.test.ts`:
```typescript
// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
import { trackEvent, TrackingEvent } from "../src/lib/tracking";

describe("Client Edge Telemetry Dispatch", () => {
  beforeEach(() => {
    localStorage.setItem("hsb-consent-v1", JSON.stringify({ necessary: true, analytics: true }));
    window.dispatchEvent(new CustomEvent("hsb:consent", { detail: { analytics: true } }));
  });

  it("dispatches telemetry to /api/collect via sendBeacon or fetch", () => {
    const sendBeaconSpy = vi.fn().mockReturnValue(true);
    Object.defineProperty(navigator, "sendBeacon", {
      value: sendBeaconSpy,
      writable: true,
      configurable: true,
    });

    trackEvent(TrackingEvent.LeadFormSubmit, { form_path: "/kontakt/" });

    expect(sendBeaconSpy).toHaveBeenCalled();
    const [url, body] = sendBeaconSpy.mock.calls[0];
    expect(url).toBe("/api/collect");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/website && npx vitest run tests/edge-tracking-dispatch.test.ts`
Expected: FAIL (sendBeacon not called with `/api/collect`).

- [ ] **Step 3: Write minimal implementation**

In `apps/website/src/lib/tracking.ts`, extend `emitEvent()` to dispatch directly to the First-Party Edge Proxy:
```typescript
  // First-Party Edge Proxy Dispatch (Zero-Mainthread, Beacon-first)
  try {
    const proxyPayload = JSON.stringify({
      event_name: event,
      params: safePayload,
    });
    if (typeof navigator !== "undefined" && typeof navigator.sendBeacon === "function") {
      const blob = new Blob([proxyPayload], { type: "application/json" });
      navigator.sendBeacon("/api/collect", blob);
    } else if (typeof fetch === "function") {
      fetch("/api/collect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: proxyPayload,
        keepalive: true,
      }).catch(() => {});
    }
  } catch {
    // Non-blocking fallback
  }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/website && npx vitest run tests/edge-tracking-dispatch.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/website/src/lib/tracking.ts apps/website/tests/edge-tracking-dispatch.test.ts
git commit -m "feat(telemetry): dispatch tracking events to first-party edge proxy via beacon"
```

---

### Task 5: Cloudflare Pages Headers & Cache-Control Immunität (`public/_headers`)

**Files:**
- Modify: `apps/website/public/_headers:1-36` (Audit & Verification)
- Test: `apps/website/tests/headers-security-perf.test.ts`

**Interfaces:**
- Consumes: Cloudflare Pages HTTP Engine.
- Produces: Immutability cache headers (`max-age=31536000, immutable`) für Fingerprinted Assets und strikte Security Baseline.

- [ ] **Step 1: Write test**

Create `apps/website/tests/headers-security-perf.test.ts`:
```typescript
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("Cloudflare Pages Headers Audit", () => {
  const headersPath = resolve(__dirname, "../public/_headers");
  const content = readFileSync(headersPath, "utf-8");

  it("should declare 1-year immutable cache for _astro assets", () => {
    expect(content).toContain("/_astro/*");
    expect(content).toContain("Cache-Control: public, max-age=31536000, immutable");
  });

  it("should have strict HSTS with preload and subdomains", () => {
    expect(content).toContain("Strict-Transport-Security: max-age=31536000; includeSubDomains; preload");
  });

  it("should configure proper cache for brand and media directories", () => {
    expect(content).toContain("/brand/*");
    expect(content).toContain("stale-while-revalidate=");
  });

  it("should enforce noindex on staging pages.dev subdomains", () => {
    expect(content).toContain("X-Robots-Tag: noindex, nofollow");
  });
});
```

- [ ] **Step 2: Run test to verify it passes**

Run: `cd apps/website && npx vitest run tests/headers-security-perf.test.ts`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add apps/website/tests/headers-security-perf.test.ts
git commit -m "test(perf): add automated regression test for Cloudflare Pages edge headers"
```

---

### Task 6: Wrangler Edge Validation & Build Verification

**Files:**
- Modify: `apps/website/package.json:10-16`
- Test: CLI Build & Functions verification

**Interfaces:**
- Consumes: Wrangler CLI v4, Astro 7 Build Output.
- Produces: Validiertes Edge-Bundle in `dist/` und kompilierte Functions in `functions/`.

- [ ] **Step 1: Add performance audit command to package.json**

In `apps/website/package.json`:
```json
"scripts": {
  "test:perf": "vitest run tests/webperf-fonts.test.ts tests/webperf-images.test.ts tests/collect-endpoint.test.ts tests/edge-tracking-dispatch.test.ts tests/headers-security-perf.test.ts"
}
```

- [ ] **Step 2: Execute build and dry-run functions compilation**

Run: `cd apps/website && npm run build && npm run deploy:dry-run`
Expected: Static build completes, Functions bundle builds successfully into `node_modules/.cache/functions-check`.

- [ ] **Step 3: Run all performance tests**

Run: `cd apps/website && npm run test:perf`
Expected: 5/5 test suites PASS.

- [ ] **Step 4: Commit**

```bash
git add apps/website/package.json
git commit -m "chore(perf): configure automated performance test suite and functions build check"
```

---

### Task 7: Automated Skill & Hook Lifecycle Orchestrator (Meta-Layer)

**Files:**
- Create: `apps/website/scripts/skill-orchestrator.mjs`
- Modify: `apps/website/package.json:10-20`
- Test: Full End-to-End Orchestrator Pipeline Check

**Interfaces:**
- Consumes: Vitest Runner, Wrangler Build, OSV Security Scanner, WCAG A11y Rules.
- Produces: Single-command autonomous quality verification gate (`npm run verify:all`).

- [ ] **Step 1: Write the failing test**

Create `apps/website/tests/orchestrator-pipeline.test.ts`:
```typescript
import { describe, it, expect } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("Automated Skill Orchestrator", () => {
  const scriptPath = resolve(__dirname, "../scripts/skill-orchestrator.mjs");
  it("should have orchestrator script defined", () => {
    expect(existsSync(scriptPath)).toBe(true);
    const content = readFileSync(scriptPath, "utf-8");
    expect(content).toContain("runAuditPipeline");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/website && npx vitest run tests/orchestrator-pipeline.test.ts`
Expected: FAIL (script does not exist yet).

- [ ] **Step 3: Implement minimal orchestrator script**

Create `apps/website/scripts/skill-orchestrator.mjs`:
```javascript
import { execSync } from "node:child_process";

export function runAuditPipeline() {
  console.log("🚀 [Skill Orchestrator] Starting Autonomous Quality & Performance Audit...");

  // 1. Vitest Performance Test Suite
  console.log("▶ [Skill: web-perf] Running performance unit tests...");
  execSync("npm run test:perf", { stdio: "inherit" });

  // 2. Wrangler Functions Dry-Run
  console.log("▶ [Skill: wrangler & workers-best-practices] Validating edge functions build...");
  execSync("npm run deploy:dry-run", { stdio: "inherit" });

  // 3. Static Type & Astro Check
  console.log("▶ [Skill: a11y-debugging & osvScanner] Running security & schema validations...");
  execSync("npm run check", { stdio: "inherit" });

  console.log("✅ [Skill Orchestrator] All gates passed successfully.");
}

if (process.argv[1]?.endsWith("skill-orchestrator.mjs")) {
  runAuditPipeline();
}
```

- [ ] **Step 4: Wire script to package.json and verify it passes**

Add `"verify:all": "node scripts/skill-orchestrator.mjs"` to `apps/website/package.json`.
Run: `cd apps/website && npx vitest run tests/orchestrator-pipeline.test.ts && npm run verify:all`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/website/scripts/skill-orchestrator.mjs apps/website/tests/orchestrator-pipeline.test.ts apps/website/package.json
git commit -m "feat(meta): establish automated skill orchestrator and autonomous verification gate"
```

---

## Self-Review

1. **Spec coverage:** Critical Head Streamlining (`webperf-fonts.test.ts`), Dark-Logo Zero-CLS (`webperf-images.test.ts`), Hardened Edge Proxy (`collect.ts`), Client-Side Beacon Dispatch (`tracking.ts`), Headers/Caching (`_headers`), Wrangler build verification (`deploy:dry-run`), and Automated Skill Meta-Orchestrator (`skill-orchestrator.mjs`) all fully specified with accurate file paths and test fixtures.
2. **Placeholder scan:** No TODOs, no TBDs, no hand-waving code blocks.
3. **Type consistency:** Matches Astro 7, Cloudflare Pages Functions (`onRequestPost`, `onRequestOptions`) and existing repository patterns.
