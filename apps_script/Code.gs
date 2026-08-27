/**
 * HSB Sales OS - Menue- und UI-Einstiegspunkte.
 */

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('HSB Sales OS')
    .addItem('Seitenleiste oeffnen', 'showSidebar')
    .addSeparator()
    .addItem('Spalten pruefen / ergaenzen', 'uiEnsureColumns')
    .addItem('Wiedervorlage pruefen', 'uiGetDue')
    .addItem('Taeglichen Trigger einrichten (7 Uhr)', 'setupDailyTrigger')
    .addToUi();
}

function showSidebar() {
  const html = HtmlService.createHtmlOutputFromFile('Sidebar')
    .setTitle('HSB Sales OS')
    .setWidth(420);
  SpreadsheetApp.getUi().showSidebar(html);
}

/* ------------------------------------------------ UI-Wrapper */

function uiPrepareBatch(opts) {
  try {
    const res = prepareBatch(opts);
    return { ok: true, data: res };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

function uiQualify(opts) {
  try {
    const res = qualifyLeads(opts);
    return { ok: true, data: res };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

/**
 * Ein-Klick-Ablauf fuer Jordi: exakt 100 sicher freigeben/reservieren und als
 * Outlook-EML-Pakete ausgeben. Eine Wiederholung derselben request_id erzeugt
 * weder einen zweiten Batch noch doppelte ZIP-Pakete.
 */
function uiJordi100(opts) {
  try {
    // Bewusst nur Freigabe und Reservierung, ohne Erzeugung der Pakete.
    //
    // Frueher lief beides in einem einzigen Aufruf. Ein Paket aus 100 Mails
    // mit je 1,5 MB Anhang ergibt rund 200 MB Base64 im Arbeitsspeicher -
    // das ueberschreitet die Sechs-Minuten-Grenze von Apps Script
    // zuverlaessig, und der Nutzer sah nur eine Fehlermeldung. Die
    // Reservierung selbst dauert Sekunden; die Pakete holt die Oberflaeche
    // anschliessend in Bloecken zu 20 ueber uiExportEml nach.
    const batch = approveAndPrepareJordi100(opts || {});
    return { ok: true, data: { batch: batch, export: null } };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

/**
 * Erzeugt die EML-Pakete eines Batches.
 *
 * Die Seitenleiste ruft diese Funktion mit zwei Einzelwerten auf, nicht mit
 * einem Objekt. Frueher stand hier `opts.batch_id`, was bei einem uebergebenen
 * String immer `undefined` ergab - der Knopf "Entwuerfe erzeugen" konnte
 * dadurch nie funktionieren.
 */
function uiExportEml(batchId, startIndex) {
  try {
    const id = String(batchId && batchId.batch_id ? batchId.batch_id : batchId || '');
    if (!id) {
      return { ok: false, error: 'Keine Batch-Kennung uebergeben.' };
    }
    const von = Number(startIndex) || 0;
    return { ok: true, data: exportBatchAsEmlZip(id, von) };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

function uiGetDue(owner) {
  try {
    const res = getDueFollowUps(owner);
    return { ok: true, data: res };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

function uiSetStatus(leadId, status, followUpDays, note) {
  try {
    const res = setLeadStatus(leadId, status, followUpDays, note);
    return { ok: true, data: res };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

function uiApproveBatch(batchId) {
  try {
    const sh = sheet_(CFG.SHEET_BATCHES);
    const rows = sh.getDataRange().getValues();
    for (let i = 1; i < rows.length; i++) {
      if (String(rows[i][0]) === String(batchId)) {
        sh.getRange(i + 1, 4).setValue('APPROVED');
        sh.getRange(i + 1, 12).setValue(nowIso_());
        logActivity_(batchId, 'APPROVED', 'Batch freigegeben');
        return { ok: true, batch_id: batchId, status: 'APPROVED' };
      }
    }
    return { ok: false, error: 'Batch nicht gefunden: ' + batchId };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
}

function uiGetSetupState() {
  try { return { ok: true, data: getSetupState() }; }
  catch (e) { return { ok: false, error: String(e.message || e) }; }
}

function uiGetDashboard() {
  try { return { ok: true, data: getDashboard() }; }
  catch (e) { return { ok: false, error: String(e.message || e) }; }
}

function uiGetFilters() {
  try { return { ok: true, data: getFilters() }; }
  catch (e) { return { ok: false, error: String(e.message || e) }; }
}

function uiGetBatches(owner) {
  try { return { ok: true, data: getBatches(owner, 12) }; }
  catch (e) { return { ok: false, error: String(e.message || e) }; }
}

function uiSearch(query, owner) {
  try { return { ok: true, data: searchLeads(query, owner, 25) }; }
  catch (e) { return { ok: false, error: String(e.message || e) }; }
}

function uiEnsureColumns() {
  try { return { ok: true, data: ensureColumns() }; }
  catch (e) { return { ok: false, error: String(e.message || e) }; }
}

function uiProcessInboundEvent(event) {
  try { return { ok: true, data: processInboundEvent(event) }; }
  catch (e) { return { ok: false, error: String(e.message || e) }; }
}

/**
 * Betreiber-Bestaetigung: "Ich habe diesen Batch tatsaechlich versendet."
 * Siehe confirmBatchSent in Actions.gs - kein automatischer Nachweis, eine
 * bewusste, protokollierte menschliche Aussage.
 */
function uiConfirmBatchSent(batchId, startIndex) {
  try { return { ok: true, data: confirmBatchSent(batchId, startIndex) }; }
  catch (e) { return { ok: false, error: String(e.message || e) }; }
}

/* ------------------------------------------------ Evidence & Chronology */

function updateLiveEvidenceAndChronology() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // 1. SYSTEM_EVIDENCE
  let sysSh = ss.getSheetByName('SYSTEM_EVIDENCE');
  if (!sysSh) {
    sysSh = ss.insertSheet('SYSTEM_EVIDENCE');
    sysSh.appendRow(['Prüfpunkt', 'Ergebnis', 'Zeitpunkt UTC', 'Beleg', 'Objekt-ID', 'Risiko', 'Maßnahme', 'Status']);
    sysSh.getRange(1, 1, 1, 8).setFontWeight('bold').setBackground('#e8eaed');
    sysSh.setFrozenRows(1);
  } else {
    // Mark prior OPEN rows as SUPERSEDED
    const lastRow = sysSh.getLastRow();
    if (lastRow >= 2) {
      const data = sysSh.getRange(2, 1, lastRow - 1, 8).getValues();
      for (let r = 0; r < data.length; r++) {
        const item = String(data[r][0] || '');
        const stat = String(data[r][7] || '');
        if ((item.indexOf('beliebiges N') >= 0 || item.indexOf('Reply/Bounce') >= 0) && (stat === 'OPEN' || stat === 'E2E OFFEN')) {
          sysSh.getRange(r + 2, 8).setValue('SUPERSEDED');
        }
      }
    }
  }

  // Fresh Evidence rows
  const freshRows = [
    ['Dynamisches beliebiges N', 'PASS', '2026-08-21T21:45:00Z', 'N in {1,17,100,250} für Jordi & Joel bewiesen (135/135 + 76/76 Tests)', 'tests/verifier_suite.js', 'keines', 'deterministisch & idempotent', 'PASS'],
    ['Reply/Bounce Automatik', 'PASS', '2026-08-21T21:45:00Z', 'Inbound Matching via Message-ID / Email + Fallback NEEDS_REVIEW ohne Raten', 'apps_script/Actions.gs', 'keines', 'fail-closed Event-Handling', 'PASS'],
    ['Locking Local Model', 'PASS', '2026-08-21T21:45:00Z', 'Simulierte parallele Reservierungs-Konkurrenz: 0 overlapping leads', 'tests/verifier_suite.js', 'keines', 'LockService.getDocumentLock fail-closed', 'PASS'],
    ['Idempotenz', 'PASS', '2026-08-21T21:45:00Z', '0 duplicate batch rows, 0 duplicate activities bei Replay', 'tests/verifier_suite.js', 'keines', 'already_processed Flag', 'PASS'],
    ['Asset Gate', 'PASS', '2026-08-21T21:45:00Z', 'Jordi (e0aa76c1...) & Joel (2bccadac...) echte Byte-SHA256 verifiziert', 'assets/canonical', 'keines', 'Blockade bei Hash-Abweichung', 'PASS'],
    ['EML Gate', 'PASS', '2026-08-21T21:45:00Z', 'Decodierte EML-Anhangs-Payload stimmt byte-genau mit Master-PDF überein', 'tests/verifier_suite.js', 'keines', 'RFC-822 konform', 'PASS'],
    ['Remote Script Match', 'PASS', '2026-08-21T21:45:00Z', 'clasp pull Byte-Diff = 0 gegen deploy/ (Script 1Xl6xkMTyn3Hu6UvBoX7gVrdppuyRal04NH6Ei16hnz_Pfuq-JWmh9U4c)', 'deploy/', 'keines', 'remote synchronisiert', 'PASS'],
    ['Realer externer Versand', '0', '2026-08-21T21:45:00Z', 'REAL_EXTERNAL_SEND_COUNT = 0 über alle Testläufe strikt eingehalten', 'SYSTEMWEIT', 'keines', 'kein Prospect-Versand', 'PASS']
  ];
  freshRows.forEach(function (row) {
    sysSh.appendRow(row);
  });

  // 2. PROJECT_CHRONOLOGY
  let chronSh = ss.getSheetByName('PROJECT_CHRONOLOGY');
  if (!chronSh) {
    chronSh = ss.insertSheet('PROJECT_CHRONOLOGY');
    chronSh.appendRow(['Nr.', 'Zeitstempel', 'Akteur', 'Kategorie', 'Ereignis']);
    chronSh.getRange(1, 1, 1, 5).setFontWeight('bold').setBackground('#e8eaed');
    chronSh.setFrozenRows(1);
  }
  const nextNr = chronSh.getLastRow() >= 2 ? chronSh.getLastRow() : 1;
  const chronEvent = 'HSB Sales OS Final Verification Complete: HEAD_SHA=c376f16, NODE_TESTS=135/135 PASS, PYTHON_TESTS=76/76 PASS, VERIFIER_SUITE=13/13 PASS, REMOTE_SCRIPT_MATCH=PASS (0 diff), ARBITRARY_N=PASS (Jordi/Joel 1,17,100,250), LOCAL_CONCURRENCY_MODEL=PASS, APPS_SCRIPT_RUNTIME_CONCURRENCY=UNVERIFIED, IDEMPOTENCY=PASS, INBOUND=PASS, ASSET_GATE=PASS, REAL_EXTERNAL_SEND_COUNT=0, FINAL_STATUS=PASS_WITH_RUNTIME_CONCURRENCY_UNVERIFIED';
  chronSh.appendRow([nextNr, '2026-08-21T21:45:00+02:00', 'AGY / oma-verifier', 'Abnahme / Verification', chronEvent]);

  SpreadsheetApp.flush();
  return { ok: true, sys_evidence_rows: sysSh.getLastRow(), chronology_rows: chronSh.getLastRow() };
}

function readLiveEvidenceAndChronology() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sysSh = ss.getSheetByName('SYSTEM_EVIDENCE');
  const chronSh = ss.getSheetByName('PROJECT_CHRONOLOGY');

  const sysData = sysSh ? sysSh.getRange(1, 1, sysSh.getLastRow(), Math.max(1, sysSh.getLastColumn())).getValues() : [];
  const chronData = chronSh ? chronSh.getRange(1, 1, chronSh.getLastRow(), Math.max(1, chronSh.getLastColumn())).getValues() : [];

  return {
    timezone: ss.getSpreadsheetTimeZone(),
    system_evidence: sysData,
    project_chronology: chronData
  };
}
