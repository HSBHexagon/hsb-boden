// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
import { trackEvent, TrackingEvent } from "../src/lib/tracking";

describe("Client Edge Telemetry Dispatch", () => {
  beforeEach(() => {
    localStorage.setItem("hsb-consent-v1", JSON.stringify({ necessary: true, analytics: true }));
    window.dispatchEvent(new CustomEvent("hsb:consent", { detail: { analytics: true } }));
  });

  it("dispatches telemetry to /api/collect via sendBeacon or fetch", () => {
    const sendBeaconSpy = vi.fn().mockReturnValue(true);
    Object.defineProperty(navigator, "sendBeacon", {
      value: sendBeaconSpy,
      writable: true,
      configurable: true,
    });

    trackEvent(TrackingEvent.LeadFormSubmit, { form_path: "/kontakt/" });

    expect(sendBeaconSpy).toHaveBeenCalled();
    const [url] = sendBeaconSpy.mock.calls[0];
    expect(url).toBe("/api/collect");
  });
});
