import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { onRequestPost, resetLeadRateLimiter } from "../functions/api/lead";

const validPayload = {
  firstName: "Max",
  lastName: "Mustermann",
  company: "Muster Produktion GmbH",
  email: "max@example.com",
  phone: "+49 123 456789",
  industry: "molkerei",
  projectType: "sanierung",
  areaSize: "450",
  liveOperation: "ja",
  loads: ["Säuren/Laugen", "Hochdruckreinigung"],
  message: "Bitte Belastungsprofil prüfen, Fugen sind beschädigt.",
  privacyConsent: true,
  source: "website",
  legalBasis: "inquiry",
};

function context(
  payload: Record<string, unknown>,
  env: {
    LEAD_WEBHOOK_URL: string;
    LEAD_WEBHOOK_SECRET?: string;
  },
) {
  return {
    request: new Request("https://www.hsb-boden.de/api/lead", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Origin: "https://www.hsb-boden.de",
        "CF-Connecting-IP": `203.0.113.${Math.floor(Math.random() * 200) + 1}`,
      },
      body: JSON.stringify(payload),
    }),
    env,
  } as Parameters<typeof onRequestPost>[0];
}

function forwardedPayload(fetchImpl: ReturnType<typeof vi.fn<typeof fetch>>) {
  expect(fetchImpl).toHaveBeenCalledTimes(1);
  const [, init] = fetchImpl.mock.calls[0];
  return JSON.parse(String(init?.body)) as Record<string, unknown>;
}

describe("lead webhook authentication", () => {
  beforeEach(() => {
    resetLeadRateLimiter();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("keeps the legacy webhook payload unchanged when no secret is configured", async () => {
    const fetchImpl = vi.fn<typeof fetch>().mockResolvedValue(new Response("", { status: 200 }));
    vi.stubGlobal("fetch", fetchImpl);

    const response = await onRequestPost(
      context(
        { ...validPayload, _hsbWebhookToken: "browser-controlled-token" },
        { LEAD_WEBHOOK_URL: "https://script.google.test/webhook" },
      ),
    );

    expect(response.status).toBe(200);
    const forwarded = forwardedPayload(fetchImpl);
    expect(forwarded).not.toHaveProperty("_hsbWebhookToken");
    expect(forwarded).toMatchObject(validPayload);
  });

  it("injects the configured secret server-side and overrides browser input", async () => {
    const fetchImpl = vi.fn<typeof fetch>().mockResolvedValue(new Response("", { status: 200 }));
    vi.stubGlobal("fetch", fetchImpl);

    const response = await onRequestPost(
      context(
        { ...validPayload, _hsbWebhookToken: "browser-controlled-token" },
        {
          LEAD_WEBHOOK_URL: "https://script.google.test/webhook",
          LEAD_WEBHOOK_SECRET: "server-controlled-secret",
        },
      ),
    );

    expect(response.status).toBe(200);
    const forwarded = forwardedPayload(fetchImpl);
    expect(forwarded._hsbWebhookToken).toBe("server-controlled-secret");
    expect(forwarded._hsbWebhookToken).not.toBe("browser-controlled-token");
    expect(forwarded).toMatchObject(validPayload);
  });
});
