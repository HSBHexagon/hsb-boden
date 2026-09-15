// @vitest-environment jsdom
import { beforeEach, describe, expect, it } from "vitest";
import {
  CLOUDFLARE_WEB_ANALYTICS_TOKEN,
  initializeCloudflareAnalytics,
} from "../src/lib/cloudflareAnalytics";

beforeEach(() => {
  document.head.innerHTML = "";
  document.body.innerHTML = "";
});

describe("Cloudflare Web Analytics production isolation", () => {
  it("loads exactly one beacon on the canonical production host", () => {
    initializeCloudflareAnalytics(window, document, "www.hsb-boden.de");
    initializeCloudflareAnalytics(window, document, "www.hsb-boden.de");

    const scripts = document.querySelectorAll<HTMLScriptElement>('script[data-hsb-cf-analytics="true"]');
    expect(scripts).toHaveLength(1);
    expect(scripts[0]?.src).toBe("https://static.cloudflareinsights.com/beacon.min.js");
    expect(scripts[0]?.dataset.cfBeacon).toContain(CLOUDFLARE_WEB_ANALYTICS_TOKEN);
  });

  it("does not load the production beacon on preview or localhost", () => {
    initializeCloudflareAnalytics(window, document, "preview.hsb-boden.pages.dev");
    initializeCloudflareAnalytics(window, document, "localhost");

    expect(document.querySelector('script[data-hsb-cf-analytics="true"]')).toBeNull();
  });
});
