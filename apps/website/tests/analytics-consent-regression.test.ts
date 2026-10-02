// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { createAnalyticsLoader } from "../src/lib/analytics";
import { analyticsPageLocation, analyticsReferrer } from "../src/lib/analyticsLocation";
let item: ReturnType<typeof createAnalyticsLoader>;
beforeEach(() => {\n  localStorage.clear();\n  document.head.innerHTML = "";\n  window.history.replaceState({}, "", "/");\n  document.cookie = "_ga=; Max-Age=0; Path=/";\n});
afterEach(() => item?.destroy());
const dispatch = (analytics: boolean) => window.dispatchEvent(new CustomEvent("hsb:consent", { detail: { analytics } }));
it("grants statistics without advertising and supports withdrawal/regrant", () => {
  const gtag = vi.fn(); (window as Window & { gtag?: unknown }).gtag = gtag;
  item = createAnalyticsLoader(window, document); item.initialize(); dispatch(true);
  expect(gtag).toHaveBeenCalledWith("consent", "update", { analytics_storage: "granted", ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied" });
  document.cookie = "_ga=test; Path=/"; dispatch(false);
  expect(document.cookie).not.toContain("_ga=");
  expect((window as unknown as Record<string, unknown>)["ga-disable-G-VC4BJBEFTV"]).toBe(true);
  dispatch(true);
  expect(gtag.mock.calls.filter(call => call[2]?.analytics_storage === "granted")).toHaveLength(2);
  expect(gtag.mock.calls.filter(call => call[0] === "config")).toHaveLength(1);
  expect(document.querySelectorAll("[data-hsb-ga4]")).toHaveLength(1);
});
it("cleans analytics cookies when consent is withdrawn on an excluded production page", () => {
  window.history.replaceState({}, "", "/abmelden/");
  localStorage.setItem("hsb-consent-v1", JSON.stringify({ analytics: true }));
  document.cookie = "_ga=existing; Path=/";

  item = createAnalyticsLoader(window, document);
  item.initialize();

  expect(document.querySelectorAll("[data-hsb-ga4]")).toHaveLength(0);
  dispatch(false);

  expect(document.cookie).not.toContain("_ga=");
  expect((window as unknown as Record<string, unknown>)["ga-disable-G-VC4BJBEFTV"]).toBe(true);
});

it("removes all query/hash data and external referrer paths", () => {
  expect(analyticsPageLocation(new URL("https://www.hsb-boden.de/kontakt/?email=private@example.com#private"))).toBe("https://www.hsb-boden.de/kontakt/");
  expect(analyticsReferrer("https://example.com/private?email=private@example.com")).toBe("https://example.com");
  expect(analyticsReferrer("mailto:private@example.com")).toBe("");
});
