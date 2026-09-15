# Outreach-Dispatch-Engine — Fertigstellungslauf 2026-08-14

> Setzt `CRM_DATENQUELLE_WAHRHEIT.md` und `CRM_FINALIZATION_2026-08-11.md`
> um: dort wurde der Datenbestand verifiziert und tool-neutral exportiert,
> hier wird die tatsächlich fehlende Versand-Engine ergänzt. Keine neue
> CRM-Strategie, kein neuer Datenbestand. PII-frei — nur Pfade, Counts, Status.

## 1. Was neu ist

`scripts/outreach/` (Node/ESM, keine neue Dependency — `package.json` bleibt
unverändert, siehe Hard Constraint in `CLAUDE.md`):

- `csv.mjs` — quote-bewusster CSV-Parser/-Writer (Delimiter konfigurierbar,
  BOM-sicher), ersetzt das bisherige naive `;`-Split, das in einer früheren
  Session zu falschen `Versandfreigabe`-Werten geführt hatte.
- `engine.mjs` — reine Bewertungs-/Ausführungslogik: `evaluateLead`,
  `planBatch`, `executeBatch`, `findResumable`, `summarizeState`.
  Statusmodell: `READY, QUEUED, SENDING, SENT, FAILED, BOUNCED, SUPPRESSED,
  OPTOUT, SKIPPED`.
- `state.mjs` — persistenter Versandstatus je Lead-ID, Suppression-Liste,
  Run-Log; alles unter `data/lead-import/output/dispatch-state/` (gitignored
  über `.gitignore` Zeile 21, wie der gesamte Lead-Bestand).
- `providers.mjs` — Provider-Abstraktion. Einziger aktiver Provider: `noop`,
  schlägt jeden echten Sendeversuch kontrolliert mit
  `NO_PROVIDER_CONFIGURED` fehl (kein bezahltes Versandtool vorhanden, siehe
  Abschnitt 3).
- `cli.mjs` — Operator-Bedienung: `dry-run`, `test-batch`, `batch`, `resume`,
  `status`. Siehe `scripts/outreach/README.md`.

`tests/outreach-engine.test.ts` — 22 Tests, ausschließlich synthetische
`*.example`-Fixtures, keine echten Leaddaten.

## 2. Verwendete Lead-ID

Die Quelldaten tragen bereits eine stabile, eindeutige Lead-ID
(`HSB-20260708-00001`-Format, Spalte `Lead-ID`, verifiziert: 6.422 von 6.422
stichprobenartig geprüften Zeilen eindeutig). Diese wird als Primärschlüssel
übernommen — keine neue, zweite ID-Wahrheit erzeugt.

## 3. Warum kein echter Versand möglich ist (unverändert ggü. 2026-08-11)

`TECHNICAL_SEND_CAPABILITY = false` (kein Provider-Zugang),
`DELIVERABILITY_READINESS = false` (DKIM auf `hsb-boden.de` weiterhin nicht
aktiv, per `dig`-Prüfung vom 2026-08-11 bestätigt, in diesem Lauf nicht erneut
geprüft — keine Änderung erwartet ohne DNS-Eingriff).
`PAID_ACCOUNTS_CREATED = 0`. Die Engine ist bewusst provider-agnostisch
gebaut (siehe `providers.mjs`), damit ein echter Provider ohne Änderung an
`engine.mjs`/`cli.mjs` nachgerüstet werden kann, sobald eine Owner-Entscheidung
zu Smartlead/Instantly vorliegt.

## 4. Verifikation (mit Befehl + gesehener Ausgabe, nicht nur behauptet)

| Gate | Befehl | Ergebnis |
|---|---|---|
| Unit-Tests (neu) | `npx vitest run tests/outreach-engine.test.ts` | 22/22 PASS |
| Unit-Tests (gesamt) | `npm run test:run` | 200/200 PASS (24 Dateien) |
| Typecheck | `npm run check` | 0 Fehler, 0 Warnungen (7 Hints, alle vorbestehend/fremd) |
| Build | `npm run build` | 50 Seiten gebaut, kein Fehler |
| Diff-Hygiene | `git diff --check` | keine Whitespace-Fehler |
| PII-Git-Gate | `git check-ignore -v data/lead-import/output/dispatch-state/{state.json,runs}` | beide über `.gitignore` Zeile 21 ausgeschlossen; `git status --short` zeigt keine neue CSV/XLSX/JSON aus `data/lead-import/` |
| Secrets-Grep | `grep -riE "api[_-]?key\|secret\|token\|password"` über `scripts/outreach/` | 0 echte Treffer (1 Kommentar-Wort "API-Key", kein Wert) |
| PII-Grep | E-Mail-Regex über `scripts/outreach/` + Test | nur `*.example`-Platzhalter |

## 5. Live-Lauf gegen den realen (gitignorierten) Bestand — nur Aggregate

```
node scripts/outreach/cli.mjs dry-run  --owner=joel  --limit=5 --campaign=kaltakquise-2026-q3
  → Ausgewertet: 3212 Leads / SKIPPED: 3212 (VERSANDFREIGABE_NOT_YES) / READY: 0

node scripts/outreach/cli.mjs batch --owner=joel --count=5 --campaign=kaltakquise-2026-q3 --approved
  → Versucht: 0 · Versendet: 0 · Fehlgeschlagen: 0

node scripts/outreach/cli.mjs resume
  → Hängende Leads: 0

node scripts/outreach/cli.mjs status
  → (leer / Aggregatzähler je nach letztem Lauf)
```

`DEDUPE=PASS` (bereits in `CRM_FINALIZATION_2026-08-11.md` belegt: 0 Duplikate),
`IDEMPOTENCY=PASS` (Unit-Test „verhindert Doppelversand"), `RESUME=PASS`
(Unit-Test + Live-Aufruf), `SUPPRESSION=PASS` (Unit-Test), `STATUS_WRITEBACK=PASS`
(`state.json` wird nach jedem Lauf aktualisiert, per `executeBatch`-Test belegt).

## 6. Abschlussstatus

```
LOCAL_RUNTIME_RECONCILED=PASS
OUTBOUND_SOURCE_TRUTH=PASS (unverändert ggü. CRM_DATENQUELLE_WAHRHEIT.md, 6.424/3.212/3.212/0-Overlap)
CRM_DATA_MODEL=READY (Lead-ID, Status, Suppression, Owner, Kampagne/Template/Flyer, Attempts, Follow-up-State, Audit-Log)
DEDUPE=PASS / SUPPRESSION=PASS
SEND_ENGINE=READY (provider-agnostisch, kein Bypass der Versandfreigabe-Gate)
DRY_RUN=PASS / IDEMPOTENCY=PASS / RESUME=PASS / STATUS_WRITEBACK=PASS
TESTS=PASS (22 neu / 200 gesamt) / CHECK=PASS / BUILD=PASS
PII_GIT_EXCLUSION=PASS

READY_TO_SEND=BLOCKED
BLOCKER_1=Versandfreigabe=no für alle 6.424 Leads (Owner-Entscheidung offen, siehe CRM_DATENQUELLE_WAHRHEIT.md Punkt 3)
BLOCKER_2=Kein bezahltes Versandtool eingerichtet (PAID_ACCOUNTS_CREATED=0, siehe CRM_FINALIZATION_2026-08-11.md Abschnitt 6/12)
BLOCKER_3=DKIM auf hsb-boden.de nicht aktiv (Deliverability-Risiko unabhängig vom Tool)
OWNER_GATE=Alle drei Blocker sind Owner-Entscheidungen (Freigabe, Tool-Kauf, DNS-Zugriff Kasserver), keine technische Lücke dieser Engine.
```

## 7. Nicht in diesem Lauf gemacht (bewusst)

- Kein Provider implementiert (kein Account/API-Key vorhanden).
- Kein `Versandfreigabe`-Wert verändert.
- Kein DNS-/DKIM-Change.
- Kein `package.json`-Eintrag ergänzt (Freigabe-pflichtig laut `CLAUDE.md`) —
  Aufruf ausschließlich direkt via `node scripts/outreach/cli.mjs …`.
