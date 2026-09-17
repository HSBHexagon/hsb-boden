# CRM-Cockpit: Visuelle Bedienschicht für Joel und Jordi — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Jeder der beiden Nutzer öffnet **einen** Tab und sieht ohne Filtern, Scrollen oder Spaltenkenntnis: *Was wurde versendet · Wer hat geantwortet · Wer hat abgemeldet · Was ist heute dran · Was ist unklar.*

**Architecture:** Das Sheet `HSB CRM MASTER 6424 – Sales OS` bleibt System of Record; `ALL_LEADS` bleibt die Datenbank (Spaltenbuchstaben unverändert, neue Spalten nur am Ende). Die Bedienschicht sind **sichtbare, formelgetriebene Cockpit-Tabs** (`HEUTE JOEL`, `HEUTE JORDI`, `POSTEINGANG`) plus **Zeilenfarben** in `ALL_LEADS` und ein bereinigtes `DASHBOARD`. Alles wird von idempotenten Sheets-API-Skripten unter `engine/operator_layer/` erzeugt (Dry-Run, mehrfach ausführbar), die Automatik schreibt zusätzlich einen sichtbaren Vertrauensanker („zuletzt abgeglichen"). Klärfälle werden im Sheet gelöst, nicht im Code.

**Tech Stack:** Python 3 + google-api-python-client (Profil `cherinodiaz` schreibt, `cherinojoel` liest; `engine/operator_layer/crm_common.py`), Apps Script (`apps_script/*.gs` → `python3 engine/build_single.py` → `deploy/`), Node-Testsuiten (`tests/test_apps_script.js`, `tests/test_graph_adapter.js`, `tests/verifier_suite.js`), pytest für Python.

**Spec:** `docs/superpowers/specs/2026-09-17-crm-sheet-operator-layer-design.md` (Ziel 1 „auf einen Blick lesbar", Komponente A) — dieser Plan ist die Bedienschicht darauf; Befunde vom 2026-09-17 (Abgleich läuft, drei Domain-Abmeldungen, `INBOUND_EVENTS` mit zwei Spaltenlayouts) sind eingearbeitet.

## Global Constraints
- Header `ALL_LEADS!A1:BD1` bleibt byte-identisch; `BE=Pipeline` bleibt; keine Spalte wird verschoben oder umbenannt (QUERY/Dashboard/Python adressieren per Buchstabe).
- Tab-Namen aus `CFG` (`ALL_LEADS`, `INBOUND_EVENTS`, `ACTIVITIES`, `BATCHES`) bleiben; neue Tabs heißen `HEUTE JOEL`, `HEUTE JORDI`, `POSTEINGANG`, `SYNC_STATUS`.
- Kein automatischer Versand; nie `Versandfreigabe=yes` per Automatik. Zero-Send bleibt.
- Jeder Schreibzugriff auf das Sheet: vorher `python3 engine/operator_layer/crm_backup.py` (Drive-Kopie + CSV + SHA-256 unter `~/KI-System/08_System/backups/<datum>-hsb-crm-sheet/`).
- Datenänderungen an bestehenden Zeilen (Task 1 Migration, Duplikat-Bereinigung) nur nach Owner-Freigabe je Regel, mit Dry-Run-Ausgabe.
- Apps Script: Quelle sind `apps_script/{Config,Engine,Actions,Code}.gs`; danach `python3 engine/build_single.py && cp apps_script/HSB_SALES_OS.gs deploy/HSB_SALES_OS.js`; `clasp push` nur mit Freigabe.
- Arbeiten im isolierten Worktree (Branch `feat/crm-domain-optout` oder Folgebranch) — ein zweiter Agent committet parallel im Haupt-Checkout.

## Spaltenkontrakt (ALL_LEADS, für alle Formeln in diesem Plan)
`A Lead-ID · B Firma · C Standort · F Tier · G Ansprechpartner · I E-Mail · R Follow-up-Datum · Y Opt-out-Status · Z Versandfreigabe · AA Verantwortlicher · AC Notizen · AN Batch_ID · AO Send_Status · AP Send_Datum · AQ Bounce_Status · AR Reply_Status · AT Suppressed · AW Draft_ID · BC Last_Reply_At · BE Pipeline`
`Verantwortlicher` enthält „Joel Cherino Diaz" bzw. „Jordi Post" (Match per `*Joel*` / `*Jordi*`).

## Farbsystem (überall identisch)
| Zustand | Pipeline | Hintergrund | Text |
|---|---|---|---|
| Abgemeldet | `Abgemeldet` | `#F4C7C3` | `#7A1F1A` |
| Bounce | `Bounce` | `#FCE8B2` | `#7A4B00` |
| Antwort | `Antwort` | `#FFF2CC` | `#5C4A00` |
| Versendet | `Versendet` | `#D9EAD3` | `#274E13` |
| Entwurf | `Entwurf` | `#DEEAF6` | `#1F3A5F` |
| Freigegeben | `Freigegeben` | `#CFE2F3` | `#0B3D91` |
| Neu | `Neu` | `#EFEFEF` | `#444444` |

---

## Dateistruktur

- Modify: `apps_script/Actions.gs` — `processInboundEvent` schreibt das kanonische 12-Spalten-Layout; `hsbKlaerfallAnwenden_` (Task 5)
- Modify: `apps_script/HSB_GraphAdapter.gs` — `hsbAutoReconcile` schreibt `SYNC_STATUS` (Task 2); Menüpunkt „Klärfälle anwenden" (Task 5, `Code.gs`)
- Modify: `engine/reconcile_cloud_mailbox.py` — `Internet_Message_ID` in Spalte F (Task 1)
- Create: `engine/operator_layer/crm_events_migrate.py` — Altzeilen auf 12 Spalten, Duplikate (Dry-Run/Apply) (Task 1)
- Create: `engine/operator_layer/crm_cockpit.py` — baut `HEUTE JOEL`, `HEUTE JORDI`, `POSTEINGANG`, Tab-Reihenfolge (Task 4/5)
- Modify: `engine/operator_layer/crm_operator_layer.py` — Zeilenfarben nach Pipeline (Task 3)
- Create: `engine/operator_layer/crm_dashboard.py` — DASHBOARD-Formeln (Task 6)
- Create: `tests/test_crm_cockpit.py`, `tests/test_crm_events_migrate.py` — reine Formel-/Request-Tests ohne Netz
- Modify: `tests/test_apps_script.js`, `tests/verifier_suite.js` — Event-Spaltenindizes (Task 1)
- Modify: `README_OPERATING.md`, README-Tab (Task 7)

---

### Task 1: `INBOUND_EVENTS` — ein Spaltenlayout, keine Duplikate

**Warum zuerst:** Der Tab hat den Header `Event_ID · Received_UTC · Mailbox · From · Subject · Internet_Message_ID · Lead_ID · Classification · Stop_Followup · Processed · Notes · Raw_Link` (kanonisch seit 2026-08-28, `docs/appsheet/inbound_events_schema_spec.json`), aber `processInboundEvent` schreibt `Event_ID · Timestamp · Type · Lead_ID · Owner · Email · Message_ID · In_Reply_To · Status · Details`. Ab Spalte C steht deshalb alles verschoben (z. B. `Stop_Followup` = „NEEDS_REVIEW"). Der Python-Schreiber legt die Message-ID in L statt F. Ohne einheitliches Layout kann `POSTEINGANG` (Task 5) nicht per Header lesen. Zusätzlich liegen 284 Wiederholungszeilen aus der Zeit vor dem Vorfilter.

**Files:**
- Modify: `apps_script/Actions.gs` (`processInboundEvent`: Header-Anlage, Dedupe-Lesen, drei `appendRow`)
- Modify: `engine/reconcile_cloud_mailbox.py` (drei `inbound_event_rows.append`)
- Create: `engine/operator_layer/crm_events_migrate.py`
- Test: `tests/test_apps_script.js`, `tests/verifier_suite.js`, `tests/test_crm_events_migrate.py`

**Interfaces:**
- Produces: `INBOUND_EVENTS`-Zeile = `[Event_ID, Received_UTC, Mailbox, From, Subject, Internet_Message_ID, Lead_ID, Classification, Stop_Followup ('yes'|'no'), Processed ('PROCESSED'|'NEEDS_REVIEW'|'ALREADY_SENT_IGNORED'), Notes, Raw_Link]`; `processInboundEvent(event)` akzeptiert zusätzlich `event.mailbox` (String).
- Produces: `python3 engine/operator_layer/crm_events_migrate.py [--apply]` — Exit 0, druckt Zählung.

- [ ] **Step 1: Failing Tests — Apps-Script-Layout**

In `tests/test_apps_script.js`, Funktion `testInboundEvents`, direkt nach dem Block „5. Nicht zuordenbare Antwort" (`lastEvt[3] === ''`) die Indizes auf das Header-Layout umstellen und einen Layout-Test ergänzen:

```js
  check('Inbound: unmatchbares Event traegt LEERE Lead-ID (kein Raten)',
        lastEvt[6] === '', 'lead_id=' + lastEvt[6]);
  check('Inbound: Ereigniszeile folgt dem 12-Spalten-Header (Classification=H, Processed=J)',
        lastEvt.length === 12 && lastEvt[7] === 'REPLY' && lastEvt[9] === 'NEEDS_REVIEW' && lastEvt[3] === 'unbekannt-gibtesnicht@nirgendwo.de',
        JSON.stringify(lastEvt));
  const headerRow = SHEETS.INBOUND_EVENTS._data[0];
  check('Inbound: Header ist kanonisch (12 Spalten)',
        headerRow.join('|') === 'Event_ID|Received_UTC|Mailbox|From|Subject|Internet_Message_ID|Lead_ID|Classification|Stop_Followup|Processed|Notes|Raw_Link',
        headerRow.join('|'));
```

Ebenso im Block „4a" (`domainEvt[9]` → `domainEvt[10]`, Notes ist Spalte K) und in `tests/verifier_suite.js` Zeilen 557–558: `unkRow[3]` → `unkRow[6]`, `unkRow[8]` → `unkRow[9]` (gleiches für `ambRow`).

- [ ] **Step 2: Tests laufen lassen — müssen fehlschlagen**

Run: `cd apps/sales-os && node tests/test_apps_script.js 2>&1 | grep -E "FAIL|ERGEBNIS"; node tests/verifier_suite.js 2>&1 | grep -E "NEEDS_REVIEW="`
Expected: mindestens „Ereigniszeile folgt dem 12-Spalten-Header" FAIL; `UNKNOWN_EVENT_NEEDS_REVIEW=FAIL`.

- [ ] **Step 3: `processInboundEvent` auf Header-Layout umstellen**

In `apps_script/Actions.gs`:

```js
// Kanonisches Layout von INBOUND_EVENTS (docs/appsheet/inbound_events_schema_spec.json).
// Alle Schreiber (Apps Script, engine/reconcile_cloud_mailbox.py) halten diese Reihenfolge ein.
var INBOUND_EVENT_HEADER_ = ['Event_ID', 'Received_UTC', 'Mailbox', 'From', 'Subject',
  'Internet_Message_ID', 'Lead_ID', 'Classification', 'Stop_Followup', 'Processed', 'Notes', 'Raw_Link'];

function inboundEventRow_(p) {
  var stop = (p.type === 'OPT_OUT' || p.type === 'HARD_BOUNCE' || p.type === 'CONTACT_CHURN' || p.type === 'NEGATIVE_REPLY') ? 'yes' : 'no';
  return [p.eventId, p.ts, p.mailbox || '', p.from || '', p.subject || '', p.messageId || '',
          p.leadId || '', p.type, stop, p.status, p.notes || '', p.inReplyTo ? ('In-Reply-To: ' + p.inReplyTo) : ''];
}
```

Header-Anlage (`eventsSh.getLastRow() === 0`): `eventsSh.appendRow(INBOUND_EVENT_HEADER_)` und `getRange(1, 1, 1, 12)`.
Dedupe-Lesen: `getRange(2, 1, n, 10)`; `rowMsgId = existingEvents[ei][5]`, `rowStatus = existingEvents[ei][9]`, `lead_id: existingEvents[ei][6]`.
Die drei `appendRow`-Aufrufe ersetzen durch `eventsSh.appendRow(inboundEventRow_({...}))`:
- unmatched: `{eventId, ts, mailbox: event.mailbox, from: email, subject: event.subject, messageId, leadId: '', type: eventType, status: 'NEEDS_REVIEW', notes: event.details || 'Nicht eindeutig zuordenbar', inReplyTo}`
- ALREADY_SENT_IGNORED: `{..., leadId, status: 'ALREADY_SENT_IGNORED', notes: 'Lead bereits als SENT vermerkt - keine erneute Statusaenderung/Aktivitaet'}`
- PROCESSED: `{..., leadId, status: 'PROCESSED', notes: eventNotiz}` (der `owner` fällt weg — er steht am Lead).

In `apps_script/HSB_GraphAdapter.gs` beide `processInboundEvent({...})`-Aufrufe um `mailbox: mailboxKonto_()` ergänzen; `eventIndexLesen_` liest `getRange(2, 1, last - 1, 10)` und Status aus `r[9]`.

- [ ] **Step 4: Bündeln und Tests grün**

Run: `python3 engine/build_single.py && cp apps_script/HSB_SALES_OS.gs deploy/HSB_SALES_OS.js && cp apps_script/HSB_GraphAdapter.gs deploy/HSB_GraphAdapter.js && node tests/test_apps_script.js | tail -1 && node tests/test_graph_adapter.js | tail -1 && node tests/verifier_suite.js | grep -c "=FAIL"`
Expected: `… 0 fehlgeschlagen`, `… 0 fehlgeschlagen`, `0`.

- [ ] **Step 5: Python-Schreiber angleichen**

`engine/reconcile_cloud_mailbox.py`: in allen drei `inbound_event_rows.append([...])` das sechste Element `""` durch `msg.get("internet_message_id", "")` ersetzen und das zwölfte Element (`Raw_Link`) auf `""` setzen. Test in `tests/test_reconcile_cloud_mailbox.py` ergänzen:

```python
def test_inbound_event_row_has_message_id_in_column_f(monkeypatch):
    from engine import reconcile_cloud_mailbox as m
    row = m.build_inbound_event_row(  # kleine Hilfsfunktion extrahieren, siehe unten
        event_id="X", msg_date="2026-09-17T00:00:00Z", mailbox="j-cherino@hsb-boden.de",
        sender="a@b.de", subject="AW", message_id="<1@b>", lead_id="HSB-1",
        classification="REPLY", stop="no", processed="PROCESSED", notes="n")
    assert row[5] == "<1@b>" and row[11] == "" and len(row) == 12
```

Dazu in `reconcile_cloud_mailbox.py`:

```python
def build_inbound_event_row(*, event_id, msg_date, mailbox, sender, subject, message_id,
                            lead_id, classification, stop, processed, notes):
    """Kanonisches 12-Spalten-Layout von INBOUND_EVENTS (Spalte F = Internet_Message_ID)."""
    return [event_id, msg_date, mailbox, sender, subject, message_id,
            lead_id, classification, stop, processed, notes, ""]
```

und die drei Listen-Literale durch Aufrufe ersetzen.

Run: `python3 -m pytest tests/test_reconcile_cloud_mailbox.py -q` → Expected: alle PASS.

- [ ] **Step 6: Migrationsskript (Dry-Run)**

`engine/operator_layer/crm_events_migrate.py`:

```python
#!/usr/bin/env python3
"""Bringt INBOUND_EVENTS-Altzeilen auf das 12-Spalten-Layout und entfernt Wiederholungszeilen.

Erkennung Alt-Layout: Spalte C enthaelt einen Ereignistyp (SENT, REPLY, ...), nicht ein Postfach.
Wiederholung: gleiche Event_ID, spaetere Zeile, Status NEEDS_REVIEW -> nur die erste bleibt.
Ohne --apply wird nichts geschrieben.
"""
import sys, collections
from crm_common import services, SID
TYPES = {"SENT","REPLY","POSITIVE_REPLY","NEGATIVE_REPLY","HARD_BOUNCE","SOFT_BOUNCE","OPT_OUT","AUTO_REPLY_OOO","CONTACT_CHURN"}
STOP = {"OPT_OUT","HARD_BOUNCE","CONTACT_CHURN","NEGATIVE_REPLY"}

def alt_zu_neu(r):
    g = lambda i: str(r[i]) if len(r) > i else ""
    typ = g(2)
    return [g(0), g(1), "", g(5), "", g(6), g(3), typ, "yes" if typ in STOP else "no", g(8), g(9),
            ("In-Reply-To: " + g(7)) if g(7) else ""]

def plan(rows):
    """rows ohne Header -> (neue_zeilen, geloeschte_indizes) ; Indizes 0-basiert relativ zu Zeile 2."""
    out, drop, seen = [], [], collections.Counter()
    for i, r in enumerate(rows):
        g = lambda k: str(r[k]) if len(r) > k else ""
        eid = g(0)
        neu = alt_zu_neu(r) if g(2) in TYPES else (list(r) + [""] * (12 - len(r)))[:12]
        seen[eid] += 1
        if seen[eid] > 1 and neu[9] == "NEEDS_REVIEW":
            drop.append(i); continue
        out.append(neu)
    return out, drop

def main(apply=False):
    sh, _ = services("cherinodiaz" if apply else "cherinojoel")
    vals = sh.spreadsheets().values().get(spreadsheetId=SID, range="INBOUND_EVENTS!A2:L").execute().get("values", [])
    out, drop = plan(vals)
    alt = sum(1 for r in vals if len(r) > 2 and str(r[2]) in TYPES)
    print(f"Zeilen: {len(vals)} | Alt-Layout: {alt} | Wiederholungen entfernt: {len(drop)} | Ergebnis: {len(out)}")
    if not apply:
        print("DRY-RUN - nichts geschrieben. Mit --apply ausfuehren (nach Backup + Owner-Freigabe)."); return 0
    sh.spreadsheets().values().clear(spreadsheetId=SID, range="INBOUND_EVENTS!A2:L").execute()
    sh.spreadsheets().values().update(spreadsheetId=SID, range="INBOUND_EVENTS!A2", valueInputOption="RAW",
                                      body={"values": out}).execute()
    print("GESCHRIEBEN."); return 0

if __name__ == "__main__":
    sys.exit(main(apply="--apply" in sys.argv))
```

Test `tests/test_crm_events_migrate.py`:

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "engine" / "operator_layer"))
from crm_events_migrate import plan, alt_zu_neu

def test_alt_layout_wird_auf_header_gemappt():
    alt = ["APIHUB-INBOX-<1>", "2026-09-17T12:00:00Z", "OPT_OUT", "HSB-1", "JORDI", "a@b.de", "<1>", "", "PROCESSED", "Abmelden"]
    neu = alt_zu_neu(alt)
    assert neu[:10] == ["APIHUB-INBOX-<1>", "2026-09-17T12:00:00Z", "", "a@b.de", "", "<1>", "HSB-1", "OPT_OUT", "yes", "PROCESSED"]
    assert len(neu) == 12

def test_wiederholte_klaerfaelle_fallen_weg_erste_bleibt():
    a = ["E1", "t1", "REPLY", "", "", "x@y.de", "<1>", "", "NEEDS_REVIEW", "s"]
    b = ["E1", "t2", "REPLY", "", "", "x@y.de", "<1>", "", "NEEDS_REVIEW", "s"]
    c = ["E2", "t3", "j@hsb.de", "x@y.de", "s", "<2>", "HSB-1", "REPLY", "no", "PROCESSED", "n", ""]
    out, drop = plan([a, b, c])
    assert drop == [1] and [r[0] for r in out] == ["E1", "E2"] and out[1] == c
```

Run: `python3 -m pytest tests/test_crm_events_migrate.py -q` → PASS; `python3 engine/operator_layer/crm_events_migrate.py` → Dry-Run-Zahlen (erwartet ≈ „Alt-Layout: 600+, Wiederholungen: 284").

- [ ] **Step 7: Owner-Gate, dann anwenden**

Dem Owner die Dry-Run-Zeile zeigen; nach „ja": `python3 engine/operator_layer/crm_backup.py && python3 engine/operator_layer/crm_events_migrate.py --apply`, danach Dry-Run erneut → „Alt-Layout: 0 | Wiederholungen entfernt: 0".

- [ ] **Step 8: Commit**

```bash
git add apps/sales-os/apps_script/Actions.gs apps/sales-os/apps_script/HSB_GraphAdapter.gs apps/sales-os/apps_script/HSB_SALES_OS.gs apps/sales-os/deploy/HSB_SALES_OS.js apps/sales-os/deploy/HSB_GraphAdapter.js apps/sales-os/engine/reconcile_cloud_mailbox.py apps/sales-os/engine/operator_layer/crm_events_migrate.py apps/sales-os/tests/test_apps_script.js apps/sales-os/tests/verifier_suite.js apps/sales-os/tests/test_reconcile_cloud_mailbox.py apps/sales-os/tests/test_crm_events_migrate.py
git commit -m "fix(sales-os): INBOUND_EVENTS auf kanonisches 12-Spalten-Layout (alle Schreiber) + Migration"
```

---

### Task 2: Vertrauensanker „zuletzt abgeglichen" (`SYNC_STATUS`)

**Warum:** Beide Nutzer müssen ohne Nachfragen sehen, dass die Automatik lebt. Ein Tab `SYNC_STATUS` (versteckt) wird vom Trigger beschrieben; `DASHBOARD` und die `HEUTE`-Tabs zeigen daraus „Postfach j-post@… zuletzt 16:45 · 52 versendet · 3 Bounces".

**Files:**
- Modify: `apps_script/HSB_GraphAdapter.gs` (`hsbAutoReconcile`)
- Test: `tests/test_graph_adapter.js` (Abschnitt 10)

**Interfaces:**
- Produces: Tab `SYNC_STATUS` mit Header `Mailbox · Letzter_Lauf_UTC · Weg · Gesendet_geprueft · Neu_versendet · Posteingang_geprueft · Antworten_Abmeldungen_Bounces · Fehler`; eine Zeile je Postfach (Upsert).

- [ ] **Step 1: Failing Test**

In `tests/test_graph_adapter.js` vor der Ergebnis-Ausgabe:

```js
console.log('\n=== 10. SYNC_STATUS wird je Postfach fortgeschrieben ===');
{
  const k = ladeAdapter({ postfach: 'j-post@hsb-boden.de' });
  const SYNC = { _data: [] };
  const sheet = {
    getLastRow: function () { return SYNC._data.length; },
    appendRow: function (r) { SYNC._data.push(r.slice()); },
    getRange: function (r, c, nr, nc) {
      return {
        getValues: function () { return SYNC._data.slice(r - 1, r - 1 + nr).map(function (x) { return x.slice(c - 1, c - 1 + nc); }); },
        setValues: function (v) { for (let i = 0; i < v.length; i++) SYNC._data[r - 1 + i] = v[i].slice(); },
        setFontWeight: function () { return this; }
      };
    },
    setFrozenRows: function () {}
  };
  k.SpreadsheetApp = { getActiveSpreadsheet: function () { return { getSheetByName: function () { return sheet; }, insertSheet: function () { return sheet; } }; } };
  k.syncStatusSchreiben_('j-post@hsb-boden.de', { ok: true, weg: 'APIHUB', sent: { checked: 100, matched: 52 }, inbox: { checked: 100, matched: 3 }, errors: [] });
  k.syncStatusSchreiben_('j-post@hsb-boden.de', { ok: true, weg: 'APIHUB', sent: { checked: 100, matched: 1 }, inbox: { checked: 100, matched: 0 }, errors: [] });
  pruefe('Header + genau eine Zeile je Postfach (Upsert)', SYNC._data.length === 2, SYNC._data.length + ' Zeilen');
  pruefe('Zweiter Lauf ueberschreibt Zaehler', SYNC._data[1][4] === 1, JSON.stringify(SYNC._data[1]));
  pruefe('Fehlerspalte leer bei ok', SYNC._data[1][7] === '');
}
```

- [ ] **Step 2: Run → FAIL** (`syncStatusSchreiben_ is not a function`)

- [ ] **Step 3: Implementieren** (in `HSB_GraphAdapter.gs`, vor `hsbAutoReconcile`)

```js
var SYNC_STATUS_SHEET_ = 'SYNC_STATUS';
var SYNC_STATUS_HEADER_ = ['Mailbox', 'Letzter_Lauf_UTC', 'Weg', 'Gesendet_geprueft', 'Neu_versendet',
  'Posteingang_geprueft', 'Antworten_Abmeldungen_Bounces', 'Fehler'];

/** Eine Zeile je Postfach: wann lief der Abgleich zuletzt, was hat er gefunden. Sichtbar fuer beide Nutzer. */
function syncStatusSchreiben_(mailbox, r) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(SYNC_STATUS_SHEET_) || ss.insertSheet(SYNC_STATUS_SHEET_);
  if (sh.getLastRow() === 0) { sh.appendRow(SYNC_STATUS_HEADER_); sh.getRange(1, 1, 1, 8).setFontWeight('bold'); sh.setFrozenRows(1); }
  var row = [mailbox, new Date().toISOString(), r.weg || '', ((r.sent || {}).checked || 0), ((r.sent || {}).matched || 0),
             ((r.inbox || {}).checked || 0), ((r.inbox || {}).matched || 0), (r.errors || []).join(' | ')];
  var n = sh.getLastRow();
  if (n >= 2) {
    var vals = sh.getRange(2, 1, n - 1, 1).getValues();
    for (var i = 0; i < vals.length; i++) {
      if (String(vals[i][0]) === mailbox) { sh.getRange(i + 2, 1, 1, 8).setValues([row]); return; }
    }
  }
  sh.appendRow(row);
}
```

In `hsbAutoReconcile` vor `return out;` (im `try`): `try { syncStatusSchreiben_(out.mailbox, out); } catch (e3) { console.warn('SYNC_STATUS: ' + e3); }`.

- [ ] **Step 4: Run → PASS**, bündeln (`cp apps_script/HSB_GraphAdapter.gs deploy/HSB_GraphAdapter.js`), alle vier Suiten grün.

- [ ] **Step 5: Commit** — `git commit -m "feat(sales-os): SYNC_STATUS je Postfach nach jedem Abgleich"`

---

### Task 3: Zeilenfarben in `ALL_LEADS` nach Pipeline

**Warum:** Die Pipeline-Spalte steht in BE — außerhalb des Bildschirms. Der Zustand muss an der ganzen Zeile ablesbar sein.

**Files:**
- Modify: `engine/operator_layer/crm_operator_layer.py` (Funktion `pipeline_row_tints()`; bestehende `rng`, `rgb`, `SH` nutzen)
- Test: `tests/test_crm_cockpit.py::test_row_tint_rules`

- [ ] **Step 1: Failing Test**

```python
# tests/test_crm_cockpit.py
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "engine" / "operator_layer"))
from crm_operator_layer import pipeline_row_tints, PIPELINE_COLORS

def test_row_tint_rules():
    reqs = pipeline_row_tints(sheet_id=123, last_row=6425, last_col=57)
    assert len(reqs) == 7
    r0 = reqs[0]["addConditionalFormatRule"]["rule"]
    assert r0["booleanRule"]["condition"]["type"] == "CUSTOM_FORMULA"
    assert r0["booleanRule"]["condition"]["values"][0]["userEnteredValue"] == '=$BE2="Abgemeldet"'
    rng = r0["ranges"][0]
    assert (rng["startColumnIndex"], rng["endColumnIndex"], rng["startRowIndex"]) == (0, 57, 1)
    assert set(PIPELINE_COLORS) == {"Abgemeldet", "Bounce", "Antwort", "Versendet", "Entwurf", "Freigegeben", "Neu"}
```

- [ ] **Step 2: Run → FAIL** (`ImportError: pipeline_row_tints`)

- [ ] **Step 3: Implementieren** (in `crm_operator_layer.py`, als reine Funktion — kein Netz beim Import)

```python
PIPELINE_COLORS = {  # (Hintergrund, Text) - identisch mit Cockpit-Tabs und Dashboard
    "Abgemeldet": ("F4C7C3", "7A1F1A"), "Bounce": ("FCE8B2", "7A4B00"), "Antwort": ("FFF2CC", "5C4A00"),
    "Versendet": ("D9EAD3", "274E13"), "Entwurf": ("DEEAF6", "1F3A5F"), "Freigegeben": ("CFE2F3", "0B3D91"),
    "Neu": ("EFEFEF", "444444"),
}

def pipeline_row_tints(sheet_id, last_row, last_col):
    """Ganze Zeile einfaerben nach BE (Pipeline). Reihenfolge = Prioritaet (Abgemeldet zuerst)."""
    reqs = []
    for i, (state, (bg, fg)) in enumerate(PIPELINE_COLORS.items()):
        reqs.append({"addConditionalFormatRule": {"index": i, "rule": {
            "ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": last_row,
                        "startColumnIndex": 0, "endColumnIndex": last_col}],
            "booleanRule": {"condition": {"type": "CUSTOM_FORMULA",
                                          "values": [{"userEnteredValue": f'=$BE2="{state}"'}]},
                            "format": {"backgroundColor": rgb(bg), "textFormat": {"foregroundColor": rgb(fg)}}}}}})
    return reqs
```

Idempotenz: vor dem Anfügen alle bestehenden Regeln löschen, deren Formel mit `=$BE2=` beginnt (`deleteConditionalFormatRule` von hinten nach vorn), dann `pipeline_row_tints` anfügen. Bestehende 21 Regeln bleiben.

- [ ] **Step 4: Run → PASS**; Dry-Run ausführen (`python3 engine/operator_layer/crm_operator_layer.py --dry-run` druckt die Requests), dann `--apply` (Profil `cherinodiaz`), dann `crm_analyze.py`: „conditionalFormats: 28, davon 7 Zeilentönungen".

- [ ] **Step 5: Commit** — `git commit -m "feat(sales-os): Zeilenfarben in ALL_LEADS nach Pipeline"`

---

### Task 4: Cockpit-Tabs `HEUTE JOEL` / `HEUTE JORDI`

**Warum:** Ein Tab pro Person, fünf Blöcke untereinander, jeder Block eine QUERY mit sechs Spalten. Kein Filter, kein Scrollen nach rechts. Blocküberschrift trägt die Zählung.

**Files:**
- Create: `engine/operator_layer/crm_cockpit.py`
- Test: `tests/test_crm_cockpit.py`

**Interfaces:**
- Produces: `cockpit_blocks(owner_match: str) -> list[dict]` mit `title`, `color`, `formula`; `build_cockpit_requests(sheet_id, owner_match, mailbox) -> list[dict]` (batchUpdate); CLI `python3 engine/operator_layer/crm_cockpit.py [--apply]`.

- [ ] **Step 1: Failing Test**

```python
from crm_cockpit import cockpit_blocks, BLOCK_COLS

def test_cockpit_blocks_joel():
    b = cockpit_blocks("Joel")
    assert [x["title"] for x in b] == ["🔴 Abgemeldet", "🟡 Antworten offen", "🟠 Bounce", "🟢 Versendet (letzte 7 Tage)", "🔵 Heute dran (freigegeben / Entwurf)"]
    assert all("AA contains 'Joel'" in x["formula"] for x in b)
    assert "BE = 'Abgemeldet'" in b[0]["formula"]
    assert "AP >= date '" in b[3]["formula"]
    assert BLOCK_COLS == "B, G, I, BE, AP, AR, AC"
```

- [ ] **Step 2: Run → FAIL**

- [ ] **Step 3: Implementieren**

```python
#!/usr/bin/env python3
"""Baut die Cockpit-Tabs HEUTE JOEL / HEUTE JORDI: fuenf QUERY-Bloecke, Farben, Zaehler, Sync-Anker."""
import sys, datetime
from crm_common import services, SID, col
from crm_operator_layer import PIPELINE_COLORS, rgb

BLOCK_COLS = "B, G, I, BE, AP, AR, AC"   # Firma, Ansprechpartner, E-Mail, Pipeline, Send_Datum, Reply_Status, Notizen
HEADER_LABELS = ["Firma", "Ansprechpartner", "E-Mail", "Pipeline", "Versendet am", "Antwort", "Notizen"]

def q(where, order=""):
    return f"=IFERROR(QUERY(ALL_LEADS!A2:BE; \"select {BLOCK_COLS} where {where}{(' order by ' + order) if order else ''}\"; 0); \"— keine —\")"

def cockpit_blocks(owner_match):
    own = f"AA contains '{owner_match}'"
    seven = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    return [
        {"title": "🔴 Abgemeldet",  "color": PIPELINE_COLORS["Abgemeldet"],  "formula": q(f"{own} and BE = 'Abgemeldet'", "BC desc")},
        {"title": "🟡 Antworten offen", "color": PIPELINE_COLORS["Antwort"], "formula": q(f"{own} and BE = 'Antwort' and R is null", "BC desc")},
        {"title": "🟠 Bounce", "color": PIPELINE_COLORS["Bounce"], "formula": q(f"{own} and BE = 'Bounce'", "AP desc")},
        {"title": "🟢 Versendet (letzte 7 Tage)", "color": PIPELINE_COLORS["Versendet"], "formula": q(f"{own} and BE = 'Versendet' and AP >= date '{seven}'", "AP desc")},
        {"title": "🔵 Heute dran (freigegeben / Entwurf)", "color": PIPELINE_COLORS["Freigegeben"], "formula": q(f"{own} and (BE = 'Freigegeben' or BE = 'Entwurf')", "F, B")},
    ]

def count_formula(owner_match, state):
    return f'=COUNTIFS(ALL_LEADS!AA2:AA; "*{owner_match}*"; ALL_LEADS!BE2:BE; "{state}")'

def cockpit_values(owner_match, mailbox):
    """Zellinhalte des Tabs (Zeilenlisten). Jeder Block: Titelzeile (mit Zaehler), Kopfzeile, QUERY, 40 Zeilen Platz."""
    rows = [[f"HEUTE — {owner_match.upper()}", "", "", "", "", "", ""],
            [f'=IFERROR("Postfach " & VLOOKUP("{mailbox}"; SYNC_STATUS!A:H; 1; FALSE) & " · zuletzt abgeglichen " & TEXT(VLOOKUP("{mailbox}"; SYNC_STATUS!A:H; 2; FALSE); "dd.mm. hh:mm") & " UTC"; "Abgleich noch nicht gelaufen")'],
            []]
    states = ["Abgemeldet", "Antwort", "Bounce", "Versendet", None]
    for blk, state in zip(cockpit_blocks(owner_match), states):
        cnt = count_formula(owner_match, state) if state else f'=COUNTIFS(ALL_LEADS!AA2:AA; "*{owner_match}*"; ALL_LEADS!BE2:BE; "Freigegeben")+COUNTIFS(ALL_LEADS!AA2:AA; "*{owner_match}*"; ALL_LEADS!BE2:BE; "Entwurf")'
        rows.append([blk["title"], cnt]); rows.append(HEADER_LABELS); rows.append([blk["formula"]])
        rows.extend([[]] * 40)
    return rows

def build_cockpit_requests(sheet_id, owner_match, mailbox):
    """Formatierung: Titelzeilen farbig, Kopfzeilen fett, Spaltenbreiten, Zeile 1 fixiert, CLIP."""
    reqs = [{"updateSheetProperties": {"properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}}, "fields": "gridProperties.frozenRowCount"}},
            {"repeatCell": {"range": {"sheetId": sheet_id}, "cell": {"userEnteredFormat": {"wrapStrategy": "CLIP"}}, "fields": "userEnteredFormat.wrapStrategy"}}]
    widths = [220, 180, 220, 110, 110, 110, 300]
    for i, w in enumerate(widths):
        reqs.append({"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1}, "properties": {"pixelSize": w}, "fields": "pixelSize"}})
    r = 3
    for blk in cockpit_blocks(owner_match):
        bg, fg = blk["color"]
        reqs.append({"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": r, "endRowIndex": r + 1, "startColumnIndex": 0, "endColumnIndex": 7},
                     "cell": {"userEnteredFormat": {"backgroundColor": rgb(bg), "textFormat": {"bold": True, "fontSize": 12, "foregroundColor": rgb(fg)}}},
                     "fields": "userEnteredFormat(backgroundColor,textFormat)"}})
        reqs.append({"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": r + 1, "endRowIndex": r + 2, "startColumnIndex": 0, "endColumnIndex": 7},
                     "cell": {"userEnteredFormat": {"textFormat": {"bold": True}, "backgroundColor": rgb("F8F9FA")}}, "fields": "userEnteredFormat(textFormat,backgroundColor)"}})
        r += 43
    return reqs

TABS = {"HEUTE JOEL": ("Joel", "j-cherino@hsb-boden.de"), "HEUTE JORDI": ("Jordi", "j-post@hsb-boden.de")}

def ensure_tab(sh, title, index):
    meta = sh.spreadsheets().get(spreadsheetId=SID, fields="sheets(properties(sheetId,title))").execute()
    for s in meta["sheets"]:
        if s["properties"]["title"] == title: return s["properties"]["sheetId"]
    res = sh.spreadsheets().batchUpdate(spreadsheetId=SID, body={"requests": [{"addSheet": {"properties": {"title": title, "index": index, "gridProperties": {"rowCount": 260, "columnCount": 8}}}}]}).execute()
    return res["replies"][0]["addSheet"]["properties"]["sheetId"]

def main(apply=False):
    sh, _ = services("cherinodiaz" if apply else "cherinojoel")
    for idx, (title, (owner, mailbox)) in enumerate(TABS.items(), start=1):
        vals = cockpit_values(owner, mailbox)
        if not apply:
            print(f"[DRY-RUN] {title}: {len(vals)} Zeilen, {len(build_cockpit_requests(0, owner, mailbox))} Format-Requests"); continue
        sid = ensure_tab(sh, title, idx)
        sh.spreadsheets().values().clear(spreadsheetId=SID, range=f"'{title}'!A1:H260").execute()
        sh.spreadsheets().values().update(spreadsheetId=SID, range=f"'{title}'!A1", valueInputOption="USER_ENTERED", body={"values": vals}).execute()
        sh.spreadsheets().batchUpdate(spreadsheetId=SID, body={"requests": build_cockpit_requests(sid, owner, mailbox)}).execute()
        print(f"{title}: geschrieben (sheetId {sid})")
    return 0

if __name__ == "__main__":
    sys.exit(main(apply="--apply" in sys.argv))
```

Hinweis QUERY-Datumsvergleich: `AP` (Send_Datum) enthält ISO-Strings **und** Datumswerte (Spec B). Damit `AP >= date '…'` greift, prüft Step 4, wie viele Zeilen Text tragen; sind es mehr als 0, wird der Block auf `AP is not null` mit `order by AP desc limit 60` umgestellt (kein Datumsvergleich auf Text).

- [ ] **Step 4: Run → PASS**; `python3 engine/operator_layer/crm_cockpit.py` (Dry-Run) → dann `--apply`; im Browser beide Tabs öffnen: Blöcke sichtbar, Zähler stimmen mit Pipeline-Verteilung überein (`crm_analyze.py`).

- [ ] **Step 5: Tab-Reihenfolge und Sichtbarkeit** — `batchUpdate` mit `updateSheetProperties`: `README`(0) `HEUTE JOEL`(1) `HEUTE JORDI`(2) `POSTEINGANG`(3, Task 5) `ALL_LEADS`(4) `DASHBOARD`(5) `VERSAND`(6) `BATCHES`(7); alle anderen `hidden: true` (Ist-Zustand bleibt). In `crm_cockpit.py` als `order_tabs(sh)` ergänzen und in `main` nach den Tabs aufrufen.

- [ ] **Step 6: Commit** — `git commit -m "feat(sales-os): Cockpit-Tabs HEUTE JOEL / HEUTE JORDI"`

---

### Task 5: `POSTEINGANG` — lesbare Ereignisse und lösbare Klärfälle

**Warum:** `INBOUND_EVENTS` ist ein Maschinen-Log. Die Nutzer brauchen: „Was kam heute rein, welche Firma, was ist unklar" — und einen Weg, einen Klärfall mit zwei Klicks zu erledigen.

**Files:**
- Modify: `engine/operator_layer/crm_cockpit.py` (`posteingang_values`, `build_posteingang_requests`)
- Modify: `apps_script/Actions.gs` (`hsbKlaerfaelleAnwenden`), `apps_script/Code.gs` (Menüpunkt)
- Test: `tests/test_crm_cockpit.py`, `tests/test_apps_script.js`

**Interfaces:**
- Consumes: `INBOUND_EVENTS` 12-Spalten-Layout (Task 1); Spalte **M `Zuordnung`** (neu, ab Task 5) — Freitext des Nutzers: eine `Lead-ID` oder `ignorieren`.
- Produces: Menü „HSB Sales OS → ✅ Klärfälle anwenden": liest alle Zeilen mit `Processed=NEEDS_REVIEW` und gefülltem M; `Lead-ID` → `processInboundEvent({event_id: <Event_ID>+'-MANUAL', event_type: <Classification>, lead_id: <M>, email: <From>, message_id: <F>, subject: <E>, mailbox: <C>, details: 'Manuell zugeordnet'})` und setzt J der Ursprungszeile auf `RESOLVED`; `ignorieren` → J = `IGNORED`.

- [ ] **Step 1: Failing Tests**

`tests/test_crm_cockpit.py`:

```python
from crm_cockpit import posteingang_values

def test_posteingang_blocks():
    v = posteingang_values()
    titles = [r[0] for r in v if r and str(r[0]).startswith(("⚠️", "📥"))]
    assert titles == ["⚠️ Klärfälle — bitte in INBOUND_EVENTS Spalte M eine Lead-ID oder „ignorieren" eintragen", "📥 Letzte 200 Ereignisse"]
    f = [r[0] for r in v if r and str(r[0]).startswith("=IFERROR(QUERY(INBOUND_EVENTS")]
    assert "J = 'NEEDS_REVIEW'" in f[0] and "order by B desc" in f[0]
    assert "limit 200" in f[1]
```

`tests/test_apps_script.js` (in `testInboundEvents`, Ende):

```js
  // 6. Klaerfall per Spalte M loesen
  const evt = SHEETS.INBOUND_EVENTS._data;
  const klaer = evt.filter(function (r) { return r[9] === 'NEEDS_REVIEW'; })[0];
  klaer[12] = lead1.Lead_ID;            // Spalte M: Zuordnung
  const resK = ctx.hsbKlaerfaelleAnwenden();
  check('Klaerfall: Zeile mit Lead-ID in M wird angewendet', resK.applied === 1, JSON.stringify(resK));
  check('Klaerfall: Ursprungszeile steht auf RESOLVED', klaer[9] === 'RESOLVED');
  check('Klaerfall: neues Ereignis mit Suffix -MANUAL ist PROCESSED',
        evt.some(function (r) { return r[0] === klaer[0] + '-MANUAL' && r[9] === 'PROCESSED'; }));
```

- [ ] **Step 2: Run → FAIL**

- [ ] **Step 3: Implementieren**

`crm_cockpit.py`:

```python
EV_COLS = "B, H, G, D, E, J, K"   # Zeit, Typ, Lead-ID, Absender, Betreff, Status, Notiz
EV_LABELS = ["Zeit (UTC)", "Typ", "Lead-ID", "Absender", "Betreff", "Status", "Notiz"]

def posteingang_values():
    rows = [["POSTEINGANG — beide Postfächer", "", "", "", "", "", ""],
            ['=IFERROR("Joel zuletzt " & TEXT(VLOOKUP("j-cherino@hsb-boden.de"; SYNC_STATUS!A:H; 2; FALSE); "dd.mm. hh:mm") & " · Jordi zuletzt " & TEXT(VLOOKUP("j-post@hsb-boden.de"; SYNC_STATUS!A:H; 2; FALSE); "dd.mm. hh:mm"); "Abgleich noch nicht gelaufen")'],
            [],
            ["⚠️ Klärfälle — bitte in INBOUND_EVENTS Spalte M eine Lead-ID oder „ignorieren" eintragen", "=COUNTIF(INBOUND_EVENTS!J2:J; \"NEEDS_REVIEW\")"],
            EV_LABELS,
            [f"=IFERROR(QUERY(INBOUND_EVENTS!A2:M; \"select {EV_COLS} where J = 'NEEDS_REVIEW' order by B desc\"; 0); \"— keine —\")"]]
    rows.extend([[]] * 60)
    rows += [["📥 Letzte 200 Ereignisse", ""], EV_LABELS,
             [f"=IFERROR(QUERY(INBOUND_EVENTS!A2:M; \"select {EV_COLS} where A is not null order by B desc limit 200\"; 0); \"— keine —\")"]]
    return rows
```

Formatierung analog Task 4 (`build_posteingang_requests`): Titelzeile Klärfälle in `F4C7C3`, Ereignisse in `F8F9FA`; bedingte Formatierung auf Spalte B (Typ) mit den Farben: `OPT_OUT`→Abgemeldet, `HARD_BOUNCE`/`SOFT_BOUNCE`→Bounce, `REPLY`/`POSITIVE_REPLY`→Antwort, `SENT`→Versendet. In `INBOUND_EVENTS` Header `M1="Zuordnung"` setzen (nur wenn leer) und Datenvalidierung auf M2:M (nicht strikt, Vorschlag `ignorieren`).

`apps_script/Actions.gs`:

```js
/** Klaerfaelle aus INBOUND_EVENTS anwenden: Spalte M traegt eine Lead-ID oder "ignorieren". */
function hsbKlaerfaelleAnwenden() {
  const sh = sheet_(CFG.SHEET_EVENTS);
  const n = sh.getLastRow();
  const out = { ok: true, applied: 0, ignored: 0, errors: [] };
  if (n < 2) return out;
  const vals = sh.getRange(2, 1, n - 1, 13).getValues();
  for (let i = 0; i < vals.length; i++) {
    const r = vals[i];
    const entscheidung = String(r[12] || '').trim();
    if (String(r[9]) !== 'NEEDS_REVIEW' || !entscheidung) continue;
    if (entscheidung.toLowerCase() === 'ignorieren') {
      sh.getRange(i + 2, 10).setValue('IGNORED'); out.ignored++; continue;
    }
    try {
      const res = processInboundEvent({
        event_id: String(r[0]) + '-MANUAL', event_type: String(r[7]), lead_id: entscheidung,
        email: String(r[3] || ''), message_id: String(r[5] || ''), subject: String(r[4] || ''),
        mailbox: String(r[2] || ''), details: 'Manuell zugeordnet (Klaerfall)'
      });
      if (res && res.matched) { sh.getRange(i + 2, 10).setValue('RESOLVED'); out.applied++; }
      else out.errors.push(String(r[0]) + ': Lead-ID ' + entscheidung + ' nicht gefunden');
    } catch (e) { out.errors.push(String(r[0]) + ': ' + String(e.message || e)); }
  }
  out.ok = out.errors.length === 0;
  return out;
}

function uiKlaerfaelleAnwenden() {
  const ui = SpreadsheetApp.getUi();
  const r = hsbKlaerfaelleAnwenden();
  ui.alert('Klaerfaelle angewendet', 'Zugeordnet: ' + r.applied + '\nIgnoriert: ' + r.ignored +
           (r.errors.length ? ('\n\nFehler:\n' + r.errors.join('\n')) : ''), ui.ButtonSet.OK);
  return r;
}
```

`apps_script/Code.gs` (`onOpen`): nach „🔄 Jetzt abgleichen" → `.addItem('✅ Klärfälle anwenden (Spalte M in INBOUND_EVENTS)', 'uiKlaerfaelleAnwenden')`. Der Test-Stub `makeSheet` liefert `getRange(...).setValue` bereits über `makeRange`; falls nicht, in `makeRange` ergänzen: `setValue: function (v) { sh._data[r-1][c-1] = v; return this; }`.

- [ ] **Step 4: Run → PASS**, bündeln, alle vier Suiten grün; `crm_cockpit.py --apply` → Tab `POSTEINGANG` im Browser prüfen: Klärfälle oben (erwartet u. a. `nora.rudisch@atp.ag` POSITIVE_REPLY, zwei `mailer-daemon`-Bounces), Ereignisliste darunter.

- [ ] **Step 5: Commit** — `git commit -m "feat(sales-os): POSTEINGANG-Tab und Klaerfall-Loesung ueber Spalte M"`

---

### Task 6: `DASHBOARD` — richtige Zahlen, Trend, Abgleich-Anker

**Files:**
- Create: `engine/operator_layer/crm_dashboard.py`
- Test: `tests/test_crm_cockpit.py::test_dashboard_formulas`

- [ ] **Step 1: Failing Test**

```python
from crm_dashboard import dashboard_rows

def test_dashboard_formulas():
    rows = {r[0]: r for r in dashboard_rows() if r}
    assert rows["Abgemeldet (Opt-out)"][1] == '=COUNTIF(ALL_LEADS!Y2:Y; "yes")'
    assert rows["Bounces"][1] == '=COUNTIF(ALL_LEADS!BE2:BE; "Bounce")'
    assert rows["Antworten offen"][1] == '=COUNTIFS(ALL_LEADS!BE2:BE; "Antwort"; ALL_LEADS!R2:R; "")'
    assert rows["Klärfälle offen"][1] == '=COUNTIF(INBOUND_EVENTS!J2:J; "NEEDS_REVIEW")'
    assert rows["Versendet letzte 30 Tage"][1].startswith("=SPARKLINE(")
```

- [ ] **Step 2: Run → FAIL**

- [ ] **Step 3: Implementieren**

```python
#!/usr/bin/env python3
"""Ersetzt den Kennzahlenblock (Zeilen 3-11) des DASHBOARD und ergaenzt Trend + Abgleich-Anker. Idempotent."""
import sys
from crm_common import services, SID

def per_owner(f_all, f_owner):
    return [f_all, f_owner.format(o="Jordi"), f_owner.format(o="Joel")]

def dashboard_rows():
    R = lambda label, f_all, f_owner, ziel: [label] + per_owner(f_all, f_owner) + [ziel]
    return [
        ["HSB SALES OS · VERTRIEBS-COCKPIT"], [],
        ["Kennzahl", "Gesamt", "Jordi Post", "Joel Cherino Diaz", "Bedeutung"],
        R("Kontakte gesamt", '=COUNTA(ALL_LEADS!A2:A)', '=COUNTIF(ALL_LEADS!AA2:AA; "*{o}*")', "Datenbank"),
        R("Versendet", '=COUNTIF(ALL_LEADS!AO2:AO; "sent")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*{o}*"; ALL_LEADS!AO2:AO; "sent")', "automatisch aus Gesendete Elemente"),
        R("Antworten offen", '=COUNTIFS(ALL_LEADS!BE2:BE; "Antwort"; ALL_LEADS!R2:R; "")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*{o}*"; ALL_LEADS!BE2:BE; "Antwort"; ALL_LEADS!R2:R; "")', "ohne Follow-up-Datum"),
        R("Abgemeldet (Opt-out)", '=COUNTIF(ALL_LEADS!Y2:Y; "yes")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*{o}*"; ALL_LEADS!Y2:Y; "yes")', "dauerhaft gesperrt"),
        R("Bounces", '=COUNTIF(ALL_LEADS!BE2:BE; "Bounce")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*{o}*"; ALL_LEADS!BE2:BE; "Bounce")', "unzustellbar"),
        R("Freigegeben, noch nicht versendet", '=COUNTIF(ALL_LEADS!BE2:BE; "Freigegeben")+COUNTIF(ALL_LEADS!BE2:BE; "Entwurf")', '=COUNTIFS(ALL_LEADS!AA2:AA; "*{o}*"; ALL_LEADS!BE2:BE; "Freigegeben")+COUNTIFS(ALL_LEADS!AA2:AA; "*{o}*"; ALL_LEADS!BE2:BE; "Entwurf")', "naechste Sendungen"),
        ["Klärfälle offen", '=COUNTIF(INBOUND_EVENTS!J2:J; "NEEDS_REVIEW")',
         '=COUNTIFS(INBOUND_EVENTS!J2:J; "NEEDS_REVIEW"; INBOUND_EVENTS!C2:C; "j-post@hsb-boden.de")',
         '=COUNTIFS(INBOUND_EVENTS!J2:J; "NEEDS_REVIEW"; INBOUND_EVENTS!C2:C; "j-cherino@hsb-boden.de")', "im Tab POSTEINGANG loesen"],
        [],
        ["Versendet letzte 30 Tage", '=SPARKLINE(ARRAYFORMULA(COUNTIF(LEFT(ALL_LEADS!AP2:AP; 10); TEXT(SEQUENCE(30; 1; TODAY()-29; 1); "yyyy-mm-dd"))); {"charttype"\\;"column"})', "", "", "Tage links = älter"],
        ["Letzter Abgleich Joel", '=IFERROR(TEXT(VLOOKUP("j-cherino@hsb-boden.de"; SYNC_STATUS!A:H; 2; FALSE); "dd.mm.yyyy hh:mm") & " UTC"; "noch nicht")', "", "", "alle 15 Minuten"],
        ["Letzter Abgleich Jordi", '=IFERROR(TEXT(VLOOKUP("j-post@hsb-boden.de"; SYNC_STATUS!A:H; 2; FALSE); "dd.mm.yyyy hh:mm") & " UTC"; "noch nicht")', "", "", "alle 15 Minuten"],
    ]

def main(apply=False):
    sh, _ = services("cherinodiaz" if apply else "cherinojoel")
    rows = dashboard_rows()
    if not apply:
        print(f"[DRY-RUN] DASHBOARD!A1:E{len(rows)} wuerde {len(rows)} Zeilen erhalten"); return 0
    sh.spreadsheets().values().update(spreadsheetId=SID, range=f"DASHBOARD!A1:E{len(rows)}", valueInputOption="USER_ENTERED", body={"values": rows}).execute()
    print("DASHBOARD geschrieben."); return 0

if __name__ == "__main__":
    sys.exit(main(apply="--apply" in sys.argv))
```

Vor dem Apply prüfen (Step 4), dass der Batch-Block „ERZEUGTE BATCHES (Letzte 10)" unterhalb von Zeile 15 beginnt; sonst `rows` mit Leerzeilen auffüllen, damit nichts überschrieben wird. Die Klärfälle-Zeile bekommt pro Person die Zählung nach `INBOUND_EVENTS!C` (Mailbox) — erst sinnvoll nach Task 1 (Mailbox gefüllt).

- [ ] **Step 4: Run → PASS**; Dry-Run, Apply, Browser: Zahlen plausibel gegen `crm_analyze.py` (Versendet = `Send_Status=sent`, Bounces = Pipeline Bounce).

- [ ] **Step 5: Commit** — `git commit -m "feat(sales-os): DASHBOARD mit Opt-out/Bounce/Klaerfall-Zahlen, 30-Tage-Trend, Abgleich-Anker"`

---

### Task 7: README-Tab, Betriebsdoku, End-to-End-Nachweis

**Files:**
- Modify: README-Tab (per `crm_cockpit.py readme_values()`), `README_OPERATING.md`, `CHECKPOINT_STATE.json`, `SESSION_LOG.md`, `~/KI-System/ObsidianVault/brain/CURRENT_HANDOFF.md`

- [ ] **Step 1: README-Tab „Schnellstart" ersetzen** (Zeilen 14–19) durch:

```
1. Dein Tab öffnen        HEUTE JOEL bzw. HEUTE JORDI – alles Wichtige auf einer Seite, oben steht, wann dein Postfach zuletzt abgeglichen wurde.
2. Rot = Abgemeldet       Diese Firmen werden nie wieder angeschrieben. Automatisch gesperrt (auch bei "Abmelden" von einer Kollegenadresse derselben Firma).
3. Gelb = Antwort offen   Antworten, zu denen noch kein Follow-up-Datum (Spalte R in ALL_LEADS) steht.
4. Grün = Versendet       Kommt automatisch aus deinem Ordner "Gesendete Elemente" (alle 15 Minuten). Nichts bestätigen.
5. Unklare Fälle          Tab POSTEINGANG, Block "Klärfälle": in INBOUND_EVENTS Spalte M eine Lead-ID oder "ignorieren" eintragen, dann Menü HSB Sales OS → Klärfälle anwenden.
6. Neue Entwürfe          Seitenleiste öffnen (Menü HSB Sales OS → Seitenleiste öffnen), wie bisher.
```

- [ ] **Step 2: `README_OPERATING.md`** — Abschnitt „Auto-Abgleich" um „Cockpit-Tabs", „Domain-Abmeldung", „Klärfälle lösen", „SYNC_STATUS" ergänzen; Graph-Anleitung (Admin-Zustimmung) entfernen.

- [ ] **Step 3: End-to-End-Nachweis (ohne Test-Lead im Sheet)** — mit Owner-Freigabe eine echte Testmail von `j-cherino` an eine eigene, als Lead vorhandene Adresse; nach dem nächsten Trigger-Lauf: `HEUTE JOEL` zeigt die Zeile grün; Antwort „Abmelden" von einer Kollegenadresse derselben Domain → Zeile rot, `DASHBOARD` „Abgemeldet" +1, `POSTEINGANG` zeigt `OPT_OUT PROCESSED` mit „Domain-Abmeldung". Ausgabe von `crm_analyze.py` vor/nach in den Report.

- [ ] **Step 4: Report** `~/KI-System/08_System/reports/validation/2026-09-17-hsb-crm-cockpit.md` (Zählungen, Screenshots-Pfade, Testfall-Ergebnisse), `CHECKPOINT_STATE.json`, `SESSION_LOG.md`, `CURRENT_HANDOFF.md`, `~/KI-System/tools/handoff.sh write "Claude Code" "…" "…"`.

- [ ] **Step 5: Commit** — `git commit -m "docs(sales-os): Cockpit-Betrieb, README-Tab, E2E-Nachweis"`

---

## Empfehlungen außerhalb dieses Plans (Ausbaustufen, jeweils kostenfrei)
1. **Follow-up-Disziplin:** Block „🟡 Antworten offen" lebt von Spalte R (Follow-up-Datum). Wer eine Antwort bearbeitet hat, trägt ein Datum ein — dann verschwindet die Zeile. Ein späterer Block „⏰ Wiedervorlage fällig" (`R <= today()`) ist eine Zeile QUERY.
2. **Abmelde-Link** in der Signatur (`mailto:j-cherino@hsb-boden.de?subject=Abmelden`) — läuft über denselben Opt-out-Pfad, kein neuer Code.
3. **AppSheet** (in Google Workspace enthalten) als Handy-Ansicht auf `HEUTE *` und `POSTEINGANG` — Spec `docs/appsheet/` existiert bereits.
4. **Sende-Fenster:** Der Abgleich liest die letzten 100 Nachrichten je Ordner je Lauf. Bei mehr als 100 Sendungen innerhalb von 15 Minuten würde ein Teil erst über den Rückabgleich (`engine/reconcile_cloud_mailbox.py`) erfasst — Grenze in `README_OPERATING.md` festhalten, `top` bei Bedarf auf 250 setzen.

## Self-Review
- **Spec-Abdeckung:** Ziel 1 (lesbar) → Task 3/4; Ziel 2 (Pipeline sichtbar) → Task 3/4/6; Ziel 3 (Statuswechsel automatisch, mit Beleg) → Task 1/2/5 (Beleg lesbar) — Versand/Antwort/Abmeldung/Bounce selbst laufen bereits (Commits `d13455c`, `b9fe6c9`); Ziel 4 (Header unverändert) → Global Constraints; Ziel 5 (kostenfrei, kein zweiter Speicher) → nur Sheet-Tabs und Formeln.
- **Platzhalter:** keine „TBD"; jeder Code-Schritt trägt Code. Die Klärfälle-pro-Person-Zeile in Task 6 ist bewusst erst nach Task 1 aktiv (Mailbox-Spalte).
- **Typkonsistenz:** `PIPELINE_COLORS` (Task 3) wird in Task 4/5 importiert; `SYNC_STATUS` Spalten A/B (Task 2) werden in Task 4/5/6 per `VLOOKUP(...; 2; FALSE)` gelesen; `INBOUND_EVENTS` J=Processed, M=Zuordnung (Task 1/5) überall gleich; `processInboundEvent` bekommt `mailbox` in Task 1 und wird in Task 5 mit `mailbox` aufgerufen.
