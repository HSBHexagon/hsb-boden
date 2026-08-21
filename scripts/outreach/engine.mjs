// Kern der Outreach-Dispatch-Engine. Bewusst reine Funktionen ohne Datei-I/O,
// damit sie ohne echte Lead-Dateien (PII) getestet werden können — siehe
// tests/outreach-engine.test.ts, das ausschließlich mit synthetischen
// Fixtures arbeitet.
import { createHash } from "node:crypto";
//
// Statusmodell (aus dem Masterauftrag übernommen, an bestehende
// `Send_Status`-Spalte angelehnt):
export const STATUS = Object.freeze({
  READY: "READY",
  QUEUED: "QUEUED",
  SENDING: "SENDING",
  SENT: "SENT",
  FAILED: "FAILED",
  BOUNCED: "BOUNCED",
  SUPPRESSED: "SUPPRESSED",
  OPTOUT: "OPTOUT",
  SKIPPED: "SKIPPED",
});

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Die Quelldaten haben bereits eine stabile, eindeutige Lead-ID
// (`HSB-20260708-00001`-Format, siehe docs/crm/CRM_DATENQUELLE_WAHRHEIT.md).
// Diese wird als kanonischer Primärschlüssel übernommen statt eine neue ID
// zu erfinden — vermeidet eine zweite parallele ID-Wahrheit.
export function leadKey(lead) {
  const id = (lead.leadId || "").trim();
  if (id) return id;
  // Fallback nur falls eine Quelle ausnahmsweise keine Lead-ID mitbringt.
  return `EMAIL:${(lead.email || "").trim().toLowerCase()}`;
}

export function isValidEmail(email) {
  return EMAIL_RE.test((email || "").trim());
}

/**
 * Bewertet einen einzelnen Lead gegen alle Versandvoraussetzungen.
 * Gibt eine Entscheidung zurück, niemals einen Seiteneffekt.
 *
 * @param {object} lead - normalisierter Lead (siehe cli.mjs mapRecordToLead)
 * @param {object} ctx
 * @param {object} ctx.state - { leads: { [leadKey]: {...} } }
 * @param {Set<string>} ctx.suppression - lowercase E-Mails
 * @param {string} ctx.campaignId - angeforderte Kampagne, oder undefined
 */
export function evaluateLead(lead, ctx) {
  const { state, suppression, campaignId } = ctx;
  const key = leadKey(lead);
  const email = (lead.email || "").trim();

  if (!isValidEmail(email)) {
    return { key, decision: STATUS.SKIPPED, reason: "INVALID_EMAIL" };
  }
  if (suppression.has(email.toLowerCase())) {
    return { key, decision: STATUS.SUPPRESSED, reason: "SUPPRESSION_LIST" };
  }
  if ((lead.optOutStatus || "").toLowerCase() === "opted_out") {
    return { key, decision: STATUS.OPTOUT, reason: "OPT_OUT_STATUS" };
  }
  const existing = state.leads[key];
  if (existing && existing.status === STATUS.SENT) {
    return { key, decision: STATUS.SKIPPED, reason: "ALREADY_SENT" };
  }
  if ((lead.versandfreigabe || "").toLowerCase() !== "yes") {
    return { key, decision: STATUS.SKIPPED, reason: "VERSANDFREIGABE_NOT_YES" };
  }
  if (campaignId && (lead.campaignId || "") !== campaignId) {
    return { key, decision: STATUS.SKIPPED, reason: "CAMPAIGN_MISMATCH" };
  }
  if (!lead.emailTemplateId) {
    return { key, decision: STATUS.SKIPPED, reason: "TEMPLATE_MISSING" };
  }
  if (!lead.flyerUrl) {
    return { key, decision: STATUS.SKIPPED, reason: "FLYER_MISSING" };
  }
  if (!lead.owner) {
    return { key, decision: STATUS.SKIPPED, reason: "SENDER_UNAVAILABLE" };
  }
  return { key, decision: STATUS.READY, reason: null };
}

/**
 * Wertet alle Leads aus und trennt in READY / nicht-READY. `limit`
 * beschränkt nur die READY-Menge (Batch-Größe), nicht die Auswertung selbst
 * — Zähldistributionen sollen immer den vollen Bestand widerspiegeln.
 */
export function planBatch(leads, ctx, limit) {
  const evaluations = leads.map((lead) => ({ lead, evaluation: evaluateLead(lead, ctx) }));
  /** @type {Record<string, number>} */
  const byDecision = {};
  for (const { evaluation } of evaluations) {
    byDecision[evaluation.decision] = (byDecision[evaluation.decision] || 0) + 1;
  }
  const ready = evaluations.filter((e) => e.evaluation.decision === STATUS.READY);
  return {
    evaluations,
    byDecision,
    ready: typeof limit === "number" ? ready.slice(0, limit) : ready,
  };
}

/**
 * Führt einen Batch aus. Bei dryRun=true wird kein Provider aufgerufen und
 * kein Lead auf SENT gesetzt — nur QUEUED zur Simulation. Idempotent: ein
 * Lead, der laut state bereits SENT ist, wird nicht erneut verarbeitet
 * (Race-Schutz zusätzlich zu evaluateLead, falls state zwischen planBatch
 * und executeBatch verändert wurde).
 */
export async function executeBatch(readyItems, { state, provider, dryRun, campaignId, runId, now = () => new Date().toISOString() }) {
  const results = [];
  for (const { lead, evaluation } of readyItems) {
    const key = evaluation.key;
    const prior = state.leads[key] || { attempts: 0, status: STATUS.READY };

    if (prior.status === STATUS.SENT) {
      results.push({ key, status: STATUS.SKIPPED, reason: "ALREADY_SENT_RACE" });
      continue;
    }

    if (dryRun) {
      state.leads[key] = {
        ...prior,
        status: STATUS.QUEUED,
        campaignId,
        dryRun: true,
        lastRunId: runId,
        lastAttemptAt: now(),
      };
      results.push({ key, status: STATUS.QUEUED, dryRun: true });
      continue;
    }

    const attempt = (prior.attempts || 0) + 1;
    const idempotencyKey = createHash("sha256").update(`${key}_${campaignId || "default"}_${attempt}`).digest("hex");
    state.leads[key] = { ...prior, status: STATUS.SENDING, campaignId, lastAttemptAt: now(), lastRunId: runId, idempotencyKey };

    let sendResult;
    try {
      sendResult = await provider.send(lead, { campaignId, idempotencyKey });
    } catch (err) {
      sendResult = { ok: false, error: `PROVIDER_EXCEPTION: ${err.message}` };
    }

    if (sendResult.ok) {
      state.leads[key] = {
        ...state.leads[key],
        status: STATUS.SENT,
        attempts: attempt,
        sentAt: now(),
        providerMessageId: sendResult.messageId ?? null,
        error: null,
        followUpState: "PENDING",
        nextAction: "FOLLOW_UP_14D",
      };
      results.push({ key, status: STATUS.SENT, messageId: sendResult.messageId ?? null });
    } else {
      state.leads[key] = {
        ...state.leads[key],
        status: STATUS.FAILED,
        attempts: attempt,
        error: sendResult.error,
      };
      results.push({ key, status: STATUS.FAILED, error: sendResult.error });
    }
  }
  return results;
}

/** Leads, deren letzter Lauf abgebrochen wurde (Status SENDING/QUEUED hängen geblieben). */
export function findResumable(state) {
  return Object.entries(state.leads)
    .filter(([, v]) => v.status === STATUS.SENDING)
    .map(([key]) => key);
}

export function summarizeState(state) {
  const counts = {};
  for (const v of Object.values(state.leads)) {
    counts[v.status] = (counts[v.status] || 0) + 1;
  }
  return counts;
}
