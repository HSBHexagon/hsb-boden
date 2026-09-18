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
