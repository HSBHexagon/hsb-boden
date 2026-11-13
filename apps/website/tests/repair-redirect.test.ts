import { describe, it, expect } from "vitest";
import { onRequestGet, onRequestHead, REPAIR_TARGET } from "../functions/reparatur/index";

class FakeKV {
  keys: string[] = [];
  async put(key: string) { this.keys.push(key); }
}

function ctx(headers: Record<string, string>, kv: FakeKV | null, cf?: any) {
  const request = new Request("https://www.hsb-boden.de/reparatur/", { headers });
  if (cf) (request as any).cf = cf;
  const promises: Promise<unknown>[] = [];
  return {
    c: { request, env: kv ? { EMAIL_CLICKS: kv } : {}, waitUntil: (p: Promise<unknown>) => promises.push(p) } as any,
    flush: () => Promise.all(promises),
  };
}

const BROWSER = { "User-Agent": "Mozilla/5.0 Chrome/126", "Accept-Language": "de-DE" };

describe("/reparatur/", () => {
  it("leitet mit Kampagnen-UTM weiter und zählt einen menschlichen Klick ohne Personenbezug", async () => {
    const kv = new FakeKV();
    const { c, flush } = ctx(BROWSER, kv);
    const res = await onRequestGet(c);
    await flush();
    expect(res.status).toBe(302);
    expect(res.headers.get("Location")).toBe(REPAIR_TARGET);
    expect(REPAIR_TARGET).toContain("utm_campaign=reparatur-2026-11");
    // Mail-Empfänger landen direkt auf der Upload-Dropzone, nicht im Fließtext (Regel L28).
    expect(REPAIR_TARGET.endsWith("#repair-photo")).toBe(true);
    expect(kv.keys).toHaveLength(1);
    expect(kv.keys[0]).toMatch(/^agg:reparatur:\d{4}-\d{2}-\d{2}:human:\d+-[a-z0-9]+$/);
  });

  it("markiert Scanner aus Rechenzentren als bot", async () => {
    const kv = new FakeKV();
    const { c, flush } = ctx(BROWSER, kv, { asn: 8075 });
    await onRequestGet(c);
    await flush();
    expect(kv.keys[0]).toContain(":bot:");
  });

  it("HEAD und fehlendes KV leiten nur weiter", async () => {
    expect((await onRequestHead()).headers.get("Location")).toBe(REPAIR_TARGET);
    const { c } = ctx(BROWSER, null);
    expect((await onRequestGet(c)).status).toBe(302);
  });
});
