// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  b2bDataLayer,
  trackB2BConversion,
  trackNormInteraction,
  trackReferenceInteraction,
  trackStressCheck,
} from "../src/lib/analytics";

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

describe("B2B DataLayer-Interface", () => {
  it("exponiert die vier typisierten Methoden", () => {
    expect(typeof b2bDataLayer.trackStressCheck).toBe("function");
    expect(typeof b2bDataLayer.trackReferenceInteraction).toBe("function");
    expect(typeof b2bDataLayer.trackNormInteraction).toBe("function");
    expect(typeof b2bDataLayer.trackB2BConversion).toBe("function");
  });

  it("trackStressCheck liefert Schritt und Parameter vollständig an gtag", () => {
    const gtag = vi.fn();
    win.gtag = gtag;
    trackStressCheck(2, { medium: "milchsaeure-molke", tempRange: "thermoschock-85" });
    expect(gtag).toHaveBeenCalledWith("event", "stress_check_step", {
      step: 2,
      medium: "milchsaeure-molke",
      temp_range: "thermoschock-85",
      send_to: "G-VC4BJBEFTV",
    });
  });

  it("trackStressCheck verwirft ungültige Schritte und Nicht-Slugs", () => {
    const gtag = vi.fn();
    win.gtag = gtag;
    trackStressCheck(0, { medium: "<script>" });
    expect(gtag).toHaveBeenCalledWith("event", "stress_check_step", { send_to: "G-VC4BJBEFTV" });
  });

  it("trackReferenceInteraction überträgt Kundennamen mit Umlauten und Sonderzeichen", () => {
    const gtag = vi.fn();
    win.gtag = gtag;
    trackReferenceInteraction("Molkerei Gropper GmbH & Co. KG", "molkerei", "click");
    expect(gtag).toHaveBeenCalledWith("event", "reference_interaction", {
      client_name: "Molkerei Gropper GmbH & Co. KG",
      industry: "molkerei",
      action: "click",
      send_to: "G-VC4BJBEFTV",
    });
  });

  it("trackNormInteraction akzeptiert nur die drei bekannten Normen", () => {
    const gtag = vi.fn();
    win.gtag = gtag;
    trackNormInteraction("WHG § 62", "expand");
    expect(gtag).toHaveBeenCalledWith("event", "norm_interaction", {
      norm: "WHG § 62",
      action: "expand",
      send_to: "G-VC4BJBEFTV",
    });
  });

  it("trackB2BConversion lässt keine personenbezogenen Daten nach GA4 durch", () => {
    const gtag = vi.fn();
    win.gtag = gtag;
    trackB2BConversion("audit_request", {
      recommended_system: "agi-s40-ruettelkeramik",
      industry: "molkerei",
      email: "test@example.com",
      phone: "+491234",
      name: "Test Person",
      message: "vertraulich",
    });
    expect(gtag).toHaveBeenCalledWith("event", "b2b_conversion", {
      conversion_type: "audit_request",
      recommended_system: "agi-s40-ruettelkeramik",
      industry: "molkerei",
      send_to: "G-VC4BJBEFTV",
    });
  });

  it("legt dataLayer an, wenn gtag fehlt und dataLayer noch undefiniert ist", () => {
    trackB2BConversion("technical_inquiry", { industry: "chemieindustrie" });
    expect(Array.isArray(win.dataLayer)).toBe(true);
    expect(win.dataLayer).toContainEqual({
      event: "b2b_conversion",
      conversion_type: "technical_inquiry",
      industry: "chemieindustrie",
      send_to: "G-VC4BJBEFTV",
    });
  });

  it("sendet ohne Analytics-Einwilligung nichts", () => {
    localStorage.clear();
    window.dispatchEvent(new CustomEvent("hsb:consent", { detail: { analytics: false } }));
    trackStressCheck(1, { medium: "fette-oele" });
    expect(win.dataLayer).toBeUndefined();
  });
});
