// @vitest-environment jsdom
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { initLeadForm } from "../src/components/forms/LeadForm.client";

// Mock tracking as it accesses globals/window logic that we don't need for this form test
vi.mock("../src/lib/tracking", () => ({
  trackEvent: vi.fn(),
  TrackingEvent: { LeadFormStart: "LeadFormStart", LeadFormSubmit: "LeadFormSubmit" }
}));

describe("LeadForm", () => {
  beforeEach(() => {
    // Set up a dummy DOM reflecting what LeadForm.astro outputs
    document.body.innerHTML = `
      <form id="lead-form" data-delivery-configured="true">
        <input name="firstName" value="John" />
        <input name="lastName" value="Doe" />
        <input name="company" value="Doe Inc" />
        <input name="email" value="john@example.com" />
        <input name="phone" value="123456789" />
        <select name="industry"><option value="molkerei" selected>Molkerei</option></select>
        <select name="projectType"><option value="neubau" selected>Neubau</option></select>
        <select name="liveOperation"><option value="ja" selected>Ja</option></select>

        <fieldset id="loads-fieldset">
          <input type="checkbox" name="loads" value="Säuren/Laugen" checked id="load-checkbox" />
        </fieldset>

        <textarea name="message">This is a test message that is long enough.</textarea>
        <input type="checkbox" name="privacyConsent" checked />

        <p id="form-error" class="hidden">Generic error message.</p>
        <button id="form-submit" type="submit">Senden</button>
      </form>
    `;

    // Reset window.location mock
    Object.defineProperty(window, 'location', {
      value: { href: 'http://localhost/' },
      writable: true
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("successfully submits the form and redirects on happy path", async () => {
    const { onSubmit } = initLeadForm();

    // Mock fetch to return success
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
    });

    const submitEvent = new Event("submit", { cancelable: true });
    await onSubmit(submitEvent);

    expect(global.fetch).toHaveBeenCalledTimes(1);

    // Check if trackEvent was called for submission
    const trackingModule = await import("../src/lib/tracking");
    expect(trackingModule.trackEvent).toHaveBeenCalledWith(trackingModule.TrackingEvent.LeadFormSubmit);

    // Verify redirection
    expect(window.location.href).toBe("/danke-projektanfrage/");
  });

  it("shows an error message when the fetch request fails", async () => {
    const { onSubmit } = initLeadForm();

    // Mock fetch to return a failure status to trigger the error path
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
    });

    const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    const submitEvent = new Event("submit", { cancelable: true });
    await onSubmit(submitEvent);

    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(consoleErrorSpy).toHaveBeenCalled();

    const errorMsg = document.getElementById("form-error");
    const submitBtn = document.getElementById("form-submit") as HTMLButtonElement;

    expect(errorMsg?.classList.contains("hidden")).toBe(false);
    expect(submitBtn.disabled).toBe(false);
    expect(submitBtn.textContent).toBe("Senden");
  });

  it("blocks submission and shows an error if no loads are selected", async () => {
    // Uncheck the loads checkbox
    const checkbox = document.getElementById("load-checkbox") as HTMLInputElement;
    checkbox.checked = false;

    const { onSubmit } = initLeadForm();

    global.fetch = vi.fn();

    const submitEvent = new Event("submit", { cancelable: true });
    await onSubmit(submitEvent);

    // Fetch should not be called due to validation failure
    expect(global.fetch).not.toHaveBeenCalled();

    const errorMsg = document.getElementById("form-error");
    expect(errorMsg?.classList.contains("hidden")).toBe(false);
    expect(errorMsg?.textContent).toContain("Bitte wählen Sie mindestens eine Belastung aus");
  });
});
