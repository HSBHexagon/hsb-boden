import { describe, it, expect, vi } from "vitest";
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

    // Malicious origin mimicking pages.dev domain prefix/suffix
    const reqBypassOrigin = new Request("https://www.hsb-boden.de/api/collect", {
      method: "POST",
      headers: { Origin: "https://malicious.hsb-boden.pages.dev.attacker.com" },
      body: JSON.stringify({ event_name: "test" }),
    });
    const resBypassOrigin = await onRequestPost({ request: reqBypassOrigin, env: {}, waitUntil: () => {} } as any);
    expect(resBypassOrigin.status).toBe(403);
  });

  it("should accept valid local and Cloudflare Pages preview origins", async () => {
    const validOrigins = [
      "http://localhost:3000",
      "http://127.0.0.1:8788",
      "https://preview-123.hsb-boden.pages.dev",
    ];

    for (const origin of validOrigins) {
      const req = new Request("https://www.hsb-boden.de/api/collect", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Origin: origin,
        },
        body: JSON.stringify({ event_name: "page_view" }),
      });
      const res = await onRequestPost({ request: req, env: {}, waitUntil: () => {} } as any);
      expect(res.status).toBe(204);
    }
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

  it("should sanitize parameters and fallback client_id when forwarding to GA4", async () => {
    const originalFetch = globalThis.fetch;
    const fetchSpy = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    globalThis.fetch = fetchSpy;

    try {
      const mockRequest = new Request("https://www.hsb-boden.de/api/collect", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Origin: "https://www.hsb-boden.de",
        },
        body: JSON.stringify({
          event_name: "lead_form_submit",
          client_id: "invalid client id with spaces!",
          params: {
            valid_str: "hello",
            valid_num: 42,
            valid_bool: true,
            "invalid-key-with-dashes": "value",
            nested_obj: { bad: "data" },
            too_long_str: "a".repeat(600),
          },
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

      await Promise.all(waitUntilPromises);

      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const [endpoint, options] = fetchSpy.mock.calls[0];
      expect(endpoint).toContain("https://www.google-analytics.com/mp/collect");

      const body = JSON.parse(options.body);
      expect(body.client_id).toBe("anonymous-edge-user");
      expect(body.events[0].params).toEqual({
        valid_str: "hello",
        valid_num: 42,
        valid_bool: true,
        engagement_time_msec: "100",
      });
    } finally {
      globalThis.fetch = originalFetch;
    }
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
