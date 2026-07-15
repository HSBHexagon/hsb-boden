export enum TrackingEvent {
  LeadFormStart = "lead_form_start",
  LeadFormSubmit = "lead_form_submit",
  PhoneClick = "phone_click",
  EmailClick = "email_click",
  CtaClick = "cta_click",
  ReferenceFilterUse = "reference_filter_use",
  ReferenceMapOpen = "reference_map_open",
  FileUploadAdd = "file_upload_add",
  FlyerQrVisit = "flyer_qr_visit"
}

type AnalyticsValue = string | number | boolean;
type GtagEventParameters = Record<string, AnalyticsValue | (() => void)>;

const EVENT_CALLBACK_TIMEOUT_MS = 1000;
const GA4_DESTINATION = "G-VC4BJBEFTV";

const SAFE_TOKEN_PATTERN = /^[a-z0-9_-]{1,64}$/i;
const LOCAL_PATH_PATTERN = /^\/[a-z0-9/_-]{0,120}$/i;

let currentPageAnalyticsConsent: boolean | undefined;

if (typeof window !== "undefined") {
  window.addEventListener("hsb:consent", (event) => {
    const detail = (event as CustomEvent<{ analytics?: unknown }>).detail;
    currentPageAnalyticsConsent = detail?.analytics === true;
  });
}

// Expanding this map requires a privacy review; raw lead and URL data stay out.
const ANALYTICS_PARAMETER_VALIDATORS: Record<
  string,
  (value: AnalyticsValue) => boolean
> = {
  form_id: (value) => typeof value === "string" && SAFE_TOKEN_PATTERN.test(value),
  form_path: (value) => typeof value === "string" && LOCAL_PATH_PATTERN.test(value),
  placement: (value) => typeof value === "string" && SAFE_TOKEN_PATTERN.test(value),
  qualified: (value) => typeof value === "boolean",
};

function sanitizeAnalyticsPayload(payload: Record<string, AnalyticsValue>): Record<string, AnalyticsValue> {
  return Object.fromEntries(
    Object.entries(payload).filter(([key, value]) => {
      const validate = ANALYTICS_PARAMETER_VALIDATORS[key];
      return validate?.(value) === true;
    }),
  );
}

function hasAnalyticsConsent(): boolean {
  if (currentPageAnalyticsConsent !== undefined) return currentPageAnalyticsConsent;
  try {
    const raw = window.localStorage.getItem("hsb-consent-v1");
    if (!raw) return false;
    return (JSON.parse(raw) as { analytics?: unknown }).analytics === true;
  } catch {
    return false;
  }
}

function dispatchTrackingEvent(
  event: TrackingEvent,
  payload: Record<string, AnalyticsValue>,
  completion?: { callback: () => void; timeoutMs: number },
): boolean {
  if (typeof window === "undefined") {
    completion?.callback();
    return false;
  }

  if (!hasAnalyticsConsent()) {
    completion?.callback();
    return false;
  }

  const analyticsPayload = sanitizeAnalyticsPayload(payload);
  const externalPayload: Record<string, AnalyticsValue> = event === TrackingEvent.LeadFormSubmit
    ? { ...analyticsPayload, method: "contact_form" }
    : analyticsPayload;
  window.dispatchEvent(new CustomEvent("hsb:tracking", {
    detail: { event, payload: { ...externalPayload } },
  }));

  const trackingWindow = window as Window & {
    dataLayer?: unknown[];
    gtag?: (command: "event", eventName: string, params: GtagEventParameters) => void;
  };
  const dataLayer = trackingWindow.dataLayer;
  if (Array.isArray(dataLayer)) {
    try {
      dataLayer.push({ event, ...externalPayload });
    } catch {
      // A third-party dataLayer wrapper must not interrupt the user flow.
    }
  }
  if (typeof trackingWindow.gtag !== "function") {
    completion?.callback();
    return false;
  }

  const eventName = event === TrackingEvent.LeadFormSubmit ? "generate_lead" : event;
  const eventPayload: GtagEventParameters = {
    ...externalPayload,
    send_to: GA4_DESTINATION,
  };
  if (completion) {
    eventPayload.event_callback = completion.callback;
    eventPayload.event_timeout = completion.timeoutMs;
  }

  try {
    trackingWindow.gtag("event", eventName, eventPayload);
    return true;
  } catch {
    completion?.callback();
    return false;
  }
}

/**
 * Emits non-PII analytics metadata through the Consent Mode v2 tag configured
 * in BaseLayout. Only allowlisted parameters can leave the page; contact and
 * message fields are discarded even if a caller passes them accidentally.
 */
export function trackEvent(event: TrackingEvent, payload: Record<string, AnalyticsValue> = {}) {
  dispatchTrackingEvent(event, payload);
}

/** Waits briefly for the Google event callback without blocking indefinitely. */
export function trackEventAndWait(
  event: TrackingEvent,
  payload: Record<string, AnalyticsValue> = {},
): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();

  return new Promise((resolve) => {
    let settled = false;
    let fallbackTimer: number | undefined;
    const finish = () => {
      if (settled) return;
      settled = true;
      if (fallbackTimer !== undefined) window.clearTimeout(fallbackTimer);
      resolve();
    };

    fallbackTimer = window.setTimeout(finish, EVENT_CALLBACK_TIMEOUT_MS + 100);
    const emitted = dispatchTrackingEvent(event, payload, {
      callback: finish,
      timeoutMs: EVENT_CALLBACK_TIMEOUT_MS,
    });
    if (!emitted) finish();
  });
}
