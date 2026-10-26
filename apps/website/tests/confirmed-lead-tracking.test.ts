import { afterEach, describe, expect, it, vi } from "vitest";
import { trackAfterConfirmedLead, trackConfirmedLead } from "../src/lib/confirmedLeadTracking";

type TrackingWindow = Window & {
  gtag?: (command: string, event: string, payload: Record<string, unknown>) => void;
};

describe("tracking after accepted lead", () => {
  it("does not treat analytics failure as delivery failure", async () => {
    const tracking = vi.fn().mockRejectedValue(new Error("GA4 callback failed"));
    await expect(trackAfterConfirmedLead(tracking)).resolves.toBeUndefined();
    expect(tracking).toHaveBeenCalledTimes(1);
  });

  it("waits for tracking when available", async () => {
    const tracking = vi.fn().mockResolvedValue(undefined);
    await expect(trackAfterConfirmedLead(tracking)).resolves.toBeUndefined();
    expect(tracking).toHaveBeenCalledTimes(1);
  });

  it("safely handles synchronous analytics exceptions", async () => {
    const tracking = vi.fn((): Promise<void> => {
      throw new Error("tracking transport unavailable");
    });
    await expect(trackAfterConfirmedLead(tracking)).resolves.toBeUndefined();
    expect(tracking).toHaveBeenCalledTimes(1);
  });
});

describe("trackConfirmedLead", () => {
  afterEach(() => {
    delete (window as TrackingWindow).gtag;
    vi.restoreAllMocks();
  });

  it("calls window.gtag with generate_lead event and lead payload when gtag is present", () => {
    const gtagMock = vi.fn();
    (window as TrackingWindow).gtag = gtagMock;

    trackConfirmedLead("lead_12345");

    expect(gtagMock).toHaveBeenCalledTimes(1);
    expect(gtagMock).toHaveBeenCalledWith("event", "generate_lead", {
      event_category: "engagement",
      event_label: "Lead Confirmed",
      transaction_id: "lead_12345",
    });
  });

  it("safely handles missing or non-function window.gtag", () => {
    delete (window as TrackingWindow).gtag;
    expect(() => trackConfirmedLead("lead_12345")).not.toThrow();

    // @ts-expect-error testing non-function gtag
    (window as TrackingWindow).gtag = "not-a-function";
    expect(() => trackConfirmedLead("lead_12345")).not.toThrow();
  });

  it("catches and logs errors when window.gtag throws an exception", () => {
    const trackingError = new Error("gtag failed");
    (window as TrackingWindow).gtag = vi.fn().mockImplementation(() => {
      throw trackingError;
    });

    const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    expect(() => trackConfirmedLead("lead_12345")).not.toThrow();
    expect(consoleErrorSpy).toHaveBeenCalledWith("[Analytics] Failed to track confirmed lead:", trackingError);
  });
});
