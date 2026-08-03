const CONSENT_STORAGE_KEY = "hsb-consent-v1";

export const GA4_MEASUREMENT_ID = "G-VC4BJBEFTV";

type Gtag = (...args: unknown[]) => void;

type AnalyticsWindow = Window & {
  dataLayer?: unknown[];
  gtag?: Gtag;
};

function hasStoredAnalyticsConsent(storage: Storage): boolean {
  try {
    const raw = storage.getItem(CONSENT_STORAGE_KEY);
    return raw !== null && (JSON.parse(raw) as { analytics?: unknown }).analytics === true;
  } catch {
    return false;
  }
}

export function createAnalyticsLoader(
  browserWindow: Window,
  browserDocument: Document,
  measurementId = GA4_MEASUREMENT_ID,
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
    if (loaded) return;
    loaded = true;

    const gtag = getGtag();
    gtag("consent", "update", { analytics_storage: "granted" });
    gtag("js", new Date());
    gtag("config", measurementId, { send_page_view: true });

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

    if (loaded) getGtag()("consent", "update", { analytics_storage: "denied" });
  }

  return {
    initialize() {
      if (initialized) return;
      initialized = true;
      browserWindow.addEventListener("hsb:consent", updateConsent);
      if (hasStoredAnalyticsConsent(browserWindow.localStorage)) loadAfterConsent();
    },
  };
}

export function initializeAnalytics() {
  if (typeof window === "undefined" || typeof document === "undefined") return;
  createAnalyticsLoader(window, document).initialize();
}
