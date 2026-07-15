import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { onRequestPost, onRequestOptions, onRequestGet, resetLeadRateLimiter } from "../functions/api/lead";

const testEnv = { LEAD_WEBHOOK_URL: "https://script.google.com/macros/s/EXAMPLE/exec" };

const validBody = {
  firstName: "Max",
  lastName: "Mustermann",
  company: "Muster Produktion GmbH",
  email: "max@example.com",
  phone: "+49 123 456789",
  industry: "molkerei",
  projectType: "sanierung",
  areaSize: "450",
  liveOperation: "ja",
  loads: ["Säuren/Laugen"],
  message: "Bitte Belastungsprofil prüfen, Fugen sind beschädigt.",
  privacyConsent: true,
  source: "website",
  legalBasis: "inquiry",
};

function makeRequest(body: unknown, opts: { ip?: string; origin?: string; method?: string } = {}) {
  const { ip = "203.0.113.1", origin = "https://hsb-boden.de", method = "POST" } = opts;
  return new Request("https://hsb-boden.de/api/lead", {
    method,
    headers: {
      "Content-Type": "application/json",
      "CF-Connecting-IP": ip,
      Origin: origin,
    },
    body: method === "GET" ? undefined : JSON.stringify(body),
  });
}

function makeContext(request: Request) {
  return { request, env: testEnv } as any;
}

describe("POST /api/lead", () => {
  beforeEach(() => {
    resetLeadRateLimiter();
    vi.restoreAllMocks();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("forwards a valid lead to the configured webhook and returns 200", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("{}", { status: 200 }));
    const res = await onRequestPost(makeContext(makeRequest(validBody)));
    expect(res.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, init] = fetchMock.mock.calls[0];
    expect(init?.body).not.toContain("honeypot");
  });

  it("returns 400 on invalid payload without leaking internals", async () => {
    const res = await onRequestPost(makeContext(makeRequest({ ...validBody, email: "not-an-email" })));
    expect(res.status).toBe(400);
    const json = await res.json();
    expect(JSON.stringify(json)).not.toMatch(/webhook|n8n|stack/i);
  });

  it("silently rejects a filled honeypot without calling the webhook", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("{}", { status: 200 }));
    const res = await onRequestPost(makeContext(makeRequest({ ...validBody, honeypot: "i-am-a-bot" })));
    expect(res.status).toBe(400);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("rejects a foreign Origin", async () => {
    const res = await onRequestPost(makeContext(makeRequest(validBody, { origin: "https://evil.example" })));
    expect(res.status).toBe(403);
  });

  it("rejects a payload larger than 16 KB", async () => {
    const res = await onRequestPost(makeContext(makeRequest({ ...validBody, message: "x".repeat(20_000) })));
    expect(res.status).toBe(413);
  });

  it("returns 502 when the lead webhook is unreachable", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("network down"));
    const res = await onRequestPost(makeContext(makeRequest(validBody)));
    expect(res.status).toBe(502);
  });

  it("returns 502 when the lead webhook responds with a non-success status", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("upstream failure", { status: 503 }),
    );

    const res = await onRequestPost(makeContext(makeRequest(validBody)));

    expect(res.status).toBe(502);
    await expect(res.json()).resolves.toEqual({
      ok: false,
      error: "webhook_unreachable",
    });
  });

  it("rate-limits after 5 requests from the same IP within 10 minutes", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("{}", { status: 200 }));
    const ip = "203.0.113.42";
    for (let i = 0; i < 5; i++) {
      const res = await onRequestPost(makeContext(makeRequest({ ...validBody, email: `lead${i}@example.com` }, { ip })));
      expect(res.status).toBe(200);
    }
    const res6 = await onRequestPost(makeContext(makeRequest({ ...validBody, email: "lead6@example.com" }, { ip })));
    expect(res6.status).toBe(429);
  });

  it("rate-limits after 2 requests from the same email within 30 minutes regardless of IP", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("{}", { status: 200 }));
    const email = "repeat-lead@example.com";
    const res1 = await onRequestPost(makeContext(makeRequest({ ...validBody, email }, { ip: "203.0.113.10" })));
    const res2 = await onRequestPost(makeContext(makeRequest({ ...validBody, email }, { ip: "203.0.113.11" })));
    const res3 = await onRequestPost(makeContext(makeRequest({ ...validBody, email }, { ip: "203.0.113.12" })));
    expect(res1.status).toBe(200);
    expect(res2.status).toBe(200);
    expect(res3.status).toBe(429);
  });
});

describe("GET/PUT/DELETE /api/lead", () => {
  it("rejects GET with 405", async () => {
    const res = await onRequestGet(makeContext(makeRequest(undefined, { method: "GET" })));
    expect(res.status).toBe(405);
  });
});

describe("OPTIONS /api/lead", () => {
  it("answers CORS preflight for the own origin", async () => {
    const res = await onRequestOptions(makeContext(makeRequest(undefined, { method: "OPTIONS" })));
    expect(res.status).toBe(204);
    expect(res.headers.get("Access-Control-Allow-Methods")).toContain("POST");
  });
});
