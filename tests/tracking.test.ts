// @vitest-environment jsdom

import { beforeEach, describe, expect, it, vi } from "vitest";
import { trackEvent, trackEventAndWait, TrackingEvent } from "../src/lib/tracking";

type TrackingWindow = Window &
  typeof globalThis & {
    dataLayer?: unknown[];
    gtag?: (...args: unknown[]) => void;
  };

const trackingWindow = window as TrackingWindow;

describe("trackEvent", () => {
  beforeEach(() => {
    trackingWindow.dataLayer = [];
    delete trackingWindow.gtag;
    localStorage.setItem(
      "hsb-consent-v1",
      JSON.stringify({ necessary: true, analytics: true, ts: "2026-07-15T00:00:00.000Z" }),
    );
    window.dispatchEvent(new CustomEvent("hsb:consent", { detail: { analytics: true } }));
  });

  it("sends a lead form submission as the recommended GA4 generate_lead event", () => {
    const gtag = vi.fn();
    trackingWindow.gtag = gtag;
    const payload = { form_path: "/kontakt/", qualified: true, method: "caller_override" };

    trackEvent(TrackingEvent.LeadFormSubmit, payload);

    expect(gtag).toHaveBeenCalledWith("event", "generate_lead", {
      ...payload,
      method: "contact_form",
      send_to: "G-VC4BJBEFTV",
    });
    expect(trackingWindow.dataLayer).toContainEqual({
      event: TrackingEvent.LeadFormSubmit,
      form_path: "/kontakt/",
      qualified: true,
      method: "contact_form",
    });
  });

  it("keeps a non-submit event name and payload in the direct GA4 call", () => {
    const gtag = vi.fn();
    trackingWindow.gtag = gtag;
    const payload = { placement: "hero" };

    trackEvent(TrackingEvent.CtaClick, payload);

    expect(gtag).toHaveBeenCalledWith("event", TrackingEvent.CtaClick, {
      ...payload,
      send_to: "G-VC4BJBEFTV",
    });
  });

  it("does not emit tracking signals before analytics consent", () => {
    const gtag = vi.fn();
    trackingWindow.gtag = gtag;
    const listener = vi.fn();
    window.addEventListener("hsb:tracking", listener, { once: true });
    localStorage.removeItem("hsb-consent-v1");
    window.dispatchEvent(new CustomEvent("hsb:consent", { detail: { analytics: false } }));

    trackEvent(TrackingEvent.LeadFormStart, { form_id: "lead_form" });

    expect(gtag).not.toHaveBeenCalled();
    expect(trackingWindow.dataLayer).toEqual([]);
    expect(listener).not.toHaveBeenCalled();
  });

  it("honors current-page consent when it could not be persisted", () => {
    const gtag = vi.fn();
    trackingWindow.gtag = gtag;
    localStorage.removeItem("hsb-consent-v1");
    window.dispatchEvent(new CustomEvent("hsb:consent", { detail: { analytics: true } }));

    trackEvent(TrackingEvent.LeadFormStart, { form_id: "lead_form" });

    expect(gtag).toHaveBeenCalledWith("event", TrackingEvent.LeadFormStart, {
      form_id: "lead_form",
      send_to: "G-VC4BJBEFTV",
    });
  });

  it("removes contact and message fields before external analytics dispatch", () => {
    const gtag = vi.fn();
    trackingWindow.gtag = gtag;
    const listener = vi.fn();
    window.addEventListener("hsb:tracking", listener, { once: true });
    const unsafePayload = {
      form_path: "/kontakt/",
      email: "probe@example.invalid",
      firstName: "Test",
      phone: "+49000000000",
      message: "Synthetic test message",
    };

    trackEvent(TrackingEvent.LeadFormSubmit, unsafePayload);

    expect(gtag).toHaveBeenCalledWith("event", "generate_lead", {
      form_path: "/kontakt/",
      method: "contact_form",
      send_to: "G-VC4BJBEFTV",
    });
    expect(trackingWindow.dataLayer).toContainEqual({
      event: TrackingEvent.LeadFormSubmit,
      form_path: "/kontakt/",
      method: "contact_form",
    });
    expect((listener.mock.calls[0][0] as CustomEvent).detail.payload).toEqual({
      form_path: "/kontakt/",
      method: "contact_form",
    });
  });

  it("rejects user-controlled campaign values even when syntactically safe", () => {
    const gtag = vi.fn();
    trackingWindow.gtag = gtag;

    trackEvent(TrackingEvent.LeadFormSubmit, { campaign: "customer123" });

    expect(gtag).toHaveBeenCalledWith("event", "generate_lead", {
      method: "contact_form",
      send_to: "G-VC4BJBEFTV",
    });
  });

  it("isolates external dispatch from CustomEvent listener mutations", () => {
    const gtag = vi.fn();
    trackingWindow.gtag = gtag;
    window.addEventListener(
      "hsb:tracking",
      (event) => {
        const payload = (event as CustomEvent).detail.payload as Record<string, unknown>;
        payload.email = "injected@example.invalid";
        payload.method = "listener_override";
      },
      { once: true },
    );

    trackEvent(TrackingEvent.LeadFormSubmit);

    expect(trackingWindow.dataLayer).toContainEqual({
      event: TrackingEvent.LeadFormSubmit,
      method: "contact_form",
    });
    expect(gtag).toHaveBeenCalledWith("event", "generate_lead", {
      method: "contact_form",
      send_to: "G-VC4BJBEFTV",
    });
  });

  it("rejects unsafe values even when their parameter names are allowlisted", () => {
    const gtag = vi.fn();
    trackingWindow.gtag = gtag;

    trackEvent(TrackingEvent.CtaClick, {
      form_path: "/kontakt/?email=probe@example.invalid",
      campaign: "probe@example.invalid",
      placement: "hero",
      qualified: "true",
    });

    expect(gtag).toHaveBeenCalledWith("event", TrackingEvent.CtaClick, {
      placement: "hero",
      send_to: "G-VC4BJBEFTV",
    });
  });

  it("isolates failures in an optional gtag wrapper", () => {
    trackingWindow.gtag = vi.fn(() => {
      throw new Error("synthetic gtag failure");
    });

    expect(() => trackEvent(TrackingEvent.CtaClick, { placement: "hero" })).not.toThrow();
    expect(trackingWindow.dataLayer).toContainEqual({
      event: TrackingEvent.CtaClick,
      placement: "hero",
    });
  });

  it("waits for the gtag event callback before a submit flow continues", async () => {
    const gtag = vi.fn((...args: unknown[]) => {
      const params = args[2] as { event_callback?: () => void; event_timeout?: number };
      expect(params.event_timeout).toBe(1000);
      params.event_callback?.();
    });
    trackingWindow.gtag = gtag;

    await trackEventAndWait(TrackingEvent.LeadFormSubmit);

    expect(gtag).toHaveBeenCalledOnce();
  });

  it("resolves immediately without dispatch when analytics consent is declined", async () => {
    const gtag = vi.fn();
    trackingWindow.gtag = gtag;
    localStorage.removeItem("hsb-consent-v1");
    window.dispatchEvent(new CustomEvent("hsb:consent", { detail: { analytics: false } }));

    await trackEventAndWait(TrackingEvent.LeadFormSubmit);

    expect(gtag).not.toHaveBeenCalled();
    expect(trackingWindow.dataLayer).toEqual([]);
  });

  it("stops waiting when a gtag wrapper never invokes its callback", async () => {
    vi.useFakeTimers();
    try {
      trackingWindow.gtag = vi.fn();
      let resolved = false;
      const pending = trackEventAndWait(TrackingEvent.LeadFormSubmit).then(() => {
        resolved = true;
      });

      await Promise.resolve();
      expect(resolved).toBe(false);
      await vi.advanceTimersByTimeAsync(1100);
      await pending;

      expect(resolved).toBe(true);
    } finally {
      vi.useRealTimers();
    }
  });

  it("preserves the tracking CustomEvent and GTM-style dataLayer object", () => {
    const listener = vi.fn();
    window.addEventListener("hsb:tracking", listener, { once: true });
    const payload = { placement: "header" };

    trackEvent(TrackingEvent.PhoneClick, payload);

    expect(listener).toHaveBeenCalledOnce();
    expect((listener.mock.calls[0][0] as CustomEvent).detail).toEqual({
      event: TrackingEvent.PhoneClick,
      payload,
    });
    expect(trackingWindow.dataLayer).toContainEqual({
      event: TrackingEvent.PhoneClick,
      ...payload,
    });
  });

  it("keeps existing behavior and does not throw when gtag is absent", () => {
    expect(() => trackEvent(TrackingEvent.EmailClick)).not.toThrow();
    expect(trackingWindow.dataLayer).toContainEqual({ event: TrackingEvent.EmailClick });
  });
});
