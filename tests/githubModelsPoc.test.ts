import { describe, expect, it, vi } from "vitest";
import {
  handleGithubModelsPoc,
  type GithubModelsPocEnv,
} from "../src/lib/githubModelsPoc";

const validBody = {
  model: "openai/gpt-5",
  messages: [{ role: "user", content: "Return the word OK." }],
  max_tokens: 32,
};

const enabledEnv: GithubModelsPocEnv = {
  AI_POC_ENABLED: "true",
  AI_POC_ACCESS_TOKEN: "internal-test-token",
  CF_ACCOUNT_ID: "account123",
  CF_AI_GATEWAY_ID: "hsb-boden-ai",
  CF_AIG_TOKEN: "gateway-test-token",
};

function request(body: unknown = validBody, token = "internal-test-token") {
  return new Request("https://www.hsb-boden.de/api/github-models", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

async function json(response: Response) {
  return response.json() as Promise<Record<string, unknown>>;
}

describe("handleGithubModelsPoc", () => {
  it("returns 404 while the PoC is disabled and does not call upstream", async () => {
    const fetchImpl = vi.fn<typeof fetch>();

    const response = await handleGithubModelsPoc(
      request(),
      { ...enabledEnv, AI_POC_ENABLED: "false" },
      fetchImpl,
    );

    expect(response.status).toBe(404);
    expect(await json(response)).toEqual({ ok: false, error: "not_found" });
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it("returns 401 when the internal bearer token is missing or wrong", async () => {
    const fetchImpl = vi.fn<typeof fetch>();

    const response = await handleGithubModelsPoc(
      request(validBody, "wrong-token"),
      enabledEnv,
      fetchImpl,
    );

    expect(response.status).toBe(401);
    expect(await json(response)).toEqual({ ok: false, error: "unauthorized" });
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it("rejects models outside the explicit allowlist", async () => {
    const fetchImpl = vi.fn<typeof fetch>();

    const response = await handleGithubModelsPoc(
      request({ ...validBody, model: "unapproved/model" }),
      enabledEnv,
      fetchImpl,
    );

    expect(response.status).toBe(400);
    expect(await json(response)).toEqual({ ok: false, error: "validation_failed" });
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it("routes a valid request through the configured GitHub Models custom provider", async () => {
    const fetchImpl = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          choices: [{ message: { role: "assistant", content: "OK" } }],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    const response = await handleGithubModelsPoc(request(), enabledEnv, fetchImpl);

    expect(response.status).toBe(200);
    expect(await json(response)).toEqual({
      ok: true,
      result: {
        choices: [{ message: { role: "assistant", content: "OK" } }],
      },
    });
    expect(fetchImpl).toHaveBeenCalledTimes(1);

    const [url, init] = fetchImpl.mock.calls[0];
    expect(url).toBe(
      "https://gateway.ai.cloudflare.com/v1/account123/hsb-boden-ai/custom-github-models/inference/chat/completions",
    );
    expect(init?.method).toBe("POST");
    expect(new Headers(init?.headers).get("cf-aig-authorization")).toBe(
      "Bearer gateway-test-token",
    );
    expect(new Headers(init?.headers).get("cf-aig-cache-ttl")).toBe("0");
    expect(new Headers(init?.headers).has("Authorization")).toBe(false);
    expect(JSON.parse(String(init?.body))).toEqual(validBody);
  });

  it("returns a sanitized 502 when the upstream provider fails", async () => {
    const fetchImpl = vi.fn<typeof fetch>().mockResolvedValue(
      new Response("upstream secret error text", { status: 429 }),
    );

    const response = await handleGithubModelsPoc(request(), enabledEnv, fetchImpl);

    expect(response.status).toBe(502);
    expect(await json(response)).toEqual({ ok: false, error: "upstream_unavailable" });
  });
});
