// Persistenz für den Versandstatus. Liegt unter data/lead-import/output/,
// also per .gitignore Zeile 21 vollständig von Git ausgeschlossen (siehe
// docs/crm/CRM_DATENQUELLE_WAHRHEIT.md) — PII (E-Mail etc. steckt nur
// indirekt über die Lead-ID im State, keine Klartext-Kontaktdaten).
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

export const DISPATCH_DIR = join("data", "lead-import", "output", "dispatch-state");
export const STATE_PATH = join(DISPATCH_DIR, "state.json");
export const SUPPRESSION_PATH = join(DISPATCH_DIR, "suppression.json");
export const RUNS_DIR = join(DISPATCH_DIR, "runs");

export function loadState(path = STATE_PATH) {
  if (!existsSync(path)) return { version: 1, leads: {} };
  return JSON.parse(readFileSync(path, "utf-8"));
}

export function saveState(state, path = STATE_PATH) {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, JSON.stringify(state, null, 2) + "\n", "utf-8");
}

export function loadSuppression(path = SUPPRESSION_PATH) {
  if (!existsSync(path)) return new Set();
  const list = JSON.parse(readFileSync(path, "utf-8"));
  return new Set(list.map((e) => String(e).trim().toLowerCase()));
}

export function saveSuppression(set, path = SUPPRESSION_PATH) {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, JSON.stringify([...set].sort(), null, 2) + "\n", "utf-8");
}

/** Audit-Log pro Lauf. Enthält nur Aggregate/Lead-IDs, keine E-Mail-Adressen. */
export function writeRunLog(runId, payload, dir = RUNS_DIR) {
  mkdirSync(dir, { recursive: true });
  const path = join(dir, `${runId}.json`);
  writeFileSync(path, JSON.stringify(payload, null, 2) + "\n", "utf-8");
  return path;
}
