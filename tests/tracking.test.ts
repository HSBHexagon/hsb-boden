// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from "vitest";
import { trackEvent, trackEventAndWait, TrackingEvent } from "../src/lib/tracking";

type TrackingWindow = Window & {
  dataLayer?: unknown[];
  gtag?: (...args: unknown[]) => void;
};

const win = window as TrackingWindow;

beforeEach(() => {
  delete win.dataLayer;
  delete win.gtag;
  localStorage.setItem("hsb-consent-v1", JSON.stringify({ necessary: true, analytics: true }));
  window.dispatchEvent(new CustomEvent("hsb:consent", { detail: { analytics: true } }));
});

describe("trackEvent", () => {
  it("ordnet erfolgreiche Leads dem empfohlenen GA4-Event zu", () => {
    const gtag = vi.fn();
    win.gtag = gtag;
    trackEvent(TrackingEvent.LeadFormSubmit, { form_path: "/kontakt/" });
    expect(gtag).toHaveBeenCalledWith(
      "event",
      "generate_lead",
      { form_path: "/kontakt/", method: "contact_form", send_to: "G-VC4BJBEFTV" },
    );
  });

  it("beschränkt reguläre Events auf die GA4-Destination", () => {
    const gtag = vi.fn();
    win.gtag = gtag;
    trackEvent(TrackingEvent.PhoneClick);
    expect(gtag).toHaveBeenCalledWith("event", "phone_click", { send_to: "G-VC4BJBEFTV" });
  });

  it("pusht weiterhin ins dataLayer, wenn vorhanden (GTM-Kompatibilität)", () => {
    win.dataLayer = [];
    trackEvent(TrackingEvent.CtaClick, { cta: "hero" });
    expect(win.dataLayer).toContainEqual({ event: "cta_click", cta: "hero", send_to: "G-VC4BJBEFTV" });
  });

  it("lässt den echten Eventnamen nicht durch ein payload.event-Feld überschreiben (dataLayer-Fallback)", () => {
    win.dataLayer = [];
    trackEvent(TrackingEvent.CtaClick, { event: "fake_event", cta: "hero" });
    expect(win.dataLayer).toContainEqual({ event: "cta_click", cta: "hero", send_to: "G-VC4BJBEFTV" });
  });

  it("nutzt dataLayer nur als Fallback, wenn gtag fehlt — kein Doppel-Event bei gtag", () => {
    const gtag = vi.fn();
    win.gtag = gtag;
    win.dataLayer = [];
    trackEvent(TrackingEvent.EmailClick);
    expect(gtag).toHaveBeenCalledTimes(1);
    expect(win.dataLayer).toHaveLength(0);
  });

  it("wirft nicht, wenn weder gtag noch dataLayer existieren", () => {
    expect(() => trackEvent(TrackingEvent.LeadFormStart)).not.toThrow();
  });

  it("feuert das hsb:tracking CustomEvent unabhängig vom Transport", () => {
    const listener = vi.fn();
    window.addEventListener("hsb:tracking", listener, { once: true });
    trackEvent(TrackingEvent.FlyerQrVisit, { source: "qr" });
    expect(listener).toHaveBeenCalledTimes(1);
  });

  it("wirft nicht, wenn gtag intern eine Exception auslöst", () => {
    win.gtag = () => {
      throw new Error("boom");
    };
    expect(() => trackEvent(TrackingEvent.LeadFormSubmit)).not.toThrow();
  });

  it("sendet ohne Analytics-Einwilligung kein Event an gtag oder dataLayer", () => {
    localStorage.clear();
    window.dispatchEvent(new CustomEvent("hsb:consent", { detail: { analytics: false } }));
    const gtag = vi.fn();
    win.gtag = gtag;
    win.dataLayer = [];

    trackEvent(TrackingEvent.LeadFormSubmit);

    expect(gtag).not.toHaveBeenCalled();
    expect(win.dataLayer).toHaveLength(0);
  });

  it("verwendet eine gerade erteilte Einwilligung auch bei blockiertem Storage", () => {
    localStorage.clear();
    window.dispatchEvent(new CustomEvent("hsb:consent", { detail: { analytics: true } }));
    const gtag = vi.fn();
    win.gtag = gtag;

    trackEvent(TrackingEvent.PhoneClick);

    expect(gtag).toHaveBeenCalledWith("event", "phone_click", { send_to: "G-VC4BJBEFTV" });
  });

  it("ordnet einen erfolgreichen Lead der empfohlenen GA4-Conversion zu und wartet auf den Callback", async () => {
    const gtag = vi.fn((command, event, payload) => {
      if (command === "event" && event === "generate_lead") {
        (payload as { event_callback: () => void }).event_callback();
      }
    });
    win.gtag = gtag;

    await trackEventAndWait(TrackingEvent.LeadFormSubmit);

    expect(gtag).toHaveBeenCalledWith(
      "event",
      "generate_lead",
      expect.objectContaining({ method: "contact_form", send_to: "G-VC4BJBEFTV", event_timeout: 1000 }),
    );
  });

  it("legt im dataLayer-Fallback keinen JavaScript-Callback ab", async () => {
    win.dataLayer = [];

    await trackEventAndWait(TrackingEvent.LeadFormSubmit);

    expect(win.dataLayer).toContainEqual({
      event: "generate_lead",
      method: "contact_form",
      send_to: "G-VC4BJBEFTV",
    });
  });
});
