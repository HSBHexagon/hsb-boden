# Entscheidung: Kein `HSB_QUEUE_ENGINE.gs` — keine Parallelarchitektur

**Datum:** 2026-09-05
**Status:** Entschieden, nicht umgesetzt.

## Kontext

Ein Dispatch-Text schlug ein neues Apps-Script-Modul `HSB_QUEUE_ENGINE.gs` mit
eigenen Sheet-Tabs (`DRAFT_QUEUE`, `RUN_LOG`, `ASSET_CONFIG`) und einer eigenen
Funktion `pushSelectedToFlow()` vor, die zeilenweise per `UrlFetchApp.fetch`
an einen Power-Automate-Flow sendet.

## Warum abgelehnt

1. **Duplikat der bestehenden Pipeline:** `apps_script/HSB_DraftAdapter.gs.js`
   erledigt exakt dasselbe (Batch -> Flyer-Asset-Gate -> Power-Automate-Flow
   -> Sheet-Rueckschreibung von `Draft_ID`/`Internet_Message_ID`), ist aber
   bereits mit 321/321 (`test_apps_script.js`), 24/24
   (`test_draft_chunking.js`) und 7/7 (`verifier_suite.js`) Tests verifiziert
   und live deployt (Commit fbdb41a, Sync 16:38:35 Uhr).
2. **Der Dispatch-Text widerspricht sich selbst:** Seine eigene Kopfzeile
   fordert "kein neues Versandmodell, kein Auto-Send, keine
   Parallelarchitektur" — `HSB_QUEUE_ENGINE.gs` waere aber genau das.
3. **Produktionsrisiko:** Zwei unabhaengige Schreibpfade auf demselben Sheet
   mit 6.424 echten Kontakten (Tabs `ALL_LEADS`, `JOEL`, `JORDI`) erhoehen das
   Risiko von Race Conditions und widerspruechlichen `Draft_ID`-Eintraegen,
   ohne einen belegten funktionalen Mehrwert gegenueber dem bestehenden
   `uiCreateDraftsChunk`/10er-Chunking zu bieten.
4. **Kein Nachweis eines Luecken-Falls:** Der Dispatch-Text nennt keinen
   konkreten Anwendungsfall, den `HSB_DraftAdapter.gs.js` nicht bereits
   abdeckt.

## Konsequenz

- Es wird **keine neue `.gs`-Datei** und **kein neuer Tab** im Live-Sheet
  angelegt.
- Kuenftige Anfragen nach "Selbstpruefung", "Queue validieren" oder
  "Fehlerjournal" werden stattdessen als Erweiterung der bestehenden
  `RUN_LOG`-aequivalenten Funktion `logActivity_()` und des bestehenden
  `SYSTEM_EVIDENCE`-Tabs geprueft, nicht als neues Modul.
- Falls tatsaechlich ein Luecken-Fall auftritt (z. B. Zeilen-Selektion in der
  Tabelle statt Sidebar-Bedienung), wird das als **Erweiterung** von
  `HSB_DraftAdapter.gs.js` behandelt, nicht als neues System.
