import { beforeEach, describe, expect, it } from "vitest";
import {
  ATTRIBUTION_STORAGE_KEY,
  buildLeadAttributionFields,
  captureAttribution,
  loadAttribution,
  resolveChannel,
  updateSessionAttribution,
  sanitizeUtmValue,
} from "../src/lib/attribution";

const ORIGIN = "https://www.hsb-boden.de";

function memoryStorage(): Pick<Storage, "getItem" | "setItem"> & { data: Map<string, string> } {
  const data = new Map<string, string>();
  return {
    data,
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => {
      data.set(key, value);
    },
  };
}

describe("captureAttribution", () => {
  it("extracts all five utm parameters from a full campaign URL", () => {
    const attr = captureAttribution({
      search: "?utm_source=google&utm_medium=cpc&utm_campaign=kaltakquise-2026-q3&utm_term=industrieboden&utm_content=joel-flyer",
      referrer: "https://www.google.com/",
      pathname: "/leistungen/",
      origin: ORIGIN,
    });

    expect(attr.utm_source).toBe("google");
    expect(attr.utm_medium).toBe("cpc");
    expect(attr.utm_campaign).toBe("kaltakquise-2026-q3");
    expect(attr.utm_term).toBe("industrieboden");
    expect(attr.utm_content).toBe("joel-flyer");
    expect(attr.landing_page).toBe("/leistungen/");
  });

  it("keeps partially present utm values and leaves the rest undefined", () => {
    const attr = captureAttribution({
      search: "?utm_source=linkedin&utm_campaign=messe-2026",
      referrer: "",
      pathname: "/",
      origin: ORIGIN,
    });

    expect(attr.utm_source).toBe("linkedin");
    expect(attr.utm_campaign).toBe("messe-2026");
    expect(attr.utm_medium).toBeUndefined();
    expect(attr.utm_term).toBeUndefined();
    expect(attr.utm_content).toBeUndefined();
  });

  it("returns only the landing page for a plain visit without utm values", () => {
    const attr = captureAttribution({ search: "", referrer: "", pathname: "/kontakt/", origin: ORIGIN });

    expect(attr.utm_source).toBeUndefined();
    expect(attr.referrer).toBeUndefined();
    expect(attr.landing_page).toBe("/kontakt/");
  });

  it("reduces an external referrer to its origin only", () => {
    const attr = captureAttribution({
      search: "",
      referrer: "https://www.google.com/search?q=industrieboden+molkerei&sei=abc123",
      pathname: "/",
      origin: ORIGIN,
    });

    expect(attr.referrer).toBe("https://www.google.com");
  });

  it("drops same-origin referrers (internal navigation is not a source)", () => {
    const attr = captureAttribution({
      search: "",
      referrer: `${ORIGIN}/leistungen/`,
      pathname: "/kontakt/",
      origin: ORIGIN,
    });

    expect(attr.referrer).toBeUndefined();
  });

  it("sanitizes malicious or oversized values instead of passing them through", () => {
    const attr = captureAttribution({
      search: `?utm_source=${encodeURIComponent('<script>"x"</script>')}&utm_campaign=${"a".repeat(500)}`,
      referrer: "not a url",
      pathname: "javascript:alert(1)",
      origin: ORIGIN,
    });

    expect(attr.utm_source).toBe("scriptxscript");
    expect(attr.utm_campaign).toHaveLength(100);
    expect(attr.referrer).toBeUndefined();
    expect(attr.landing_page).toBeUndefined();
  });
});

describe("updateSessionAttribution / loadAttribution", () => {
  let storage: ReturnType<typeof memoryStorage>;

  beforeEach(() => {
    storage = memoryStorage();
  });

  it("stores the first entry attribution and keeps it on later utm-free pages", () => {
    const landing = captureAttribution({
      search: "?utm_source=email&utm_medium=outreach&utm_campaign=followup-batch-01",
      referrer: "https://mail.google.com/",
      pathname: "/referenzen/",
      origin: ORIGIN,
    });
    updateSessionAttribution(storage, landing);

    const kontakt = captureAttribution({ search: "", referrer: `${ORIGIN}/referenzen/`, pathname: "/kontakt/", origin: ORIGIN });
    const effective = updateSessionAttribution(storage, kontakt);

    expect(effective.utm_campaign).toBe("followup-batch-01");
    expect(effective.landing_page).toBe("/referenzen/");
    expect(loadAttribution(storage)?.utm_source).toBe("email");
  });

  it("overwrites a stored session attribution when a new campaign arrives", () => {
    updateSessionAttribution(
      storage,
      captureAttribution({ search: "?utm_campaign=alt", referrer: "", pathname: "/", origin: ORIGIN }),
    );
    const effective = updateSessionAttribution(
      storage,
      captureAttribution({ search: "?utm_campaign=neu&utm_source=qr", referrer: "", pathname: "/leistungen/", origin: ORIGIN }),
    );

    expect(effective.utm_campaign).toBe("neu");
    expect(loadAttribution(storage)?.utm_campaign).toBe("neu");
    expect(loadAttribution(storage)?.landing_page).toBe("/leistungen/");
  });

  it("survives a throwing or unavailable storage without breaking", () => {
    const broken = {
      getItem: () => {
        throw new Error("blocked");
      },
      setItem: () => {
        throw new Error("blocked");
      },
    };
    const current = captureAttribution({ search: "?utm_source=x", referrer: "", pathname: "/", origin: ORIGIN });

    expect(() => updateSessionAttribution(broken, current)).not.toThrow();
    expect(updateSessionAttribution(broken, current).utm_source).toBe("x");
    expect(loadAttribution(broken)).toBeUndefined();
    expect(loadAttribution(null)).toBeUndefined();
    expect(() => updateSessionAttribution(null, current)).not.toThrow();
  });

  it("ignores corrupted stored payloads", () => {
    storage.setItem(ATTRIBUTION_STORAGE_KEY, "{not json");
    expect(loadAttribution(storage)).toBeUndefined();

    storage.setItem(ATTRIBUTION_STORAGE_KEY, JSON.stringify({ utm_source: { nested: true }, landing_page: 42 }));
    const loaded = loadAttribution(storage);
    expect(loaded?.utm_source).toBeUndefined();
    expect(loaded?.landing_page).toBeUndefined();
  });
});

describe("resolveChannel", () => {
  it("prioritizes campaign over referral over direct", () => {
    expect(resolveChannel({ utm_source: "google", referrer: "https://www.google.com" })).toBe("campaign");
    expect(resolveChannel({ referrer: "https://www.google.com" })).toBe("referral");
    expect(resolveChannel({})).toBe("direct");
  });
});

describe("buildLeadAttributionFields", () => {
  it("builds the complete payload extension for an attributed lead", () => {
    const fields = buildLeadAttributionFields(
      {
        utm_source: "qr",
        utm_medium: "flyer",
        utm_campaign: "messe-2026",
        landing_page: "/leistungen/",
        referrer: "https://www.google.com",
      },
      "/kontakt/",
    );

    expect(fields).toEqual({
      utm_source: "qr",
      utm_medium: "flyer",
      utm_campaign: "messe-2026",
      referrer: "https://www.google.com",
      landing_page: "/leistungen/",
      form_path: "/kontakt/",
      attribution_channel: "campaign",
    });
  });

  it("marks a lead without any attribution unambiguously as direct", () => {
    const fields = buildLeadAttributionFields(undefined, "/kontakt/");

    expect(fields).toEqual({ form_path: "/kontakt/", attribution_channel: "direct" });
    expect(Object.keys(fields)).not.toContain("utm_source");
  });
});

describe("sanitizeUtmValue", () => {
  it("returns undefined for non-string inputs", () => {
    expect(sanitizeUtmValue(null)).toBeUndefined();
    expect(sanitizeUtmValue(undefined)).toBeUndefined();
    expect(sanitizeUtmValue(123)).toBeUndefined();
    expect(sanitizeUtmValue({})).toBeUndefined();
    expect(sanitizeUtmValue([])).toBeUndefined();
  });

  it("returns undefined for empty or fully invalid strings", () => {
    expect(sanitizeUtmValue("")).toBeUndefined();
    expect(sanitizeUtmValue("   ")).toBeUndefined();
    expect(sanitizeUtmValue("<>")).toBeUndefined();
    expect(sanitizeUtmValue("<script>")).toBe("script");
    expect(sanitizeUtmValue("!!!")).toBeUndefined();
  });

  it("preserves allowed characters and trims spaces", () => {
    expect(sanitizeUtmValue("  valid-UTM_123.~%+  ")).toBe("valid-UTM_123.~%+");
  });

  it("strips disallowed characters", () => {
    expect(sanitizeUtmValue("utm<script>alert(1)</script>value!")).toBe("utmscriptalert1scriptvalue");
    expect(sanitizeUtmValue("something\\with\\slashes")).toBe("somethingwithslashes");
    expect(sanitizeUtmValue("value (with parens)")).toBe("value with parens");
  });

  it("strips leading spreadsheet formula injection characters", () => {
    expect(sanitizeUtmValue("=cmd")).toBe("cmd");
    expect(sanitizeUtmValue("+cmd")).toBe("cmd");
    expect(sanitizeUtmValue("-cmd")).toBe("cmd");
    expect(sanitizeUtmValue("@cmd")).toBe("cmd");
    // Should handle them even if preceded by spaces, because we trim before stripping prefixes
    expect(sanitizeUtmValue("   =cmd")).toBe("cmd");
    expect(sanitizeUtmValue("  + SUM(1,2)")).toBe("SUM12");
  });

  it("allows formula characters in the middle or end of strings", () => {
    expect(sanitizeUtmValue("val=1")).toBe("val1"); // = is not allowed per regex
    expect(sanitizeUtmValue("user@example")).toBe("userexample"); // @ is not in allowed chars so it gets stripped in first regex anyway!
    // Let's test with allowed characters that might be formula chars (+, -)
    expect(sanitizeUtmValue("a+b")).toBe("a+b");
    expect(sanitizeUtmValue("a-b")).toBe("a-b");
    expect(sanitizeUtmValue("valid+")).toBe("valid+");
  });

  it("truncates values to UTM_MAX (100) characters max", () => {
    const longString = "a".repeat(150);
    const sanitized = sanitizeUtmValue(longString);
    expect(sanitized).toBe("a".repeat(100));
    expect(sanitized?.length).toBe(100);
  });
});
