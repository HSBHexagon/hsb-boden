import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { sanitizeTrackingPayload, TrackingEvent } from "../src/lib/tracking";

function source(path: string) {
  return readFileSync(join(process.cwd(), path), "utf8");
}

describe("analytics and consent hardening", () => {
  it("uses the canonical GA4 lead event", () => {
    expect(TrackingEvent.GenerateLead).toBe("generate_lead");
    expect(Object.values(TrackingEvent)).not.toContain("lead_form_submit");
  });

  it("removes PII keys and obvious PII values from tracking payloads", () => {
    expect(
      sanitizeTrackingPayload({
        placement: "hero",
        firstName: "Max",
        email: "max@example.com",
        phone: "+49 123 456789",
        message: "Bitte zurückrufen",
        count: 2,
      }),
    ).toEqual({ placement: "hero", count: 2 });
  });

  it("keeps consent denied by default", () => {
    const layout = source("src/layouts/BaseLayout.astro");

    expect(layout).toContain("ad_storage: 'denied'");
    expect(layout).toContain("ad_user_data: 'denied'");
    expect(layout).toContain("ad_personalization: 'denied'");
    expect(layout).toContain("analytics_storage: hsbConsent && hsbConsent.analytics ? 'granted' : 'denied'");
  });

  it("awaits bounded conversion transport only after successful lead delivery", () => {
    const form = source("src/components/forms/LeadForm.astro");
    const tracking = source("src/lib/tracking.ts");

    expect(form).toContain('import { trackConversion, trackEvent, TrackingEvent }');
    expect(form).toContain("if (!res.ok) throw new Error");
    expect(form).toContain("await trackConversion(TrackingEvent.GenerateLead)");
    expect(form.indexOf("await trackConversion(TrackingEvent.GenerateLead)")).toBeGreaterThan(
      form.indexOf("if (!res.ok) throw new Error"),
    );
    expect(form.indexOf('window.location.href = "/danke-projektanfrage/"')).toBeGreaterThan(
      form.indexOf("await trackConversion(TrackingEvent.GenerateLead)"),
    );
    expect(tracking).toContain("event_callback");
    expect(tracking).toContain("event_timeout");
  });
});
