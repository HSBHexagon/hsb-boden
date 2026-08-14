import { describe, expect, it } from "vitest";
import { parseCsv, parseCsvRecords, toCsv } from "../scripts/outreach/csv.mjs";
import {
  evaluateLead,
  executeBatch,
  findResumable,
  planBatch,
  STATUS,
  summarizeState,
} from "../scripts/outreach/engine.mjs";
import { noopProvider, resolveProvider } from "../scripts/outreach/providers.mjs";

// Ausschließlich synthetische Fixtures — keine echten Lead-Daten aus
// data/lead-import/output/ (gitignored, PII). Siehe docs/crm/CRM_DATENQUELLE_WAHRHEIT.md.
function makeLead(overrides = {}) {
  return {
    leadId: "HSB-TEST-00001",
    email: "kontakt@beispiel-firma.example",
    tier: "A",
    versandfreigabe: "yes",
    optOutStatus: "unknown",
    owner: "Joel",
    campaignId: "kaltakquise-test",
    emailTemplateId: "EMAIL_TEMPLATE_JOEL_PRIMARY",
    flyerUrl: "https://www.hsb-boden.de/HSB-Flyer-Joel-Cherino.pdf",
    ...overrides,
  };
}

function baseCtx(overrides = {}) {
  return {
    state: { leads: {} as Record<string, any> },
    suppression: new Set<string>(),
    campaignId: "kaltakquise-test",
    ...overrides,
  };
}

describe("csv.mjs", () => {
  it("parst semikolon-getrennte Felder inkl. Anführungszeichen und eingebettetem Trennzeichen", () => {
    const text = 'a;b;c\n1;"Hallo; Welt";3\n';
    const { header, records } = parseCsvRecords(text, ";");
    expect(header).toEqual(["a", "b", "c"]);
    expect(records).toEqual([{ a: "1", b: "Hallo; Welt", c: "3" }]);
  });

  it("entfernt ein UTF-8-BOM am Dateianfang", () => {
    const text = "﻿a,b\n1,2\n";
    const { header } = parseCsvRecords(text, ",");
    expect(header).toEqual(["a", "b"]);
  });

  it("behandelt eingebettete Zeilenumbrüche in Anführungszeichen-Feldern korrekt", () => {
    const text = 'a,b\n1,"Zeile 1\nZeile 2"\n';
    const rows = parseCsv(text, ",");
    expect(rows).toEqual([
      ["a", "b"],
      ["1", "Zeile 1\nZeile 2"],
    ]);
  });

  it("toCsv/parseCsvRecords sind roundtrip-stabil", () => {
    const header = ["a", "b"];
    const records = [{ a: "1", b: "x;y" }];
    const csv = toCsv(header, records, ";");
    const parsed = parseCsvRecords(csv, ";");
    expect(parsed.records).toEqual(records);
  });
});

describe("engine.mjs — evaluateLead", () => {
  it("markiert einen vollständigen, freigegebenen Lead als READY", () => {
    const result = evaluateLead(makeLead(), baseCtx());
    expect(result.decision).toBe(STATUS.READY);
  });

  it("lehnt ungültige E-Mail-Adressen ab (INVALID_EMAIL)", () => {
    const result = evaluateLead(makeLead({ email: "keine-email" }), baseCtx());
    expect(result).toMatchObject({ decision: STATUS.SKIPPED, reason: "INVALID_EMAIL" });
  });

  it("blockiert Leads ohne Versandfreigabe=yes (aktueller Realzustand: alle no)", () => {
    const result = evaluateLead(makeLead({ versandfreigabe: "no" }), baseCtx());
    expect(result).toMatchObject({ decision: STATUS.SKIPPED, reason: "VERSANDFREIGABE_NOT_YES" });
  });

  it("suppresst Leads auf der Suppression-Liste, unabhängig von Versandfreigabe", () => {
    const ctx = baseCtx({ suppression: new Set(["kontakt@beispiel-firma.example"]) });
    const result = evaluateLead(makeLead(), ctx);
    expect(result).toMatchObject({ decision: STATUS.SUPPRESSED, reason: "SUPPRESSION_LIST" });
  });

  it("respektiert Opt-out-Status=opted_out", () => {
    const result = evaluateLead(makeLead({ optOutStatus: "opted_out" }), baseCtx());
    expect(result).toMatchObject({ decision: STATUS.OPTOUT, reason: "OPT_OUT_STATUS" });
  });

  it("überspringt bereits versendete Leads (Idempotenz-Grundlage)", () => {
    const ctx = baseCtx({
      state: { leads: { "HSB-TEST-00001": { status: STATUS.SENT } } },
    });
    const result = evaluateLead(makeLead(), ctx);
    expect(result).toMatchObject({ decision: STATUS.SKIPPED, reason: "ALREADY_SENT" });
  });

  it("verlangt eine passende Kampagne, Template, Flyer und Owner", () => {
    expect(evaluateLead(makeLead({ campaignId: "andere-kampagne" }), baseCtx())).toMatchObject({
      reason: "CAMPAIGN_MISMATCH",
    });
    expect(evaluateLead(makeLead({ emailTemplateId: "" }), baseCtx())).toMatchObject({
      reason: "TEMPLATE_MISSING",
    });
    expect(evaluateLead(makeLead({ flyerUrl: "" }), baseCtx())).toMatchObject({
      reason: "FLYER_MISSING",
    });
    expect(evaluateLead(makeLead({ owner: "" }), baseCtx())).toMatchObject({
      reason: "SENDER_UNAVAILABLE",
    });
  });
});

describe("engine.mjs — planBatch / executeBatch (dry-run)", () => {
  it("simuliert einen Batch ohne den Provider aufzurufen und ohne SENT zu setzen", async () => {
    const leads = [makeLead(), makeLead({ leadId: "HSB-TEST-00002", email: "zweite@beispiel-firma.example" })];
    const ctx = baseCtx();
    const { ready, byDecision } = planBatch(leads, ctx, 10);
    expect(byDecision[STATUS.READY]).toBe(2);

    let providerCalled = false;
    const spyProvider = { name: "spy", async send() { providerCalled = true; return { ok: true }; } };
    const results = await executeBatch(ready, { state: ctx.state, provider: spyProvider, dryRun: true, campaignId: "kaltakquise-test", runId: "test-run" });

    expect(providerCalled).toBe(false);
    expect(results.every((r) => r.status === STATUS.QUEUED)).toBe(true);
    expect(ctx.state.leads["HSB-TEST-00001"].status).toBe(STATUS.QUEUED);
  });

  it("respektiert das Limit nur für die READY-Menge, nicht für die Auswertung", () => {
    const leads = [makeLead(), makeLead({ leadId: "HSB-TEST-00002", email: "zweite@beispiel-firma.example" })];
    const { evaluations, ready } = planBatch(leads, baseCtx(), 1);
    expect(evaluations).toHaveLength(2);
    expect(ready).toHaveLength(1);
  });
});

describe("engine.mjs — executeBatch (realer Versand über Provider)", () => {
  it("markiert einen Lead nach erfolgreichem Provider-Send als SENT mit Message-ID", async () => {
    const leads = [makeLead()];
    const ctx = baseCtx();
    const { ready } = planBatch(leads, ctx, 10);
    const provider = { name: "fake", async send() { return { ok: true, messageId: "msg-123" }; } };

    const results = await executeBatch(ready, { state: ctx.state, provider, dryRun: false, campaignId: "kaltakquise-test", runId: "run-1" });

    expect(results).toEqual([{ key: "HSB-TEST-00001", status: STATUS.SENT, messageId: "msg-123" }]);
    expect(ctx.state.leads["HSB-TEST-00001"]).toMatchObject({
      status: STATUS.SENT,
      providerMessageId: "msg-123",
      attempts: 1,
      followUpState: "PENDING",
    });
  });

  it("markiert einen Lead nach fehlgeschlagenem Provider-Send als FAILED mit Fehlertext und erhöhtem Attempt-Count", async () => {
    const leads = [makeLead()];
    const ctx = baseCtx();
    const { ready } = planBatch(leads, ctx, 10);
    const provider = { name: "fake-fail", async send() { return { ok: false, error: "SMTP_TIMEOUT" }; } };

    const results = await executeBatch(ready, { state: ctx.state, provider, dryRun: false, campaignId: "kaltakquise-test", runId: "run-1" });

    expect(results).toEqual([{ key: "HSB-TEST-00001", status: STATUS.FAILED, error: "SMTP_TIMEOUT" }]);
    expect(ctx.state.leads["HSB-TEST-00001"].attempts).toBe(1);
  });

  it("fängt eine Provider-Exception ab, statt den Lauf abzubrechen", async () => {
    const leads = [makeLead()];
    const ctx = baseCtx();
    const { ready } = planBatch(leads, ctx, 10);
    const provider = { name: "throws", async send() { throw new Error("boom"); } };

    const results = await executeBatch(ready, { state: ctx.state, provider, dryRun: false, campaignId: "kaltakquise-test", runId: "run-1" });
    expect(results[0].status).toBe(STATUS.FAILED);
    expect(results[0].error).toContain("PROVIDER_EXCEPTION");
  });

  it("verhindert Doppelversand: ein zweiter Lauf über denselben Lead sendet nicht erneut", async () => {
    const leads = [makeLead()];
    const provider = { name: "counting", calls: 0, async send() { this.calls++; return { ok: true, messageId: `msg-${this.calls}` }; } };
    const state = { leads: {} as Record<string, any> };

    // Erster Lauf: sendet.
    let ctx = baseCtx({ state });
    let { ready } = planBatch(leads, ctx, 10);
    await executeBatch(ready, { state, provider, dryRun: false, campaignId: "kaltakquise-test", runId: "run-1" });
    expect(provider.calls).toBe(1);
    expect(state.leads["HSB-TEST-00001"].status).toBe(STATUS.SENT);

    // Zweiter Lauf (z. B. erneuter CLI-Aufruf): evaluateLead greift ALREADY_SENT,
    // planBatch liefert daher keine READY-Kandidaten mehr für diesen Lead.
    ctx = baseCtx({ state });
    ({ ready } = planBatch(leads, ctx, 10));
    expect(ready).toHaveLength(0);
    await executeBatch(ready, { state, provider, dryRun: false, campaignId: "kaltakquise-test", runId: "run-2" });
    expect(provider.calls).toBe(1); // unverändert — kein zweiter Versand
  });
});

describe("engine.mjs — resume", () => {
  it("findResumable liefert Leads, die in einem abgebrochenen Lauf bei SENDING hängen geblieben sind", () => {
    const state = {
      leads: {
        "HSB-TEST-00001": { status: STATUS.SENDING },
        "HSB-TEST-00002": { status: STATUS.SENT },
        "HSB-TEST-00003": { status: STATUS.FAILED },
      },
    };
    expect(findResumable(state)).toEqual(["HSB-TEST-00001"]);
  });
});

describe("engine.mjs — summarizeState", () => {
  it("aggregiert den State nach Status", () => {
    const state = {
      leads: {
        a: { status: STATUS.SENT },
        b: { status: STATUS.SENT },
        c: { status: STATUS.FAILED },
      },
    };
    expect(summarizeState(state)).toEqual({ [STATUS.SENT]: 2, [STATUS.FAILED]: 1 });
  });
});

describe("providers.mjs", () => {
  it("der noop-Provider schlägt jeden echten Sendeversuch kontrolliert fehl", async () => {
    const result = await noopProvider.send(makeLead(), { campaignId: "x" });
    expect(result.ok).toBe(false);
    expect(result.error).toContain("NO_PROVIDER_CONFIGURED");
  });

  it("resolveProvider wirft für unbekannte/nicht konfigurierte Provider, statt einen Fake-Erfolg zu liefern", () => {
    expect(() => resolveProvider("smartlead")).toThrow(/UNKNOWN_OR_UNCONFIGURED_PROVIDER/);
  });

  it("resolveProvider liefert ohne Angabe den sicheren noop-Default", () => {
    expect(resolveProvider(undefined)).toBe(noopProvider);
  });
});
