import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { trackEvent, TrackingEvent } from "../src/lib/tracking";

describe("trackEvent", () => {
  let originalWindow: any;

  beforeEach(() => {
    originalWindow = global.window;
    // Set up mock window properties we care about
    global.window = Object.create(originalWindow || {});
    // Mock dispatchEvent
    global.window.dispatchEvent = vi.fn();
  });

  afterEach(() => {
    global.window = originalWindow;
    vi.restoreAllMocks();
  });

  it("should return early if window is undefined", () => {
    // Temporarily remove window
    const win = global.window;
    // @ts-ignore
    delete global.window;

    // Should not throw
    expect(() => trackEvent(TrackingEvent.LeadFormStart)).not.toThrow();

    // Restore window
    global.window = win;
  });

  it("should dispatch a CustomEvent on the window object", () => {
    const payload = { test: true, num: 1 };
    trackEvent(TrackingEvent.CtaClick, payload);

    expect(global.window.dispatchEvent).toHaveBeenCalledTimes(1);
    const event = (global.window.dispatchEvent as any).mock.calls[0][0] as CustomEvent;

    expect(event).toBeInstanceOf(CustomEvent);
    expect(event.type).toBe("hsb:tracking");
    expect(event.detail).toEqual({
      event: TrackingEvent.CtaClick,
      payload
    });
  });

  it("should push event and payload to dataLayer if it exists as an array", () => {
    const dataLayer: any[] = [];
    (global.window as any).dataLayer = dataLayer;

    const payload = { source: "test" };
    trackEvent(TrackingEvent.LeadFormSubmit, payload);

    expect(dataLayer).toHaveLength(1);
    expect(dataLayer[0]).toEqual({
      event: TrackingEvent.LeadFormSubmit,
      source: "test"
    });
  });

  it("should not error if dataLayer exists but is not an array", () => {
    (global.window as any).dataLayer = { push: vi.fn() };

    expect(() => trackEvent(TrackingEvent.PhoneClick)).not.toThrow();
    // The push should not be called because it's not an Array
    expect((global.window as any).dataLayer.push).not.toHaveBeenCalled();
  });

  it("should not error if dataLayer is undefined", () => {
    (global.window as any).dataLayer = undefined;

    expect(() => trackEvent(TrackingEvent.EmailClick)).not.toThrow();
  });

  it("should handle default empty payload", () => {
    trackEvent(TrackingEvent.ReferenceMapOpen);

    const event = (global.window.dispatchEvent as any).mock.calls[0][0] as CustomEvent;
    expect(event.detail.payload).toEqual({});
  });
});
