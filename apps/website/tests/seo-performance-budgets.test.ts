import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

describe("Lighthouse performance and SEO regression budgets", () => {
  const config = JSON.parse(readFileSync(join(process.cwd(), ".lighthouserc.json"), "utf8"));
  const assertions = config.ci.assert.assertions;

  it("checks LCP, CLS and TBT as measurable lab warnings", () => {
    expect(assertions["largest-contentful-paint"]).toEqual(["warn", { maxNumericValue: 2500 }]);
    expect(assertions["cumulative-layout-shift"]).toEqual(["warn", { maxNumericValue: 0.1 }]);
    expect(assertions["total-blocking-time"]).toEqual(["warn", { maxNumericValue: 200 }]);
  });

  it("keeps SEO and accessibility failures blocking", () => {
    expect(assertions["categories:seo"][0]).toBe("error");
    expect(assertions["categories:accessibility"][0]).toBe("error");
  });

  it("tests five relevant public page paths, not noindex or conversion URLs", () => {
    const urls: string[] = config.ci.collect.url;
    expect(urls).toHaveLength(5);
    expect(urls.some((x) => x.includes("standorte/nrw/"))).toBe(true);
    expect(urls.some((x) => x.includes("branchen/molkerei/"))).toBe(true);
    expect(urls.some((x) => /abmelden|danke-projektanfrage/.test(x))).toBe(false);
  });
});
