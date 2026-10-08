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
