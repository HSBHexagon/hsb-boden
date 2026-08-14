// Provider-Abstraktion für den tatsächlichen Versand.
//
// Live geprüft am 2026-08-14 (get_status auf allen drei angebundenen
// Google-Workspace-MCP-Profilen):
//   - Profil "hsb-boden"   → tatsächlich authentifiziert auf das private Outlook-Konto des
//     Nutzers (PRIVAT! Adresse bewusst nicht im Repo genannt, siehe Hard Constraint)
//   - Profil "cherinodiaz" → dasselbe private Konto
//   - Profil "info"        → ebenfalls dasselbe private Konto (NICHT info@hsb-boden.de)
//   - Profil "cherinojoel" → cherinojoel@gmail.com (das einzige nicht-private, für
//     HSB-CRM bereits etablierte Konto, siehe Memory "HSB Google-Account-Mapping")
// Profilnamen entsprechen NICHT den tatsächlichen Konten — nur "cherinojoel" ist
// laut Hard Constraint überhaupt für HSB-Geschäftsflüsse nutzbar.
//
// DNS-Realzustand (dig, erneut geprüft 2026-08-14, unverändert ggü. 2026-08-11):
// hsb-boden.de NS liegt bei Kasserver, nicht bei Cloudflare (Cloudflare-Account
// "Info@hsb-boden.de's Account" hat 0 Zonen). DKIM auf hsb-boden.de ist inaktiv.
// Das ist für den Gratis-Pfad hier aber irrelevant: `gmailApiProvider` versendet
// über die Gmail-API als echte @gmail.com-Adresse — Google signiert selbst mit
// seinem eigenen DKIM, kein hsb-boden.de-DNS-Eingriff nötig.
//
// Kein Provider hier enthält echte Zugangsdaten. Der Nutzer muss die OAuth-
// Zugangsdaten selbst erzeugen (Hard Constraint: "Echte OAuth-Credentials und
// Token-Rotationen macht der Nutzer selbst") — siehe README.md.

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { DISPATCH_DIR } from "./state.mjs";

export const noopProvider = {
  name: "noop",
  async send(_lead, _opts) {
    return {
      ok: false,
      error:
        "NO_PROVIDER_CONFIGURED: kein Versandtool eingerichtet — Owner-Entscheidung ausstehend " +
        "(siehe docs/crm/CRM_FINALIZATION_2026-08-11.md Abschnitt 6 + 12).",
    };
  },
};

const GMAIL_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token";
const GMAIL_SEND_ENDPOINT = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send";
const QUOTA_PATH = join(DISPATCH_DIR, "gmail-quota.json");

function base64url(str) {
  return Buffer.from(str, "utf-8").toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function buildMime({ fromName, fromEmail, to, subject, body }) {
  const encodedSubject = `=?UTF-8?B?${Buffer.from(subject, "utf-8").toString("base64")}?=`;
  return [
    `From: ${fromName} <${fromEmail}>`,
    `To: ${to}`,
    `Subject: ${encodedSubject}`,
    "MIME-Version: 1.0",
    "Content-Type: text/plain; charset=UTF-8",
    "",
    body,
  ].join("\r\n");
}

function todayKey(now = new Date()) {
  return now.toISOString().slice(0, 10);
}

function readQuota(path) {
  if (!existsSync(path)) return {};
  return JSON.parse(readFileSync(path, "utf-8"));
}

function bumpQuota(path, key) {
  mkdirSync(dirname(path), { recursive: true });
  const quota = readQuota(path);
  quota[key] = (quota[key] || 0) + 1;
  writeFileSync(path, JSON.stringify(quota, null, 2) + "\n", "utf-8");
  return quota[key];
}

async function refreshAccessToken() {
  if (process.env.GMAIL_ACCESS_TOKEN) return process.env.GMAIL_ACCESS_TOKEN;
  const { GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN } = process.env;
  if (!GMAIL_CLIENT_ID || !GMAIL_CLIENT_SECRET || !GMAIL_REFRESH_TOKEN) {
    throw new Error(
      "GMAIL_NOT_CONFIGURED: GMAIL_CLIENT_ID/GMAIL_CLIENT_SECRET/GMAIL_REFRESH_TOKEN (oder GMAIL_ACCESS_TOKEN) " +
        "nicht gesetzt. Der Nutzer muss diese OAuth-Zugangsdaten selbst in der Google Cloud Console erzeugen " +
        "(siehe scripts/outreach/README.md, Abschnitt 'Gratis-Versandweg'). Nie vom Agenten erzeugt/gespeichert.",
    );
  }
  const res = await fetch(GMAIL_TOKEN_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      client_id: GMAIL_CLIENT_ID,
      client_secret: GMAIL_CLIENT_SECRET,
      refresh_token: GMAIL_REFRESH_TOKEN,
      grant_type: "refresh_token",
    }),
  });
  if (!res.ok) throw new Error(`GMAIL_TOKEN_REFRESH_FAILED: HTTP ${res.status}`);
  const data = await res.json();
  return data.access_token;
}

/**
 * Echter, gratis nutzbarer Provider über die Gmail-API einer bereits
 * bestehenden, für HSB legitimen @gmail.com-Adresse (Consumer-Gmail-Quota:
 * ~500 Mails/Tag laut Google-Dokumentation, hier konservativ auf dailyLimit
 * begrenzt). Erfordert `renderTemplate(lead)` → {subject, body}, da die
 * eigentlichen Mail-Texte aktuell nur als Markdown in
 * docs/email/EMAIL_DELIVERABILITY_AND_TEMPLATE_READINESS.md vorliegen und
 * hier bewusst nicht automatisch geparst werden (Risiko, den freigegebenen
 * Text unbemerkt zu verändern) — Owner-Aufgabe: renderTemplate anbinden,
 * bevor produktiv gesendet wird.
 */
export function makeGmailApiProvider({ fromEmail, fromName, dailyLimit = 450, renderTemplate, quotaPath = QUOTA_PATH }) {
  if (!fromEmail) throw new Error("makeGmailApiProvider: fromEmail ist Pflicht.");
  if (typeof renderTemplate !== "function") {
    throw new Error(
      "TEMPLATE_RENDERER_NOT_CONFIGURED: makeGmailApiProvider() braucht renderTemplate(lead) → {subject, body}. " +
        "Absichtlich nicht automatisch aus EMAIL_DELIVERABILITY_AND_TEMPLATE_READINESS.md geparst.",
    );
  }
  return {
    name: "gmail-api",
    async send(lead) {
      const key = todayKey();
      const usedToday = (readQuota(quotaPath)[key]) || 0;
      if (usedToday >= dailyLimit) {
        return { ok: false, error: `GMAIL_DAILY_LIMIT_REACHED: ${usedToday}/${dailyLimit} für ${key} bereits ausgeschöpft.` };
      }
      const accessToken = await refreshAccessToken();
      const { subject, body } = renderTemplate(lead);
      const raw = base64url(buildMime({ fromName: fromName || fromEmail, fromEmail, to: lead.email, subject, body }));
      const res = await fetch(GMAIL_SEND_ENDPOINT, {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}`, "Content-Type": "application/json" },
        body: JSON.stringify({ raw }),
      });
      if (!res.ok) {
        const text = await res.text();
        return { ok: false, error: `GMAIL_SEND_FAILED: HTTP ${res.status} ${text.slice(0, 200)}` };
      }
      const data = await res.json();
      bumpQuota(quotaPath, key);
      return { ok: true, messageId: data.id };
    },
  };
}

const PROVIDER_FACTORIES = {
  noop: () => noopProvider,
  "gmail-api": () =>
    makeGmailApiProvider({
      fromEmail: process.env.GMAIL_FROM_EMAIL || "cherinojoel@gmail.com",
      fromName: process.env.GMAIL_FROM_NAME || "Joel Cherino",
      dailyLimit: process.env.GMAIL_DAILY_LIMIT ? Number(process.env.GMAIL_DAILY_LIMIT) : 450,
      renderTemplate: () => {
        throw new Error(
          "TEMPLATE_RENDERER_NOT_CONFIGURED: siehe scripts/outreach/README.md — vor Produktivbetrieb anbinden.",
        );
      },
    }),
};

export function resolveProvider(name) {
  const key = name || "noop";
  const factory = PROVIDER_FACTORIES[key];
  if (!factory) {
    throw new Error(
      `UNKNOWN_OR_UNCONFIGURED_PROVIDER: "${name}" ist nicht implementiert. ` +
        `Verfügbar: ${Object.keys(PROVIDER_FACTORIES).join(", ")}.`,
    );
  }
  return factory();
}
