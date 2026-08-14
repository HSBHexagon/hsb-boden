// Provider-Abstraktion für den tatsächlichen Versand. Aktuell gibt es KEIN
// bezahltes/eingerichtetes Versandtool (siehe
// docs/crm/CRM_FINALIZATION_2026-08-11.md Abschnitt 6/12: PAID_ACCOUNTS_CREATED=0,
// kein Smartlead-/Instantly-Konto angelegt, DKIM auf hsb-boden.de nicht aktiv).
// Die Engine ist deshalb bewusst provider-agnostisch: `noop` ist der einzige
// aktive Provider und schlägt jeden echten Sendeversuch kontrolliert fehl,
// statt eine falsche Erfolgsmeldung vorzutäuschen. Ein echter Provider
// (z. B. Smartlead-API) wird erst angebunden, sobald ein Account inkl.
// API-Key existiert — das ist eine Owner-Entscheidung (Kosten), keine
// technische Lücke dieser Engine.

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

export function resolveProvider(name) {
  if (!name || name === "noop") return noopProvider;
  throw new Error(
    `UNKNOWN_OR_UNCONFIGURED_PROVIDER: "${name}" ist nicht implementiert. ` +
      `Aktuell einzig verfügbar: "noop" (immer BLOCKED, siehe providers.mjs).`,
  );
}
