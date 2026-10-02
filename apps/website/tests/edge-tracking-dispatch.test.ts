// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { trackEvent, TrackingEvent } from "../src/lib/tracking";
beforeEach(() => window.dispatchEvent(new CustomEvent("hsb:consent", { detail: { analytics: true } })));
afterEach(() => vi.unstubAllGlobals());
it("sends a lead once through gtag without the retired edge proxy", () => {
  const gtag = vi.fn(); const request = vi.fn(); const beacon = vi.fn();
  (window as Window & { gtag?: unknown }).gtag = gtag;
  vi.stubGlobal("fetch", request);
  Object.defineProperty(navigator, "sendBeacon", { value: beacon, configurable: true });
  trackEvent(TrackingEvent.LeadFormSubmit);
  expect(gtag).toHaveBeenCalledTimes(1); expect(request).not.toHaveBeenCalled(); expect(beacon).not.toHaveBeenCalled();
});
it.each([["preview.hsb-boden.pages.dev", "/kontakt/"], ["www.hsb-boden.de", "/abmelden/"]])("isolates %s %s", (hostname, pathname) => {
  const gtag = vi.fn();
  vi.stubGlobal("window", { location: { hostname, pathname }, dispatchEvent: vi.fn(), gtag });
  trackEvent(TrackingEvent.PhoneClick);
  expect(gtag).not.toHaveBeenCalled();
});
