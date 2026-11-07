type TrackingWindow = Window & {
  gtag?: (command: string, event: string, payload: Record<string, unknown>) => void;
};

/**
 * Tracking is optional after a successful backend acknowledgement.
 * Its failure must never make a delivered lead look undelivered.
 */
export async function trackAfterConfirmedLead(track: () => Promise<void>): Promise<void> {
  try {
    await track();
  } catch {
    // Analytics errors are non-fatal for an already confirmed lead.
  }
}

export function trackConfirmedLead(leadId: string): void {
  const trackingWindow = window as TrackingWindow;
  try {
    if (typeof trackingWindow.gtag === "function") {
      trackingWindow.gtag("event", "generate_lead", {
        event_category: "engagement",
        event_label: "Lead Confirmed",
        transaction_id: leadId, // Deduplication key
      });
    }
  } catch (error) {
    console.error("[Analytics] Failed to track confirmed lead:", error);
  }
}
