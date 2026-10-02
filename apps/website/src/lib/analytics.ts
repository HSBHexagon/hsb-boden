import { analyticsPageLocation, analyticsReferrer } from "./analyticsLocation";
import { GA4_MEASUREMENT_ID, PRODUCTION_ANALYTICS_HOST, canTrackAnalyticsLocation } from "./analyticsConfig";
import { TrackingEvent, trackEvent, type AnalyticsPayload, type AnalyticsValue } from "./tracking";
import type { NormId } from "../data/standards";

export { GA4_MEASUREMENT_ID, PRODUCTION_ANALYTICS_HOST };

const CONSENT_STORAGE_KEY = "hsb-consent-v1";

type Gtag = (...args: unknown[]) => void;

type AnalyticsWindow = Window & {
  dataLayer?: unknown[];
  gtag?: Gtag;
  [key: string]: unknown;
};

export function isProductionAnalyticsHost(hostname: string): boolean {
  return hostname.toLowerCase() === PRODUCTION_ANALYTICS_HOST;
}

export function hasStoredAnalyticsConsent(browserWindow: Window): boolean {
  try {
    const raw = browserWindow.localStorage.getItem(CONSENT_STORAGE_KEY);
    return raw !== null && (JSON.parse(raw) as { analytics?: unknown })?.analytics === true;
  } catch {
    return false;
  }
}

function clearAnalyticsCookies(browserWindow: Window, browserDocument: Document) {
  try {
    for (const cookie of browserDocument.cookie.split(";")) {
      const name = cookie.trim().split("=", 1)[0];
      if (!/^_ga(?:_|$)/.test(name)) continue;
      for (const domain of ["", browserWindow.location.hostname, ".hsb-boden.de", "hsb-boden.de"]) {
        browserDocument.cookie = `${name}=; Max-Age=0; Path=/; SameSite=Lax${domain ? `; Domain=${domain}` : ""}`;
      }
    }
  } catch { /* Browser-Storage kann gesperrt sein. */ }
}

export function createAnalyticsLoader(
  browserWindow: Window,
  browserDocument: Document,
  measurementId = GA4_MEASUREMENT_ID,
  hostname = browserWindow.location.hostname,
) {
  const analyticsWindow = browserWindow as AnalyticsWindow;
  let initialized = false;
  let loaded = false;

  function getGtag(): Gtag {
    if (typeof analyticsWindow.gtag === "function") return analyticsWindow.gtag;

    analyticsWindow.dataLayer = analyticsWindow.dataLayer ?? [];
    analyticsWindow.gtag = (...args: unknown[]) => {
      analyticsWindow.dataLayer?.push(args);
    };
    return analyticsWindow.gtag;
  }

  function loadAfterConsent() {
    if (!canTrackAnalyticsLocation(hostname, browserWindow.location.pathname)) return;
    analyticsWindow[`ga-disable-${measurementId}`] = false;

    const gtag = getGtag();
    gtag("consent", "update", {
      analytics_storage: "granted",
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied",
    });
    if (loaded) return;
    loaded = true;
    gtag("js", new Date());
    gtag("config", measurementId, {
      send_page_view: true, page_location: analyticsPageLocation(browserWindow.location),
      page_referrer: analyticsReferrer(browserDocument.referrer),
      allow_google_signals: false, allow_ad_personalization_signals: false,
    });

    if (!browserDocument.querySelector('script[data-hsb-ga4="true"]')) {
      const script = browserDocument.createElement("script");
      script.async = true;
      script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(measurementId)}`;
      script.dataset.hsbGa4 = "true";
      browserDocument.head.appendChild(script);
    }
  }

  function updateConsent(event: Event) {
    const detail = (event as CustomEvent<{ analytics?: unknown }>).detail;
    if (detail?.analytics === true) {
      loadAfterConsent();
      return;
    }

    analyticsWindow[`ga-disable-${measurementId}`] = true;
    clearAnalyticsCookies(browserWindow, browserDocument);
    if (loaded) {
      getGtag()("consent", "update", {
        analytics_storage: "denied",
        ad_storage: "denied",
        ad_user_data: "denied",
        ad_personalization: "denied",
      });
    }
  }

  return {
    initialize() {
      // Auf jeder Produktionsseite auf Consent-Änderungen hören, damit ein
      // Widerruf auch auf bewusst von Analytics ausgeschlossenen Seiten
      // (z. B. /abmelden/) vorhandene GA-Cookies sofort entfernt. Das
      // eigentliche Laden/Config von GA4 bleibt weiterhin in
      // loadAfterConsent() an die zulässige Location gebunden.
      if (initialized || !isProductionAnalyticsHost(hostname)) return;
      initialized = true;
      browserWindow.addEventListener("hsb:consent", updateConsent);
      analyticsWindow[`ga-disable-${measurementId}`] = true;
      if (hasStoredAnalyticsConsent(browserWindow)) loadAfterConsent();
      else clearAnalyticsCookies(browserWindow, browserDocument);
    },
    destroy() { browserWindow.removeEventListener("hsb:consent", updateConsent); },
  };
}

export function initializeAnalytics() {
  if (typeof window === "undefined" || typeof document === "undefined") return;
  createAnalyticsLoader(window, document).initialize();
}

// ---------------------------------------------------------------------------
// Typensicheres B2B-DataLayer für GA4. Alle Methoden laufen über die
// consent-gated Schicht in tracking.ts; nicht allowlistete Parameter werden
// dort verworfen, nicht vorgesehene Kontaktfelder werden verworfen.
// ---------------------------------------------------------------------------

export interface StressCheckStepData {
  medium?: string;
  tempRange?: string;
  mechanicalLoad?: string;
  timeWindow?: string;
  recommendedSystem?: string;
}

export type ReferenceAction = "click" | "view";
export type NormAction = "expand" | "download";
export type B2BConversionType = "audit_request" | "technical_inquiry";

export interface B2BDataLayer {
  trackStressCheck(step: number, data: StressCheckStepData): void;
  trackReferenceInteraction(clientName: string, industry: string, action: ReferenceAction): void;
  trackNormInteraction(norm: NormId, action: NormAction): void;
  trackB2BConversion(type: B2BConversionType, payload: Record<string, unknown>): void;
}

const B2B_CONVERSION_KEYS = [
  "form_path",
  "placement",
  "industry",
  "project_type",
  "medium",
  "temp_range",
  "mechanical_load",
  "time_window",
  "recommended_system",
] as const;

function definedEntries(payload: Record<string, AnalyticsValue | undefined>): AnalyticsPayload {
  return Object.fromEntries(
    Object.entries(payload).filter((entry): entry is [string, AnalyticsValue] => entry[1] !== undefined),
  );
}

export function trackStressCheck(step: number, data: StressCheckStepData): void {
  trackEvent(
    TrackingEvent.StressCheckStep,
    definedEntries({
      step,
      medium: data.medium,
      temp_range: data.tempRange,
      mechanical_load: data.mechanicalLoad,
      time_window: data.timeWindow,
      recommended_system: data.recommendedSystem,
    }),
  );
}

export function trackReferenceInteraction(
  clientName: string,
  industry: string,
  action: ReferenceAction,
): void {
  trackEvent(TrackingEvent.ReferenceInteraction, { client_name: clientName, industry, action });
}

export function trackNormInteraction(norm: NormId, action: NormAction): void {
  trackEvent(TrackingEvent.NormInteraction, { norm, action });
}

export function trackB2BConversion(type: B2BConversionType, payload: Record<string, unknown>): void {
  const narrowed: Record<string, AnalyticsValue | undefined> = { conversion_type: type };
  for (const key of B2B_CONVERSION_KEYS) {
    const value = payload[key];
    if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
      narrowed[key] = value;
    }
  }
  trackEvent(TrackingEvent.B2BConversion, definedEntries(narrowed));
}

export const b2bDataLayer: B2BDataLayer = {
  trackStressCheck,
  trackReferenceInteraction,
  trackNormInteraction,
  trackB2BConversion,
};
