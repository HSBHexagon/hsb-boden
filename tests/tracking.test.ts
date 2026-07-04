import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { trackEvent, TrackingEvent } from "../src/lib/tracking";

describe("tracking", () => {
  describe("trackEvent", () => {
    let originalWindow: typeof window;

    beforeEach(() => {
      originalWindow = globalThis.window;
      if (globalThis.window) {
        vi.spyOn(globalThis.window, 'dispatchEvent');
        (globalThis.window as any).dataLayer = undefined;
      }
    });

    afterEach(() => {
      vi.restoreAllMocks();
      globalThis.window = originalWindow;
    });

    it("should return early if window is undefined", () => {
      const tempWindow = globalThis.window;
      // @ts-ignore
      delete globalThis.window;

      // This should not throw, even though window is undefined and it tries to access it otherwise
      expect(() => trackEvent(TrackingEvent.CtaClick)).not.toThrow();

      globalThis.window = tempWindow;
    });

    it("should dispatch a CustomEvent with correct details", () => {
      trackEvent(TrackingEvent.LeadFormStart, { formId: "123" });

      expect(globalThis.window.dispatchEvent).toHaveBeenCalledOnce();
      const eventArg = vi.mocked(globalThis.window.dispatchEvent).mock.calls[0][0] as unknown as CustomEvent;
      expect(eventArg.type).toBe("hsb:tracking");
      expect(eventArg.detail).toEqual({
        event: TrackingEvent.LeadFormStart,
        payload: { formId: "123" }
      });
    });

    it("should use an empty payload if none is provided", () => {
      trackEvent(TrackingEvent.PhoneClick);

      const eventArg = vi.mocked(globalThis.window.dispatchEvent).mock.calls[0][0] as unknown as CustomEvent;
      expect(eventArg.detail).toEqual({
        event: TrackingEvent.PhoneClick,
        payload: {}
      });
    });

    it("should push event and payload to dataLayer if it is an array", () => {
      const dataLayer: unknown[] = [];
      (globalThis.window as any).dataLayer = dataLayer;

      trackEvent(TrackingEvent.EmailClick, { source: "footer" });

      expect(dataLayer).toHaveLength(1);
      expect(dataLayer[0]).toEqual({
        event: TrackingEvent.EmailClick,
        source: "footer"
      });
    });

    it("should not crash if dataLayer exists but is not an array", () => {
      (globalThis.window as any).dataLayer = { some: "object" };

      expect(() => trackEvent(TrackingEvent.EmailClick)).not.toThrow();
    });
  });
});
