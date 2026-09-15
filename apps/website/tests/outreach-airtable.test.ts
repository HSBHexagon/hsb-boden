import { describe, expect, it, vi } from "vitest";
import {
  buildAirtableFields,
  chunk,
  readAirtableEnv,
  syncLeadsToAirtable,
  upsertBatch,
} from "../scripts/outreach/airtable.mjs";
import { STATUS } from "../scripts/outreach/engine.mjs";

function makeLead(overrides = {}) {
  return {
    leadId: "HSB-TEST-00001",
    company: "Beispiel GmbH",
    email: "kontakt@beispiel-firma.example",
    tier: "A",
    owner: "Joel Cherino Diaz",
    campaignId: "kaltakquise-test",
    ...overrides,
  };
}

describe("airtable.mjs — buildAirtableFields (rein, kein I/O)", () => {
  it("mappt einen unbekannten Lead (kein State-Eintrag) auf Status SKIPPED ohne Skip_Grund-Feld", () => {
    const fields = buildAirtableFields(makeLead(), undefined);
    expect(fields.Status).toBe(STATUS.SKIPPED);
    expect(fields).not.toHaveProperty("Skip_Grund");
    expect(fields["Lead-ID"]).toBe("HSB-TEST-00001");
    expect(fields.Firma).toBe("Beispiel GmbH");
    expect(fields.Verantwortlicher).toBe("Joel");
    expect(fields.Tier).toBe("A");
  });

  it("übernimmt Status, Fehler und Attempts aus dem State-Eintrag", () => {
    const leadState = { status: STATUS.FAILED, error: "SMTP_TIMEOUT", attempts: 2 };
    const fields = buildAirtableFields(makeLead(), leadState);
    expect(fields.Status).toBe(STATUS.FAILED);
    expect(fields.Skip_Grund).toBe("SMTP_TIMEOUT");
    expect(fields.Fehler).toBe("SMTP_TIMEOUT");
    expect(fields.Attempts).toBe(2);
  });

  it("erkennt Jordi als Verantwortlichen unabhängig von Groß-/Kleinschreibung", () => {
    const fields = buildAirtableFields(makeLead({ owner: "jordi post" }), undefined);
    expect(fields.Verantwortlicher).toBe("Jordi");
  });

  it("fällt auf Unassigned zurück, wenn kein Owner erkennbar ist", () => {
    const fields = buildAirtableFields(makeLead({ owner: "" }), undefined);
    expect(fields.Verantwortlicher).toBe("Unassigned");
  });

  it("lässt ungültige Tier-Werte weg statt sie zu erzwingen", () => {
    const fields = buildAirtableFields(makeLead({ tier: "" }), undefined);
    expect(fields).not.toHaveProperty("Tier");
  });

  it("enthält niemals E-Mail, Telefon oder Ansprechpartner-Felder (Status-only-Scope)", () => {
    const fields = buildAirtableFields(makeLead(), { status: STATUS.SENT });
    const keys = Object.keys(fields).join(",").toLowerCase();
    expect(keys).not.toContain("email");
    expect(keys).not.toContain("telefon");
    expect(keys).not.toContain("ansprechpartner");
  });
});

describe("airtable.mjs — chunk", () => {
  it("teilt ein Array in Batches der angegebenen Größe, letzter Batch kann kleiner sein", () => {
    const result = chunk([1, 2, 3, 4, 5], 2);
    expect(result).toEqual([[1, 2], [3, 4], [5]]);
  });
});

describe("airtable.mjs — readAirtableEnv", () => {
  it("gibt null zurück, wenn AIRTABLE_API_KEY fehlt (Sync bleibt optional/no-op)", () => {
    expect(readAirtableEnv({})).toBeNull();
  });

  it("nutzt die fest hinterlegte Base/Table-ID als Default, wenn nicht überschrieben", () => {
    const cfg = readAirtableEnv({ AIRTABLE_API_KEY: "pat_test" });
    expect(cfg).toMatchObject({ apiKey: "pat_test" });
    expect(cfg?.baseId).toMatch(/^app/);
    expect(cfg?.tableId).toMatch(/^tbl/);
  });
});

describe("airtable.mjs — upsertBatch (gemockter fetch, kein echter Netzwerkzugriff)", () => {
  it("sendet einen PATCH-Request mit performUpsert über Lead-ID", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ records: [{ id: "rec1" }] }),
    });
    const result = await upsertBatch(
      [{ fields: { "Lead-ID": "HSB-TEST-00001" } }],
      { apiKey: "pat_test", baseId: "appXXXXXXXXXXXXXXX", tableId: "tblXXXXXXXXXXXXXXX" },
      fetchMock,
    );
    expect(result.records).toHaveLength(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toContain("appXXXXXXXXXXXXXXX/tblXXXXXXXXXXXXXXX");
    expect(options.method).toBe("PATCH");
    expect(options.headers.Authorization).toBe("Bearer pat_test");
    const body = JSON.parse(options.body);
    expect(body.performUpsert).toEqual({ fieldsToMergeOn: ["Lead-ID"] });
  });

  it("wirft eine klare Fehlermeldung bei einer fehlgeschlagenen Antwort", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: false, status: 422, text: async () => "INVALID_FIELD" });
    await expect(
      upsertBatch([{ fields: {} }], { apiKey: "x", baseId: "appX", tableId: "tblX" }, fetchMock),
    ).rejects.toThrow(/AIRTABLE_UPSERT_FAILED.*422/);
  });
});

describe("airtable.mjs — syncLeadsToAirtable", () => {
  it("überspringt den Sync ohne Konfiguration, statt einen Fehler zu werfen", async () => {
    const result = await syncLeadsToAirtable([makeLead()], { leads: {} }, null);
    expect(result).toEqual({ skipped: true, reason: "AIRTABLE_NOT_CONFIGURED" });
  });

  it("batcht 12 Leads in zwei Requests (10 + 2) und zählt aktualisierte Records", async () => {
    const leads = Array.from({ length: 12 }, (_, i) => makeLead({ leadId: `HSB-TEST-${String(i).padStart(5, "0")}` }));
    const fetchMock = vi.fn().mockImplementation(async (_url, options) => {
      const body = JSON.parse(options.body);
      return { ok: true, json: async () => ({ records: body.records.map(() => ({ id: "recX" })) }) };
    });
    const result = await syncLeadsToAirtable(leads, { leads: {} }, { apiKey: "x", baseId: "appX", tableId: "tblX" }, fetchMock);
    expect(result.skipped).toBe(false);
    expect(result.batchCount).toBe(2);
    expect(result.updated).toBe(12);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("sammelt Fehler pro Batch, statt den gesamten Sync abzubrechen", async () => {
    const leads = [makeLead()];
    const fetchMock = vi.fn().mockResolvedValue({ ok: false, status: 500, text: async () => "boom" });
    const result = await syncLeadsToAirtable(leads, { leads: {} }, { apiKey: "x", baseId: "appX", tableId: "tblX" }, fetchMock);
    expect(result.errors).toHaveLength(1);
    expect(result.updated).toBe(0);
  });
});
