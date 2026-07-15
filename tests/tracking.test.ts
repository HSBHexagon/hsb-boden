// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from "vitest";
import { trackEvent, TrackingEvent } from "../src/lib/tracking";

type TrackingWindow = Window & {
  dataLayer?: unknown[];
  gtag?: (...args: unknown[]) => void;
};

const win = window as TrackingWindow;

beforeEach(() => {
  delete win.dataLayer;
  delete win.gtag;
});

describe("trackEvent", () => {
  it("ruft gtag('event', name, payload) auf, wenn gtag vorhanden ist", () => {
    const gtag = vi.fn();
    win.gtag = gtag;
    trackEvent(TrackingEvent.LeadFormSubmit, { form_path: "/kontakt/" });
    expect(gtag).toHaveBeenCalledWith("event", "lead_form_submit", { form_path: "/kontakt/" });
  });

  it("ruft gtag auch ohne Payload mit leerem Objekt auf", () => {
    const gtag = vi.fn();
    win.gtag = gtag;
    trackEvent(TrackingEvent.PhoneClick);
    expect(gtag).toHaveBeenCalledWith("event", "phone_click", {});
  });

  it("pusht weiterhin ins dataLayer, wenn vorhanden (GTM-Kompatibilität)", () => {
    win.dataLayer = [];
    trackEvent(TrackingEvent.CtaClick, { cta: "hero" });
    expect(win.dataLayer).toContainEqual({ event: "cta_click", cta: "hero" });
  });

  it("lässt den echten Eventnamen nicht durch ein payload.event-Feld überschreiben (dataLayer-Fallback)", () => {
    win.dataLayer = [];
    trackEvent(TrackingEvent.CtaClick, { event: "fake_event", cta: "hero" });
    expect(win.dataLayer).toContainEqual({ event: "cta_click", cta: "hero" });
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
});
