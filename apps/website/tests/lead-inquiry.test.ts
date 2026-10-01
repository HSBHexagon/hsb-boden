import { afterEach, expect, it, vi } from "vitest";
import { leadEndpointSchema } from "../src/lib/leadSchema";
import { leadFormSchema } from "../src/lib/validation";
import { submitLeadInquiry } from "../src/lib/leadSubmission";
const minimal = { firstName: "Max Muster", company: "Muster GmbH", email: "test@example.com", message: "Bitte die Bodenfläche prüfen.", privacyConsent: true, source: "website", legalBasis: "inquiry" };
afterEach(() => vi.useRealTimers());
it("accepts a short first inquiry on client and server while retaining CRM defaults", () => {
  expect(leadFormSchema.safeParse(minimal).success).toBe(true);
  const lead = leadEndpointSchema.parse(minimal);
  expect(lead.lastName).toBe(""); expect(lead.phone).toBe(""); expect(lead.loads).toEqual([]);
  expect(lead.projectType).toBe("bewertung"); expect(lead.liveOperation).toBe("unklar");
});
it("still rejects a filled spam trap", () => {
  expect(leadEndpointSchema.safeParse({ ...minimal, honeypot: "spam" }).success).toBe(false);
});
it.each([["{}",200],['{"ok":false}',200],["<html>wrong upstream</html>",200],['{"ok":true}',502]])(
  "does not report success for %s at status %s", async (body,status) => {
    const request = vi.fn<typeof fetch>().mockResolvedValue(new Response(body,{status}));
    await expect(submitLeadInquiry(minimal,request)).rejects.toThrow();
  },
);
it("accepts only a confirmed lead", async () => {
  const request = vi.fn<typeof fetch>().mockResolvedValue(new Response('{"ok":true}',{status:200}));
  await expect(submitLeadInquiry(minimal,request)).resolves.toBeUndefined();
});
it("aborts a stalled request", async () => {
  vi.useFakeTimers();
  const request = vi.fn<typeof fetch>().mockImplementation((_url, options) => new Promise((_resolve,reject) => {
    options?.signal?.addEventListener("abort", () => reject(new Error("aborted")));
  }));
  const result = expect(submitLeadInquiry(minimal,request)).rejects.toThrow("aborted");
  await vi.advanceTimersByTimeAsync(12000);
  await result;
});
