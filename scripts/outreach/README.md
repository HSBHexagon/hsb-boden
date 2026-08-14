# Outreach-Dispatch-Engine

Technische Fertigstellung des bestehenden Outbound-CRM-Systems
(`docs/crm/CRM_DATENQUELLE_WAHRHEIT.md`, `docs/crm/CRM_FINALIZATION_2026-08-11.md`).
Kein neues CRM, keine neue Strategie — nur die fehlende Versand-Engine über den
bereits verifizierten 6.424er-Leadbestand.

## Was das ist

Eine kleine, dependency-freie Node/ESM-CLI, die:

- die bestehenden `HSB_OUTREACH_{READY,JOEL,JORDI}_2026-08-11.csv`-Exporte liest
  (`data/lead-import/output/final_2026-08-11/`, gitignored),
- pro Lead alle Versandvoraussetzungen prüft (gültige E-Mail, nicht suppressed,
  kein Opt-out, `Versandfreigabe=yes`, passende Kampagne/Template/Flyer/Owner,
  noch nicht versendet),
- einen persistenten Versandstatus je Lead führt (`data/lead-import/output/dispatch-state/state.json`,
  gitignored) — Statusmodell: `READY, QUEUED, SENDING, SENT, FAILED, BOUNCED,
  SUPPRESSED, OPTOUT, SKIPPED`,
- Idempotenz garantiert: ein Lead mit Status `SENT` wird nie erneut angeschrieben,
  auch nicht bei wiederholtem Lauf,
- **keinen echten Versandweg hat.** Es existiert kein bezahltes Versandtool
  (siehe `docs/crm/CRM_FINALIZATION_2026-08-11.md` Abschnitt 6/12: kein
  Smartlead-/Instantly-Konto, DKIM auf `hsb-boden.de` nicht aktiv). Der einzige
  Provider ist `noop` (`providers.mjs`) und schlägt jeden echten Sendeversuch
  kontrolliert mit `NO_PROVIDER_CONFIGURED` fehl, statt eine falsche
  Erfolgsmeldung vorzutäuschen.

## Bedienung

```sh
# Dry-Run: alle Leads auswerten, README-artige Zählstatistik, kein Versand.
node scripts/outreach/cli.mjs dry-run --owner=joel --campaign=kaltakquise-2026-q3

# Test-Batch: wie dry-run, aber auf N Leads begrenzt (Default 5).
node scripts/outreach/cli.mjs test-batch --owner=joel --count=5 --campaign=kaltakquise-2026-q3

# Definierter Batch, real (nur mit --approved; sonst READY_TO_SEND=BLOCKED).
node scripts/outreach/cli.mjs batch --owner=joel --count=25 --campaign=kaltakquise-2026-q3 --approved

# Nach Abbruch: bei SENDING hängen gebliebene Leads auf FAILED zurücksetzen,
# damit der nächste batch-Lauf sie automatisch erneut versucht (kein Doppelversand).
node scripts/outreach/cli.mjs resume

# Aktuellen Versandstatus (Aggregat, keine PII) anzeigen.
node scripts/outreach/cli.mjs status
```

`--owner` wählt die Quelle: `all` (6.424), `joel` (3.212) oder `jordi` (3.212).

## Warum aktuell READY=0 für jeden Lauf

`Versandfreigabe=no` gilt für **alle** 6.424 Zeilen (siehe
`CRM_DATENQUELLE_WAHRHEIT.md`) — das ist eine bewusste, unveränderte
Owner-Entscheidung, keine technische Lücke. Die Engine respektiert das hart:
kein Bypass-Flag. Solange die Freigabe nicht gesetzt ist, bleibt
`READY_TO_SEND=BLOCKED`.

## Sobald ein echtes Versandtool gewählt ist

1. In `providers.mjs` einen neuen Provider ergänzen (z. B. `smartleadProvider`
   mit echtem API-Call), in `resolveProvider()` registrieren.
2. `batch --provider=smartlead --approved` nutzen.
3. Vorher: `Versandfreigabe` durch Owner-Entscheidung auf `yes` setzen (siehe
   offene Punkte in `docs/crm/CRM_DATENQUELLE_WAHRHEIT.md`) und DKIM/Domain-
   Setup gemäß Abschnitt 7 der Finalisierung abschließen.

## Tests

`tests/outreach-engine.test.ts` — ausschließlich synthetische Fixtures
(`*.example`-Adressen), keine echten Leaddaten. Deckt ab: Validierung,
Suppression, Opt-out, Versandfreigabe-Gate, Kampagnen-/Template-/Flyer-/
Owner-Pflichtfelder, Dry-Run (kein Provider-Call), realer Send (Erfolg/Fehler/
Exception), Doppelversand-Schutz, Resume-Erkennung, Status-Aggregation.
