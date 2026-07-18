import { trackEvent, TrackingEvent } from "../../lib/tracking";
import { buildLeadAttributionFields, captureAttribution, loadAttribution } from "../../lib/attribution";

export function initLeadForm() {
  const form = document.getElementById("lead-form") as HTMLFormElement | null;
  const submitBtn = document.getElementById("form-submit") as HTMLButtonElement | null;
  const errorMsg = document.getElementById("form-error");
  const deliveryConfigured = form?.dataset.deliveryConfigured === "true";
  const genericErrorText = errorMsg?.textContent ?? "";

  let started = false;

  function onFocus() {
    if (!started) {
      started = true;
      trackEvent(TrackingEvent.LeadFormStart);
    }
  }

  async function onSubmit(event: SubmitEvent | Event) {
    event.preventDefault();
    if (!deliveryConfigured || !form || !submitBtn || !errorMsg) return;

    const fd = new FormData(form);

    if (fd.getAll("loads").length === 0) {
      errorMsg.textContent =
        "Bitte wählen Sie mindestens eine Belastung aus, damit wir Ihr Projekt einschätzen können.";
      errorMsg.classList.remove("hidden");
      document.getElementById("loads-fieldset")?.querySelector("input")?.focus();
      return;
    }

    let attributionFields: Record<string, string> = {};
    try {
      const attribution =
        loadAttribution(window.sessionStorage) ??
        captureAttribution({
          search: window.location.search,
          referrer: document.referrer,
          pathname: window.location.pathname,
          origin: window.location.origin,
        });
      attributionFields = buildLeadAttributionFields(attribution, window.location.pathname);
    } catch {
      attributionFields = {};
    }

    const payload: Record<string, any> = {
      ...attributionFields,
      source: "website",
      legalBasis: "inquiry",
      firstName: fd.get("firstName"),
      lastName: fd.get("lastName"),
      company: fd.get("company"),
      email: fd.get("email"),
      phone: fd.get("phone"),
      industry: fd.get("industry"),
      projectType: fd.get("projectType"),
      areaSize: fd.get("areaSize") ?? "",
      liveOperation: fd.get("liveOperation"),
      loads: fd.getAll("loads"),
      message: fd.get("message"),
      privacyConsent: fd.get("privacyConsent") === "on",
    };

    submitBtn.disabled = true;
    const originalBtnText = submitBtn.textContent;
    submitBtn.textContent = "Wird gesendet …";
    errorMsg.classList.add("hidden");

    try {
      const res = await fetch("/api/lead", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`Status ${res.status}`);
      trackEvent(TrackingEvent.LeadFormSubmit);
      window.location.href = "/danke-projektanfrage/";
    } catch (e) {
      console.error("Submission error:", e);
      submitBtn.disabled = false;
      submitBtn.textContent = originalBtnText;
      errorMsg.textContent = genericErrorText;
      errorMsg.classList.remove("hidden");
    }
  }

  form?.addEventListener("focusin", onFocus, { once: true });
  form?.addEventListener("submit", onSubmit);

  return { form, submitBtn, errorMsg, onSubmit, onFocus };
}
