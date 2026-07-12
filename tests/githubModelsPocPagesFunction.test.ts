import { describe, expect, it } from "vitest";
import {
  onRequest,
  onRequestDelete,
  onRequestGet,
  onRequestHead,
  onRequestOptions,
  onRequestPatch,
  onRequestPost,
  onRequestPut,
} from "../functions/api/github-models";

const disabledEnv = { AI_POC_ENABLED: "false" };
const enabledEnv = { AI_POC_ENABLED: "true" };

const explicitNonPostWrappers = [
  { method: "GET", handler: onRequestGet },
  { method: "HEAD", handler: onRequestHead },
  { method: "PUT", handler: onRequestPut },
  { method: "PATCH", handler: onRequestPatch },
  { method: "DELETE", handler: onRequestDelete },
  { method: "OPTIONS", handler: onRequestOptions },
] as const;

function context(
  method: string,
  env = disabledEnv,
) {
  return {
    request: new Request("https://www.hsb-boden.de/api/github-models", {
      method,
    }),
    env,
  } as Parameters<typeof onRequest>[0];
}

async function expectErrorResponse(
  response: Response,
  status: number,
  error: "not_found" | "method_not_allowed",
) {
  expect(response.status).toBe(status);
  await expect(response.json()).resolves.toEqual({ ok: false, error });
}

describe("github-models Pages function", () => {
  it("returns 404 for a disabled POST request", async () => {
    await expectErrorResponse(
      await onRequestPost(context("POST")),
      404,
      "not_found",
    );
  });

  for (const { method, handler } of explicitNonPostWrappers) {
    it(`returns 404 for disabled ${method} requests`, async () => {
      await expectErrorResponse(
        await handler(context(method)),
        404,
        "not_found",
      );
    });

    it(`returns method_not_allowed for enabled ${method} requests`, async () => {
      const response = await handler(context(method, enabledEnv));

      expect(response.headers.get("Allow")).toBe("POST");
      await expectErrorResponse(response, 405, "method_not_allowed");
    });
  }

  it("returns 404 for a disabled generic PROPFIND request", async () => {
    await expectErrorResponse(await onRequest(context("PROPFIND")), 404, "not_found");
  });

  it("returns method_not_allowed for an enabled generic PROPFIND request", async () => {
    const response = await onRequest(context("PROPFIND", enabledEnv));

    expect(response.headers.get("Allow")).toBe("POST");
    await expectErrorResponse(response, 405, "method_not_allowed");
  });
});
