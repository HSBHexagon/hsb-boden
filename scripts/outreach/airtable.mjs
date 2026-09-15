// Geteilte, live-aktualisierende CRM-Ansicht für Joel + Jordi in Airtable
// (Base "HSB Outreach CRM", angelegt 2026-08-14 — Single Source of Action
// laut ObsidianVault/brain/01_core/STORAGE_ROLES.md). Status-only: nur
// Firmen-/Verkaufsdaten + Versandstatus, KEINE Ansprechpartner/E-Mail/
// Telefon — die bleiben ausschließlich lokal (gitignored).
//
// Nutzt die reguläre Airtable-REST-API direkt (kein SDK, keine neue
// package.json-Dependency). Erfordert einen vom Nutzer selbst erzeugten
// Personal Access Token (Hard Constraint: Credentials macht der Nutzer
// selbst) — siehe README.md.
import { DISPATCH_DIR } from "./state.mjs";
import { join } from "node:path";
import { existsSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";

export const AIRTABLE_BASE_ID = "appPRPqNwpt615PAW";
export const AIRTABLE_TABLE_ID = "tble6KY1SaIx0RHaX";
const API_ROOT = "https://api.airtable.com/v0";
const CHUNK_SIZE = 10; // Airtable-REST-Limit pro Update-/Upsert-Request.

/** @param {Record<string, string|undefined>} [env] */
export function readAirtableEnv(env = process.env) {
  const apiKey = env.AIRTABLE_API_KEY;
  const baseId = env.AIRTABLE_BASE_ID || AIRTABLE_BASE_ID;
  const tableId = env.AIRTABLE_TABLE_ID || AIRTABLE_TABLE_ID;
  if (!apiKey) return null;
  return { apiKey, baseId, tableId };
}

/** Reine Mapping-Funktion, kein I/O — testbar ohne Netzwerk. */
export function buildAirtableFields(lead, leadState) {
  /** @type {Record<string, string|number>} */
  const fields = {
    "Lead-ID": lead.leadId,
    Firma: lead.company,
    Verantwortlicher: lead.owner && /joel/i.test(lead.owner) ? "Joel" : lead.owner && /jordi/i.test(lead.owner) ? "Jordi" : "Unassigned",
    Kampagne_ID: lead.campaignId || "",
    Status: (leadState && leadState.status) || "SKIPPED",
    Attempts: (leadState && leadState.attempts) || 0,
  };
  if (lead.tier === "A" || lead.tier === "B" || lead.tier === "C") fields.Tier = lead.tier;
  if (leadState?.error) fields.Skip_Grund = leadState.error;
  if (leadState?.sentAt) fields.Sent_At = leadState.sentAt;
  if (leadState?.providerMessageId) fields.Provider_Message_Id = leadState.providerMessageId;
  if (leadState?.error) fields.Fehler = leadState.error;
  if (leadState?.followUpState) fields.Follow_Up_State = leadState.followUpState;
  if (leadState?.nextAction) fields.Naechste_Aktion = leadState.nextAction;
  if (leadState?.lastRunId) fields.Letzter_Lauf_Run_Id = leadState.lastRunId;
  fields.Zuletzt_Aktualisiert = new Date().toISOString();
  return fields;
}

export function chunk(array, size) {
  const out = [];
  for (let i = 0; i < array.length; i += size) out.push(array.slice(i, i + size));
  return out;
}

/** Ein Upsert-Batch (PATCH, performUpsert über Lead-ID) — max. 10 Records. */
export async function upsertBatch(records, { apiKey, baseId, tableId }, fetchImpl = fetch) {
  const res = await fetchImpl(`${API_ROOT}/${baseId}/${tableId}`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
    body: JSON.stringify({ performUpsert: { fieldsToMergeOn: ["Lead-ID"] }, records }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`AIRTABLE_UPSERT_FAILED: HTTP ${res.status} ${text.slice(0, 300)}`);
  }
  return res.json();
}

/**
 * Synchronisiert den aktuellen lokalen Status aller übergebenen Leads nach
 * Airtable. Best-effort: einzelne fehlgeschlagene Batches werden gesammelt,
 * der Lauf bricht nicht komplett ab.
 */
export async function syncLeadsToAirtable(leads, state, envConfig, fetchImpl = fetch) {
  if (!envConfig) {
    return { skipped: true, reason: "AIRTABLE_NOT_CONFIGURED" };
  }
  const records = leads.map((lead) => ({
    fields: buildAirtableFields(lead, state.leads[lead.leadId]),
  }));
  const batches = chunk(records, CHUNK_SIZE);
  let updated = 0;
  const errors = [];
  for (const [i, batch] of batches.entries()) {
    try {
      const result = await upsertBatch(batch, envConfig, fetchImpl);
      updated += (result.records || []).length;
    } catch (err) {
      errors.push({ batchIndex: i, error: err.message });
    }
  }
  return { skipped: false, updated, batchCount: batches.length, errors };
}

// Letzter Sync-Zeitpunkt/-Status, damit `status` ihn anzeigen kann.
const SYNC_LOG_PATH = join(DISPATCH_DIR, "airtable-sync-log.json");

export function recordSyncResult(result, path = SYNC_LOG_PATH) {
  mkdirSync(join(path, ".."), { recursive: true });
  writeFileSync(path, JSON.stringify({ ...result, at: new Date().toISOString() }, null, 2) + "\n", "utf-8");
}

export function readLastSyncResult(path = SYNC_LOG_PATH) {
  if (!existsSync(path)) return null;
  return JSON.parse(readFileSync(path, "utf-8"));
}
