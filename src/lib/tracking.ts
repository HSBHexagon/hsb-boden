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

export function trackEvent(event: TrackingEvent, payload: Record<string, string | number | boolean> = {}) {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent("hsb:tracking", { detail: { event, payload } }));
  const w = window as Window & { dataLayer?: unknown[]; gtag?: (...args: unknown[]) => void };
  try {
    if (typeof w.gtag === "function") {
      // Direkte gtag.js-Einbindung: nur gtag('event', …) erzeugt einen GA4-Collect.
      // Kein zusätzlicher dataLayer-Push, sonst zählt ein späteres GTM doppelt.
      w.gtag("event", event, payload);
    } else if (Array.isArray(w.dataLayer)) {
      w.dataLayer.push({ ...payload, event });
    }
  } catch {
    // Tracking darf nie die aufrufende Interaktion (z. B. Formular-Submit) brechen.
  }
}
