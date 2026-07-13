import { describe, expect, it } from "vitest";
import { leadEndpointSchema, SITE_ORIGIN } from "../src/lib/leadSchema";
import { site } from "../src/data/site";

describe("leadEndpointSchema", () => {
  it("keeps SITE_ORIGIN in sync with site.domain (drift guard)", () => {
    expect(SITE_ORIGIN).toBe(new URL(site.domain).origin);
  });

  const validPayload = {
    firstName: "Max",
    lastName: "Mustermann",
    company: "Muster Produktion GmbH",
    email: "max@example.com",
    phone: "+49 123 456789",
    industry: "molkerei",
    projectType: "sanierung",
    areaSize: "450",
    liveOperation: "ja",
    loads: ["Säuren/Laugen", "Hochdruckreinigung"],
    message: "Bitte Belastungsprofil prüfen, Fugen sind beschädigt.",
    privacyConsent: true,
    source: "website",
    legalBasis: "inquiry",
  };

  it("accepts a complete, valid lead payload", () => {
    const result = leadEndpointSchema.safeParse(validPayload);
    expect(result.success).toBe(true);
  });

  it("rejects when privacyConsent is not true", () => {
    const result = leadEndpointSchema.safeParse({ ...validPayload, privacyConsent: false });
    expect(result.success).toBe(false);
  });

  it("rejects when loads is empty", () => {
    const result = leadEndpointSchema.safeParse({ ...validPayload, loads: [] });
    expect(result.success).toBe(false);
  });

  it("rejects an invalid email", () => {
    const result = leadEndpointSchema.safeParse({ ...validPayload, email: "not-an-email" });
    expect(result.success).toBe(false);
  });

  it("rejects message shorter than 10 characters", () => {
    const result = leadEndpointSchema.safeParse({ ...validPayload, message: "zu kurz" });
    expect(result.success).toBe(false);
  });

  it("rejects an unknown projectType value", () => {
    const result = leadEndpointSchema.safeParse({ ...validPayload, projectType: "abriss" });
    expect(result.success).toBe(false);
  });

  it("rejects a filled honeypot field", () => {
    const result = leadEndpointSchema.safeParse({ ...validPayload, honeypot: "spam-bot-filled-this" });
    expect(result.success).toBe(false);
  });

  it("accepts an absent honeypot field", () => {
    const result = leadEndpointSchema.safeParse(validPayload);
    expect(result.success).toBe(true);
  });

  it("strips unknown fields instead of accepting them", () => {
    const result = leadEndpointSchema.safeParse({ ...validPayload, injectedField: "drop-me" });
    expect(result.success).toBe(true);
    if (result.success) {
      expect("injectedField" in result.data).toBe(false);
    }
  });

  it("accepts optional access_key and utm fields when present", () => {
    const result = leadEndpointSchema.safeParse({
      ...validPayload,
      access_key: "abc123",
      utm_source: "google",
      utm_medium: "cpc",
      utm_campaign: "leistungen",
    });
    expect(result.success).toBe(true);
  });

  it("passes attribution fields through to the webhook payload", () => {
    const result = leadEndpointSchema.safeParse({
      ...validPayload,
      utm_source: "qr",
      utm_medium: "flyer",
      utm_campaign: "messe-2026",
      utm_term: "industrieboden",
      utm_content: "joel-flyer",
      referrer: "https://www.google.com",
      landing_page: "/leistungen/",
      form_path: "/kontakt/",
      attribution_channel: "campaign",
    });

    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.utm_term).toBe("industrieboden");
      expect(result.data.utm_content).toBe("joel-flyer");
      expect(result.data.referrer).toBe("https://www.google.com");
      expect(result.data.landing_page).toBe("/leistungen/");
      expect(result.data.form_path).toBe("/kontakt/");
      expect(result.data.attribution_channel).toBe("campaign");
    }
  });

  it("tolerates oversized or invalid attribution values without rejecting the lead", () => {
    const result = leadEndpointSchema.safeParse({
      ...validPayload,
      utm_term: "a".repeat(101),
      referrer: "a".repeat(201),
      landing_page: "a".repeat(201),
      attribution_channel: "paid-social",
    });

    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.utm_term).toBe("a".repeat(100));
      expect(result.data.referrer).toBeUndefined();
      expect(result.data.landing_page).toBeUndefined();
      expect(result.data.attribution_channel).toBe("campaign");
    }
  });

  it("drops same-origin referrers server-side so direct POSTs cannot fake referrals", () => {
    const result = leadEndpointSchema.safeParse({
      ...validPayload,
      referrer: "https://www.hsb-boden.de/kontakt/",
      attribution_channel: "referral",
    });

    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.referrer).toBeUndefined();
      expect(result.data.attribution_channel).toBe("direct");
    }
  });

  it("re-sanitizes attribution fields server-side against direct POSTs", () => {
    const result = leadEndpointSchema.safeParse({
      ...validPayload,
      utm_source: '=HYPERLINK("https://evil.example")',
      utm_campaign: "+kampagne<script>",
      referrer: "https://evil.example/pfad?q=jemand@example.com",
      landing_page: "/kontakt/?token=geheim#fragment",
      form_path: "kein-pfad",
    });

    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.utm_source).toBe("HYPERLINKhttpsevil.example");
      expect(result.data.utm_campaign).toBe("kampagnescript");
      expect(result.data.referrer).toBe("https://evil.example");
      expect(result.data.landing_page).toBe("/kontakt/");
      expect(result.data.form_path).toBeUndefined();
    }
  });

  it("strips formula prefixes even behind leading whitespace", () => {
    const result = leadEndpointSchema.safeParse({
      ...validPayload,
      utm_source: " +SUM(A1)",
      utm_medium: "\t-2+3",
      utm_campaign: "  =HYPERLINK(x)",
      utm_term: " @import",
    });

    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.utm_source).toBe("SUMA1");
      expect(result.data.utm_medium).toBe("2+3");
      expect(result.data.utm_campaign).toBe("HYPERLINKx");
      expect(result.data.utm_term).toBe("import");
    }
  });

  it("recomputes attribution_channel server-side from sanitized fields", () => {
    const spoofed = leadEndpointSchema.safeParse({ ...validPayload, attribution_channel: "campaign" });
    expect(spoofed.success).toBe(true);
    if (spoofed.success) {
      expect(spoofed.data.attribution_channel).toBe("direct");
    }

    const legit = leadEndpointSchema.safeParse({ ...validPayload, utm_source: "qr", attribution_channel: "direct" });
    expect(legit.success).toBe(true);
    if (legit.success) {
      expect(legit.data.attribution_channel).toBe("campaign");
    }
  });

  it("drops non-http referrers and invalid paths instead of forwarding them", () => {
    const result = leadEndpointSchema.safeParse({
      ...validPayload,
      referrer: "javascript:alert(1)",
      landing_page: "javascript:alert(1)",
    });

    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.referrer).toBeUndefined();
      expect(result.data.landing_page).toBeUndefined();
    }
  });

  it("still accepts a legacy payload without any attribution fields", () => {
    const result = leadEndpointSchema.safeParse(validPayload);
    expect(result.success).toBe(true);
    if (result.success) {
      expect("attribution_channel" in result.data).toBe(false);
    }
  });
});
