import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { onRequestGet, onRequestHead } from "../functions/r/[token]";

const SECRET = "fixture-secret";
// Querfixture: identisch in apps/sales-os/tests/test_click_sync.py
const FIXTURE_TOKEN = "L-0001.e1a4bbf8b2bcf786";

class FakeKV {
  store = new Map<string, { value: string; opts?: any }>();
  fail = false;
  async put(key: string, value: string, opts?: any) {
    if (this.fail) throw new Error("kv down");
    this.store.set(key, { value, opts });
  }
  async get(key: string) {
    if (this.fail) throw new Error("kv down");
    return this.store.get(key)?.value ?? null;
  }
}

function makeContext(
  token: string,
  opts: { kv?: FakeKV | null; secret?: string | null; headers?: Record<string, string>; cf?: any; query?: string; method?: string } = {},
) {
  const headers = { "Accept-Language": "de-DE,de;q=0.9", "User-Agent": "Mozilla/5.0 Chrome/126", ...(opts.headers ?? {}) };
  const request = new Request(`https://www.hsb-boden.de/r/${token}${opts.query ?? ""}`, {
    method: opts.method ?? "GET",
    headers,
  });
  if (opts.cf) (request as any).cf = opts.cf;
  const promises: Promise<unknown>[] = [];
  const env: any = {};
  if (opts.kv !== null) env.EMAIL_CLICKS = opts.kv ?? new FakeKV();
  if (opts.secret !== null) env.CLICK_SECRET = opts.secret ?? SECRET;
  return {
    ctx: { request, env, params: { token }, waitUntil: (p: Promise<unknown>) => promises.push(p) } as any,
    flush: () => Promise.all(promises),
    env,
  };
}

const records = (kv: FakeKV) => [...kv.store.entries()].filter(([k]) => k.startsWith("click:"));

describe("Klick-Zähler /r/<token>", () => {
  it("valid_token_human_click_redirects_and_records_human", async () => {
    const kv = new FakeKV();
    const { ctx, flush } = makeContext(FIXTURE_TOKEN, { kv, query: "?s=a", cf: { asn: 3320 } });
    const res = await onRequestGet(ctx);
    await flush();
    expect(res.status).toBe(302);
    expect(res.headers.get("Location")).toBe(
      "/flyer/?utm_source=hsb_outreach&utm_medium=email&utm_campaign=iboden_v2_architekten",
    );
    expect(res.headers.get("Location")).not.toContain("L-0001");
    expect(res.headers.get("Cache-Control")).toBe("no-store");
    expect(res.headers.get("X-Robots-Tag")).toBe("noindex");
    const recs = records(kv);
    expect(recs).toHaveLength(1);
    expect(recs[0][0]).toMatch(/^click:L-0001:\d+$/);
    expect(recs[0][1].opts.expirationTtl).toBe(180 * 24 * 3600);
    const val = JSON.parse(recs[0][1].value);
    expect(val.class).toBe("human");
    expect(val.reasons).toEqual([]);
    expect(val.asn).toBe(3320);
    expect(val.ua_family).toBe("chrome");
    expect(typeof val.at).toBe("string");
  });

  it("segment_defaults_to_produktion_and_unknown_is_produktion", async () => {
    for (const query of ["", "?s=x", "?s=p"]) {
      const { ctx } = makeContext(FIXTURE_TOKEN, { query });
      const res = await onRequestGet(ctx);
      expect(res.headers.get("Location")).toContain("utm_campaign=iboden_v2_produktion");
    }
  });

  it("invalid_hmac_records_bot_and_still_redirects", async () => {
    const kv = new FakeKV();
    const { ctx, flush } = makeContext("L-ATTACK.0000000000000000", { kv });
    const res = await onRequestGet(ctx);
    await flush();
    expect(res.status).toBe(302);
    const recs = records(kv);
    expect(recs).toHaveLength(1);
    expect(recs[0][0]).toBe(`click:invalid:${Math.floor(Date.now() / 60_000)}`);
    expect(recs[0][0]).not.toContain("ATTACK");
    expect(recs[0][1].opts.expirationTtl).toBe(7 * 24 * 3600);
    const val = JSON.parse(recs[0][1].value);
    expect(val.class).toBe("bot");
    expect(val.reasons).toContain("invalid_hmac");
  });

  it("malformed_token_records_bot_without_lead", async () => {
    const kv = new FakeKV();
    const { ctx, flush } = makeContext("kaputt", { kv });
    const res = await onRequestGet(ctx);
    await flush();
    expect(res.status).toBe(302);
    expect(records(kv)[0][0]).toMatch(/^click:invalid:\d+$/);
  });

  it("invalid_flood_creates_one_key_per_minute", async () => {
    const kv = new FakeKV();
    for (let i = 0; i < 20; i++) {
      const { ctx, flush } = makeContext(`L-${i}.0000000000000000`, { kv });
      await onRequestGet(ctx);
      await flush();
    }
    expect(records(kv).length).toBeLessThanOrEqual(2);
  });

  it("bot_records_expire_after_7_days_human_after_180", async () => {
    const kv = new FakeKV();
    const { ctx, flush } = makeContext(FIXTURE_TOKEN, { kv, cf: { asn: 16509 } });
    await onRequestGet(ctx);
    await flush();
    expect(records(kv)[0][1].opts.expirationTtl).toBe(7 * 24 * 3600);
  });

  it.each(["curl/8.4.0", "python-requests/2.31", "SomeLinkPreview/1.0", ""])("ua_bot_reason_for_%s", async (ua) => {
    const kv = new FakeKV();
    const { ctx, flush } = makeContext(FIXTURE_TOKEN, { kv, headers: { "User-Agent": ua } });
    await onRequestGet(ctx);
    await flush();
    const val = JSON.parse(records(kv)[0][1].value);
    expect(val.class).toBe("bot");
    expect(val.reasons).toContain("ua_bot");
  });

  it("head_redirects_without_record", async () => {
    const kv = new FakeKV();
    const { ctx, flush } = makeContext(FIXTURE_TOKEN, { kv, method: "HEAD" });
    const res = await onRequestHead(ctx);
    await flush();
    expect(res.status).toBe(302);
    expect(res.headers.get("Cache-Control")).toBe("no-store");
    expect(kv.store.size).toBe(0);
  });

  it("datacenter_asn_records_bot", async () => {
    const kv = new FakeKV();
    const { ctx, flush } = makeContext(FIXTURE_TOKEN, { kv, cf: { asn: 8075 } });
    await onRequestGet(ctx);
    await flush();
    const val = JSON.parse(records(kv)[0][1].value);
    expect(val.class).toBe("bot");
    expect(val.reasons).toContain("datacenter_asn");
  });

  it("missing_accept_language_records_bot", async () => {
    const kv = new FakeKV();
    const { ctx, flush } = makeContext(FIXTURE_TOKEN, { kv, headers: { "Accept-Language": "" } });
    await onRequestGet(ctx);
    await flush();
    const val = JSON.parse(records(kv)[0][1].value);
    expect(val.class).toBe("bot");
    expect(val.reasons).toContain("no_accept_language");
  });

  it("second_click_within_10s_writes_no_persistent_record", async () => {
    const kv = new FakeKV();
    const first = makeContext(FIXTURE_TOKEN, { kv });
    await onRequestGet(first.ctx);
    await first.flush();
    await new Promise((r) => setTimeout(r, 5));
    const second = makeContext(FIXTURE_TOKEN, { kv });
    const res = await onRequestGet(second.ctx);
    await second.flush();
    expect(res.status).toBe(302);
    const vals = records(kv).map(([, v]) => JSON.parse(v.value));
    expect(vals).toHaveLength(1);
    expect(vals[0].class).toBe("human");
    expect(kv.store.get("last:L-0001")?.opts.expirationTtl).toBe(60);
  });

  it("kv_failure_still_redirects", async () => {
    const kv = new FakeKV();
    kv.fail = true;
    const { ctx, flush } = makeContext(FIXTURE_TOKEN, { kv });
    const res = await onRequestGet(ctx);
    await expect(flush()).resolves.toBeDefined();
    expect(res.status).toBe(302);
  });

  it("missing_binding_or_secret_still_redirects", async () => {
    for (const o of [{ kv: null }, { secret: null }, { kv: null, secret: null }] as const) {
      const { ctx, flush } = makeContext(FIXTURE_TOKEN, o as any);
      const res = await onRequestGet(ctx);
      await flush();
      expect(res.status).toBe(302);
      expect(res.headers.get("Location")).toContain("/flyer/?utm_source=hsb_outreach");
    }
  });

  it("uppercase_Flyer_redirects_to_landingpage", () => {
    const text = readFileSync(resolve(process.cwd(), "public/_redirects"), "utf8");
    const rules = text.split("\n").map((l) => l.trim().split(/\s+/)).filter((p) => p[0]?.startsWith("/"));
    expect(rules).toContainEqual(["/Flyer", "/flyer/", "301"]);
    expect(rules.find((p) => p[0] === "/flyer")).toBeUndefined();
    expect(rules.find((p) => p[0] === "/flyer/")).toBeUndefined();
    expect(rules.find((p) => p[0] === "/HSB-HEXAGON-Industrieboeden-Flyer.pdf")?.[1]).toBe("/HSB-Flyer-Geschaeftsfuehrer.pdf");
  });
});
