import { describe, it, expect } from "vitest";
import { onRequestPost, onRequestOptions, onRequestGet } from "../functions/api/optout";

describe("Cloudflare Opt-Out Endpoint (functions/api/optout)", () => {
  it("should return 200 and suppressed: true for valid opt-out payload", async () => {
    const mockRequest = new Request("https://www.hsb-boden.de/api/optout", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Origin: "https://www.hsb-boden.de",
      },
      body: JSON.stringify({
        email: "test@example-client.de",
        lead_id: "HSB-20261012-0001",
        token: "abcdef1234567890",
        reason: "Kein Industrieboden vorhanden",
      }),
    });

    const waitUntilPromises: Promise<any>[] = [];
    const mockContext: any = {
      request: mockRequest,
      env: {},
      waitUntil: (p: Promise<any>) => waitUntilPromises.push(p),
    };

    const response = await onRequestPost(mockContext);
    expect(response.status).toBe(200);

    const body = (await response.json()) as Record<string, any>;
    expect(body.ok).toBe(true);
    expect(body.suppressed).toBe(true);
    expect(body.email).toBe("test@example-client.de");
    expect(body.lead_id).toBe("HSB-20261012-0001");
  });

  it("should reject invalid email format with 422", async () => {
    const mockRequest = new Request("https://www.hsb-boden.de/api/optout", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Origin: "https://www.hsb-boden.de",
      },
      body: JSON.stringify({
        email: "not-an-email",
      }),
    });

    const response = await onRequestPost({ request: mockRequest, env: {}, waitUntil: () => {} } as any);
    expect(response.status).toBe(422);
    const body = (await response.json()) as Record<string, any>;
    expect(body.error).toBe("invalid_email");
  });

  it("should reject forbidden origins with 403", async () => {
    const mockRequest = new Request("https://www.hsb-boden.de/api/optout", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Origin: "https://malicious-site.com",
      },
      body: JSON.stringify({
        email: "chef@kunde.de",
      }),
    });

    const response = await onRequestPost({ request: mockRequest, env: {}, waitUntil: () => {} } as any);
    expect(response.status).toBe(403);
  });

  it("should respond with 204 to OPTIONS request", async () => {
    const mockRequest = new Request("https://www.hsb-boden.de/api/optout", {
      method: "OPTIONS",
      headers: { Origin: "https://www.hsb-boden.de" },
    });

    const response = await onRequestOptions({ request: mockRequest, env: {}, waitUntil: () => {} } as any);
    expect(response.status).toBe(204);
    expect(response.headers.get("Access-Control-Allow-Methods")).toContain("POST");
  });

  it("should reject GET request with 405 Method Not Allowed", async () => {
    const mockRequest = new Request("https://www.hsb-boden.de/api/optout", {
      method: "GET",
      headers: { Origin: "https://www.hsb-boden.de" },
    });

    const response = await onRequestGet({ request: mockRequest, env: {}, waitUntil: () => {} } as any);
    expect(response.status).toBe(405);
  });
});
