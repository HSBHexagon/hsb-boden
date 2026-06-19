import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { trackEvent, TrackingEvent } from '../src/lib/tracking';

describe('trackEvent', () => {
  beforeEach(() => {
    // Reset window.dataLayer
    (window as any).dataLayer = [];
    vi.restoreAllMocks();
  });

  afterEach(() => {
    delete (window as any).dataLayer;
  });

  it('should dispatch hsb:tracking custom event', () => {
    const dispatchEventSpy = vi.spyOn(window, 'dispatchEvent');

    trackEvent(TrackingEvent.LeadFormStart, { source: 'homepage' });

    expect(dispatchEventSpy).toHaveBeenCalledTimes(1);
    const event = dispatchEventSpy.mock.calls[0][0] as CustomEvent;
    expect(event.type).toBe('hsb:tracking');
    expect(event.detail).toEqual({
      event: TrackingEvent.LeadFormStart,
      payload: { source: 'homepage' }
    });
  });

  it('should push event and payload to dataLayer if it is an array', () => {
    (window as any).dataLayer = [];

    trackEvent(TrackingEvent.CtaClick, { button: 'hero' });

    expect((window as any).dataLayer).toHaveLength(1);
    expect((window as any).dataLayer[0]).toEqual({
      event: TrackingEvent.CtaClick,
      button: 'hero'
    });
  });

  it('should not push to dataLayer if it is not an array', () => {
    (window as any).dataLayer = undefined;

    trackEvent(TrackingEvent.PhoneClick);

    expect((window as any).dataLayer).toBeUndefined();
  });

  it('should not throw if window is undefined', () => {
    // Note: vi.stubGlobal can mock the global window reference
    vi.stubGlobal('window', undefined);

    expect(() => {
      trackEvent(TrackingEvent.EmailClick);
    }).not.toThrow();

    vi.unstubAllGlobals();
  });
});
