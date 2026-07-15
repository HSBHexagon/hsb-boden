export enum TrackingEvent {
  LeadFormStart = "lead_form_start",
  GenerateLead = "generate_lead",
  /** @deprecated Use GenerateLead. Kept as a source-compatible alias. */
  LeadFormSubmit = "generate_lead",
  PhoneClick = "phone_click",
  EmailClick = "email_click",
  CtaClick = "cta_click",
  ReferenceFilterUse = "reference_filter_use",
  ReferenceMapOpen = "reference_map_open",
  FileUploadAdd = "file_upload_add",
  FlyerQrVisit = "flyer_qr_visit"
}

type TrackingValue = string | number | boolean;
export type TrackingPayload = Record<string, TrackingValue>;

const PII_KEY_PATTERN = /^(?:first_?name|last_?name|full_?name|contact_?name|customer_?name|user_?name|name|email|e_?mail|phone|telephone|mobile|company|message|address|street|postal|zip)$/i;
const EMAIL_VALUE_PATTERN = /\b[^\s@]+@[^\s@]+\.[^\s@]+\b/i;
const PHONE_VALUE_PATTERN = /^\+?[\d\s()./-]{7,}$/;

function looksLikePhone(value: string) {
  return PHONE_VALUE_PATTERN.test(value.trim()) && value.replace(/\D/g, "").length >= 7;
}

export function sanitizeTrackingPayload(payload: TrackingPayload = {}): TrackingPayload {
  return Object.fromEntries(
    Object.entries(payload).filter(([key, value]) => {
      if (PII_KEY_PATTERN.test(key)) return false;
      if (typeof value !== "string") return true;
      return !EMAIL_VALUE_PATTERN.test(value) && !looksLikePhone(value);
    }),
  );
}

function trackingWindow() {
  return window as Window & { dataLayer?: unknown[]; gtag?: (...args: unknown[]) => void };
}

export function trackEvent(event: TrackingEvent, payload: TrackingPayload = {}) {
  if (typeof window === "undefined") return;
  const safePayload = sanitizeTrackingPayload(payload);
  window.dispatchEvent(new CustomEvent("hsb:tracking", { detail: { event, payload: safePayload } }));
  const w = trackingWindow();
  try {
    if (typeof w.gtag === "function") {
      // Direkte gtag.js-Einbindung: nur gtag('event', …) erzeugt einen GA4-Collect.
      // Kein zusätzlicher dataLayer-Push, sonst zählt ein späteres GTM doppelt.
      w.gtag("event", event, safePayload);
    } else if (Array.isArray(w.dataLayer)) {
      w.dataLayer.push({ ...safePayload, event });
    }
  } catch {
    // Tracking darf nie die aufrufende Interaktion brechen.
  }
}

export function trackConversion(
  event: TrackingEvent,
  payload: TrackingPayload = {},
  timeoutMs = 800,
): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();

  const safePayload = sanitizeTrackingPayload(payload);
  window.dispatchEvent(new CustomEvent("hsb:tracking", { detail: { event, payload: safePayload } }));
  const w = trackingWindow();

  return new Promise((resolve) => {
    let settled = false;
    let fallbackTimer: number | undefined;
    const finish = () => {
      if (settled) return;
      settled = true;
      if (fallbackTimer !== undefined) window.clearTimeout(fallbackTimer);
      resolve();
    };
    fallbackTimer = window.setTimeout(finish, timeoutMs + 100);

    try {
      if (typeof w.gtag === "function") {
        w.gtag("event", event, {
          ...safePayload,
          event_callback: finish,
          event_timeout: timeoutMs,
        });
        return;
      }
      if (Array.isArray(w.dataLayer)) {
        w.dataLayer.push({ ...safePayload, event });
      }
    } catch {
      // Conversion-Tracking darf den erfolgreichen Lead nie blockieren.
    }

    finish();
  });
}
