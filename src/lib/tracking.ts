export type TrackingEvent =
  | "lead_form_start"
  | "lead_form_submit"
  | "phone_click"
  | "email_click"
  | "cta_click"
  | "reference_filter_use"
  | "reference_map_open"
  | "file_upload_add"
  | "flyer_qr_visit";

export function trackEvent(event: TrackingEvent, payload: Record<string, string | number | boolean> = {}) {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent("hsb:tracking", { detail: { event, payload } }));
  const dataLayer = (window as Window & { dataLayer?: unknown[] }).dataLayer;
  if (Array.isArray(dataLayer)) {
    dataLayer.push({ event, ...payload });
  }
}
