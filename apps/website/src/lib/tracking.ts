import { GA4_MEASUREMENT_ID } from "./analyticsConfig";
import { NORM_IDS } from "../data/standards";

export enum TrackingEvent {
  LeadFormStart = "lead_form_start",
  LeadFormSubmit = "lead_form_submit",
  PhoneClick = "phone_click",
  EmailClick = "email_click",
  CtaClick = "cta_click",
  ReferenceFilterUse = "reference_filter_use",
  ReferenceMapOpen = "reference_map_open",
  FileUploadAdd = "file_upload_add",
  FlyerQrVisit = "flyer_qr_visit",
  StressCheckStep = "stress_check_step",
  ReferenceInteraction = "reference_interaction",
  NormInteraction = "norm_interaction",
  B2BConversion = "b2b_conversion",
}

export type AnalyticsValue = string | number | boolean;
export type AnalyticsPayload = Record<string, AnalyticsValue>;
type GtagEventPayload = Record<string, AnalyticsValue | (() => void) | undefined> & {
  send_to: string;
  event_callback?: () => void;
  event_timeout?: number;
};

const CONSENT_STORAGE_KEY = "hsb-consent-v1";
const EVENT_CALLBACK_TIMEOUT_MS = 1000;
const SAFE_TOKEN_PATTERN = /^[a-z0-9_-]{1,64}$/i;
const LOCAL_PATH_PATTERN = /^\/[a-z0-9/_-]{0,120}$/i;
// Anzeigename einer Referenz: Buchstaben, Ziffern, Leerzeichen und übliche
// Firmenzeichen. Kein HTML, keine Steuerzeichen.
const SAFE_LABEL_PATTERN = /^[\p{L}\p{N}][\p{L}\p{N} .,&§+()/-]{0,99}$/u;
const CONVERSION_TYPES = new Set(["audit_request", "technical_inquiry"]);
const REFERENCE_ACTIONS = new Set(["click", "view"]);
const NORM_ACTIONS = new Set(["expand", "download"]);
const NORM_SET = new Set<string>(NORM_IDS);
const isToken = (value: AnalyticsValue) => typeof value === "string" && SAFE_TOKEN_PATTERN.test(value);
let currentPageAnalyticsConsent: boolean | undefined;

if (typeof window !== "undefined") {
  window.addEventListener("hsb:consent", (event) => {
    const detail = (event as CustomEvent<{ analytics?: unknown }>).detail;
    currentPageAnalyticsConsent = detail?.analytics === true;
  });
}

const PARAMETER_VALIDATORS: Record<string, (value: AnalyticsValue) => boolean> = {
  cta: (value) => typeof value === "string" && SAFE_TOKEN_PATTERN.test(value),
  form_id: (value) => typeof value === "string" && SAFE_TOKEN_PATTERN.test(value),
  form_path: (value) => typeof value === "string" && LOCAL_PATH_PATTERN.test(value),
  placement: (value) => typeof value === "string" && SAFE_TOKEN_PATTERN.test(value),
  qualified: (value) => typeof value === "boolean",
  step: (value) => typeof value === "number" && Number.isInteger(value) && value >= 1 && value <= 10,
  medium: isToken,
  temp_range: isToken,
  mechanical_load: isToken,
  time_window: isToken,
  recommended_system: isToken,
  industry: isToken,
  project_type: isToken,
  client_name: (value) => typeof value === "string" && SAFE_LABEL_PATTERN.test(value),
  action: (value) => typeof value === "string" && (REFERENCE_ACTIONS.has(value) || NORM_ACTIONS.has(value)),
  norm: (value) => typeof value === "string" && NORM_SET.has(value),
  conversion_type: (value) => typeof value === "string" && CONVERSION_TYPES.has(value),
};

function hasAnalyticsConsent(): boolean {
  if (currentPageAnalyticsConsent !== undefined) return currentPageAnalyticsConsent;
  try {
    const raw = window.localStorage.getItem(CONSENT_STORAGE_KEY);
    return raw !== null && (JSON.parse(raw) as { analytics?: unknown }).analytics === true;
  } catch {
    return false;
  }
}

function sanitizePayload(payload: AnalyticsPayload): AnalyticsPayload {
  return Object.fromEntries(
    Object.entries(payload).filter(([key, value]) => PARAMETER_VALIDATORS[key]?.(value) === true),
  );
}

function emitEvent(
  event: TrackingEvent,
  payload: AnalyticsPayload,
  completion?: () => void,
): boolean {
  if (typeof window === "undefined") {
    completion?.();
    return false;
  }

  const safePayload = sanitizePayload(payload);
  window.dispatchEvent(new CustomEvent("hsb:tracking", { detail: { event, payload: safePayload } }));
  if (!hasAnalyticsConsent()) {
    completion?.();
    return false;
  }

  // First-Party Edge Proxy Dispatch (Zero-Mainthread, Beacon-first)
  try {
    const proxyPayload = JSON.stringify({
      event_name: event,
      params: safePayload,
    });
    if (typeof navigator !== "undefined" && typeof navigator.sendBeacon === "function") {
      const blob = new Blob([proxyPayload], { type: "application/json" });
      navigator.sendBeacon("/api/collect", blob);
    } else if (typeof fetch === "function") {
      fetch("/api/collect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: proxyPayload,
        keepalive: true,
      }).catch(() => {});
    }
  } catch {
    // Non-blocking fallback
  }

  const trackingWindow = window as Window & {
    dataLayer?: unknown[];
    gtag?: (command: "event", event: string, payload: GtagEventPayload) => void;
  };
  const isLeadSubmission = event === TrackingEvent.LeadFormSubmit;
  const eventName = isLeadSubmission ? "generate_lead" : event;
  const eventPayload: GtagEventPayload = {
    ...safePayload,
    ...(isLeadSubmission ? { method: "contact_form" } : {}),
    send_to: GA4_MEASUREMENT_ID,
  };

  try {
    if (typeof trackingWindow.gtag === "function") {
      trackingWindow.gtag("event", eventName, {
        ...eventPayload,
        ...(completion
          ? { event_callback: completion, event_timeout: EVENT_CALLBACK_TIMEOUT_MS }
          : {}),
      });
      return true;
    }
    // GTM-Fallback: dataLayer bei Bedarf anlegen, damit ein Event vor dem
    // gtag-Loader nicht verloren geht. Consent ist oben bereits geprüft.
    if (!Array.isArray(trackingWindow.dataLayer)) trackingWindow.dataLayer = [];
    trackingWindow.dataLayer.push({ event: eventName, ...eventPayload });
    completion?.();
    return true;
  } catch {
    // Tracking darf die aufrufende Interaktion nie brechen.
  }

  completion?.();
  return false;
}

export function trackEvent(event: TrackingEvent, payload: AnalyticsPayload = {}) {
  emitEvent(event, payload);
}

/** Wartet höchstens kurz auf den GA4-Callback, bevor der Browser navigiert. */
export function trackEventAndWait(event: TrackingEvent, payload: AnalyticsPayload = {}): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();

  return new Promise((resolve) => {
    let settled = false;
    let timeout: number | undefined;
    const finish = () => {
      if (settled) return;
      settled = true;
      if (timeout !== undefined) window.clearTimeout(timeout);
      resolve();
    };

    const emitted = emitEvent(event, payload, finish);
    if (emitted && !settled) timeout = window.setTimeout(finish, EVENT_CALLBACK_TIMEOUT_MS + 100);
  });
}
