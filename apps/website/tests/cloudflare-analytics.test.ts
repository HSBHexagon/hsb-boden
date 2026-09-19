// @vitest-environment jsdom
import { beforeEach, describe, expect, it } from "vitest";
import { initializeCloudflareAnalytics } from "../src/lib/cloudflareAnalytics";

const TEST_TOKEN = "test-cf-analytics-token";

beforeEach(() => {
  document.head.innerHTML = "";
  document.body.innerHTML = "";
});

describe("Cloudflare Web Analytics production isolation", () => {
  it("loads exactly one beacon on the canonical production host when token is present", () => {
    initializeCloudflareAnalytics(window, document, "www.hsb-boden.de", TEST_TOKEN);
    initializeCloudflareAnalytics(window, document, "www.hsb-boden.de", TEST_TOKEN);

    const scripts = document.querySelectorAll<HTMLScriptElement>('script[data-hsb-cf-analytics="true"]');
    expect(scripts).toHaveLength(1);
    expect(scripts[0]?.src).toBe("https://static.cloudflareinsights.com/beacon.min.js");
    expect(scripts[0]?.dataset.cfBeacon).toContain(TEST_TOKEN);
  });

  it("does not load the beacon if token is missing or empty", () => {
    initializeCloudflareAnalytics(window, document, "www.hsb-boden.de", undefined);
    initializeCloudflareAnalytics(window, document, "www.hsb-boden.de", "");

    expect(document.querySelector('script[data-hsb-cf-analytics="true"]')).toBeNull();
  });

  it("does not load the production beacon on preview or localhost even with token", () => {
    initializeCloudflareAnalytics(window, document, "preview.hsb-boden.pages.dev", TEST_TOKEN);
    initializeCloudflareAnalytics(window, document, "localhost", TEST_TOKEN);

    expect(document.querySelector('script[data-hsb-cf-analytics="true"]')).toBeNull();
  });
});
