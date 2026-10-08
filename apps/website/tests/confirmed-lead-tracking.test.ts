import { describe, expect, it, vi } from "vitest";
import { trackAfterConfirmedLead } from "../src/lib/confirmedLeadTracking";

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
