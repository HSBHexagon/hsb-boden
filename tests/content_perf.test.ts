import { describe, expect, it } from "vitest";
import { getReferencesForSlugs } from "../src/lib/content";
import { references } from "../src/data/references";

describe("Performance: getReferencesForSlugs", () => {
  it("should be fast", () => {
    const slugList = references.map(r => r.id).slice(0, 10);

    const start = performance.now();
    for (let i = 0; i < 10000; i++) {
        getReferencesForSlugs(slugList);
    }
    const end = performance.now();

    console.log(`Time taken: ${end - start} ms`);
  });
});
