import { describe, expect, it } from "vitest";
import { toTelephoneHref } from "../src/lib/phone";

describe("toTelephoneHref", () => {
  it("removes the German optional trunk zero from international numbers", () => {
    expect(toTelephoneHref("+49 (0)2562 9463030")).toBe("tel:+4925629463030");
  });

  it("keeps an already normalized international number stable", () => {
    expect(toTelephoneHref("+49 2562 9463030")).toBe("tel:+4925629463030");
  });
});
