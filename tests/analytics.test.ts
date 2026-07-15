// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createAnalyticsLoader } from "../src/lib/analytics";

const MEASUREMENT_ID = "G-TEST123";

beforeEach(() => {
  document.head.innerHTML = "";
  localStorage.clear();
  delete (window as Window & { dataLayer?: unknown[]; gtag?: unknown }).dataLayer;
  delete (window as Window & { dataLayer?: unknown[]; gtag?: unknown }).gtag;
});

describe("GA4 Basic Consent loader", () => {
  it("lädt vor einer aktiven Analytics-Einwilligung kein Google-Skript", () => {
    const loader = createAnalyticsLoader(window, document, MEASUREMENT_ID);

    loader.initialize();

    expect(document.querySelector('script[data-hsb-ga4="true"]')).toBeNull();
    expect((window as Window & { gtag?: unknown }).gtag).toBeUndefined();
  });

  it("lädt bei gespeicherter Analytics-Einwilligung genau einmal und konfiguriert genau einen Pageview", () => {
    localStorage.setItem("hsb-consent-v1", JSON.stringify({ necessary: true, analytics: true }));
    const gtag = vi.fn();
    (window as Window & { gtag?: typeof gtag }).gtag = gtag;
    const loader = createAnalyticsLoader(window, document, MEASUREMENT_ID);

    loader.initialize();
    loader.initialize();

    const script = document.querySelector<HTMLScriptElement>('script[data-hsb-ga4="true"]');
    expect(script?.src).toContain(`https://www.googletagmanager.com/gtag/js?id=${MEASUREMENT_ID}`);
    expect(gtag).toHaveBeenCalledWith("config", MEASUREMENT_ID, { send_page_view: true });
    expect(gtag).toHaveBeenCalledTimes(3);
  });

  it("lädt erst nach einem positiven Consent-Ereignis und ignoriert ein negatives", () => {
    const loader = createAnalyticsLoader(window, document, MEASUREMENT_ID);
    loader.initialize();

    window.dispatchEvent(new CustomEvent("hsb:consent", { detail: { analytics: false } }));
    expect(document.querySelector('script[data-hsb-ga4="true"]')).toBeNull();

    window.dispatchEvent(new CustomEvent("hsb:consent", { detail: { analytics: true } }));
    expect(document.querySelector('script[data-hsb-ga4="true"]')).not.toBeNull();
  });
});
