import { afterEach, expect, it, vi } from "vitest";
import { onRequestPost, onRequestOptions } from "../functions/api/collect";
afterEach(() => vi.unstubAllGlobals());
it("retires forwarding even with legacy payloads containing private fields", async () => {
  const request = new Request("https://www.hsb-boden.de/api/collect", { method: "POST", body: JSON.stringify({ event_name: "generate_lead", params: { email: "private@example.com" } }) });
  const forward = vi.fn(); vi.stubGlobal("fetch", forward);
  const response = await onRequestPost({ request });
  expect(response.status).toBe(410); expect(response.headers.get("Cache-Control")).toBe("no-store");
  expect(forward).not.toHaveBeenCalled();
});
it("does not allow a new CORS transport", async () => {
  const response = await onRequestOptions({ request: new Request("https://www.hsb-boden.de/api/collect") });
  expect(response.status).toBe(410); expect(response.headers.get("Access-Control-Allow-Origin")).toBeNull();
});
