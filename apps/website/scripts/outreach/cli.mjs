#!/usr/bin/env node
// Operator-CLI für die Outreach-Dispatch-Engine. Ein-Kommando-Bedienung,
// keine Web-App (siehe Masterauftrag, Abschnitt "BEDIENUNG").
//
// Nutzung:
//   node scripts/outreach/cli.mjs dry-run   --owner=joel --limit=25 --campaign=kaltakquise-2026-q3
//   node scripts/outreach/cli.mjs test-batch --owner=joel --count=5  --campaign=kaltakquise-2026-q3
//   node scripts/outreach/cli.mjs batch     --owner=joel --count=25 --campaign=kaltakquise-2026-q3 --approved
//   node scripts/outreach/cli.mjs resume
//   node scripts/outreach/cli.mjs status
//   node scripts/outreach/cli.mjs sync-airtable --owner=all
//
// Airtable: dry-run/test-batch/batch pushen den Status automatisch (best-
// effort, no-op ohne AIRTABLE_API_KEY) in die geteilte Live-Ansicht für
// Joel/Jordi (Base "HSB Outreach CRM"). Details: scripts/outreach/README.md.
//
// Quelle: data/lead-import/output/final_2026-08-11/HSB_OUTREACH_{READY,JOEL,JORDI}_2026-08-11.csv
// (gitignored, siehe docs/crm/CRM_DATENQUELLE_WAHRHEIT.md). Diese Dateien
// tragen bereits Email_Template_ID/Flyer_URL/Kampagne_ID — nicht neu bauen.
import { existsSync, readFileSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { join } from "node:path";
import { parseCsvRecords } from "./csv.mjs";
import { evaluateLead, executeBatch, findResumable, planBatch, STATUS, summarizeState } from "./engine.mjs";
import { loadState, loadSuppression, saveState, writeRunLog } from "./state.mjs";
import { resolveProvider } from "./providers.mjs";
import { readAirtableEnv, syncLeadsToAirtable, recordSyncResult, readLastSyncResult } from "./airtable.mjs";

const SOURCE_DIR = join("data", "lead-import", "output", "final_2026-08-11");
const SOURCE_FILES = {
  all: join(SOURCE_DIR, "HSB_OUTREACH_READY_2026-08-11.csv"),
  joel: join(SOURCE_DIR, "HSB_OUTREACH_JOEL_2026-08-11.csv"),
  jordi: join(SOURCE_DIR, "HSB_OUTREACH_JORDI_2026-08-11.csv"),
};

function parseArgs(argv) {
  const [command, ...rest] = argv;
  const flags = {};
  for (const arg of rest) {
    const m = arg.match(/^--([^=]+)(?:=(.*))?$/);
    if (m) flags[m[1]] = m[2] ?? true;
  }
  return { command, flags };
}

function mapRecordToLead(record) {
  return {
    leadId: record["Lead-ID"],
    company: record["Firma"], // wird nie geloggt, nur intern gehalten
    email: record["E-Mail"],
    tier: record["Tier"],
    versandfreigabe: record["Versandfreigabe"],
    optOutStatus: record["Opt-out-Status"],
    owner: record["Verantwortlicher"],
    campaignId: record["Kampagne_ID"],
    emailTemplateId: record["Email_Template_ID"],
    flyerUrl: record["Flyer_URL"],
    landingUrl: record["Landing_URL"],
  };
}

function loadLeads(sourceKey) {
  const path = SOURCE_FILES[sourceKey];
  if (!path) {
    throw new Error(`UNKNOWN_SOURCE: "${sourceKey}". Erlaubt: ${Object.keys(SOURCE_FILES).join(", ")}`);
  }
  if (!existsSync(path)) {
    throw new Error(
      `SOURCE_NOT_FOUND: ${path}. Erwartet aus docs/crm/CRM_FINALIZATION_2026-08-11.md — ` +
        `wurde die lokale Lead-Ablage verschoben oder gelöscht?`,
    );
  }
  const text = readFileSync(path, "utf-8");
  const { records } = parseCsvRecords(text, ",");
  return records.map(mapRecordToLead);
}

// Best-effort: pusht den aktuellen Status aller geladenen Leads nach
// Airtable (geteilte Live-Ansicht für Joel/Jordi). Läuft ohne
// AIRTABLE_API_KEY klaglos leer (kein Blocker für lokale Läufe), meldet
// aber klar, dass Airtable nicht konfiguriert ist.
async function trySyncAirtable(leads, state) {
  const envConfig = readAirtableEnv();
  if (!envConfig) {
    console.log("Airtable-Sync übersprungen: AIRTABLE_API_KEY nicht gesetzt (siehe scripts/outreach/README.md).");
    return;
  }
  const result = await syncLeadsToAirtable(leads, state, envConfig);
  recordSyncResult(result);
  if (result.errors?.length) {
    console.log(`Airtable-Sync: ${result.updated} aktualisiert, ${result.errors.length} Batch(es) fehlgeschlagen.`);
  } else {
    console.log(`Airtable-Sync: ${result.updated} Leads aktualisiert (${result.batchCount} Batches).`);
  }
}

// Nur Aggregate loggen — niemals E-Mail/Firma/Ansprechpartner in Konsole
// oder Run-Log ausgeben (PII_IN_GIT/PII-Ausgabe-Verbot).
function printDecisionSummary(byDecision, total) {
  console.log(`Ausgewertet: ${total} Leads`);
  for (const [decision, count] of Object.entries(byDecision).sort()) {
    console.log(`  ${decision}: ${count}`);
  }
}

async function cmdPlanOnly(flags, { dryRun, count }) {
  const sourceKey = (flags.owner || "all").toLowerCase();
  const leads = loadLeads(sourceKey);
  const state = loadState();
  const suppression = loadSuppression();
  const campaignId = flags.campaign;
  const limit = count ?? (flags.limit ? Number(flags.limit) : undefined);

  const { evaluations, byDecision, ready } = planBatch(leads, { state, suppression, campaignId }, limit);
  printDecisionSummary(byDecision, evaluations.length);
  console.log(`READY (im gewählten Limit): ${ready.length}`);

  const runId = `${dryRun ? "dryrun" : "testbatch"}-${new Date().toISOString().replace(/[:.]/g, "-")}-${randomUUID().slice(0, 8)}`;
  const provider = resolveProvider("noop");
  const results = await executeBatch(ready, { state, provider, dryRun: true, campaignId, runId });
  saveState(state);
  writeRunLog(runId, { runId, mode: dryRun ? "dry-run" : "test-batch", flags, byDecision, resultCount: results.length });
  console.log(`Simuliert (QUEUED, kein echter Versand): ${results.length}. Run-ID: ${runId}`);
  await trySyncAirtable(leads, state);
}

async function cmdBatch(flags) {
  const sourceKey = (flags.owner || "all").toLowerCase();
  const leads = loadLeads(sourceKey);
  const state = loadState();
  const suppression = loadSuppression();
  const campaignId = flags.campaign;
  const limit = flags.count ? Number(flags.count) : undefined;
  const approved = Boolean(flags.approved);

  const { evaluations, byDecision, ready } = planBatch(leads, { state, suppression, campaignId }, limit);
  printDecisionSummary(byDecision, evaluations.length);

  if (!approved) {
    console.log(
      "READY_TO_SEND=BLOCKED — kein --approved-Flag gesetzt. Kein Versand ohne explizite Freigabe " +
        "(sicherer Default, siehe Masterauftrag 'PRODUKTIVER VERSAND').",
    );
    saveState(state);
    await trySyncAirtable(leads, state);
    return;
  }

  const runId = `batch-${new Date().toISOString().replace(/[:.]/g, "-")}-${randomUUID().slice(0, 8)}`;
  const provider = resolveProvider(flags.provider);
  const results = await executeBatch(ready, { state, provider, dryRun: false, campaignId, runId });
  saveState(state);

  const sent = results.filter((r) => r.status === STATUS.SENT).length;
  const failed = results.filter((r) => r.status === STATUS.FAILED).length;
  writeRunLog(runId, { runId, mode: "batch", flags: { ...flags, provider: provider.name }, byDecision, sent, failed });

  console.log(`Versucht: ${results.length} · Versendet: ${sent} · Fehlgeschlagen: ${failed}. Run-ID: ${runId}`);
  if (sent === 0 && ready.length > 0) {
    console.log(
      `READY_TO_SEND=BLOCKED — READY-Kandidaten vorhanden (${ready.length}), aber Provider "${provider.name}" ` +
        "hat keinen echten Versandweg (siehe scripts/outreach/providers.mjs).",
    );
  }
}

function cmdResume() {
  const state = loadState();
  const stuck = findResumable(state);
  console.log(`Hängende Leads (Status SENDING aus abgebrochenem Lauf): ${stuck.length}`);
  if (stuck.length > 0) {
    for (const key of stuck) {
      state.leads[key] = { ...state.leads[key], status: STATUS.FAILED, error: "RESUME_RESET_FROM_SENDING" };
    }
    saveState(state);
    console.log("Zurückgesetzt auf FAILED — erneuter batch-Lauf wird sie automatisch erneut versuchen (kein Doppelversand, da status != SENT).");
  }
}

async function cmdSyncAirtable(flags) {
  const sourceKey = (flags.owner || "all").toLowerCase();
  const leads = loadLeads(sourceKey);
  const state = loadState();
  await trySyncAirtable(leads, state);
  const last = readLastSyncResult();
  if (last) console.log(`Letzter Sync: ${last.at} · aktualisiert: ${last.updated ?? "n/a"} · Fehler: ${last.errors?.length ?? 0}`);
}

function cmdStatus() {
  const state = loadState();
  const counts = summarizeState(state);
  console.log("Versandstatus (gesamter State):");
  for (const [status, count] of Object.entries(counts).sort()) {
    console.log(`  ${status}: ${count}`);
  }
  if (Object.keys(counts).length === 0) console.log("  (leer — noch kein Lauf ausgeführt)");
}

async function main() {
  const { command, flags } = parseArgs(process.argv.slice(2));
  switch (command) {
    case "dry-run":
      await cmdPlanOnly(flags, { dryRun: true });
      break;
    case "test-batch":
      await cmdPlanOnly(flags, { dryRun: true, count: flags.count ? Number(flags.count) : 5 });
      break;
    case "batch":
      await cmdBatch(flags);
      break;
    case "resume":
      cmdResume();
      break;
    case "status":
      cmdStatus();
      break;
    case "sync-airtable":
      await cmdSyncAirtable(flags);
      break;
    default:
      console.error(
        "Nutzung: node scripts/outreach/cli.mjs <dry-run|test-batch|batch|resume|status|sync-airtable> " +
          "[--owner=all|joel|jordi] [--campaign=ID] [--count=N] [--limit=N] [--approved]",
      );
      process.exit(1);
  }
}

main().catch((err) => {
  console.error(`FEHLER: ${err.message}`);
  process.exit(1);
});
