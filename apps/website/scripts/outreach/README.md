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

## Geteiltes, live-aktualisierendes CRM (Joel + Jordi) — Airtable

Base „HSB Outreach CRM" (angelegt 2026-08-14, `appPRPqNwpt615PAW`, Tabelle
„Leads" `tble6KY1SaIx0RHaX`) — Status-only: Lead-ID, Firma, Tier,
Verantwortlicher, Kampagne, Status, Skip-Grund, Attempts, Sent_At,
Provider_Message_Id, Fehler, Follow-up-State, Nächste Aktion, Run-ID,
Zuletzt aktualisiert. **Keine** Ansprechpartner/E-Mail/Telefon — die bleiben
ausschließlich lokal (gitignored). Grund: 6.424 reale B2B-Kontakte
vollständig in ein Drittanbieter-SaaS zu spiegeln vergrößert die
PII-Angriffsfläche unnötig; der Status allein reicht für die tägliche
Arbeit von Joel und Jordi.

**Zugriff einrichten (einmalig, manuell in der Airtable-Weboberfläche):**
Base öffnen → „Share" → `j-cherino@hsb-boden.de` und `j-post@hsb-boden.de`
als Collaborator (Editor) einladen. Die Airtable-MCP-Anbindung hier bietet
keinen Collaborator-Invite-Tool-Aufruf, das muss manuell passieren.

**Automatischer Sync:** `dry-run`, `test-batch` und `batch` pushen nach
jedem Lauf automatisch den aktuellen Status aller geladenen Leads nach
Airtable (`trySyncAirtable` in `cli.mjs`) — best-effort, no-op ohne
`AIRTABLE_API_KEY`. Manuell erzwingen:

```sh
AIRTABLE_API_KEY=pat_xxx node scripts/outreach/cli.mjs sync-airtable --owner=all
```

`AIRTABLE_API_KEY` ist ein Personal Access Token, den **der Nutzer selbst**
unter airtable.com → Account → „Developer hub" → „Personal access tokens"
erzeugt (Scopes: `data.records:read`, `data.records:write`, Zugriff auf
diese eine Base). Der Agent erzeugt oder speichert diesen Token nicht
(Hard Constraint: Credentials macht der Nutzer selbst). Optional
überschreibbar: `AIRTABLE_BASE_ID`, `AIRTABLE_TABLE_ID`.

Initialer Seed (2026-08-14): alle 6.424 Leads sind in Airtable angelegt,
`Status=SKIPPED`, `Skip_Grund=VERSANDFREIGABE_NOT_YES` — Spiegelbild des
lokalen Realzustands zum Seed-Zeitpunkt, per Subagent über 129 Batch-Uploads
befüllt (Airtable-REST-Limit: 50 Records/Request bei der MCP-Variante).

## Gratis-Versandweg (Blocker 2) — was real geprüft ist, nicht vermutet

Live geprüft am 2026-08-14 (`get_status` auf allen vier Google-Workspace-
MCP-Profilen dieses Environments):

| Profil | Tatsächliches Konto | Für HSB nutzbar? |
|---|---|---|
| `hsb-boden` | privates Outlook-verknüpftes Google-Konto | ❌ Nein (Hard Constraint) |
| `cherinodiaz` | dasselbe private Konto | ❌ Nein |
| `info` | ebenfalls dasselbe private Konto — **nicht** info@hsb-boden.de | ❌ Nein, trotz Profilnamen |
| `cherinojoel` | `cherinojoel@gmail.com` | ✅ Ja — laut Memory bereits etabliertes CRM-Konto |

Für Jordi ist hier kein Konto angebunden — `j-post@hsb-boden.de` (M365) ist
laut `marketing/flyer/akquise-email-jordi.md` weiterhin DKIM-ungeprüft, ein
eigenes Jordi-Gmail müsste Jordi selbst per eigenem Login anbinden.

`makeGmailApiProvider()` in `providers.mjs` ist der reale, gratis nutzbare
Versandweg über die Gmail-API (Consumer-Gmail-Quota ca. 500/Tag, hier
default auf 450 begrenzt). **Kein DKIM-Setup auf `hsb-boden.de` nötig** —
Google signiert `@gmail.com`-Mails mit seinem eigenen DKIM. Erfordert vom
Nutzer selbst erzeugte OAuth-Zugangsdaten (`GMAIL_CLIENT_ID`,
`GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN` — Google Cloud Console, oder
ein kurzlebiges `GMAIL_ACCESS_TOKEN` zum Testen) sowie eine
`renderTemplate(lead)`-Funktion (noch nicht angebunden — die Mail-Texte
liegen aktuell nur als Markdown in
`docs/email/EMAIL_DELIVERABILITY_AND_TEMPLATE_READINESS.md` und werden
bewusst nicht automatisch geparst, um den freigegebenen Text nicht
unbemerkt zu verändern).

`hsb-boden.de` selbst: DNS-Autorität liegt weiterhin bei Kasserver, nicht
bei Cloudflare (Cloudflare-Account „Info@hsb-boden.de's Account" hat 0
Zonen, per Live-API-Check 2026-08-14 — Cloudflare kann für `hsb-boden.de`
technisch nichts an DKIM ändern, solange die Domain dort nicht als Zone
liegt). Für den Gmail-Gratis-Pfad ist das irrelevant (s. o.); für einen
späteren professionelleren Absender (`@mail.hsb-boden.de` o. ä.) bliebe nur
der Weg über eine neue, tatsächlich Cloudflare-verwaltete Subdomain — das
ist ein echter DNS-Wechsel und braucht explizite Freigabe, siehe
`docs/crm/CRM_DISPATCH_ENGINE_2026-08-14.md`.

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
